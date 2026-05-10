import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timezone  # using timezone.utc for timezone-aware snapshots
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, TypeAlias

from sqlalchemy import Select, and_, delete, func, or_, select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from sdd_cash_manager.lib.encryption import SensitiveDataCipher
from sdd_cash_manager.lib.security_events import log_account_merge, log_critical_application_error  # New import
from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.account_merge_plan import AccountMergePlan
from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.enums import AccountingCategory, BankingProductType, ReconciliationStatus
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.schemas.transaction_schema import AccountMergePlanRequest

if TYPE_CHECKING:
    from sdd_cash_manager.services.transaction_service import TransactionService

AccountFieldValue: TypeAlias = str | Decimal | float | bool | None  # NOSONAR - TypeAlias needed for 3.10/3.11 compatibility


@dataclass
class AccountBalanceSnapshot:
    timestamp: datetime
    balance: Decimal
    reason: str | None = None


@dataclass(frozen=True)
class AccountQueryCriteria:
    """Structured filters used to build database lookup queries."""

    hidden: bool | None = None
    placeholder: bool | None = None
    search_term: str | None = None

    def build_filters(self) -> list[ColumnElement[Any]]:
        """Translate the criteria into SQLAlchemy expressions."""
        filters = []
        if self.hidden is not None:
            filters.append(Account.hidden == self.hidden)
        if self.placeholder is not None:
            filters.append(Account.placeholder == self.placeholder)
        if self.search_term:
            filters.append(func.lower(Account.name).contains(self.search_term.lower()))
        return filters


class AccountService:
    """Manage accounts using an authoritative SQLAlchemy session and domain helpers."""

    def __init__(self, db_session: Session | None = None, session_factory: Callable[[], Session] | None = None):
        """Initialize the account service.

        Args:
            db_session: Optional SQLAlchemy session used for persistence.
            session_factory: Optional factory for tests that need to open isolated sessions.
        """
        self.db_session = db_session
        self.session_factory = session_factory
        self.accounts: dict[str, Account] = {}
        self._use_db = bool(db_session or session_factory)
        self.balance_history: dict[str, list[AccountBalanceSnapshot]] = {}
        self._cipher = SensitiveDataCipher()
        self._hierarchy_balance_cache: dict[str, Decimal] = {}

    def _acquire_session(self) -> tuple[Session, bool]:
        """Return a session plus a flag indicating whether the caller must close it."""
        try:
            if self.session_factory:
                return self.session_factory(), True
            if self.db_session is None:
                raise ValueError("Database session is required for account operations.")
            return self.db_session, False
        except Exception as e:
            log_critical_application_error(f"Failed to acquire database session: {e}", metadata={"service": "AccountService"})
            raise RuntimeError("Failed to acquire database session due to unexpected error.") from e

    def _record_balance_snapshot(
        self,
        account: Account,
        *,
        reason: str | None = None,
        timestamp: datetime | None = None
    ) -> None:
        """Track the latest balance for an account along with optional metadata."""
        snapshot = AccountBalanceSnapshot(
            timestamp=timestamp or datetime.now(timezone.utc),
            balance=account.available_balance,
            reason=reason
        )
        self.balance_history.setdefault(account.id, []).append(snapshot)

    def record_balance_snapshot(
        self,
        account_id: str,
        *,
        reason: str | None = None,
        timestamp: datetime | None = None
    ) -> None:
        """Expose historical balance tracking to external callers."""
        account = self.get_account(account_id)
        if account is not None:
            self._record_balance_snapshot(account, reason=reason, timestamp=timestamp)

    def _invalidate_hierarchy_cache(self) -> None:
        """Clear the in-memory hierarchy balance cache."""
        self._hierarchy_balance_cache.clear()

    def _calculate_hierarchy_balance_in_memory(self, account_id: str) -> Decimal:
        visited: set[str] = set()

        def _sum_hierarchy(acc_id: str) -> Decimal:
            if acc_id in visited:
                return Decimal("0.0")
            visited.add(acc_id)
            account = self.accounts.get(acc_id)
            if account is None:
                return Decimal("0.0")

            subtotal = account.available_balance
            for child in self.accounts.values():
                if child.parent_account_id == acc_id:
                    subtotal += _sum_hierarchy(child.id)
            return subtotal

        return _sum_hierarchy(account_id)

    def _calculate_hierarchy_balance_from_db(self, account_id: str) -> Decimal:
        session, should_close = self._acquire_session()
        try:
            hierarchy_cte = (
                select(Account.id, Account.available_balance)
                .where(Account.id == account_id)
                .cte(name="account_hierarchy", recursive=True)
            )
            hierarchy_cte = hierarchy_cte.union_all(
                select(Account.id, Account.available_balance)
                .where(Account.parent_account_id == hierarchy_cte.c.id)
            )
            total_query = select(func.coalesce(func.sum(hierarchy_cte.c.available_balance), Decimal("0.0")))
            total = session.scalar(total_query)
            return total or Decimal("0.0")
        except Exception as e:
            log_critical_application_error(f"Failed to calculate hierarchy balance for account {account_id}: {e}", account_id=account_id, metadata={"service": "AccountService"})
            raise RuntimeError(f"Failed to calculate hierarchy balance for account {account_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def _should_encrypt_notes(self) -> bool:
        """Return True when notes should be encrypted before persistence."""
        return self._use_db

    def _encrypt_notes(self, value: str | None) -> str | None:
        """Encrypt the provided notes when storage encryption is enabled."""
        if value is None or not self._should_encrypt_notes():
            return value
        return self._cipher.encrypt(value)

    def decrypt_notes(self, encrypted_value: str | None) -> str | None:
        """Decrypt persisted notes, returning the plaintext fallback when decryption fails."""
        if encrypted_value is None:
            return None
        if not self._should_encrypt_notes():
            return encrypted_value
        try:
            return self._cipher.decrypt(encrypted_value)
        except ValueError:
            return encrypted_value


    @staticmethod
    def _validate_currency(currency: str) -> str:
        if len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            raise ValueError("Currency must be a 3-letter uppercase ISO 4217 code.")
        return currency

    @staticmethod
    def _validate_enum(value: Enum | str, enum_cls: type[Enum], field_name: str) -> str:
        if isinstance(value, Enum):
            return str(value.value)

        normalized_value = str(value).strip()
        if not normalized_value:
            raise ValueError(f"{field_name} cannot be empty.")

        normalized_value_fold = normalized_value.casefold()

        for member_name, member in enum_cls.__members__.items():
            if normalized_value_fold == member_name.casefold():
                return str(member.value)

        for member in enum_cls.__members__.values():
            if normalized_value_fold == str(member.value).casefold():
                return str(member.value)

        raise ValueError(f"Invalid {field_name} '{value}'.")

    @staticmethod
    def _validate_string_field(
        value: str,
        field_name: str,
        min_length: int = 1,
        max_length: int | None = None,
        allowed_chars_regex: str | None = None,
        forbidden_chars_regex: str | None = r"[<>;]" # Default forbidden chars from spec
    ) -> str:
        import re  # Import regex

        stripped_value = value.strip()
        if len(stripped_value) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters long.")
        if max_length is not None and len(stripped_value) > max_length:
            raise ValueError(f"{field_name} cannot exceed {max_length} characters.")

        if forbidden_chars_regex and re.search(forbidden_chars_regex, stripped_value):
            raise ValueError(f"{field_name} contains forbidden characters: {forbidden_chars_regex}")

        if allowed_chars_regex and not re.fullmatch(allowed_chars_regex, stripped_value):
            raise ValueError(f"{field_name} contains invalid characters. Allowed pattern: {allowed_chars_regex}")

        return stripped_value

    @staticmethod
    def _quantize_value(value: AccountFieldValue) -> Decimal | None: # Changed return type
        if value is None:
            return None
        # Ensure Decimal is used for quantization
        return quantize_currency(Decimal(str(value))) # Cast to Decimal before quantizing

    def _get_update_handlers(self, account: Account) -> dict[str, Callable[[AccountFieldValue], None]]:
        return {
            "currency": lambda value: self._update_currency(account, value),
            "accounting_category": lambda value: self._update_accounting_category(account, value),
            "banking_product_type": lambda value: self._update_banking_product_type(account, value),
            "available_balance": lambda value: self._update_available_balance(account, value),
            "credit_limit": lambda value: self._update_credit_limit(account, value),
            "name": lambda value: self._update_name(account, value),
            "account_number": lambda value: self._update_account_number(account, value),
            "parent_account_id": lambda value: self._update_parent_account_id(account, value),
            "notes": lambda value: self._update_notes(account, value),
            "hidden": lambda value: self._update_hidden(account, value),
            "placeholder": lambda value: self._update_placeholder(account, value),
        }

    def _apply_updates(self, account: Account, updates: dict[str, AccountFieldValue]) -> None:
        """Apply validated handlers to updateable account attributes."""
        handlers = self._get_update_handlers(account)
        for key, value in updates.items():
            handler = handlers.get(key)
            if handler is None:
                raise ValueError(f"Cannot update unsupported field '{key}'.")
            handler(value)

    def _update_currency(self, account: Account, value: AccountFieldValue) -> None:
        if value is None:
            raise ValueError("currency cannot be null.")
        account.currency = self._validate_currency(str(value))

    def _update_accounting_category(self, account: Account, value: AccountFieldValue) -> None:
        if value is None:
            raise ValueError("accounting_category cannot be null.")
        account.accounting_category = self._validate_enum(
            str(value),
            AccountingCategory,
            "accounting_category"
        )

    def _update_banking_product_type(self, account: Account, value: AccountFieldValue) -> None:
        if value is None:
            account.banking_product_type = None
        else:
            account.banking_product_type = self._validate_enum(
                str(value),
                BankingProductType,
                "banking_product_type"
            )

    def _update_available_balance(self, account: Account, value: AccountFieldValue) -> None:
        quantized = self._quantize_value(value)
        if quantized is None:
            raise ValueError("available_balance cannot be null.")
        account.available_balance = quantized
        self._record_balance_snapshot(account)

    def _update_credit_limit(self, account: Account, value: AccountFieldValue) -> None:
        account.credit_limit = self._quantize_value(value)

    def _update_name(self, account: Account, value: AccountFieldValue) -> None:
        if value is None:
            raise ValueError("name cannot be null.")
        account.name = self._validate_string_field(str(value), "name", max_length=100, allowed_chars_regex=r"^[a-zA-Z0-9\s.,\-_()&']+$")

    def _update_account_number(self, account: Account, value: AccountFieldValue) -> None:
        account.account_number = self._validate_string_field(str(value), "account_number", max_length=50, allowed_chars_regex=r"^[a-zA-Z0-9\-]+$") if value is not None else None

    def _update_parent_account_id(self, account: Account, value: AccountFieldValue) -> None:
        account.parent_account_id = str(value) if value is not None else None

    def _update_notes(self, account: Account, value: AccountFieldValue) -> None:
        account.notes = self._encrypt_notes(self._validate_string_field(str(value), "notes", max_length=500, forbidden_chars_regex=r"[<>;]")) if value is not None else None

    def _update_hidden(self, account: Account, value: AccountFieldValue) -> None:
        if not isinstance(value, bool):
            raise ValueError("hidden must be a boolean value.")
        account.hidden = value

    def _update_placeholder(self, account: Account, value: AccountFieldValue) -> None:
        if not isinstance(value, bool):
            raise ValueError("placeholder must be a boolean value.")
        account.placeholder = value

    def create_account(
        self,
        name: str,
        currency: str,
        accounting_category: str,
        account_number: str | None = None,
        banking_product_type: str | None = None,
        available_balance: AccountFieldValue = Decimal("0.0"),
        credit_limit: AccountFieldValue = None,
        notes: str | None = None,
        parent_account_id: str | None = None,
        hidden: bool = False,
        placeholder: bool = False,
        id: str | None = None # NEW OPTIONAL PARAMETER
    ) -> Account:
        """Create and persist a new account with validated metadata and quantized balances."""
        if not name or not currency or not accounting_category:
            raise ValueError("Name, currency, and accounting category are required.")

        validated_currency = self._validate_currency(currency)
        validated_category = self._validate_enum(accounting_category, AccountingCategory, "accounting_category")
        validated_banking_type = None
        if banking_product_type is not None:
            validated_banking_type = self._validate_enum(
                banking_product_type,
                BankingProductType,
                "banking_product_type"
            )

        quantized_available_balance = self._quantize_value(available_balance)
        if quantized_available_balance is None:
            quantized_available_balance = Decimal("0.0")

        # Use provided ID or generate a new one
        account_id_to_use = id if id is not None else str(uuid.uuid4()) # Use new parameter

        account = Account(
            name=name,
            currency=validated_currency,
            accounting_category=validated_category,
            id=account_id_to_use, # Pass the chosen ID
            account_number=account_number,
            banking_product_type=validated_banking_type,
            available_balance=quantized_available_balance,
            credit_limit=self._quantize_value(credit_limit),
            notes=self._encrypt_notes(notes),
            parent_account_id=parent_account_id,
            hidden=hidden,
            placeholder=placeholder
        )

        self._record_balance_snapshot(account, reason="account creation")

        if not self._use_db:
            self.accounts[account.id] = account
            self._invalidate_hierarchy_cache()
            return account

        session, should_close = self._acquire_session()
        try:
            session.add(account)
            session.flush()
            session.commit()
            session.refresh(account)
            self._invalidate_hierarchy_cache()
            return account
        except Exception as e:
            log_critical_application_error(f"Failed to create account {account_id_to_use}: {e}", account_id=account_id_to_use, metadata={"service": "AccountService"})
            raise RuntimeError(f"Failed to create account {account_id_to_use} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def get_account(self, account_id: str, *, session: Session | None = None) -> Account | None:
        """Return an account by ID when it exists, otherwise None."""
        if not self._use_db:
            return self.accounts.get(account_id)

        if session is not None:
            try:
                return session.get(Account, account_id)
            except Exception as e:
                log_critical_application_error(f"Failed to retrieve account {account_id}: {e}", account_id=account_id, metadata={"service": "AccountService"})
                raise RuntimeError(f"Failed to retrieve account {account_id} due to unexpected error.") from e

        active_session, should_close = self._acquire_session()
        try:
            return active_session.get(Account, account_id)
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve account {account_id}: {e}", account_id=account_id, metadata={"service": "AccountService"})
            raise RuntimeError(f"Failed to retrieve account {account_id} due to unexpected error.") from e
        finally:
            if should_close:
                active_session.close()

    def get_all_accounts(
        self,
        hidden: bool | None = None,
        placeholder: bool | None = None,
        search_term: str | None = None
    ) -> list[Account]:
        """Return accounts matching the optional hidden/placeholder/search filters."""
        if not self._use_db:
            accounts = list(self.accounts.values())
            if hidden is not None:
                accounts = [acc for acc in accounts if acc.hidden == hidden]
            if placeholder is not None:
                accounts = [acc for acc in accounts if acc.placeholder == placeholder]
            if search_term:
                term = search_term.lower()
                accounts = [
                    acc for acc in accounts
                    if term in acc.name.lower()
                ]
            return sorted(accounts, key=lambda acc: acc.name)

        criteria = AccountQueryCriteria(hidden=hidden, placeholder=placeholder, search_term=search_term)

        session, should_close = self._acquire_session()
        try:
            query = self._build_account_query(criteria)
            return list(session.scalars(query).all())
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve all accounts: {e}", metadata={"service": "AccountService"})
            raise RuntimeError("Failed to retrieve all accounts due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def _build_account_query(self, criteria: AccountQueryCriteria) -> Select[Any]:
        """Compose an optimized query based on the supplied criteria."""
        query = select(Account).order_by(Account.name)
        filters = criteria.build_filters()
        if filters:
            query = query.where(and_(*filters))
        return query

    def update_account(self, account_id: str, **kwargs: AccountFieldValue) -> Account | None:
        """Apply partial updates to persisted account attributes with validation."""
        session = None
        should_close = False
        if self._use_db:
            session, should_close = self._acquire_session()
        try:
            # Use with_for_update() to acquire a pessimistic lock on the account row
            if self._use_db and session is not None:
                account = session.execute(
                    select(Account)
                    .filter_by(id=account_id)
                    .with_for_update()  # Acquire pessimistic lock
                ).scalar_one_or_none()
            else:
                account = self.get_account(account_id, session=session) # Fallback for non-db mode

            if account is None:
                return None

            self._apply_updates(account, kwargs)
            self._invalidate_hierarchy_cache() # Invalidate cache after update

            if self._use_db and session is not None:
                # Changes to the 'account' object are already tracked by the session
                # No need for session.add(account) if it was already retrieved from the session
                session.flush() # Persist changes within the transaction
                session.commit()
                session.refresh(account) # Reload fresh state after flush
            self._invalidate_hierarchy_cache() # Invalidate cache after update
            return account
        except ValueError:
            raise
        except Exception as e:
            log_critical_application_error(f"Failed to update account {account_id}: {e}", account_id=account_id, metadata={"service": "AccountService"})
            raise RuntimeError(f"Failed to update account {account_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def delete_account(self, account_id: str) -> bool:
        """Remove the account after validating child states."""
        if not self._use_db:
            account = self.accounts.get(account_id)
            if account is None:
                return False

            placeholder_children = [
                child for child in self.accounts.values()
                if child.parent_account_id == account_id and child.placeholder
            ]
            if placeholder_children:
                raise ValueError("Cannot delete an account that still has placeholder child accounts.")

            del self.accounts[account_id]
            self._invalidate_hierarchy_cache()
            return True

        session, should_close = self._acquire_session()
        try:
            account = self.get_account(account_id, session=session)
            if account is None:
                return False

            placeholder_children_count = int(
                session.scalar(
                    select(func.count())
                    .where(
                        and_(
                            Account.parent_account_id == account_id,
                            Account.placeholder.is_(True)
                        )
                    )
                ) or 0
            )

            if placeholder_children_count:
                raise ValueError("Cannot delete an account that still has placeholder child accounts.")

            self._remove_account_dependents(session, account_id)
            session.delete(account)
            session.flush()
            self._invalidate_hierarchy_cache()
            return True
        except Exception as e:
            log_critical_application_error(f"Failed to delete account {account_id}: {e}", account_id=account_id, metadata={"service": "AccountService"})
            raise RuntimeError(f"Failed to delete account {account_id} due to unexpected error.") from e
        finally:
            if should_close:
                session.close()

    def _remove_account_dependents(self, session: Session, account_id: str) -> None:
        """Remove records tied to the account before deleting the account itself."""
        session.execute(
            delete(ReconciliationViewEntry)
            .where(ReconciliationViewEntry.account_id == account_id)
        )
        session.execute(
            delete(ManualBalanceAdjustment)
            .where(ManualBalanceAdjustment.account_id == account_id)
        )
        session.execute(
            delete(AdjustmentTransaction)
            .where(AdjustmentTransaction.account_id == account_id)
        )
        transaction_ids = session.scalars(
            select(Transaction.id).where(
                or_(
                    Transaction.debit_account_id == account_id,
                    Transaction.credit_account_id == account_id
                )
            )
        ).all()

        if transaction_ids:
            session.execute(
                delete(Entry)
                .where(Entry.transaction_id.in_(transaction_ids))
            )
            session.execute(
                delete(Transaction)
                .where(Transaction.id.in_(transaction_ids))
            )
        session.flush()

    def merge_accounts(  # noqa: C901
        self,
        plan_request: AccountMergePlanRequest,
        transaction_service: "TransactionService",
        *,
        executed_by: str | None = None,
        session: Session | None = None
    ) -> AccountMergePlan:
        """Reparent accounts and reassign entries/transactions during a planned merge."""
        if not self._use_db:
            raise RuntimeError("Account merges require database persistence.")

        active_session, close_session = (session, False) if session else self._acquire_session()
        try:
            source = active_session.get(Account, plan_request.source_account_id)
            target = active_session.get(Account, plan_request.target_account_id)
            if source is None or target is None:
                raise ValueError("Source or target account not found.")

            reparent_map = plan_request.reparenting_map or {}

            plan = AccountMergePlan(
                source_account_id=source.id,
                target_account_id=target.id,
                reparenting_map=reparent_map,
                audit_notes=plan_request.audit_notes,
                initiated_by=plan_request.initiated_by,
                metadata=plan_request.metadata,
            )
            active_session.add(plan)
            active_session.flush()

            valid, message = transaction_service.validate_merge_depth(source.id, target.id)
            if not valid:
                plan.depth_validation_error = message
                plan.status = "rejected"
                active_session.flush()
                raise ValueError(message)

            explicit_children = self._reparent_explicit_children(
                active_session,
                reparent_map,
                source.id,
                target.id,
            )
            self._reparent_remaining_children(
                active_session,
                source.id,
                target.id,
                explicit_children,
            )
            entry_count = self._transfer_entries_and_transactions(
                active_session,
                source.id,
                target.id,
            )

            source.hidden = True
            source.placeholder = True
            source.parent_account_id = target.id

            plan.affected_entries_count = entry_count
            plan.status = "executed"
            plan.executed_at = datetime.now(timezone.utc)
            active_session.flush()

            log_account_merge(
                plan.plan_id,
                source.id,
                target.id,
                executed_by=executed_by or plan_request.initiated_by,
                reparenting_map=reparent_map,
                affected_entries_count=plan.affected_entries_count,
                status=plan.status,
            )

            self._invalidate_hierarchy_cache()
            return plan
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(
                f"Failed to merge accounts {plan_request.source_account_id} -> {plan_request.target_account_id}: {exc}",
                metadata={"service": "AccountService"},
            )
            raise RuntimeError("Account merge failed due to unexpected error.") from exc
        finally:
            if close_session and active_session is not None:
                active_session.close()

    def _reparent_explicit_children(
        self,
        session: Session,
        reparenting_map: dict[str, str],
        source_id: str,
        target_id: str,
    ) -> set[str]:
        explicit_children: set[str] = set()
        for child_id, new_parent in reparenting_map.items():
            child = session.get(Account, child_id)
            if child is None:
                raise ValueError(f"Child account {child_id} not found.")
            if new_parent not in (child.parent_account_id, target_id, source_id):
                parent = session.get(Account, new_parent)
                if parent is None:
                    raise ValueError(f"Reparent target {new_parent} not found.")
            child.parent_account_id = new_parent
            explicit_children.add(child_id)
        return explicit_children

    def _reparent_remaining_children(
        self,
        session: Session,
        source_id: str,
        target_id: str,
        excluded_children: set[str],
    ) -> None:
        direct_children = session.scalars(
            select(Account).where(Account.parent_account_id == source_id)
        ).all()
        for child in direct_children:
            if child.id in excluded_children:
                continue
            child.parent_account_id = target_id

    def _transfer_entries_and_transactions(
        self,
        session: Session,
        source_id: str,
        target_id: str,
    ) -> int:
        entry_count = session.scalar(
            select(func.count()).where(Entry.account_id == source_id)
        ) or 0

        session.execute(
            update(Entry).where(Entry.account_id == source_id).values(account_id=target_id)
        )
        session.execute(
            update(Transaction).where(Transaction.debit_account_id == source_id).values(debit_account_id=target_id)
        )
        session.execute(
            update(Transaction).where(Transaction.credit_account_id == source_id).values(credit_account_id=target_id)
        )
        return int(entry_count)

    def search_accounts_by_name(
        self,
        name_query: str,
        include_hidden: bool = False,
        include_placeholder: bool = False
    ) -> list[Account]:
        """Search accounts by name with optional visibility filters."""
        if not name_query:
            return []

        term = name_query.lower()

        if not self._use_db:
            matches = [
                acc for acc in self.accounts.values()
                if term in acc.name.lower()
            ]
            if not include_hidden:
                matches = [acc for acc in matches if not acc.hidden]
            if not include_placeholder:
                matches = [acc for acc in matches if not acc.placeholder]
            return sorted(matches, key=lambda acc: acc.name)

        filters = [func.lower(Account.name).contains(term)]

        if not include_hidden:
            filters.append(Account.hidden.is_(False))
        if not include_placeholder:
            filters.append(Account.placeholder.is_(False))

        session, should_close = self._acquire_session()
        try:
            query = select(Account).where(and_(*filters)).order_by(Account.name)
            return list(session.scalars(query).all())
        except Exception as e:
            log_critical_application_error(f"Failed to search accounts by name '{term}': {e}", metadata={"service": "AccountService", "search_term": term})
            raise RuntimeError("Failed to search accounts due to unexpected error.") from e
        finally:
            if should_close:
                session.close()

    def _aggregate_balance(
        self,
        account_id: str,
        *,
        effective_date: datetime | date | None = None,
        reconciled_only: bool = False
    ) -> Decimal:
        """Return the net balance for the account filtered by criteria."""
        session, should_close = self._acquire_session()
        try:
            stmt = (
                select(
                    func.coalesce(func.sum(Entry.debit_amount), Decimal("0.0")),
                    func.coalesce(func.sum(Entry.credit_amount), Decimal("0.0")),
                )
                .join(Transaction, Entry.transaction)
                .where(Entry.account_id == account_id)
            )

            if effective_date is not None:
                effective_datetime = (
                    effective_date
                    if isinstance(effective_date, datetime)
                    else datetime.combine(effective_date, time.max, tzinfo=timezone.utc)
                )
                stmt = stmt.where(Transaction.effective_date <= effective_datetime)

            if reconciled_only:
                stmt = stmt.where(Transaction.reconciliation_status == ReconciliationStatus.RECONCILED)

            debit_total, credit_total = session.execute(stmt).one()
            debit_total = debit_total or Decimal("0.0")
            credit_total = credit_total or Decimal("0.0")
            balance = debit_total - credit_total
            return quantize_currency(balance)
        except Exception as e:
            log_critical_application_error(
                f"Failed to aggregate balance for account {account_id}: {e}",
                account_id=account_id,
                metadata={"service": "AccountService"},
            )
            raise RuntimeError(f"Failed to calculate balance for account {account_id}") from e
        finally:
            if should_close and session is not None:
                session.close()

    def calculate_running_balance_as_of(self, account_id: str, effective_date: datetime | date) -> Decimal:
        """Return the running balance as of the requested effective date."""
        return self._aggregate_balance(account_id, effective_date=effective_date, reconciled_only=False)

    def calculate_cleared_balance_as_of(self, account_id: str, effective_date: datetime | date) -> Decimal:
        """Return the cleared (reconciled) balance as of the requested effective date."""
        return self._aggregate_balance(account_id, effective_date=effective_date, reconciled_only=True)

    def calculate_running_balance(self, account_id: str) -> Decimal:
        """Return the quantized running balance using the current time."""
        account = self.get_account(account_id)
        if account is None:
            return Decimal("0.0")
        return quantize_currency(account.available_balance)

    def calculate_reconciled_balance(self, account_id: str) -> Decimal:
        """Return the quantized reconciled balance using the current time."""
        account = self.get_account(account_id)
        if account is None:
            return Decimal("0.0")
        return quantize_currency(account.available_balance)

    def get_account_hierarchy_balance(self, account_id: str) -> Decimal:
        """Return the aggregated balance for an account and its descendants.
        Uses an in-memory cache for performance.
        """
        if not account_id:
            return Decimal("0.0")

        # Check cache first
        if account_id in self._hierarchy_balance_cache:
            return self._hierarchy_balance_cache[account_id]

        if not self._use_db:
            balance = self._calculate_hierarchy_balance_in_memory(account_id)
        else:
            balance = self._calculate_hierarchy_balance_from_db(account_id)

        self._hierarchy_balance_cache[account_id] = balance # Cache result
        return balance
