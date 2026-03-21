"""Captures planned account merges along with audit/state metadata."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base

ACCOUNTS_ID_FOREIGN_KEY = "accounts.id"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AccountMergePlan(Base):
    """Represents a proposed account merge, including validation state and audit notes."""

    __tablename__ = "account_merge_plans"

    plan_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY), nullable=False)
    target_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY), nullable=False)
    reparenting_map: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    affected_entries_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    audit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    initiated_by: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    depth_validation_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_metadata: Mapped[dict[str, str] | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_account: Mapped[Account] = relationship("Account", foreign_keys=[source_account_id])
    target_account: Mapped[Account] = relationship("Account", foreign_keys=[target_account_id])

    def mark_validated(self) -> None:
        """Note that validation succeeded and update timestamps accordingly."""
        self.status = "validated"
        self.updated_at = _utc_now()
