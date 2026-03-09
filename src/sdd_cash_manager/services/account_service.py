import uuid
from dataclasses import dataclass
from datetime import datetime, timezone  # using timezone.utc for timezone-aware snapshots
from decimal import Decimal
from enum import Enum
from typing import Callable, TypeAlias

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.enums import AccountingCategory, BankingProductType

AccountFieldValue: TypeAlias = str | float | Decimal | bool | None


@dataclass
class AccountBalanceSnapshot:
    timestamp: datetime
    balance: float
    reason: str | None = None


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

    def _acquire_session(self) -> tuple[Session, bool]:
        """Return a session plus a flag indicating whether the caller must close it."""
        if self.session_factory:
            return self.session_factory(), True
        if self.db_session is None:
            raise ValueError("Database session is required for account operations.")
        return self.db_session, False

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

        for member in enum_cls:
            if normalized_value_fold == str(member.value).casefold():
                return str(member.value)

        raise ValueError(f"Invalid {field_name} '{value}'.")

    @staticmethod
    def _quantize_value(value: AccountFieldValue) -> float | None:
        if value is None:
            return None
        return float(quantize_currency(str(value)))

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
        account.name = str(value)

    def _update_account_number(self, account: Account, value: AccountFieldValue) -> None:
        account.account_number = str(value) if value is not None else None

    def _update_parent_account_id(self, account: Account, value: AccountFieldValue) -> None:
        account.parent_account_id = str(value) if value is not None else None

    def _update_notes(self, account: Account, value: AccountFieldValue) -> None:
        account.notes = str(value) if value is not None else None

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
        available_balance: AccountFieldValue = 0.0,
        credit_limit: AccountFieldValue = None,
        notes: str | None = None,
        parent_account_id: str | None = None,
        hidden: bool = False,
        placeholder: bool = False
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
            quantized_available_balance = 0.0

        account_id = str(uuid.uuid4())

        account = Account(
            name=name,
            currency=validated_currency,
            accounting_category=validated_category,
            id=account_id,
            account_number=account_number,
            banking_product_type=validated_banking_type,
            available_balance=quantized_available_balance,
            credit_limit=self._quantize_value(credit_limit),
            notes=notes,
            parent_account_id=parent_account_id,
            hidden=hidden,
            placeholder=placeholder
        )

        self._record_balance_snapshot(account, reason="account creation")

        if not self._use_db:
            self.accounts[account.id] = account
            return account

        session, should_close = self._acquire_session()
        try:
            session.add(account)
            session.flush()
            session.refresh(account)
            return account
        finally:
            if should_close and session is not None:
                session.close()

    def get_account(self, account_id: str, *, session: Session | None = None) -> Account | None:
        """Return an account by ID when it exists, otherwise None."""
        if not self._use_db:
            return self.accounts.get(account_id)

        active_session = session or self.db_session
        if active_session is None:
            raise ValueError("Database session is required to retrieve accounts.")
        return active_session.get(Account, account_id)

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

        filters = []
        if hidden is not None:
            filters.append(Account.hidden == hidden)
        if placeholder is not None:
            filters.append(Account.placeholder == placeholder)
        if search_term:
            filters.append(func.lower(Account.name).contains(search_term.lower()))

        session, should_close = self._acquire_session()
        try:
            query = select(Account)
            if filters:
                query = query.where(and_(*filters))
            return list(session.scalars(query.order_by(Account.name)).all())
        finally:
            if should_close and session is not None:
                session.close()

    def update_account(self, account_id: str, **kwargs: AccountFieldValue) -> Account | None:
        """Apply partial updates to persisted account attributes with validation."""
        session = None
        should_close = False
        if self._use_db:
            session, should_close = self._acquire_session()
        try:
            account = self.get_account(account_id, session=session)
            if account is None:
                return None

            self._apply_updates(account, kwargs)

            if self._use_db and session is not None:
                session.add(account)
                session.flush()
                session.refresh(account)
            return account
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

            session.delete(account)
            session.flush()
            return True
        finally:
            if should_close:
                session.close()

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
        finally:
            if should_close:
                session.close()

    def calculate_running_balance(self, account_id: str) -> float:
        """Return the quantized running balance for the account."""
        account = self.get_account(account_id)
        if account is None:
            return 0.0
        return float(quantize_currency(str(account.available_balance)))

    def calculate_reconciled_balance(self, account_id: str) -> float:
        """Return the quantized reconciled balance for the account."""
        account = self.get_account(account_id)
        if account is None:
            return 0.0
        return float(quantize_currency(str(account.available_balance)))
