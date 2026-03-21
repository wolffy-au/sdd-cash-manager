from datetime import date, datetime
from decimal import Decimal  # New import
from typing import Dict, List

from pydantic import BaseModel


class BalanceAdjustmentRequest(BaseModel):
    """Request schema for manually adjusting an account balance."""
    target_balance: Decimal # Changed to Decimal
    adjustment_date: datetime
    description: str
    action_type: str
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


class QuickFillTemplateResponse(BaseModel):
    """DTO returned for approved QuickFill templates."""

    id: str
    action: str
    currency: str
    transfer_from_account_id: str
    transfer_to_account_id: str
    amount: Decimal
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
