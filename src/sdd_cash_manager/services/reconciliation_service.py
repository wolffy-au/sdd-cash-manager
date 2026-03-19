from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.enums import ReconciliationStatus
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry


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
    # Add other methods for fetching, updating reconciliation entries if needed
