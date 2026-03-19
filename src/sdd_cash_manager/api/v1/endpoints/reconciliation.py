from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry as ReconciliationViewEntryModel
from sdd_cash_manager.schemas.reconciliation import ReconciliationViewEntry as ReconciliationViewEntrySchema

router = APIRouter()
_get_db_dependency = Depends(get_db)

@router.get(
    "/accounts/{account_id}/reconciliation",
    response_model=List[ReconciliationViewEntrySchema],  # Return a list of entries
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
        # In a real application, this would likely involve a ReconciliationService
        # to query the database for ReconciliationViewEntry records associated with the account_id.
        # For now, we'll simulate a query.

        # Example of how a service might be used:
        # reconciliation_service = ReconciliationService(db)
        # entries = reconciliation_service.get_reconciliation_entries(account_id)

        account_id_value = str(account_id)
        reconciliation_models = db.query(ReconciliationViewEntryModel).filter(
            ReconciliationViewEntryModel.account_id == account_id_value
        ).all()

        if not reconciliation_models:
            return []

        reconciliation_entries = [
            ReconciliationViewEntrySchema.model_validate(model)
            for model in reconciliation_models
        ]
        return reconciliation_entries

    except NoResultFound:
        # Although .all() returns an empty list, a .one_or_none() might raise NoResultFound
        # We handle it defensively, but an empty list is more common for .all()
        return [] # Return empty list if no entries found for the account
    except Exception as e:
        # Log the exception details for debugging
        print(f"Error fetching reconciliation view for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while fetching reconciliation data."
        ) from e
