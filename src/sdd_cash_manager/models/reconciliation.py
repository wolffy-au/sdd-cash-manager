import uuid

from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship

from sdd_cash_manager.database import Base


class ReconciliationViewEntry(Base):
    """
    SQLAlchemy model representing an entry in the reconciliation view.

    This model captures details of transactions (including manual adjustments)
    as they appear in reconciliation reports. It provides a structured way
    to query and display reconciliation-relevant data.

    Attributes:
        entry_id (UUID): Unique identifier for the reconciliation entry.
        account_id (UUID): Foreign key referencing the associated account.
        entry_date (date): The date of the reconciliation entry.
        amount (Decimal): The monetary amount of the entry.
        description (str): A description of the entry.
        is_adjustment (bool): Flag indicating if this entry is from a manual balance adjustment.
        reconciled_status (str): The reconciliation status (e.g., PENDING_RECONCILIATION, RECONCILED, UNRECONCILED).
        original_transaction_id (Optional[UUID]): Foreign key referencing the original transaction, if applicable.
    """
    __tablename__ = "reconciliation_view_entries"

    entry_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    amount = Column(Numeric, nullable=False)
    description = Column(String, nullable=False)
    is_adjustment = Column(Boolean, nullable=False, default=False)
    reconciled_status = Column(String, nullable=False)  # e.g., PENDING_RECONCILIATION, RECONCILED, UNRECONCILED
    original_transaction_id = Column(String, ForeignKey("adjustment_transactions.transaction_id"), nullable=True) # Assuming adjustment_transactions table exists

    # Relationships
    account = relationship("Account", back_populates="reconciliation_view_entries")
    # original_transaction = relationship("AdjustmentTransaction") # Example of relationship if needed
