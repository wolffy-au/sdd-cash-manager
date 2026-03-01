import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from sdd_cash_manager.models.base import Base


class Account(Base):
    __tablename__ = "accounts"

    # Define attributes with explicit types that align with SQLAlchemy Columns
    # Using Mapped for better type hinting with SQLAlchemy 2.0+
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    accounting_category: Mapped[str] = mapped_column(String, nullable=False)
    account_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    banking_product_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    available_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    credit_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parent_account_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    placeholder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __init__(
        self,
        name: str,
        currency: str,
        accounting_category: str,
        id: Optional[str] = None,
        account_number: Optional[str] = None,
        banking_product_type: Optional[str] = None,
        available_balance: float = 0.0,
        credit_limit: Optional[float] = None,
        notes: Optional[str] = None,
        parent_account_id: Optional[str] = None,
        hidden: bool = False,
        placeholder: bool = False
    ):
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
