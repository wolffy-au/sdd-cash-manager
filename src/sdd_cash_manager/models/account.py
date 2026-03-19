from __future__ import annotations

import uuid
from decimal import Decimal  # New import
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Index, Numeric, String  # Changed Float to Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry

if TYPE_CHECKING:
    from sdd_cash_manager.models.transaction import Entry


class Account(Base):
    """Persistent model representing a financial account."""
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_parent_account_id", "parent_account_id"),
        Index("ix_accounts_name", "name"),
    )

    # Define attributes with explicit types that align with SQLAlchemy Columns
    # Using Mapped for better type hinting with SQLAlchemy 2.0+
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    accounting_category: Mapped[str] = mapped_column(String, nullable=False)
    account_number: Mapped[str | None] = mapped_column(String, nullable=True)
    banking_product_type: Mapped[str | None] = mapped_column(String, nullable=True)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.0"))
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    placeholder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    entries: Mapped[List["Entry"]] = relationship(back_populates="account")
    reconciliation_view_entries: Mapped[List[ReconciliationViewEntry]] = relationship(back_populates="account")
    manual_balance_adjustments: Mapped[List["ManualBalanceAdjustment"]] = relationship(back_populates="account")
    adjustment_transactions: Mapped[List["AdjustmentTransaction"]] = relationship(back_populates="account")

    def __init__(
        self,
        name: str,
        currency: str,
        accounting_category: str,
        id: str | None = None,
        account_number: str | None = None,
        banking_product_type: str | None = None,
        available_balance: Decimal = Decimal("0.0"),
        credit_limit: Decimal | None = None,
        notes: str | None = None,
        parent_account_id: str | None = None,
        hidden: bool = False,
        placeholder: bool = False
    ):
        """Initialize an account instance.

        Args:
            name: Human-readable name for the account.
            currency: ISO 4217 currency code.
            accounting_category: Financial classification of the account.
            id: Optional identifier; a new UUID string is generated when omitted.
            account_number: External reference number for the account.
            banking_product_type: Banking product type represented by the account.
            available_balance: Starting available balance.
            credit_limit: Optional credit limit for the account.
            notes: User-provided notes.
            parent_account_id: Identifier of a parent account, if any.
            hidden: Flag indicating if the account should be hidden.
            placeholder: Flag indicating if the account is a placeholder.

        Returns:
            None: Attributes are assigned, and `id` is auto-generated when necessary.
        """
        # Assign values to the ORM-mapped attributes.
        # SQLAlchemy will handle the actual column mapping.
        # The `id` default handles creation, so we only assign if provided.
        if id is not None:
            self.id = id
        else:
            self.id = str(uuid.uuid4())  # Ensure id is always set, even if not provided
        self.name = name
        self.currency = currency
        self.accounting_category = accounting_category
        self.account_number = account_number
        self.banking_product_type = banking_product_type
        self.available_balance = available_balance
        self.credit_limit = credit_limit
        self.notes = notes
        self.parent_account_id = parent_account_id
        self.hidden = hidden
        self.placeholder = placeholder
