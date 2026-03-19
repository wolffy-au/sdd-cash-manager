from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReconciliationViewEntryBase(BaseModel):
    account_id: UUID
    entry_date: date
    amount: Decimal
    description: str
    is_adjustment: bool = False
    reconciled_status: str # Assuming string representation for now, can be Enum later


class ReconciliationViewEntryCreate(ReconciliationViewEntryBase):
    pass


class ReconciliationViewEntryUpdate(ReconciliationViewEntryBase):
    # Allow updating status, etc. if needed
    reconciled_status: str


class ReconciliationViewEntry(ReconciliationViewEntryBase):
    entry_id: UUID
    original_transaction_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
