"""Tracks sets of transactions that appear identical and require manual review."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base

ACCOUNTS_ID_FOREIGN_KEY = "accounts.id"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DuplicateCandidate(Base):
    """Represents a detected set of duplicate ledger entries for review."""

    __tablename__ = "duplicate_candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="account")
    matching_transaction_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0"))
    recommended_action: Mapped[str] = mapped_column(String(32), nullable=False, default="merge")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    account: Mapped[Account] = relationship("Account")

    def touch(self) -> None:
        """Refresh the timestamp when the candidate is updated."""
        self.updated_at = _utc_now()
