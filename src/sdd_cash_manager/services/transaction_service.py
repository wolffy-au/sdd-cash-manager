from datetime import datetime
from decimal import Decimal  # New import
from typing import Callable

from sqlalchemy import select  # New import
from sqlalchemy.orm import Session  # New import

from sdd_cash_manager.lib.security_events import log_critical_application_error  # New import
from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.services.account_service import AccountService

BALANCING_ACCOUNT_ID = "balancing-account-id"


class TransactionService:
    """Manage transaction creation and persistence."""

    def __init__(self, db_session: Session | None = None, session_factory: Callable[[], Session] | None = None):
        """Initialize the transaction service with a database session or factory.

        Args:
            db_session: Optional SQLAlchemy session used for persistence.
            session_factory: Optional factory for tests that need to open isolated sessions.
        """
        self.db_session = db_session
        self.session_factory = session_factory
        self._use_db = bool(db_session or session_factory)
        self.account_service: AccountService | None = None  # Reference to AccountService

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

    def set_account_service(self, account_service: AccountService) -> None:
        """Attach an AccountService to enable account interactions.

        Args:
            account_service: Service managing account persistence.

        Returns:
            None: Stores the provided service for future adjustments.
        """
        self.account_service = account_service

    def _build_entry(
        self,
        transaction_id: str | None, # transaction_id can be None before flush
        account_id: str,
        debit_amount: Decimal, # Changed from float to Decimal
        credit_amount: Decimal, # Changed from float to Decimal
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
        if difference.copy_abs() > Decimal("0.00001"): # Use Decimal for comparison
            raise ValueError("Transaction entries must balance.")

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


    def create_transaction(
        self,
        effective_date: datetime,
        booking_date: datetime,
        description: str,
        amount: Decimal, # Changed from float to Decimal
        debit_account_id: str,
        credit_account_id: str,
        action_type: str,
        notes: str | None = None,
        entries: list[Entry] | None = None
    ) -> Transaction:
        """Create a new transaction record backed by ledger entries and persist it."""
        # --- Validation Block ---
        # Validate description
        validated_description = self._validate_string_field(description, "description", max_length=255, forbidden_chars_regex=r"[<>;]")

        # Validate notes if present
        validated_notes = None
        if notes is not None:
            validated_notes = self._validate_string_field(notes, "notes", max_length=500, forbidden_chars_regex=r"[<>;]")

        if not debit_account_id or not credit_account_id or not action_type:
            raise ValueError("Debit account ID, credit account ID, and action type are required.")
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same.")
        if amount <= Decimal(0): # Use Decimal for comparison
            raise ValueError("Transaction amount must be greater than zero.")
        # --- End Validation Block ---

        ledger_entries = entries or [
            self._build_entry(None, debit_account_id, amount, Decimal(0.0), validated_notes), # transaction_id will be set by SQLAlchemy
            self._build_entry(None, credit_account_id, Decimal(0.0), amount, validated_notes), # transaction_id will be set by SQLAlchemy
        ]
        self._ensure_double_entry(ledger_entries)

        transaction = Transaction(
            effective_date=effective_date,
            booking_date=booking_date,
            description=validated_description,
            amount=amount,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            action_type=action_type,
            entries=ledger_entries, # Assign entries to trigger cascade
            notes=validated_notes,
            processing_status=ProcessingStatus.PENDING,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )

        session, should_close = self._acquire_session()
        try:
            session.add(transaction)
            session.flush() # Generate ID and persist entries via cascade
            session.refresh(transaction) # Reload with fresh state and IDs
            return transaction
        except Exception as e:
            log_critical_application_error(f"Failed to create transaction {transaction.description}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to create transaction {transaction.description} due to unexpected error.") from e
        finally:
            if should_close and session is not None:
                session.close()

    def get_transaction(self, transaction_id: str, *, session: Session | None = None) -> Transaction | None:
        """Retrieve a transaction by identifier from the database.

        Args:
            transaction_id: Identifier of the transaction to fetch.
            session: Optional SQLAlchemy session to use.

        Returns:
            Transaction | None: The transaction if it exists, otherwise None.
        """
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to get transactions.")

        active_session = session or self.db_session
        if active_session is None:
            raise ValueError("Database session is required to retrieve transactions.")
        try:
            return active_session.get(Transaction, transaction_id)
        except Exception as e:
            log_critical_application_error(f"Failed to retrieve transaction {transaction_id}: {e}", metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to retrieve transaction {transaction_id} due to unexpected error.") from e

    def get_transactions_by_account(self, account_id: str) -> list[Transaction]:
        """Return all transactions involving the given account from the database.

        Args:
            account_id: Identifier to filter transactions.

        Returns:
            list[Transaction]: Matching transactions.
        """
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
        """Update processing or reconciliation status for a transaction in the database.

        Args:
            transaction_id: Identifier of the transaction to update.
            processing_status: Optional new processing status.
            reconciliation_status: Optional new reconciliation status.

        Returns:
            Transaction | None: The updated transaction or None if not found.
        """
        if not self._use_db:
            raise RuntimeError("TransactionService must be used with a database session to update transaction status.")

        session, should_close = self._acquire_session()
        try:
            transaction = self.get_transaction(transaction_id, session=session) # Use the same session
            if transaction:
                if processing_status:
                    transaction.processing_status = processing_status
                if reconciliation_status:
                    transaction.reconciliation_status = reconciliation_status
                session.flush() # Persist changes
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
        target_balance: Decimal, # Changed from float to Decimal
        adjustment_date: datetime,
        description: str,
        action_type: str,
        notes: str | None = None
    ) -> Transaction | None:
        """Adjust an account balance by creating a balancing transaction.

        Args:
            account_id: Identifier of the account to adjust.
            target_balance: Desired balance after adjustment.
            adjustment_date: Effective datetime for the adjustment.
            description: Description used in the transaction.
            action_type: Classification of the adjustment.
            notes: Optional notes for the transaction.

        Returns:
            Transaction | None: Created adjustment transaction when a change occurred.

        Raises:
            RuntimeError: If AccountService has not been attached or unexpected database error.
            ValueError: If the account cannot be found or validation fails.
        """
        try: # Added outer try-except for critical errors
            if not self.account_service:
                raise RuntimeError("AccountService is not set.")

            account = self.account_service.get_account(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found.")

            current_balance = Decimal(account.available_balance)  # Coerce to Decimal for strict typing
            amount_difference = target_balance - current_balance

            if amount_difference.copy_abs() < Decimal("0.001"):  # Use Decimal for comparison
                return None

            transaction_amount = amount_difference.copy_abs()  # This will already be Decimal
            if amount_difference < 0: # Debit account (balance decreases)
                debit_id = account_id
                credit_id = BALANCING_ACCOUNT_ID
            else: # Credit account (balance increases)
                debit_id = BALANCING_ACCOUNT_ID
                credit_id = account_id

            created_transaction = self.create_transaction(
                effective_date=adjustment_date,
                booking_date=datetime.now(),
                description=f"{description} for account {account.name}", # Use account name for clearer description
                amount=transaction_amount,
                debit_account_id=debit_id,
                credit_account_id=credit_id,
                action_type=action_type,
                notes=notes
            )

            updated_account = self.account_service.update_account(account_id, available_balance=target_balance)
            if updated_account is None:
                raise ValueError(f"Account with ID {account_id} not found.")

            self.account_service.record_balance_snapshot(
                account_id,
                timestamp=adjustment_date,
                reason=f"Balance adjustment to {target_balance}"
            )

            # Mark transaction as posted immediately for balance adjustments
            self.update_transaction_status(
                created_transaction.id,
                processing_status=ProcessingStatus.POSTED,
                reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
            )

            return created_transaction
        except (ValueError, RuntimeError):
            raise
        except Exception as exc:
            log_critical_application_error(f"Failed to perform balance adjustment for account {account_id}: {exc}", account_id=account_id, metadata={"service": "TransactionService"})
            raise RuntimeError(f"Failed to perform balance adjustment for account {account_id} due to unexpected error.") from exc
