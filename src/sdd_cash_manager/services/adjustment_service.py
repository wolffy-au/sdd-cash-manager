import logging
from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.enums import BankingProductType
from sdd_cash_manager.schemas.adjustment import ManualBalanceAdjustmentCreate
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.reconciliation_service import ReconciliationService
from sdd_cash_manager.services.transaction_service import BALANCING_ACCOUNT_ID, TransactionService

logger = logging.getLogger(__name__)

MANUAL_ADJUSTMENT_ACTION = "MANUAL_BALANCE_ADJUSTMENT"

class ManualBalanceAdjustmentService:
    """
    Service layer for handling manual balance adjustment logic.
    Manages creation of adjustments, ledger postings, and reconciliation entries.
    """

    def __init__(self, db: Session):
        self.db = db
        self.account_service = AccountService(db)
        self.transaction_service = TransactionService(db_session=db)
        self.transaction_service.set_account_service(self.account_service)
        self.reconciliation_service = ReconciliationService(db)

    def create_adjustment(
        self,
        account_id: UUID,
        adjustment_data: ManualBalanceAdjustmentCreate
    ) -> ManualBalanceAdjustment:
        logger.info("Starting manual balance adjustment for account %s with requested balance %s",
                    account_id, adjustment_data.target_balance)

        account_id_str = str(account_id)
        account = self.account_service.get_account(account_id_str)
        if not account:
            logger.error("Account %s not found for manual adjustment.", account_id_str)
            raise ValueError(f"Account with id {account_id} not found")

        current_running_balance = self.account_service.calculate_running_balance_as_of(
            account_id_str,
            adjustment_data.effective_date
        )
        difference = quantize_currency(adjustment_data.target_balance - current_running_balance)
        logger.debug("Calculated running balance as of %s: %s (difference: %s)",
                     adjustment_data.effective_date, current_running_balance, difference)

        adjustment = ManualBalanceAdjustment(
            account_id=account_id_str,
            target_balance=adjustment_data.target_balance,
            effective_date=adjustment_data.effective_date,
            submitted_by_user_id=adjustment_data.submitted_by_user_id,
            adjustment_attempt_timestamp=datetime.now(timezone.utc),
            status="PENDING",
        )

        self.db.add(adjustment)
        self.db.flush()

        if difference == Decimal("0"):
            adjustment.status = "ZERO_DIFFERENCE"
            adjustment.created_transaction_id = None
            logger.info("Zero-difference adjustment recorded for account %s", account_id_str)
            self.reconciliation_service.create_reconciliation_entry_for_manual_adjustment(
                manual_adjustment=adjustment,
                auto_commit=False,
            )
            self.db.commit()
            return adjustment

        try:
            transaction_description = f"Manual adjustment to {adjustment_data.target_balance}"
            effective_datetime = datetime.combine(
                adjustment_data.effective_date,
                time.min,
                tzinfo=timezone.utc
            )

            debit_account_id, credit_account_id = self._determine_entry_sides(account_id_str, difference)
            created_transaction = self.transaction_service.create_transaction(
                effective_date=effective_datetime,
                booking_date=datetime.now(timezone.utc),
                description=transaction_description,
                amount=difference.copy_abs(),
                debit_account_id=debit_account_id,
                credit_account_id=credit_account_id,
                action_type=MANUAL_ADJUSTMENT_ACTION,
            )

            account.available_balance = quantize_currency(adjustment_data.target_balance)
            self.db.add(account)

            transaction_type = self._transaction_type_for_difference(difference)

            adjustment_transaction = AdjustmentTransaction(
                transaction_id=created_transaction.id,
                account_id=account_id_str,
                effective_date=adjustment_data.effective_date,
                amount=created_transaction.amount,
                transaction_type=transaction_type,
                description=created_transaction.description,
                reconciliation_metadata={
                    "processing_status": created_transaction.processing_status,
                    "reconciliation_status": created_transaction.reconciliation_status,
                },
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(adjustment_transaction)
            self.db.flush()

            adjustment.created_transaction_id = adjustment_transaction.transaction_id
            adjustment.status = "COMPLETED"

            self.reconciliation_service.create_reconciliation_entry_from_transaction(
                account_id=UUID(account_id_str),
                transaction=adjustment_transaction,
                auto_commit=False,
            )

            self.db.commit()
            logger.info("Manual adjustment %s completed for account %s", adjustment.id, account_id_str)
            return adjustment
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.error("SQLAlchemy error while creating adjustment for account %s: %s",
                         account_id_str, exc, exc_info=True)
            raise RuntimeError("Failed to create adjustment transaction") from exc
        except Exception as exc:
            self.db.rollback()
            logger.error("Unexpected error while creating adjustment for account %s: %s",
                         account_id_str, exc, exc_info=True)
            raise RuntimeError("An unexpected error occurred during adjustment creation") from exc

    @staticmethod
    def _transaction_type_for_difference(difference: Decimal) -> str:
        return BankingProductType.ADJUSTMENT_DEBIT.value if difference > 0 else BankingProductType.ADJUSTMENT_CREDIT.value

    @staticmethod
    def _determine_entry_sides(account_id: str, difference: Decimal) -> tuple[str, str]:
        if difference > 0:
            return account_id, BALANCING_ACCOUNT_ID
        return BALANCING_ACCOUNT_ID, account_id
