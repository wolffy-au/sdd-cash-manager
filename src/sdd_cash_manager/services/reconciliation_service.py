from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sdd_cash_manager.models.adjustment import AdjustmentTransaction
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
            # Create the entry from transaction data
            # is_adjustment flag should be True for adjustment transactions
            # reconciled_status could be defaulted or determined by business logic
            reconciliation_entry = ReconciliationViewEntry(
                account_id=account_id,
                entry_date=transaction.effective_date,
                amount=transaction.amount,
                description=transaction.description,
                is_adjustment=True, # Explicitly mark as adjustment
                reconciled_status="PENDING_RECONCILIATION", # Default status
                original_transaction_id=transaction.transaction_id,
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

    # Add other methods for fetching, updating reconciliation entries if needed
