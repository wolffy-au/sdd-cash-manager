import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.schemas.reconciliation_schema import (
    DifferenceResponse,
    ReconciliationSessionRequest,
    ReconciliationSessionResponse,
    TransactionSelectionRequest,
    TransactionSummary,
    UnreconciledTransactionsResponse,
)
from sdd_cash_manager.services.reconciliation_service import ReconciliationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])
_get_db_dependency = Depends(get_db)


@router.post("/sessions")
async def create_reconciliation_session(
    payload: ReconciliationSessionRequest,
    db: Session = _get_db_dependency,
) -> ReconciliationSessionResponse:
    service = ReconciliationService(db)
    session_obj = service.create_reconciliation_session(
        db,
        statement_date=payload.statement_date,
        ending_balance=payload.ending_balance,
    )
    service.create_bank_statement_snapshot(
        db,
        closing_date=payload.statement_date,
        closing_balance=payload.ending_balance,
    )
    return ReconciliationSessionResponse(
        id=session_obj.id,
        statement_date=session_obj.statement_date,
        ending_balance=session_obj.ending_balance,
        difference=session_obj.difference,
        state=session_obj.state,
        created_by=session_obj.created_by,
        created_at=session_obj.created_at,
    )


@router.get("/sessions/unreconciled")
async def list_unreconciled_transactions(
    db: Session = _get_db_dependency,
) -> UnreconciledTransactionsResponse:
    service = ReconciliationService(db)
    cutoff = service.get_latest_statement_cutoff(db)
    transactions = service.get_unreconciled_transactions(db, cutoff)
    payload = [
        TransactionSummary(
            id=tx.id,
            amount=tx.amount,
            date=tx.effective_date.date(),
            description=tx.description,
            processing_status=tx.processing_status.value if hasattr(tx.processing_status, "value") else str(tx.processing_status),
            reconciliation_status=tx.reconciliation_status.value if hasattr(tx.reconciliation_status, "value") else str(tx.reconciliation_status),
        )
        for tx in transactions
    ]
    return UnreconciledTransactionsResponse(transactions=payload)


@router.post("/sessions/{session_id}/transactions")
async def apply_reconciliation_transactions(
    session_id: str,
    payload: TransactionSelectionRequest,
    db: Session = _get_db_dependency,
) -> DifferenceResponse:
    service = ReconciliationService(db)
    try:
        _, response_payload = service.add_transactions_to_session(db, session_id, payload.transaction_ids)
        return DifferenceResponse(**response_payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Failed to update reconciliation session", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update reconciliation session",
        ) from exc
