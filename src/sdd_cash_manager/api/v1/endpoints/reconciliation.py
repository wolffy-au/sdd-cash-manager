from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from sdd_cash_manager.database import get_db
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry
from sdd_cash_manager.schemas.reconciliation import ReconciliationViewEntry # Assuming schema maps directly to model for GET
from sdd_cash_manager.services.reconciliation_service import ReconciliationService # For potential service interaction if needed for fetching

router = APIRouter()

@router.get(
    "/accounts/{account_id}/reconciliation",
    response_model=List[ReconciliationViewEntry], # Return a list of entries
    summary="Get reconciliation view entries for an account",
)
async def get_reconciliation_view(
    account_id: UUID,
    db: Session = Depends(get_db),
):
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

        # Simulating a query result for demonstration purposes
        # Replace this with actual database query logic
        reconciliation_entries = db.query(ReconciliationViewEntry).filter(
            ReconciliationViewEntry.account_id == account_id
        ).all()

        if not reconciliation_entries:
            # Return empty list if no entries found, not necessarily an error
            return [] 
        
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
        )
