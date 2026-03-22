from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict


class ReconciliationSessionRequest(BaseModel):
    statement_date: date
    ending_balance: Decimal

    model_config = ConfigDict(extra="forbid")


class ReconciliationSessionResponse(BaseModel):
    id: str
    statement_date: date
    ending_balance: Decimal
    difference: Decimal
    state: str
    created_by: str | None = None
    created_at: datetime


class TransactionSelectionRequest(BaseModel):
    transaction_ids: List[str]

    model_config = ConfigDict(extra="forbid")


class DifferenceResponse(BaseModel):
    difference: Decimal
    remaining_uncleared: int
    difference_status: str
    guidance: str | None = None


class TransactionSummary(BaseModel):
    id: str
    amount: Decimal
    date: date
    description: str | None = None
    processing_status: str
    reconciliation_status: str
