import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.schemas.adjustment import (
    ManualBalanceAdjustmentCreate,
)
from sdd_cash_manager.services.account_service import AccountService  # Assuming AccountService exists

logger = logging.getLogger(__name__)

class ManualBalanceAdjustmentService:
    """
    Service layer for handling manual balance adjustment logic.
    Manages creation of adjustments and associated transactions.
    """
    def __init__(self, db: Session):
        """
        Initializes the service with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db
        self.account_service = AccountService(db) # Initialize AccountService

    def create_adjustment(self, account_id: UUID, adjustment_data: ManualBalanceAdjustmentCreate) -> ManualBalanceAdjustment:
        """
        Creates a manual balance adjustment and an associated transaction if necessary.

        Args:
            account_id: The UUID of the account to adjust.
            adjustment_data: The data for the balance adjustment, including target balance,
                             effective date, and submitting user ID.

        Returns:
            The created ManualBalanceAdjustment object.

        Raises:
            ValueError: If the account is not found.
            RuntimeError: If there's a database error during transaction creation.
        """
        logger.info(f"Starting balance adjustment for account_id: {account_id} with data: {adjustment_data}")

        # Fetch account and ensure it exists
        account = self.account_service.get_account(account_id)
        if not account:
            logger.error(f"Account with id {account_id} not found.")
            raise ValueError(f"Account with id {account_id} not found")

        # Calculate difference
        current_running_balance = account.running_balance # Placeholder, needs actual logic from AccountService
        difference = adjustment_data.target_balance - current_running_balance
        logger.debug(f"Calculated difference: {difference}")

        adjustment = ManualBalanceAdjustment(
            account_id=account_id,
            target_balance=adjustment_data.target_balance,
            effective_date=adjustment_data.effective_date,
            submitted_by_user_id=adjustment_data.submitted_by_user_id, # Assuming this comes from auth context
            adjustment_attempt_timestamp=datetime.utcnow(), # Use UTC now
            status="PENDING" # Initial status
        )
        self.db.add(adjustment)
        self.db.flush() # Flush to get the adjustment ID
        logger.info(f"ManualBalanceAdjustment record created with ID: {adjustment.id}, initial status: PENDING")

        if difference != Decimal("0"):
            try:
                logger.info(f"Difference detected ({difference}). Proceeding to create AdjustmentTransaction.")
                transaction_type = "ADJUSTMENT_DEBIT" if difference > Decimal("0") else "ADJUSTMENT_CREDIT"
                description = "Manual balance adjustment"

                new_transaction_id = uuid4()

                new_transaction = AdjustmentTransaction(
                    transaction_id=new_transaction_id,
                    account_id=account_id,
                    effective_date=adjustment_data.effective_date,
                    amount=abs(difference),
                    transaction_type=transaction_type,
                    description=description,
                    created_at=datetime.utcnow(),
                )
                self.db.add(new_transaction)
                self.db.flush()
                logger.info(f"AdjustmentTransaction created with ID: {new_transaction_id}")

                # Update account balance
                account.running_balance += difference
                self.db.add(account)
                self.db.flush()
                logger.debug(f"Account {account_id} balance updated to {account.running_balance}")

                adjustment.created_transaction_id = new_transaction.transaction_id
                adjustment.status = "COMPLETED"
                logger.info(f"Adjustment {adjustment.id} marked as COMPLETED.")

            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error(f"SQLAlchemyError during transaction creation for adjustment {adjustment.id}: {e}", exc_info=True)
                raise RuntimeError(f"Failed to create adjustment transaction: {e}") from e
            except Exception as e:
                self.db.rollback()
                logger.error(f"Unexpected error during transaction creation for adjustment {adjustment.id}: {e}", exc_info=True)
                raise RuntimeError(f"An unexpected error occurred during transaction creation: {e}") from e
        else:
            adjustment.status = "ZERO_DIFFERENCE"
            adjustment.created_transaction_id = None
            logger.info(f"Adjustment {adjustment.id} has zero difference, status set to ZERO_DIFFERENCE.")

        self.db.commit()
        logger.info(f"Balance adjustment process finished for adjustment {adjustment.id}. Final status: {adjustment.status}")
        return adjustment

    # Add other methods for CRUD operations or specific business logic if needed
