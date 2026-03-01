from typing import Optional

from pydantic import BaseModel


class AccountCreateUpdate(BaseModel):
    name: str
    currency: str
    accounting_category: str
    account_number: Optional[str] = None
    banking_product_type: Optional[str] = None
    available_balance: float = 0.0
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    parent_account_id: Optional[str] = None
    hidden: bool = False
    placeholder: bool = False

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    accounting_category: Optional[str] = None
    account_number: Optional[str] = None
    banking_product_type: Optional[str] = None
    available_balance: Optional[float] = None
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    parent_account_id: Optional[str] = None
    hidden: Optional[bool] = None
    placeholder: Optional[bool] = None

class AccountResponse(BaseModel):
    """
    Rely on BaseModel's default __init__ so Pydantic can track optional fields
    (such as account_number) when they are provided in the request.
    """
    id: str
    name: str
    currency: str
    accounting_category: str
    account_number: Optional[str] = None
    banking_product_type: Optional[str] = None
    available_balance: float
    credit_limit: Optional[float] = None
    notes: Optional[str] = None
    parent_account_id: Optional[str] = None
    hidden: bool
    placeholder: bool

