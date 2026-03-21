from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal  # New import
from typing import Annotated, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, condecimal, constr, field_validator


class BalanceAdjustmentRequest(BaseModel):
    """Request schema for manually adjusting an account balance."""
    target_balance: Decimal # Changed to Decimal
    adjustment_date: datetime
    description: str
    action_type: str
    action: str
    notes: str | None = None

class BalanceAdjustmentResponse(BaseModel):
    """Response schema describing a balance adjustment transaction."""
    transaction_id: str
    account_id: str
    new_balance: Decimal # Changed to Decimal
    id: str
    effective_date: datetime
    booking_date: datetime
    description: str
    amount: Decimal # Changed to Decimal
    debit_account_id: str
    credit_account_id: str
    processing_status: str # Use string to match enum value serialization
    reconciliation_status: str # Use string to match enum value serialization
    action_type: str
    notes: str | None = None


DateType = date

AmountField = Annotated[Decimal, condecimal(gt=Decimal("0.00"), max_digits=18, decimal_places=2)]
CurrencyField = Annotated[str, constr(min_length=3, max_length=3)]
ActionField = Annotated[str, constr(strip_whitespace=True, min_length=1, max_length=64)]

class TransactionRequest(BaseModel):
    """API payload for creating double-entry transactions."""

    transfer_from: UUID
    transfer_to: UUID
    action: ActionField
    amount: AmountField
    currency: CurrencyField
    description: str | None = None
    memo: str | None = None
    date: DateType | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("currency")
    def _normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("action")
    def _normalize_action(cls, value: str) -> str:
        return value.strip()


class TransactionEntryResponse(BaseModel):
    """Representation of individual entries returned after transaction creation."""

    entry_id: str
    account_id: str
    debit_amount: Decimal
    credit_amount: Decimal
    notes: str | None = None


class TransactionResponse(BaseModel):
    """Response payload covering the canonical transaction plus entries."""

    transaction_id: str
    effective_date: datetime
    booking_date: datetime
    description: str
    action_type: str
    action: str
    amount: Decimal
    currency: str
    transfer_from_account_id: str
    transfer_to_account_id: str
    debit_account_id: str
    credit_account_id: str
    processing_status: str
    reconciliation_status: str
    notes: str | None = None
    memo: str | None = None
    entries: List[TransactionEntryResponse]


class QuickFillTemplateResponse(BaseModel):
    """DTO returned for approved QuickFill templates."""

    id: str
    action: str
    currency: str
    transfer_from_account_id: str
    transfer_to_account_id: str
    amount: Decimal
    description: str | None = None
    memo: str | None = None
    confidence_score: Decimal
    history_count: int
    last_used_at: datetime | None = None
    is_approved: bool
    approved_at: datetime | None = None


class DuplicateCandidateResponse(BaseModel):
    """Structured view of detected duplicate transaction candidates."""

    candidate_id: str
    account_id: str
    scope: str
    matching_transaction_ids: List[str]
    amount: Decimal
    date: date
    description: str | None = None
    confidence: Decimal
    status: str


class DuplicateMergeRequest(BaseModel):
    """Payload for consolidating duplicate transactions."""

    candidate_id: str
    preserve_audit: bool = False


class DuplicateMergeResponse(BaseModel):
    """Summary of the duplicate consolidation result."""

    candidate_id: str
    canonical_transaction_id: str
    removed_transaction_ids: List[str]
    before_balance: Decimal
    after_balance: Decimal
    status: str


class AccountMergePlanRequest(BaseModel):
    """Payload for proposing an account merge."""

    source_account_id: str
    target_account_id: str
    reparenting_map: Dict[str, str]
    audit_notes: str | None = None
    initiated_by: str | None = None
    metadata: Dict[str, str] | None = None


class AccountMergePlanResponse(BaseModel):
    """Response describing the status of an account merge plan."""

    plan_id: str
    source_account_id: str
    target_account_id: str
    reparenting_map: Dict[str, str]
    affected_entries_count: int
    status: str
    depth_validation_error: str | None = None
    audit_notes: str | None = None
    initiated_by: str | None = None
    metadata: Dict[str, str] | None = None
    created_at: datetime
    updated_at: datetime
    executed_at: datetime | None = None
