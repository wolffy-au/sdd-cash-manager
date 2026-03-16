from datetime import datetime
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from sdd_cash_manager.database import get_db
from sdd_cash_manager.schemas.adjustment import (
    ManualBalanceAdjustmentCreate,
    ManualBalanceAdjustment,
)
from sdd_cash_manager.services.adjustment_service import ManualBalanceAdjustmentService
# Assuming a dependency for user authentication and authorization exists
# from sdd_cash_manager.security.auth import get_current_user # Example auth dependency

router = APIRouter()

logger = logging.getLogger(__name__)

# Placeholder for a function that returns user permissions or roles
async def get_user_permissions():
    # In a real application, this would check JWT, session, etc.
    # and return user roles or permissions. For now, returning a mock user.
    # This mock user would need to have an attribute like 'can_adjust_balance'
    return {"user_id": UUID(int=2), "roles": ["reconciler"]} # Example permissions

@router.post(
    "/accounts/{account_id}/adjust-balance",
    response_model=ManualBalanceAdjustment,
    status_code=status.HTTP_201_CREATED,
    summary="Manually adjust an account's balance",
)
async def create_manual_balance_adjustment(
    account_id: UUID,
    adjustment_data: ManualBalanceAdjustmentCreate,
    db: Session = Depends(get_db),
    # current_user: Dict[str, Any] = Depends(get_user_permissions) # Dependency for authorization
):
    """
    Manually adjust an account's balance.

    This endpoint allows users to set a target balance for an account.
    The system will automatically create a new transaction if the target balance
    differs from the current running balance as of the effective date.
    Requires 'reconciler' role or equivalent permission.
    """
    # --- T030: Implement permissioning logic ---
    # Check if the current user has the necessary permissions to perform balance adjustments.
    # This logic should be integrated with your authentication and authorization system.
    # Example check:
    # if "reconciler" not in current_user.get("roles", []):
    #     logger.warning(f"Unauthorized attempt to adjust balance for account {account_id} by user {current_user.get('user_id')}")
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to adjust balance.")
    # --- End T030: Permissioning ---

    logger.info(f"Received request to adjust balance for account {account_id}. Data: {adjustment_data}")
    
    # Placeholder for user ID from authentication context
    submitted_by_user_id = UUID(int=2) # Using the mocked user ID from get_user_permissions

    try:
        adjustment_service = ManualBalanceAdjustmentService(db)
        
        adjustment = adjustment_service.create_adjustment(
            account_id=account_id,
            adjustment_data=adjustment_data
        )
        
        # --- T030: Log audit entry ---
        # Log this successful adjustment attempt for audit purposes.
        logger.info(f"Manual balance adjustment created successfully for account {account_id} by user {submitted_by_user_id}. Adjustment ID: {adjustment.id}, Status: {adjustment.status}")
        # --- End T030: Audit logging ---
        
        return adjustment

    except ValueError as e:
        # Example: Account not found
        logger.error(f"ValueError during balance adjustment for account {account_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        # Catch errors from the service layer (e.g., transaction creation failure)
        logger.error(f"RuntimeError during balance adjustment for account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        # Log the exception details for debugging
        logger.error(f"Unexpected error during balance adjustment for account {account_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred during balance adjustment.")
