import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.lib.auth import Role, TokenPayload, require_role
from sdd_cash_manager.models.adjustment import ManualBalanceAdjustment as ManualBalanceAdjustmentModel
from sdd_cash_manager.schemas.adjustment import (
    ManualBalanceAdjustment as ManualBalanceAdjustmentSchema,
)
from sdd_cash_manager.schemas.adjustment import (
    ManualBalanceAdjustmentCreate,
)
from sdd_cash_manager.services.adjustment_service import ManualBalanceAdjustmentService

router = APIRouter()
logger = logging.getLogger(__name__)
_adjustment_operator_dependency = Depends(require_role(Role.OPERATOR))
_get_db_dependency = Depends(get_db)


@router.post(
    "/accounts/{account_id}/adjust-balance",
    response_model=ManualBalanceAdjustmentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Manually adjust an account's balance",
)
async def create_manual_balance_adjustment(
    account_id: UUID,
    adjustment_data: ManualBalanceAdjustmentCreate,
    db: Session = _get_db_dependency,
    current_user: TokenPayload = _adjustment_operator_dependency,
) -> ManualBalanceAdjustmentModel:
    """
    Manually adjust an account's balance.

    Requires operator-level permission and records the request in the audit trail.
    """
    submitted_by_user_id = current_user.subject or adjustment_data.submitted_by_user_id
    adjustment_payload = adjustment_data.model_copy(
        update={"submitted_by_user_id": submitted_by_user_id}
    )

    logger.info(
        "Received manual adjustment for account %s (requested by %s) to %s",
        account_id,
        submitted_by_user_id,
        adjustment_payload.target_balance,
    )

    try:
        adjustment_service = ManualBalanceAdjustmentService(db)
        adjustment = adjustment_service.create_adjustment(
            account_id=account_id,
            adjustment_data=adjustment_payload,
        )
        logger.info(
            "Manual balance adjustment %s for account %s completed with status %s",
            adjustment.id,
            account_id,
            adjustment.status,
        )
        return adjustment
    except ValueError as exc:
        logger.warning("Adjustment request failed for account %s: %s", account_id, exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error(
            "Runtime failure creating balance adjustment for account %s: %s",
            account_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(
            "Unexpected error during balance adjustment for account %s: %s",
            account_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during balance adjustment.",
        ) from exc
