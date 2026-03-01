import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Transaction
from sdd_cash_manager.services.account_service import AccountService  # Added this import


class TransactionService:
    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self.account_service: Optional[AccountService] = None # Reference to AccountService

    def set_account_service(self, account_service: AccountService) -> None:
        self.account_service = account_service

    def create_transaction(
        self,
        effective_date: datetime,
        booking_date: datetime,
        description: str,
        amount: float,
        debit_account_id: str,
        credit_account_id: str,
        action_type: str,
        notes: Optional[str] = None
    ) -> Transaction:
        if not description or not debit_account_id or not credit_account_id or not action_type:
            raise ValueError("Description, debit account ID, credit account ID, and action type are required.")
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and credit accounts cannot be the same.")

        tx_id = str(uuid.uuid4())
        transaction = Transaction(
            id=tx_id,
            effective_date=effective_date,
            booking_date=booking_date,
            description=description,
            amount=amount,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            action_type=action_type,
            notes=notes,
            processing_status=ProcessingStatus.PENDING,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )
        self.transactions[tx_id] = transaction
        return transaction

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        return self.transactions.get(transaction_id)

    def get_transactions_by_account(self, account_id: str) -> List[Transaction]:
        return [
            tx for tx in self.transactions.values()
            if tx.debit_account_id == account_id or tx.credit_account_id == account_id
        ]

    def update_transaction_status(
        self,
        transaction_id: str,
        processing_status: Optional[ProcessingStatus] = None,
        reconciliation_status: Optional[ReconciliationStatus] = None
    ) -> Optional[Transaction]:
        transaction = self.get_transaction(transaction_id)
        if transaction:
            if processing_status:
                transaction.processing_status = processing_status
            if reconciliation_status:
                transaction.reconciliation_status = reconciliation_status
            return transaction
        return None

    def perform_balance_adjustment(
        self,
        account_id: str,
        target_balance: float,
        adjustment_date: datetime,
        description: str,
        action_type: str,
        notes: Optional[str] = None
    ) -> Optional[Transaction]:
        if not self.account_service:
            raise RuntimeError("AccountService is not set.")

        account = self.account_service.get_account(account_id)
        if not account:
            raise ValueError(f"Account with ID {account_id} not found.")

        current_balance = account.available_balance
        amount_difference = target_balance - current_balance

        if abs(amount_difference) < 0.001: # Use a small tolerance for float comparison
            return None

        debit_id = account_id
        credit_id = "balancing-account-id"
        transaction_amount = abs(amount_difference)

        if amount_difference < 0: # Debit account (balance decreases)
            debit_id = account_id
            credit_id = "balancing-account-id"
        else: # Credit account (balance increases)
            debit_id = "balancing-account-id"
            credit_id = account_id

        created_transaction = self.create_transaction(
            effective_date=adjustment_date,
            booking_date=datetime.now(),
            description=f"{description} for account {account.name}", # Use account name for clearer description
            amount=transaction_amount,
            debit_account_id=debit_id,
            credit_account_id=credit_id,
            action_type=action_type,
            notes=notes
        )

        # Update account balance via AccountService
        self.account_service.update_account(account_id, available_balance=target_balance)

        # Mark transaction as posted immediately for balance adjustments
        self.update_transaction_status(
            created_transaction.id,
            processing_status=ProcessingStatus.POSTED,
            reconciliation_status=ReconciliationStatus.PENDING_RECONCILIATION
        )

        return created_transaction
