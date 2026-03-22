from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry
from sdd_cash_manager.models.reconciliation_session import (
    BankStatementSnapshot,
    ReconciliationSession,
    ReconciliationSessionState,
)
from sdd_cash_manager.models.transaction import Transaction


class ReconciliationService:
    def __init__(self, db: Session):
        self.db = db

    def create_reconciliation_entry_from_transaction(
        self,
        account_id: UUID,
        transaction: AdjustmentTransaction,
        auto_commit: bool = True
    ) -> ReconciliationViewEntry:
        """
        Creates a ReconciliationViewEntry from an AdjustmentTransaction.
        """
        try:
            account_id_value = str(account_id)
            # Create the entry from transaction data
            # is_adjustment flag should be True for adjustment transactions
            # reconciled_status could be defaulted or determined by business logic
            reconciliation_entry = ReconciliationViewEntry(
                account_id=account_id_value,
                entry_date=transaction.effective_date,
                amount=transaction.amount,
                description=transaction.description,
                is_adjustment=True, # Explicitly mark as adjustment
                reconciled_status=ReconciliationStatus.PENDING_RECONCILIATION.value, # Default status
                original_transaction_id=str(transaction.transaction_id),
            )
            self.db.add(reconciliation_entry)
            self.db.flush()
            if auto_commit:
                self.db.commit()
            return reconciliation_entry

        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"SQLAlchemyError creating reconciliation entry: {e}") # Log error
            raise RuntimeError(f"Failed to create reconciliation entry: {e}") from e
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error creating reconciliation entry: {e}") # Log error
            raise RuntimeError(f"An unexpected error occurred during reconciliation entry creation: {e}") from e

    def create_reconciliation_entry_for_manual_adjustment(
        self,
        manual_adjustment: ManualBalanceAdjustment,
        auto_commit: bool = True
    ) -> ReconciliationViewEntry:
        """
        Creates a reconciliation view entry for a zero-difference manual adjustment.
        """
        try:
            reconciliation_entry = ReconciliationViewEntry(
                account_id=str(manual_adjustment.account_id),
                entry_date=manual_adjustment.effective_date,
                amount=Decimal("0.00"),
                description="Manual balance adjustment (zero difference)",
                is_adjustment=True,
                reconciled_status=ReconciliationStatus.ZERO_DIFFERENCE.value,
                original_transaction_id=None,
            )
            self.db.add(reconciliation_entry)
            self.db.flush()
            if auto_commit:
                self.db.commit()
            return reconciliation_entry
        except SQLAlchemyError as e:
            self.db.rollback()
            print(f"SQLAlchemyError creating zero-difference reconciliation entry: {e}")
            raise RuntimeError(f"Failed to create reconciliation entry: {e}") from e
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error creating zero-difference reconciliation entry: {e}")
            raise RuntimeError(f"An unexpected error occurred during reconciliation entry creation: {e}") from e

    def get_reconciliation_entries_for_account(
        self,
        account_id: UUID,
    ) -> list[ReconciliationViewEntry]:
        """
        Retrieve reconciliation view entries for the given account.
        """
        account_id_value = str(account_id)
        return (
            self.db.query(ReconciliationViewEntry)
            .filter(ReconciliationViewEntry.account_id == account_id_value)
            .all()
        )

    def _recalculate_difference(self, session_obj: ReconciliationSession) -> Decimal:
        total = sum((transaction.amount for transaction in session_obj.transactions), Decimal("0"))
        new_difference = quantize_currency(session_obj.ending_balance - total)
        session_obj.difference = new_difference
        return new_difference

    def create_reconciliation_session(
        self,
        session: Session,
        statement_date: date,
        ending_balance: Decimal,
        created_by: str | None = None,
    ) -> ReconciliationSession:
        quantized_balance = quantize_currency(ending_balance)
        session_obj = ReconciliationSession(
            statement_date=statement_date,
            ending_balance=quantized_balance,
            difference=quantized_balance,
            created_by=created_by,
            state=ReconciliationSessionState.IN_PROGRESS,
        )
        session.add(session_obj)
        session.flush()
        session.commit()
        return session_obj

    def add_transactions_to_session(
        self,
        session: Session,
        reconciliation_session_id: str,
        transaction_ids: list[str],
    ) -> tuple[ReconciliationSession, dict[str, Any]]:
        session_obj = session.get(ReconciliationSession, reconciliation_session_id)
        if session_obj is None:
            raise ValueError(f"ReconciliationSession {reconciliation_session_id} not found")

        transactions = (
            session.query(Transaction)
            .filter(Transaction.id.in_(transaction_ids))
            .all()
        )
        for transaction in transactions:
            if transaction not in session_obj.transactions:
                session_obj.transactions.append(transaction)
            if transaction.reconciliation_status == ReconciliationStatus.UNCLEARED:
                transaction.reconciliation_status = ReconciliationStatus.CLEARED
            session.add(transaction)

        new_difference = self._recalculate_difference(session_obj)
        if new_difference == Decimal("0"):
            session_obj.state = ReconciliationSessionState.COMPLETED
            for txn in transactions:
                txn.reconciliation_status = ReconciliationStatus.RECONCILED
                session.add(txn)

        session.flush()
        remaining = self._count_remaining_uncleared(session)
        payload = {
            "difference": new_difference,
            "difference_status": self._difference_status(new_difference),
            "remaining_uncleared": remaining,
            "guidance": self._guidance_message(new_difference),
        }
        session.commit()
        return session_obj, payload

    def get_unreconciled_transactions(
        self,
        session: Session,
        cutoff_date: date | None = None,
    ) -> list[Transaction]:
        stmt = select(Transaction).where(
            Transaction.processing_status.in_(
                [
                    ProcessingStatus.PENDING,
                    ProcessingStatus.COMPLETED,
                    ProcessingStatus.POSTED,
                ]
            ),
            Transaction.reconciliation_status.in_(
                [
                    ReconciliationStatus.UNCLEARED,
                    ReconciliationStatus.CLEARED,
                ]
            ),
        )
        if cutoff_date:
            stmt = stmt.where(Transaction.effective_date >= cutoff_date)
        stmt = stmt.order_by(Transaction.effective_date)
        return list(session.scalars(stmt))

    def create_bank_statement_snapshot(
        self,
        session: Session,
        closing_date: date,
        closing_balance: Decimal,
        statement_id: str | None = None,
    ) -> BankStatementSnapshot:
        quantized_balance = quantize_currency(closing_balance)
        snapshot = BankStatementSnapshot(
            closing_date=closing_date,
            closing_balance=quantized_balance,
            statement_id=statement_id,
            transaction_cutoff=closing_date,
        )
        session.add(snapshot)
        session.flush()
        return snapshot

    def get_latest_statement_cutoff(self, session: Session) -> date | None:
        stmt = select(BankStatementSnapshot).order_by(BankStatementSnapshot.closing_date.desc())
        snapshot = session.scalars(stmt).first()
        return snapshot.transaction_cutoff if snapshot else None

    def _difference_status(self, value: Decimal) -> str:
        if value == Decimal("0"):
            return "balanced"
        if value > Decimal("0"):
            return "positive"
        return "negative"

    def _guidance_message(self, difference: Decimal) -> str | None:
        if difference == Decimal("0"):
            return "All selected transactions have been reconciled."
        if difference > Decimal("0"):
            return "Review missing transactions or adjust the ending balance downward."
        return "Verify you have not overselected transactions or adjust the statement balance upward."

    def _count_remaining_uncleared(self, session: Session) -> int:
        stmt = select(func.count()).select_from(Transaction).where(
            Transaction.reconciliation_status == ReconciliationStatus.UNCLEARED
        )
        result = session.scalar(stmt)
        return int(result or 0)
