from datetime import datetime
from decimal import Decimal  # New import

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
