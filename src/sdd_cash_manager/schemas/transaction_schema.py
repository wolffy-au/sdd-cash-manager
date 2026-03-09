from datetime import datetime

from pydantic import BaseModel


class BalanceAdjustmentRequest(BaseModel):
    """Request schema for manually adjusting an account balance."""
    target_balance: float
    adjustment_date: datetime
    description: str
    action_type: str
    notes: str | None = None

class BalanceAdjustmentResponse(BaseModel):
    """Response schema describing a balance adjustment transaction."""
    transaction_id: str
    account_id: str
    new_balance: float
    id: str
    effective_date: datetime
    booking_date: datetime
    description: str
    amount: float
    debit_account_id: str
    credit_account_id: str
    processing_status: str # Use string to match enum value serialization
    reconciliation_status: str # Use string to match enum value serialization
    action_type: str
    notes: str | None = None
