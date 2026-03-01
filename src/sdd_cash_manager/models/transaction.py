import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus


@dataclass
class Transaction:
    effective_date: datetime # Date when the transaction's effect is recognized
    booking_date: datetime # Date when the transaction is entered into the system
    description: str # Description of the transaction
    amount: float # The amount of the transaction. Positive for income/credits, negative for expenses/debits.
    debit_account_id: str # The ID of the account from which funds are debited
    credit_account_id: str # The ID of the account to which funds are credited
    action_type: str # Type of action (e.g., "Manual Adjustment", "Payment", "Transfer")
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    processing_status: ProcessingStatus = ProcessingStatus.PENDING # Current status of the transaction processing
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING_RECONCILIATION # Status regarding account reconciliation
    notes: Optional[str] = None # Additional notes for the transaction

    def __post_init__(self):
        if not self.description:
            raise ValueError("Description cannot be empty.")
        if not self.debit_account_id:
            raise ValueError("Debit account ID cannot be empty.")
        if not self.credit_account_id:
            raise ValueError("Credit account ID cannot be empty.")
        if not self.action_type:
            raise ValueError("Action type cannot be empty.")

