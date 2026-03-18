from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator # Import field_validator
from pydantic import ConfigDict # Import ConfigDict


# --- ManualBalanceAdjustment Schemas ---
class ManualBalanceAdjustmentBase(BaseModel):
    """
    Base Pydantic model for manual balance adjustment data.
    Includes common fields used in create and update operations.
    """
    target_balance: Decimal = Field(..., ge=0, description="The desired new balance for the account.")
    effective_date: date = Field(..., description="The date on which this adjustment should take effect.")
    submitted_by_user_id: UUID = Field(..., description="The UUID of the user who initiated the adjustment.")

    # Update @validator to @field_validator for Pydantic V2 compatibility
    @field_validator("effective_date")
    def check_effective_date_validity(cls, value):
        """
        Validates that the effective date is within a reasonable range.
        
        Note: Actual business logic for 'current statement range' might require
        external context or configuration and should be refined.
        """
        today = date.today()
        # Example: disallow dates more than 1 year in the past or future
        if not (date(today.year - 1, today.month, today.day) <= value <= date(today.year + 1, today.month, today.day)):
             raise ValueError("Effective date must be within a reasonable range (e.g., +/- 1 year from today).")
        return value


class ManualBalanceAdjustmentCreate(ManualBalanceAdjustmentBase):
    """
    Pydantic schema for creating a manual balance adjustment.
    Inherits base fields and is used for incoming request data.
    """
    pass


class ManualBalanceAdjustmentUpdate(ManualBalanceAdjustmentBase):
    """
    Pydantic schema for updating a manual balance adjustment.
    Fields that can be updated after creation, such as status.
    """
    status: Literal["PENDING", "COMPLETED", "ZERO_DIFFERENCE"]


class ManualBalanceAdjustment(ManualBalanceAdjustmentBase):
    """
    Pydantic model representing a full manual balance adjustment, including system-generated fields.
    Used for response payloads and ORM mapping.
    """
    id: int
    account_id: UUID
    adjustment_attempt_timestamp: datetime
    created_transaction_id: Optional[UUID] = None
    status: Literal["PENDING", "COMPLETED", "ZERO_DIFFERENCE"]

    # Update Config class to use model_config for Pydantic V2 compatibility
    # orm_mode is renamed to from_attributes
    model_config = ConfigDict(from_attributes=True)


# --- AdjustmentTransaction Schemas ---
class AdjustmentTransactionBase(BaseModel):
    """
    Base Pydantic model for adjustment transaction data.
    Contains common fields for transaction details.
    """
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="The absolute amount of the transaction.")
    transaction_type: Literal["ADJUSTMENT_DEBIT", "ADJUSTMENT_CREDIT"] = Field(..., description="Type of adjustment transaction.")
    description: str = Field(..., min_length=1, description="A brief description of the transaction.")
    reconciliation_metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata for reconciliation purposes.")


class AdjustmentTransactionCreate(AdjustmentTransactionBase):
    """
    Pydantic schema for creating an adjustment transaction.
    System-generated fields like transaction_id, account_id, effective_date, created_at
    are handled by the service or ORM and are not included here for creation payload.
    """
    pass


class AdjustmentTransactionUpdate(AdjustmentTransactionBase):
    """
    Pydantic schema for updating an adjustment transaction.
    Fields that might be updated after creation, if applicable.
    """
    pass


class AdjustmentTransaction(AdjustmentTransactionBase):
    """
    Pydantic model representing a full adjustment transaction, including system-generated fields.
    Used for response payloads and ORM mapping.
    """
    transaction_id: UUID
    account_id: UUID
    effective_date: date
    created_at: datetime

    # Update Config class to use model_config for Pydantic V2 compatibility
    # orm_mode is renamed to from_attributes
    model_config = ConfigDict(from_attributes=True)

