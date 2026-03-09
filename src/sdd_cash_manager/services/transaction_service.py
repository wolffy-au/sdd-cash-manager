import uuid
from datetime import datetime

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.services.account_service import AccountService  # Added this import

BALANCING_ACCOUNT_ID = "balancing-account-id"


class TransactionService:
    """Manage transaction creation and balance adjustments."""

    def __init__(self):
        """Initialize the transaction service.

        Returns:
            None: Prepares in-memory storage until an AccountService is attached.
        """
        self.transactions: dict[str, Transaction] = {}
        self.entries: dict[str, list[Entry]] = {}
        self.account_service: AccountService | None = None  # Reference to AccountService

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
        transaction_id: str,
        account_id: str,
        debit_amount: float,
        credit_amount: float,
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
        total_debits = sum(entry.debit_amount for entry in entries)
        total_credits = sum(entry.credit_amount for entry in entries)
        if abs(total_debits - total_credits) > 0.00001:
            raise ValueError("Transaction entries must balance.")

    def _register_entry(self, entry: Entry) -> None:
        """Index an entry by account for later lookup."""
        self.entries.setdefault(entry.account_id, []).append(entry)

    def get_entries_by_account(self, account_id: str) -> list[Entry]:
        """Return all ledger entries that touch the given account."""
        return list(self.entries.get(account_id, []))

    def create_transaction(
        self,
        effective_date: datetime,
        booking_date: datetime,
        description: str,
        amount: float,
        debit_account_id: str,
        credit_account_id: str,
        action_type: str,
        notes: str | None = None,
        entries: list[Entry] | None = None
    ) -> Transaction:
        """Create a new transaction record backed by ledger entries.

        Args:
            effective_date: Date when the transaction takes effect.
            booking_date: Date when the transaction is booked.
            description: Description of the transaction.
            amount: Transaction amount.
            debit_account_id: Account from which funds are debited.
            credit_account_id: Account receiving the funds.
            action_type: Classification of the transaction.
            notes: Optional notes about the transaction.
            entries: Optional ledger entries to attach (used by more complex flows).

        Returns:
            Transaction: The newly created transaction.

        Raises:
            ValueError: If required fields are missing or debit and credit accounts match.
        """
        if not description or not debit_account_id or not credit_account_id or not action_type:
            raise ValueError("Description, debit account ID, credit account ID, and action type are required.")
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same.")
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero.")

        tx_id = str(uuid.uuid4())
        ledger_entries = entries or [
            self._build_entry(tx_id, debit_account_id, amount, 0.0, notes),
            self._build_entry(tx_id, credit_account_id, 0.0, amount, notes),
        ]
        self._ensure_double_entry(ledger_entries)
        for entry in ledger_entries:
            self._register_entry(entry)

        transaction = Transaction(
            id=tx_id,
            effective_date=effective_date,
            booking_date=booking_date,
            description=description,
            amount=amount,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            action_type=action_type,
            entries=ledger_entries,
            notes=notes,
            processing_status=ProcessingStatus.PENDING,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )
        self.transactions[tx_id] = transaction
        return transaction

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Retrieve a transaction by identifier.

        Args:
            transaction_id: Identifier of the transaction to fetch.

        Returns:
            Transaction | None: The transaction if it exists, otherwise None.
        """
        return self.transactions.get(transaction_id)

    def get_transactions_by_account(self, account_id: str) -> list[Transaction]:
        """Return all transactions involving the given account.

        Args:
            account_id: Identifier to filter transactions.

        Returns:
            list[Transaction]: Matching transactions.
        """
        return [
            tx for tx in self.transactions.values()
            if tx.debit_account_id == account_id or tx.credit_account_id == account_id
        ]

    def update_transaction_status(
        self,
        transaction_id: str,
        processing_status: ProcessingStatus | None = None,
        reconciliation_status: ReconciliationStatus | None = None
    ) -> Transaction | None:
        """Update processing or reconciliation status for a transaction.

        Args:
            transaction_id: Identifier of the transaction to update.
            processing_status: Optional new processing status.
            reconciliation_status: Optional new reconciliation status.

        Returns:
            Transaction | None: The updated transaction or None if not found.
        """
        transaction = self.get_transaction(transaction_id)
        if transaction:
            if processing_status:
                transaction.processing_status = processing_status
            if reconciliation_status:
                transaction.reconciliation_status = reconciliation_status
            return transaction
        return None

    def perform_balance_adjustment(
        self,
        account_id: str,
        target_balance: float,
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
            RuntimeError: If AccountService has not been attached.
            ValueError: If the account cannot be found.
        """
        if not self.account_service:
            raise RuntimeError("AccountService is not set.")

        account = self.account_service.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found.")

        current_balance = account.available_balance
        amount_difference = target_balance - current_balance

        if abs(amount_difference) < 0.001: # Use a small tolerance for float comparison
            return None

        transaction_amount = abs(amount_difference)
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
