
from pydantic import BaseModel


class AccountCreateUpdate(BaseModel):
    name: str
    currency: str
    accounting_category: str
    account_number: str | None = None
    banking_product_type: str | None = None
    available_balance: float = 0.0
    credit_limit: float | None = None
    notes: str | None = None
    parent_account_id: str | None = None
    hidden: bool = False
    placeholder: bool = False

class AccountUpdate(BaseModel):
    name: str | None = None
    currency: str | None = None
    accounting_category: str | None = None
    account_number: str | None = None
    banking_product_type: str | None = None
    available_balance: float | None = None
    credit_limit: float | None = None
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
    available_balance: float
    hierarchy_balance: float
    credit_limit: float | None = None
    notes: str | None = None
    parent_account_id: str | None = None
    hidden: bool
    placeholder: bool
