from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.schemas.reconciliation import ReconciliationViewEntry as ReconciliationViewEntrySchema
from sdd_cash_manager.services.reconciliation_service import ReconciliationService

router = APIRouter()
_get_db_dependency = Depends(get_db)

@router.get(
    "/accounts/{account_id}/reconciliation",
    summary="Get reconciliation view entries for an account",
)
async def get_reconciliation_view(
    account_id: UUID,
    db: Session = _get_db_dependency,
) -> List[ReconciliationViewEntrySchema]:
    """
    Retrieve reconciliation entries for a specific account.

    This endpoint returns a list of entries that are visible in the reconciliation view,
    including both standard transactions and manual adjustments.
    """
    try:
        reconciliation_service = ReconciliationService(db)
        reconciliation_models = reconciliation_service.get_reconciliation_entries_for_account(account_id)
        return [
            ReconciliationViewEntrySchema.model_validate(model)
            for model in reconciliation_models
        ]
    except Exception as e:
        print(f"Error fetching reconciliation view for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while fetching reconciliation data."
        ) from e
