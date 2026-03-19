from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from sdd_cash_manager.models.enums import ReconciliationStatus


class ReconciliationViewEntryBase(BaseModel):
    account_id: UUID
    entry_date: date
    amount: Decimal
    description: str
    is_adjustment: bool = False
    reconciled_status: ReconciliationStatus


class ReconciliationViewEntryCreate(ReconciliationViewEntryBase):
    pass


class ReconciliationViewEntryUpdate(ReconciliationViewEntryBase):
    # Allow updating status, etc. if needed
    reconciled_status: ReconciliationStatus


class ReconciliationViewEntry(ReconciliationViewEntryBase):
    entry_id: UUID
    original_transaction_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)
