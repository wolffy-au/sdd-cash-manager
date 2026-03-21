from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, List

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.enums import (
    ProcessingStatus,
    ReconciliationStatus,
)

ACCOUNTS_ID_FOREIGN_KEY = "accounts.id"

def _current_utc_time() -> datetime:
    """Return the current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


def _coerce_decimal_value(value: Any, *, allow_none: bool = False) -> Decimal:
    if value is None:
        if allow_none:
            return Decimal(0)
        raise ValueError("Amount is required.")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)



class Entry(Base):
    """SQLAlchemy model for a double-entry ledger row used by transactions."""
    __tablename__ = "entries"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.id"))
    account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY))
    debit_amount: Mapped[Decimal] = mapped_column(
        nullable=False, default=Decimal(0.0))
    credit_amount: Mapped[Decimal] = mapped_column(
        nullable=False, default=Decimal(0.0))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_current_utc_time)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __init__(self, **kwargs: Any):
        debit_amount = _coerce_decimal_value(kwargs.get("debit_amount"), allow_none=True)
        credit_amount = _coerce_decimal_value(kwargs.get("credit_amount"), allow_none=True)

        if debit_amount < Decimal(0) or credit_amount < Decimal(0):
            raise ValueError("Entry amounts must not be negative.")
        if debit_amount > 0 and credit_amount > 0:
            raise ValueError("Entry cannot have both debit and credit amounts.")
        if debit_amount == 0 and credit_amount == 0:
            raise ValueError("Entry must have a non-zero debit or credit amount.")

        kwargs["debit_amount"] = debit_amount
        kwargs["credit_amount"] = credit_amount
        super().__init__(**kwargs)

    # Relationships
    transaction: Mapped["Transaction"] = relationship(back_populates="entries")
    # Use string literal for forward reference
    account: Mapped["Account"] = relationship(
        "Account", back_populates="entries")


class Transaction(Base):
    """SQLAlchemy model for an account transaction."""
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()))
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    booking_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # The amount of the transaction.
    amount: Mapped[Decimal] = mapped_column(nullable=False)
    debit_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY))
    credit_account_id: Mapped[str] = mapped_column(ForeignKey(ACCOUNTS_ID_FOREIGN_KEY))
    # e.g., "Manual Adjustment", "Payment"
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        String(50), default=ProcessingStatus.PENDING)
    reconciliation_status: Mapped[ReconciliationStatus] = mapped_column(
        String(50), default=ReconciliationStatus.PENDING_RECONCILIATION)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_current_utc_time)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_current_utc_time,
        onupdate=_current_utc_time,
    )

    # Relationships
    entries: Mapped[List["Entry"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan")
    debit_account: Mapped["Account"] = relationship("Account", foreign_keys=[
                                                    debit_account_id], post_update=True)  # Explicit foreign_keys, string literal
    credit_account: Mapped["Account"] = relationship("Account", foreign_keys=[
                                                     credit_account_id], post_update=True)  # Explicit foreign_keys, string literal

    def __init__(self, **kw: Any):
        entries = kw.pop("entries", None)
        kw.setdefault("id", str(uuid.uuid4()))
        kw["amount"] = self._coerce_transaction_amount(kw.get("amount"))
        self._ensure_required_fields(kw)
        kw.setdefault("processing_status", ProcessingStatus.PENDING)
        kw.setdefault("reconciliation_status", ReconciliationStatus.PENDING_RECONCILIATION)

        super().__init__(**kw)

        if entries is None:
            self._populate_default_entries()
        else:
            self._assign_entries(entries)

    def __repr__(self):
        return (
            f"<Transaction(id='{self.id}', description='{self.description}', "
            f"amount={self.amount}, effective_date='{self.effective_date}')>"
        )

    def _ensure_required_fields(self, kw: dict[str, Any]) -> None:
        kw["description"] = self._validate_required_text(
            kw.get("description"), "Description cannot be empty."
        )
        kw["debit_account_id"] = self._validate_required_text(
            kw.get("debit_account_id"), "Debit account ID cannot be empty."
        )
        kw["credit_account_id"] = self._validate_required_text(
            kw.get("credit_account_id"), "Credit account ID cannot be empty."
        )

    @staticmethod
    def _validate_required_text(value: str | None, message: str) -> str:
        if value is None or not value.strip():
            raise ValueError(message)
        return value

    @staticmethod
    def _coerce_transaction_amount(value: Any) -> Decimal:
        amount = _coerce_decimal_value(value)
        if amount == 0:
            raise ValueError("Amount must be non-zero.")
        return amount

    def _populate_default_entries(self) -> None:
        amount = abs(self.amount)
        if amount == 0:
            raise ValueError("Amount must be non-zero.")
        debit_entry = Entry(
            transaction_id=self.id,
            account_id=self.debit_account_id,
            debit_amount=amount,
            credit_amount=Decimal(0),
        )
        credit_entry = Entry(
            transaction_id=self.id,
            account_id=self.credit_account_id,
            debit_amount=Decimal(0),
            credit_amount=amount,
        )
        self.entries = [debit_entry, credit_entry]
        self._validate_entries_balance(self.entries)

    def _assign_entries(self, entries: list[Entry] | tuple[Entry, ...]) -> None:
        normalized_entries = list(entries)
        if not normalized_entries:
            raise ValueError("Entries collection cannot be empty.")
        for entry in normalized_entries:
            entry.transaction_id = self.id
        self.entries = normalized_entries
        self._validate_entries_balance(self.entries)

    def _validate_entries_balance(self, entries: list[Entry]) -> None:
        total_debits = sum((entry.debit_amount for entry in entries), Decimal(0))
        total_credits = sum((entry.credit_amount for entry in entries), Decimal(0))
        if total_debits != total_credits:
            raise ValueError("Entries must balance.")
