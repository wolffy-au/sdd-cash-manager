from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Table, func
from sqlalchemy import Numeric as SqlNumeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.base import Base

if TYPE_CHECKING:
    from sdd_cash_manager.models.transaction import Transaction


class ReconciliationSessionState(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"


reconciliation_session_transactions = Table(
    "reconciliation_session_transactions",
    Base.metadata,
    Column("session_id", String, ForeignKey("reconciliation_sessions.id"), primary_key=True),
    Column("transaction_id", String, ForeignKey("transactions.id"), primary_key=True),
    Column("selected_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


class ReconciliationSession(Base):
    __tablename__ = "reconciliation_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    ending_balance: Mapped[Decimal] = mapped_column(SqlNumeric(18, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(SqlNumeric(18, 2), nullable=False)
    state: Mapped[ReconciliationSessionState] = mapped_column(String(32), default=ReconciliationSessionState.IN_PROGRESS.value)
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        secondary=reconciliation_session_transactions,
        back_populates="reconciliation_sessions",
        lazy="selectin",
    )


class BankStatementSnapshot(Base):
    __tablename__ = "bank_statement_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(SqlNumeric(18, 2), nullable=False)
    statement_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transaction_cutoff: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
