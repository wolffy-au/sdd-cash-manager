import uuid
from typing import Optional

from sqlalchemy import Boolean, Column, Float, String

from sdd_cash_manager.models.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    currency = Column(String, nullable=False)
    accounting_category = Column(String, nullable=False)
    account_number = Column(String, nullable=True)
    banking_product_type = Column(String, nullable=True)
    available_balance = Column(Float, nullable=False, default=0.0)
    credit_limit = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    parent_account_id = Column(String, nullable=True)
    hidden = Column(Boolean, nullable=False, default=False)
    placeholder = Column(Boolean, nullable=False, default=False)

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
        self.id = id or str(uuid.uuid4())
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
