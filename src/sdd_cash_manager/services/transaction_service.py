from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable

from sqlalchemy import delete, literal, or_, select
from sqlalchemy.orm import Session, selectinload

from sdd_cash_manager.core.config import settings
from sdd_cash_manager.lib.logging_config import get_logger
from sdd_cash_manager.lib.security_events import (
    log_critical_application_error,
    log_duplicate_merge,
    log_quickfill_template_approved,
)
from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.duplicate_candidate import DuplicateCandidate
from sdd_cash_manager.models.enums import AccountingCategory, ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.quickfill_template import QuickFillTemplate
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.services.account_service import AccountService

logger = get_logger(__name__)

MAX_HIERARCHY_DEPTH = 5
DUPLICATE_SCAN_LIMIT = 1000

BALANCING_ACCOUNT_ID = "00000000-0000-0000-0000-000000000099"
FORBIDDEN_CHAR_PATTERN = r"[<>;]"


class TransactionService:
    """Manage transaction creation and persistence."""

    def __init__(self, db_session: Session | None = None, session_factory: Callable[[], Session] | None = None):
        """Initialize the transaction service with a database session or factory."""
        self.db_session = db_session
        self.session_factory = session_factory
        self._use_db = bool(db_session or session_factory)
        self.account_service: AccountService | None = None

    def _acquire_session(self) -> tuple[Session, bool]:
        """Return a session plus a flag indicating whether the caller must close it."""
        try:
            if self.session_factory:
                return self.session_factory(), True
            if self.db_session is None:
                raise ValueError("Database session is required for transaction operations.")
            return self.db_session, False
        except Exception as e:
            log_critical_application_error(f"Failed to acquire database session for transaction service: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError("Failed to acquire database session for transaction service due to unexpected error.") from e

    def _ensure_account_service(self) -> None:
        """Ensure an AccountService has been attached before touching balances."""
        if self.account_service is None:
            raise RuntimeError("AccountService is not set.")

    @staticmethod
    def _ensure_account_active(account: Account) -> None:
        """Reject accounts that are flagged as hidden or placeholder."""
        if getattr(account, "hidden", False) or getattr(account, "placeholder", False):
            raise ValueError(f"Account {account.id} is not available for transactions.")

    def _apply_account_balance_delta(
        self,
        debit_account: Account,
        credit_account: Account,
        amount: Decimal
    ) -> None:
        """Adjust the source and destination account balances atomically."""
        debit_balance = quantize_currency(debit_account.available_balance - amount)
        credit_balance = quantize_currency(credit_account.available_balance + amount)
        debit_account.available_balance = debit_balance
        credit_account.available_balance = credit_balance

    def set_account_service(self, account_service: AccountService) -> None:
        """Attach an AccountService to enable account interactions."""
        self.account_service = account_service

    def _build_entry(
        self,
        transaction_id: str | None,
        account_id: str,
        debit_amount: Decimal,
        credit_amount: Decimal,
        notes: str | None = None
    ) -> Entry:
        """Create a single ledger entry for a transaction."""
        return Entry(
            transaction_id=transaction_id,
            account_id=account_id,
            debit_amount=debit_amount,
            credit_amount=credit_amount,
            notes=notes
        )

    def _ensure_double_entry(self, entries: list[Entry]) -> None:
        """Verify that debits and credits balance across provided entries."""
        total_debits = sum((entry.debit_amount for entry in entries), start=Decimal("0"))
        total_credits = sum((entry.credit_amount for entry in entries), start=Decimal("0"))
        difference: Decimal = total_debits - total_credits
        if difference.copy_abs() > Decimal("0.00001"):
            raise ValueError("Transaction entries must balance.")

    @staticmethod
    def _validate_string_field(
        value: str,
        field_name: str,
        min_length: int = 1,
        max_length: int | None = None,
        allowed_chars_regex: str | None = None,
        forbidden_chars_regex: str | None = FORBIDDEN_CHAR_PATTERN
    ) -> str:
        import re

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

    def _validate_accounts_and_currency(
        self,
        session: Session,
        debit_account_id: str,
        credit_account_id: str,
        currency: str | None,
        transaction_description: str,
    ) -> tuple[Account, Account]:
        """Load and validate both sides of the transaction plus optional currency."""
        self._ensure_account_service()
        account_service = self.account_service
        assert account_service is not None
        debit_account = account_service.get_account(debit_account_id)
        credit_account = account_service.get_account(credit_account_id)
        if debit_account is None or credit_account is None:
            missing = [
                identifier for identifier, account in (
                    (debit_account_id, debit_account),
                    (credit_account_id, credit_account),
                )
                if account is None
            ]
            existing_ids = session.scalars(select(Account.id)).all()
            log_critical_application_error(
                f"Missing account(s) {missing} before creating transaction {transaction_description}",
                metadata={
                    "service": "TransactionService",
                    "missing_account_ids": missing,
                    "known_account_ids": existing_ids,
                },
            )
            raise ValueError("Debit or credit account could not be found.")

        self._ensure_account_active(debit_account)
        self._ensure_account_active(credit_account)

        if currency:
            normalized_currency = currency.strip().upper()
            if normalized_currency != debit_account.currency.upper():
                raise ValueError("Debit account currency does not match requested currency.")
            if normalized_currency != credit_account.currency.upper():
                raise ValueError("Credit account currency does not match requested currency.")

        return debit_account, credit_account

    def _persist_transaction(
        self,
        session: Session,
        transaction: Transaction,
        debit_account: Account,
        credit_account: Account,
        amount: Decimal,
        currency: str,
    ) -> Transaction:
        """Persist the transaction plus snapshots and balance adjustments."""
        session.add(transaction)
        session.flush()
        self._apply_account_balance_delta(debit_account, credit_account, amount)
        snapshot_reason = f"Transaction {transaction.id} posted"
        account_service = self.account_service
        assert account_service is not None
        account_service.record_balance_snapshot(debit_account.id, reason=snapshot_reason)
        account_service.record_balance_snapshot(credit_account.id, reason=snapshot_reason)
        session.flush()
        self._record_quickfill_candidate(session, transaction, currency)
        session.commit()
        session.refresh(transaction)
        return transaction

    def create_transaction(
        self,
        effective_date: datetime,
        booking_date: datetime,
        description: str,
        amount: Decimal,
        debit_account_id: str,
        credit_account_id: str,
        action_type: str,
        notes: str | None = None,
        currency: str | None = None,
        entries: list[Entry] | None = None
    ) -> Transaction:
        """Create a new transaction record backed by ledger entries and persist it."""
        validated_description, validated_notes = self._validate_transaction_metadata(description, notes)
        self._verify_account_ids(debit_account_id, credit_account_id, action_type)
        self._ensure_positive_amount(amount)

        ledger_entries = entries or self._build_default_entries(
            debit_account_id,
            credit_account_id,
            amount,
            validated_notes,
        )
        self._ensure_double_entry(ledger_entries)

        transaction = Transaction(
            effective_date=effective_date,
            booking_date=booking_date,
            description=validated_description,
            amount=amount,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            action_type=action_type,
            entries=ledger_entries,
            notes=validated_notes,
            processing_status=ProcessingStatus.POSTED,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )

        session, should_close = self._acquire_session()
        try:
            debit_account, credit_account = self._validate_accounts_and_currency(
                session,
                debit_account_id,
                credit_account_id,
                currency,
                transaction.description,
            )
            currency_value = currency or debit_account.currency
            assert currency_value is not None
            currency_to_use = currency_value.strip().upper()
            return self._persist_transaction(
                session,
                transaction,
                debit_account,
                credit_account,
                amount,
                currency_to_use,
            )
        except Exception as e:
            log_critical_application_error(f"Failed to create transaction {transaction.description}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to create transaction {transaction.description} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def _validate_transaction_metadata(self, description: str, notes: str | None) -> tuple[str, str | None]:
        validated_description = self._validate_string_field(description, "description", max_length=255, forbidden_chars_regex=FORBIDDEN_CHAR_PATTERN)
        validated_notes = None
        if notes is not None:
            validated_notes = self._validate_string_field(notes, "notes", max_length=500, forbidden_chars_regex=FORBIDDEN_CHAR_PATTERN)
        return validated_description, validated_notes

    @staticmethod
    def _verify_account_ids(debit_account_id: str, credit_account_id: str, action_type: str) -> None:
        if not debit_account_id or not credit_account_id or not action_type:
            raise ValueError("Debit account ID, credit account ID, and action type are required.")
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same.")

    @staticmethod
    def _ensure_positive_amount(amount: Decimal) -> None:
        if amount <= Decimal(0):
            raise ValueError("Transaction amount must be greater than zero.")

    def _build_default_entries(
        self,
        debit_account_id: str,
        credit_account_id: str,
        amount: Decimal,
        notes: str | None
    ) -> list[Entry]:
        return [
            self._build_entry(None, debit_account_id, amount, Decimal(0.0), notes),
            self._build_entry(None, credit_account_id, Decimal(0.0), amount, notes),
        ]

    def get_transaction(self, transaction_id: str, *, session: Session | None = None) -> Transaction | None:
        """Retrieve a transaction by identifier from the database."""
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to get transactions.")

        active_session = session or self.db_session
        if active_session is None:
            raise ValueError("Database session is required to retrieve transactions.")
        try:
            return active_session.get(Transaction, transaction_id)
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve transaction {transaction_id}: {e}", account_id=transaction_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to retrieve transaction {transaction_id} due to unexpected error.") from e

    def get_transactions_by_account(self, account_id: str) -> list[Transaction]:
        """Return all transactions involving the given account from the database."""
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to get transactions by account.")

        session, should_close = self._acquire_session()
        try:
            query = select(Transaction).where(
                (Transaction.debit_account_id == account_id) |
                (Transaction.credit_account_id == account_id)
            )
            return list(session.scalars(query).all())
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve transactions for account {account_id}: {e}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to retrieve transactions for account {account_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def update_transaction_status(
        self,
        transaction_id: str,
        processing_status: ProcessingStatus | None = None,
        reconciliation_status: ReconciliationStatus | None = None
    ) -> Transaction | None:
        """Update processing or reconciliation status for a transaction in the database."""
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to update transaction status.")

        session, should_close = self._acquire_session()
        try:
            transaction = self.get_transaction(transaction_id, session=session)
            if transaction:
                if processing_status:
                    transaction.processing_status = processing_status
                if reconciliation_status:
                    transaction.reconciliation_status = reconciliation_status
                session.flush()
            return transaction
        except Exception as e:
            log_critical_application_error(f"Failed to update status for transaction {transaction_id}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to update status for transaction {transaction_id} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def perform_balance_adjustment(
        self,
        account_id: str,
        target_balance: Decimal,
        adjustment_date: datetime,
        description: str,
        action_type: str,
        notes: str | None = None
    ) -> Transaction | None:
        """Adjust an account balance by creating a balancing transaction."""
        try:
            self._ensure_account_service()
            account_service = self.account_service
            assert account_service is not None
            account = account_service.get_account(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found.")
            self._ensure_balancing_account(account_service, account.currency)

            current_balance = Decimal(account.available_balance)
            amount_difference = target_balance - current_balance

            if amount_difference.copy_abs() < Decimal("0.001"):
                return None

            debit_id, credit_id = self._determine_adjustment_accounts(amount_difference, account_id)
            transaction_amount = amount_difference.copy_abs()

            created_transaction = self._create_adjustment_transaction(
                adjustment_date,
                description,
                action_type,
                transaction_amount,
                account,
                debit_id,
                credit_id,
                notes,
            )

            account_service = self.account_service
            assert account_service is not None
            self._finalize_balance_adjustment(
                account_id,
                target_balance,
                adjustment_date,
                created_transaction,
                account_service,
            )

            return created_transaction
        except ValueError:
            raise
        except RuntimeError as exc:
            if str(exc) == "AccountService is not set.":
                raise
            log_critical_application_error(f"Failed to perform balance adjustment for account {account_id}: {exc}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to perform balance adjustment for account {account_id} due to unexpected error.") from exc
        except Exception as exc:
            log_critical_application_error(f"Failed to perform balance adjustment for account {account_id}: {exc}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to perform balance adjustment for account {account_id} due to unexpected error.") from exc

    def _determine_adjustment_accounts(self, amount_difference: Decimal, account_id: str) -> tuple[str, str]:
        if amount_difference < 0:
            return account_id, BALANCING_ACCOUNT_ID
        return BALANCING_ACCOUNT_ID, account_id

    def _create_adjustment_transaction(
        self,
        adjustment_date: datetime,
        description: str,
        action_type: str,
        transaction_amount: Decimal,
        account: Account,
        debit_id: str,
        credit_id: str,
        notes: str | None,
    ) -> Transaction:
        try:
            return self.create_transaction(
                effective_date=adjustment_date,
                booking_date=datetime.now(),
                description=f"{description} for account {account.name}",
                amount=transaction_amount,
                debit_account_id=debit_id,
                credit_account_id=credit_id,
                action_type=action_type,
                currency=account.currency,
                notes=notes,
            )
        except RuntimeError as exc:
            log_critical_application_error(f"Failed to create adjustment transaction for account {account.id}: {exc}", account_id=account.id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to perform balance adjustment for account {account.id} due to unexpected error.") from exc

    def _finalize_balance_adjustment(
        self,
        account_id: str,
        target_balance: Decimal,
        adjustment_date: datetime,
        created_transaction: Transaction,
        account_service: AccountService,
    ) -> None:
        updated_account = account_service.update_account(account_id, available_balance=target_balance)
        if updated_account is None:
            raise ValueError(f"Account with ID {account_id} not found.")

        account_service.record_balance_snapshot(
            account_id,
            timestamp=adjustment_date,
            reason=f"Balance adjustment to {target_balance}"
        )

        self.update_transaction_status(
            created_transaction.id,
            processing_status=ProcessingStatus.POSTED,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )

    def _ensure_balancing_account(self, account_service: AccountService, currency: str) -> None:
        logger.debug("Checking if balancing account %s exists", BALANCING_ACCOUNT_ID)
        balancing_account = account_service.get_account(BALANCING_ACCOUNT_ID)
        if balancing_account is None:
            logger.info("Balancing account %s not found, creating it.", BALANCING_ACCOUNT_ID)
            account_service.create_account(
                name="Balancing Account",
                currency=currency,
                accounting_category=AccountingCategory.EQUITY,
                available_balance=Decimal("0.0"),
                id=BALANCING_ACCOUNT_ID
            )
        else:
            logger.debug("Balancing account %s already exists.", BALANCING_ACCOUNT_ID)

    def ensure_balancing_account_exists(self, currency: str) -> None:
        """Create the balancing account when it does not already exist."""
        self._ensure_account_service()
        account_service = self.account_service
        assert account_service is not None
        self._ensure_balancing_account(account_service, currency)

    def rank_quickfill_candidates(
        self,
        action_type: str,
        currency: str,
        query: str | None = None,
        limit: int = 5,
        include_unapproved: bool = False,
    ) -> list[QuickFillTemplate]:
        """Rank QuickFill templates by confidence for the given action/currency pair."""
        if not self._use_db:
            raise RuntimeError("QuickFill ranking requires a database session.")

        limit = max(1, limit)
        normalized_action = action_type.strip()
        normalized_currency = currency.strip().upper()
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=max(settings.quickfill_history_days, 1))

        session, should_close = self._acquire_session()
        try:
            stmt = select(QuickFillTemplate).options(selectinload(QuickFillTemplate.source_transaction)).where(
                QuickFillTemplate.action == normalized_action,
                QuickFillTemplate.currency == normalized_currency,
                QuickFillTemplate.last_used_at >= recent_cutoff,
            )
            if not include_unapproved:
                stmt = stmt.where(QuickFillTemplate.is_approved.is_(True))

            if query:
                term = f"%{query.strip()}%"
                stmt = stmt.outerjoin(QuickFillTemplate.source_transaction).where(
                    or_(
                        QuickFillTemplate.memo.ilike(term),
                        Transaction.description.ilike(term),
                    )
                )

            stmt = stmt.order_by(
                QuickFillTemplate.confidence_score.desc(),
                QuickFillTemplate.history_count.desc(),
                QuickFillTemplate.last_used_at.desc()
            )

            stmt = stmt.limit(limit)
            return list(session.scalars(stmt).all())
        except Exception as exc:
            log_critical_application_error(
                f"Failed to rank QuickFill templates for {action_type}/{currency}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to rank QuickFill templates due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def approve_quickfill_template(
        self,
        template_id: str,
        approved_by: str | None = None
    ) -> QuickFillTemplate:
        """Mark a QuickFill template as approved and emit an audit event."""
        if not self._use_db:
            raise RuntimeError("QuickFill approval requires an active database session.")

        session, should_close = self._acquire_session()
        try:
            template = session.get(QuickFillTemplate, template_id)
            if template is None:
                raise ValueError("QuickFill template not found.")

            template.is_approved = True
            approved_at = datetime.now(timezone.utc)
            template.approved_at = approved_at
            template.last_used_at = template.last_used_at or approved_at
            template.confidence_score = self._calculate_quickfill_confidence(
                template.history_count or 1,
                template.last_used_at,
            )
            session.flush()
            session.commit()
            session.refresh(template)
            log_quickfill_template_approved(
                template_id=template.id,
                approved_by=approved_by,
                action=template.action,
                currency=template.currency,
                transfer_from=template.transfer_from_account_id,
                transfer_to=template.transfer_to_account_id,
                confidence_score=float(template.confidence_score),
            )
            return template
        except ValueError:
            raise
        except Exception as exc:
            log_critical_application_error(
                f"Failed to approve QuickFill template {template_id}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to approve QuickFill template due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def _record_quickfill_candidate(
        self,
        session: Session,
        transaction: Transaction,
        currency: str,
    ) -> None:
        """Capture transaction metadata as a QuickFill template candidate."""
        raw_memo = (transaction.notes or transaction.description or "").strip()
        memo_value: str | None = raw_memo[:255] if raw_memo else None
        action = transaction.action_type.strip()
        normalized_currency = currency.strip().upper()
        stmt = select(QuickFillTemplate).where(
            QuickFillTemplate.action == action,
            QuickFillTemplate.currency == normalized_currency,
            QuickFillTemplate.transfer_from_account_id == transaction.debit_account_id,
            QuickFillTemplate.transfer_to_account_id == transaction.credit_account_id,
            QuickFillTemplate.amount == transaction.amount,
            QuickFillTemplate.memo == memo_value,
        )

        existing = session.scalars(stmt).one_or_none()

        if existing:
            existing.history_count += 1
            existing.source_transaction_id = transaction.id
            existing.mark_used()
            existing.confidence_score = self._calculate_quickfill_confidence(
                existing.history_count,
                existing.last_used_at,
            )
            return

        template = QuickFillTemplate(
            action=action,
            currency=normalized_currency,
            transfer_from_account_id=transaction.debit_account_id,
            transfer_to_account_id=transaction.credit_account_id,
            amount=transaction.amount,
            memo=memo_value,
            source_transaction_id=transaction.id,
        )
        template.history_count = 1
        template.mark_used()
        template.confidence_score = self._calculate_quickfill_confidence(
            template.history_count,
            template.last_used_at,
        )
        session.add(template)

    @staticmethod
    def _calculate_quickfill_confidence(history_count: int, last_used_at: datetime | None) -> Decimal:
        """Estimate confidence using frequency within the configured QuickFill history window."""
        window_days = max(settings.quickfill_history_days, 1)
        base_hits = min(history_count, window_days)
        base_score = Decimal(base_hits) / Decimal(window_days)
        if last_used_at:
            normalized_last_used = (
                last_used_at
                if last_used_at.tzinfo is not None
                else last_used_at.replace(tzinfo=timezone.utc)
            )
            recency_bonus = Decimal("0.1") if datetime.now(timezone.utc) - normalized_last_used <= timedelta(days=7) else Decimal("0")
        else:
            recency_bonus = Decimal("0")
        return min(Decimal("1.0"), base_score + recency_bonus)

    def scan_duplicate_candidates(
        self,
        *,
        account_id: str,
        scope: str = "account",
        limit: int = 25
    ) -> list[DuplicateCandidate]:
        """Scan recent transactions and persist candidates for manual review (account scope only)."""
        if scope not in {"account", "account_group"}:
            raise ValueError("scope must be either 'account' or 'account_group'.")

        if scope == "account_group":
            raise NotImplementedError("Account group duplicate scanning is not supported yet.")

        if scope == "account" and not account_id:
            raise ValueError("account_id is required for account-scoped duplicate scans.")

        if not self._use_db:
            raise RuntimeError("Duplicate scanning requires an active database session.")

        if limit <= 0:
            limit = 25

        session, should_close = self._acquire_session()
        try:
            transactions = self._fetch_recent_transactions(session, account_id)
            groups = self._group_transactions(transactions)
            self._persist_duplicate_candidates(session, groups, account_id, scope)

            session.flush()
            session.commit()

            result_stmt = (
                select(DuplicateCandidate)
                .where(
                    DuplicateCandidate.account_id == account_id,
                    DuplicateCandidate.scope == scope
                )
                .order_by(DuplicateCandidate.confidence.desc(), DuplicateCandidate.updated_at.desc())
                .limit(limit)
            )
            return list(session.scalars(result_stmt).all())
        except Exception as exc:
            session.rollback()
            log_critical_application_error(
                f"Failed to scan duplicate candidates for account {account_id}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to scan duplicate candidates due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def _fetch_recent_transactions(self, session: Session, account_id: str) -> list[Transaction]:
        txn_query = (
            select(Transaction)
            .where(
                (Transaction.debit_account_id == account_id) |
                (Transaction.credit_account_id == account_id)
            )
            .order_by(Transaction.effective_date.desc())
            .limit(DUPLICATE_SCAN_LIMIT)
        )
        return list(session.scalars(txn_query).all())

    @staticmethod
    def _group_transactions(transactions: list[Transaction]) -> dict[tuple[Decimal, date, str], list[Transaction]]:
        groups: dict[tuple[Decimal, date, str], list[Transaction]] = {}
        for txn in transactions:
            txn_date = txn.effective_date.date()
            description = (txn.description or txn.notes or "").strip()
            normalized_description = description[:255]
            key = (txn.amount, txn_date, normalized_description)
            groups.setdefault(key, []).append(txn)
        return groups

    def _persist_duplicate_candidates(
        self,
        session: Session,
        groups: dict[tuple[Decimal, date, str], list[Transaction]],
        account_id: str,
        scope: str,
    ) -> list[DuplicateCandidate]:
        candidates: list[DuplicateCandidate] = []
        for (amount, txn_date, normalized_description), matches in groups.items():
            if len(matches) < 2:
                continue

            matches.sort(key=lambda t: t.effective_date, reverse=True)
            txn_ids = [t.id for t in matches]
            confidence = min(Decimal("1.0"), Decimal(len(matches)) / Decimal("5.0"))

            existing = session.scalars(
                select(DuplicateCandidate)
                .where(
                    DuplicateCandidate.account_id == account_id,
                    DuplicateCandidate.scope == scope,
                    DuplicateCandidate.amount == amount,
                    DuplicateCandidate.date == txn_date,
                    DuplicateCandidate.description == normalized_description
                )
            ).one_or_none()

            if existing:
                existing.matching_transaction_ids = txn_ids
                existing.confidence = confidence
                existing.touch()
                candidate = existing
            else:
                candidate = DuplicateCandidate(
                    account_id=account_id,
                    scope=scope,
                    matching_transaction_ids=txn_ids,
                    amount=amount,
                    date=txn_date,
                    description=normalized_description or None,
                    confidence=confidence,
                    recommended_action="merge",
                    status="review"
                )
                session.add(candidate)

            candidates.append(candidate)

        return candidates

    def list_duplicate_candidates(
        self,
        *,
        account_id: str,
        scope: str = "account",
        limit: int = 25
    ) -> list[DuplicateCandidate]:
        """Return candidates for the provided account scope, refreshing the scan first."""
        return self.scan_duplicate_candidates(account_id=account_id, scope=scope, limit=limit)

    def merge_duplicate_candidate(
        self,
        candidate_id: str,
        *,
        preserve_audit: bool = False,
        merged_by: str | None = None
    ) -> tuple[DuplicateCandidate, str, list[str], Decimal, Decimal]:
        """Consolidate duplicate transactions and keep a single canonical entry."""
        if not self._use_db:
            raise RuntimeError("Duplicate merge requires a database session.")
        self._ensure_account_service()
        account_service = self.account_service
        assert account_service is not None

        session, should_close = self._acquire_session()
        try:
            candidate = session.get(DuplicateCandidate, candidate_id)
            if not candidate:
                raise ValueError(f"Duplicate candidate {candidate_id} not found.")

            txn_ids = candidate.matching_transaction_ids or []
            if len(txn_ids) < 2:
                raise ValueError("Candidate must reference multiple transactions to merge.")

            canonical_txn = txn_ids[0]
            removals = txn_ids[1:]

            before_balance = account_service.calculate_running_balance(candidate.account_id)

            session.execute(delete(Transaction).where(Transaction.id.in_(removals)))
            session.flush()

            candidate.matching_transaction_ids = [canonical_txn]
            candidate.confidence = Decimal("1.0")
            candidate.status = "merged"
            candidate.touch()
            session.flush()

            after_balance = account_service.calculate_running_balance(candidate.account_id)

            log_duplicate_merge(
                candidate.id,
                removals,
                candidate.account_id,
                merged_by=merged_by,
                preserve_audit=preserve_audit,
            )

            return candidate, canonical_txn, removals, before_balance, after_balance
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(
                f"Failed to merge duplicate candidate {candidate_id}: {exc}",
                metadata={"service": "TransactionService", "candidate_id": candidate_id},
            )
            raise RuntimeError("Failed to merge duplicate candidate due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    def validate_merge_depth(
        self,
        source_account_id: str,
        target_account_id: str
    ) -> tuple[bool, str | None]:
        """Ensure moving the source subtree under the target respects hierarchy depth limits."""
        if not self._use_db:
            raise RuntimeError("Account merge validation requires a database session.")

        session, should_close = self._acquire_session()
        try:
            depth_map = self._account_depth_map(session)
            source_depth = depth_map.get(source_account_id)
            target_depth = depth_map.get(target_account_id)

            if source_depth is None or target_depth is None:
                raise ValueError("Source or target account not found.")

            descendant_ids = self._collect_descendant_ids(session, source_account_id)
            max_descendant_depth = max((depth_map.get(acc_id, source_depth) for acc_id in descendant_ids), default=source_depth)
            delta = max_descendant_depth - source_depth
            new_depth = target_depth + 1 + delta

            if new_depth > MAX_HIERARCHY_DEPTH:
                message = (
                    f"Merge would place the deepest descendant at depth {new_depth}, "
                    f"exceeding the allowed limit of {MAX_HIERARCHY_DEPTH}."
                )
                return False, message

            return True, None
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(
                f"Failed to validate merge depth between {source_account_id} and {target_account_id}: {exc}",
                metadata={"service": "TransactionService"}
            )
            raise RuntimeError("Failed to validate merge depth due to unexpected error.") from exc
        finally:
            if should_close and session is not None:
                session.close()

    @staticmethod
    def _account_depth_map(session: Session) -> dict[str, int]:
        """Return a mapping of account IDs to their depth within the hierarchy."""
        hierarchy_cte = (
            select(
                Account.id.label("account_id"),
                literal(1).label("depth")
            )
            .where(Account.parent_account_id.is_(None))
            .cte(name="account_depth", recursive=True)
        )
        hierarchy_cte = hierarchy_cte.union_all(
            select(
                Account.id,
                (hierarchy_cte.c.depth + 1).label("depth")
            )
            .where(Account.parent_account_id == hierarchy_cte.c.account_id)
        )
        rows = session.execute(
            select(hierarchy_cte.c.account_id, hierarchy_cte.c.depth)
        ).all()
        return {row.account_id: row.depth for row in rows}

    @staticmethod
    def _collect_descendant_ids(session: Session, root_account_id: str) -> set[str]:
        """Return all account IDs in the subtree rooted at the provided account."""
        descendant_cte = (
            select(Account.id)
            .where(Account.id == root_account_id)
            .cte(name="merge_descendants", recursive=True)
        )
        descendant_cte = descendant_cte.union_all(
            select(Account.id)
            .where(Account.parent_account_id == descendant_cte.c.id)
        )
        rows = session.scalars(select(descendant_cte.c.id)).all()
        return set(rows)
