import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus


@dataclass
class Entry:
    """Double-entry ledger row used by transactions."""
    transaction_id: str
    account_id: str
    debit_amount: float
    credit_amount: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValueError("Entry amounts must be non-negative.")
        if self.debit_amount and self.credit_amount:
            raise ValueError("An entry cannot have both debit and credit amounts.")
        if not (self.debit_amount or self.credit_amount):
            raise ValueError("An entry must debit or credit a non-zero amount.")


@dataclass
class Transaction:
    """In-memory representation of an account transaction."""
    effective_date: datetime  # Date when the transaction's effect is recognized
    booking_date: datetime  # Date when the transaction is entered into the system
    description: str  # Description of the transaction
    amount: float  # The amount of the transaction. Positive for income/credits, negative for expenses/debits.
    debit_account_id: str  # The ID of the account from which funds are debited
    credit_account_id: str  # The ID of the account to which funds are credited
    action_type: str  # Type of action (e.g., "Manual Adjustment", "Payment", "Transfer")
    entries: list[Entry] = field(default_factory=list)  # Ledger rows representing this transaction
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processing_status: ProcessingStatus = ProcessingStatus.PENDING  # Current status of the transaction processing
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING_RECONCILIATION  # Status regarding account reconciliation
    notes: str | None = None  # Additional notes for the transaction

    def _build_default_entries(self) -> list[Entry]:
        """Construct default debit and credit ledger rows when none are supplied."""
        amount_value = abs(self.amount)
        if amount_value == 0:
            raise ValueError("Transaction amount must be non-zero when building ledger entries.")
        return [
            Entry(
                transaction_id=self.id,
                account_id=self.debit_account_id,
                debit_amount=amount_value,
                credit_amount=0.0,
                notes=self.notes
            ),
            Entry(
                transaction_id=self.id,
                account_id=self.credit_account_id,
                debit_amount=0.0,
                credit_amount=amount_value,
                notes=self.notes
            ),
        ]

    def __post_init__(self) -> None:
        """Validate required transaction fields and ensure ledger integrity."""
        if not self.description:
            raise ValueError("Description cannot be empty.")
        if not self.debit_account_id:
            raise ValueError("Debit account ID cannot be empty.")
        if not self.credit_account_id:
            raise ValueError("Credit account ID cannot be empty.")
        if not self.action_type:
            raise ValueError("Action type cannot be empty.")
        if not self.entries:
            self.entries = self._build_default_entries()
        total_debits = sum(entry.debit_amount for entry in self.entries)
        total_credits = sum(entry.credit_amount for entry in self.entries)
        if abs(total_debits - total_credits) > 0.00001:
            raise ValueError("Transaction entries must balance.")

