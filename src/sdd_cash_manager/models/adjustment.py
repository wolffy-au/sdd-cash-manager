from datetime import datetime
import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from sdd_cash_manager.database import Base
from sdd_cash_manager.models.account import Account


class User(Base):
    """Lightweight placeholder representing a user who can submit adjustments."""

    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manual_balance_adjustments = relationship("ManualBalanceAdjustment", back_populates="user")


class ManualBalanceAdjustment(Base):
    """
    SQLAlchemy model representing a manual balance adjustment request.

    Stores the target balance, effective date, user submitting the request,
    and the status of the adjustment process. Links to the created transaction if any.
    """

    __tablename__ = "manual_balance_adjustments"

    id = Column(Integer, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    target_balance = Column(Numeric(18, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    submitted_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    adjustment_attempt_timestamp = Column(DateTime, nullable=False)
    created_transaction_id = Column(String, ForeignKey("adjustment_transactions.transaction_id"), nullable=True)
    status = Column(String, nullable=False)  # e.g., PENDING, COMPLETED, ZERO_DIFFERENCE

    account = relationship("Account", back_populates="manual_balance_adjustments")
    user = relationship("User", back_populates="manual_balance_adjustments")
    transaction = relationship("AdjustmentTransaction", back_populates="manual_balance_adjustment", uselist=False)


class AdjustmentTransaction(Base):
    """
    SQLAlchemy model representing an automatically generated transaction for balance adjustments.

    Stores details of the transaction, including amount, type, description, and creation timestamp.
    Links back to the original adjustment request.
    """

    __tablename__ = "adjustment_transactions"

    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    transaction_type = Column(String, nullable=False)  # e.g., ADJUSTMENT_DEBIT, ADJUSTMENT_CREDIT
    description = Column(String, nullable=False)
    reconciliation_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    account = relationship("Account", back_populates="adjustment_transactions")
    manual_balance_adjustment = relationship("ManualBalanceAdjustment", back_populates="transaction", uselist=False)
