from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import Column, Date, Boolean, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from sdd_cash_manager.database import Base

# Placeholder model for Account, assuming it exists for ForeignKey
class Account(Base):
    """
    Placeholder SQLAlchemy model for the Account entity.
    Assumed to exist for defining foreign key relationships and ORM back_populates.
    """
    __tablename__ = "accounts"
    id = Column(UUID, primary_key=True)
    running_balance = Column(Numeric, nullable=False)
    manual_balance_adjustments = relationship("ManualBalanceAdjustment", back_populates="account")
    adjustment_transactions = relationship("AdjustmentTransaction", back_populates="account")
    reconciliation_view_entries = relationship("ReconciliationViewEntry", back_populates="account")


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

    entry_id = Column(UUID, primary_key=True, default=uuid4)
    account_id = Column(UUID, ForeignKey("accounts.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    amount = Column(Numeric, nullable=False)
    description = Column(String, nullable=False)
    is_adjustment = Column(Boolean, nullable=False, default=False)
    reconciled_status = Column(String, nullable=False)  # e.g., PENDING_RECONCILIATION, RECONCILED, UNRECONCILED
    original_transaction_id = Column(UUID, ForeignKey("adjustment_transactions.transaction_id"), nullable=True) # Assuming adjustment_transactions table exists

    # Relationships
    account = relationship("Account", back_populates="reconciliation_view_entries")
    # original_transaction = relationship("AdjustmentTransaction") # Example of relationship if needed
