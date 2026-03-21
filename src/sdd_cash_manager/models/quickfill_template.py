"""QuickFill suggestion templates derived from historical transactions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.transaction import Transaction

ACCOUNTS_ID_FOREIGN_KEY = "accounts.id"
TRANSACTIONS_ID_FOREIGN_KEY = "transactions.id"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QuickFillTemplate(Base):
    """Represents a high-confidence suggestion for creating a transaction."""

    __tablename__ = "quickfill_templates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transfer_from_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY), nullable=False)
    transfer_to_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    memo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0"))
    history_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_transaction_id: Mapped[str | None] = mapped_column(ForeignKey(TRANSACTIONS_ID_FOREIGN_KEY), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    transfer_from_account: Mapped[Account] = relationship("Account", foreign_keys=[transfer_from_account_id])
    transfer_to_account: Mapped[Account] = relationship("Account", foreign_keys=[transfer_to_account_id])
    source_transaction: Mapped[Transaction | None] = relationship("Transaction")

    def mark_used(self) -> None:
        """Update the last used timestamp when a template is surfaced."""
        self.last_used_at = datetime.now(timezone.utc)
