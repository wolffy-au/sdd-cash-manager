from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.base import Base

if TYPE_CHECKING:
    from sdd_cash_manager.models.account import Account


class User(Base):
    """Lightweight placeholder representing a user who can submit adjustments."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manual_balance_adjustments: Mapped[List["ManualBalanceAdjustment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ManualBalanceAdjustment(Base):
    """SQLAlchemy model representing a manual balance adjustment request."""

    __tablename__ = "manual_balance_adjustments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    target_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    submitted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    adjustment_attempt_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_transaction_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("adjustment_transactions.transaction_id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)

    account: Mapped["Account"] = relationship(
        back_populates="manual_balance_adjustments",
        cascade="merge",
    )
    user: Mapped["User"] = relationship(back_populates="manual_balance_adjustments")
    transaction: Mapped["AdjustmentTransaction"] = relationship(
        back_populates="manual_balance_adjustment",
        uselist=False,
    )


class AdjustmentTransaction(Base):
    """SQLAlchemy model representing an automatically generated transaction for balance adjustments."""

    __tablename__ = "adjustment_transactions"

    transaction_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    reconciliation_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    account: Mapped["Account"] = relationship(back_populates="adjustment_transactions")
    manual_balance_adjustment: Mapped["ManualBalanceAdjustment"] = relationship(
        back_populates="transaction",
        uselist=False,
    )
