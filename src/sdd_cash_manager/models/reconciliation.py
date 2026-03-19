import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.base import Base

if TYPE_CHECKING:
    from sdd_cash_manager.models.account import Account


class ReconciliationViewEntry(Base):
    """SQLAlchemy model representing an entry in the reconciliation view."""

    __tablename__ = "reconciliation_view_entries"

    entry_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    entry_date: Mapped[Date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    is_adjustment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reconciled_status: Mapped[str] = mapped_column(String, nullable=False)
    original_transaction_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("adjustment_transactions.transaction_id"),
        nullable=True,
    )

    account: Mapped["Account"] = relationship(back_populates="reconciliation_view_entries")
