
from decimal import Decimal  # New import

from pydantic import BaseModel


class AccountCreateUpdate(BaseModel):
    name: str
    currency: str
    accounting_category: str
    account_number: str | None = None
    banking_product_type: str | None = None
    available_balance: Decimal = Decimal("0.0") # Changed to Decimal
    credit_limit: Decimal | None = None # Changed to Decimal
    notes: str | None = None
    parent_account_id: str | None = None
    hidden: bool = False
    placeholder: bool = False

class AccountUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    accounting_category: str | None = None
    banking_product_type: str | None = None
    account_number: str | None = None
    available_balance: Decimal | None = None # Changed to Decimal
    credit_limit: Decimal | None = None # Changed to Decimal
    notes: str | None = None
    parent_account_id: str | None = None
    hidden: bool | None = None
    placeholder: bool | None = None

class AccountResponse(BaseModel):
    """
    Rely on BaseModel's default __init__ so Pydantic can track optional fields
    (such as account_number) when they are provided in the request.
    """
    id: str
    name: str
    currency: str
    accounting_category: str
    account_number: str | None = None
    banking_product_type: str | None = None
    available_balance: Decimal # Changed to Decimal
    hierarchy_balance: Decimal # Changed to Decimal
    credit_limit: Decimal | None = None # Changed to Decimal
    notes: str | None = None
    parent_account_id: str | None = None
    hidden: bool
    placeholder: bool
