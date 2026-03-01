from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.schemas.account_schema import AccountCreateUpdate, AccountResponse, AccountUpdate
from sdd_cash_manager.schemas.transaction_schema import BalanceAdjustmentRequest, BalanceAdjustmentResponse
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import TransactionService


# Helper functions for dependency implementation
# These are NOT the FastAPI providers themselves, but the logic they use.
def _get_account_service_impl(db: Session) -> AccountService:
    return AccountService(db)

def _get_transaction_service_impl(account_service: AccountService) -> TransactionService:
    ts = TransactionService()
    ts.set_account_service(account_service)
    return ts

# Module-level dependency instances (these ARE the FastAPI providers)
db_dependency = Depends(get_db)
account_service_dependency = Depends(lambda db=db_dependency: _get_account_service_impl(db=db))
transaction_service_dependency = Depends(lambda acc_svc=account_service_dependency: _get_transaction_service_impl(account_service=acc_svc))

# --- API Router ---
router = APIRouter(prefix="/accounts", tags=["Accounts"])

# --- Account Endpoints ---

@router.post("/", response_model=AccountResponse, status_code=201)
def create_account(
    account_data: AccountCreateUpdate,
    account_service: AccountService = account_service_dependency
) -> AccountResponse:
    """
    Create a new financial account.
    """
    try:
        new_account = account_service.create_account(
            name=account_data.name,
            currency=account_data.currency,
            accounting_category=account_data.accounting_category,
            account_number=account_data.account_number,
            banking_product_type=account_data.banking_product_type,
            available_balance=account_data.available_balance,
            credit_limit=account_data.credit_limit,
            notes=account_data.notes,
            parent_account_id=account_data.parent_account_id,
            hidden=account_data.hidden,
            placeholder=account_data.placeholder
        )
        return AccountResponse(**new_account.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        # Log the exception here in a real app
        raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the account.") from None

@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    search_term: Optional[str] = None,
    hidden: Optional[bool] = None,
    placeholder: Optional[bool] = None,
    account_service: AccountService = account_service_dependency
) -> List[AccountResponse]:
    """
    Retrieve a list of accounts.
    Supports filtering by search term (name), hidden status, and placeholder status.
    """
    all_accounts = account_service.get_all_accounts()

    # Apply filters
    filtered_accounts = all_accounts
    if search_term:
        filtered_accounts = [acc for acc in filtered_accounts if search_term.lower() in acc.name.lower()]
    if hidden is not None:
        filtered_accounts = [acc for acc in filtered_accounts if acc.hidden == hidden]
    if placeholder is not None:
        filtered_accounts = [acc for acc in filtered_accounts if acc.placeholder == placeholder]

    return [AccountResponse(**acc.__dict__) for acc in filtered_accounts]

@router.get("/{account_id}", response_model=AccountResponse)
def get_account_by_id(
    account_id: str,
    account_service: AccountService = account_service_dependency
) -> AccountResponse:
    """
    Retrieve a specific account by its ID.
    """
    account = account_service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse(**account.__dict__)

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: str,
    account_data: AccountUpdate,
    account_service: AccountService = account_service_dependency
) -> AccountResponse:
    """
    Update an existing account.
    """
    # Prepare data for update, excluding fields that should not be updated or have defaults
    update_kwargs = account_data.model_dump(exclude_unset=True) # Only include fields that were provided

    updated_account = account_service.update_account(account_id, **update_kwargs)

    if updated_account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return AccountResponse(**updated_account.__dict__)

@router.delete("/{account_id}", status_code=204)
def delete_account(
    account_id: str,
    account_service: AccountService = account_service_dependency
) -> None:
    """
    Delete an account by its ID.
    """
    success = account_service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    # No content to return on successful deletion
    return

# --- Balance Adjustment Endpoint ---

@router.post("/{account_id}/adjust_balance", response_model=BalanceAdjustmentResponse)
def adjust_account_balance(
    account_id: str,
    request_data: BalanceAdjustmentRequest,
    transaction_service: TransactionService = transaction_service_dependency
) -> BalanceAdjustmentResponse:
    """
    Manually adjust an account's balance by creating a new transaction.
    This endpoint triggers the core logic for US3.
    """
    try:
        transaction = transaction_service.perform_balance_adjustment(
            account_id=account_id,
            target_balance=request_data.target_balance,
            adjustment_date=request_data.adjustment_date,
            description=request_data.description,
            action_type=request_data.action_type,
            notes=request_data.notes
        )

        if transaction is None:
            # This case happens if target_balance == current_balance, no adjustment needed.
            # Depending on requirements, this could be a 200 OK with a message, or a 400 Bad Request.
            # For now, let's raise a 400 if no adjustment was made.
            # In a real app, consider if this should return a specific response.
            raise HTTPException(status_code=400, detail="No adjustment needed as target balance matches current balance.")

        transaction_data = transaction.__dict__.copy()

        return BalanceAdjustmentResponse(
            transaction_id=transaction.id,
            account_id=account_id,
            new_balance=request_data.target_balance,
            **transaction_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e # e.g., AccountService not set
    except Exception:
        # Log the exception here in a real app
        raise HTTPException(status_code=500, detail="An unexpected error occurred during balance adjustment.") from None
