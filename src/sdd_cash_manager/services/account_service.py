import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from sdd_cash_manager.models.account import Account


class AccountService:
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session: Optional[Session] = db_session
        self.accounts: Dict[str, Account] = {}

    def create_account(
        self,
        name: str,
        currency: str,
        accounting_category: str,
        account_number: Optional[str] = None,
        banking_product_type: Optional[str] = None,
        available_balance: float = 0.0,
        credit_limit: Optional[float] = None,
        notes: Optional[str] = None,
        parent_account_id: Optional[str] = None,
        hidden: bool = False,
        placeholder: bool = False
    ) -> Account:
        if not name or not currency or not accounting_category:
            raise ValueError("Name, currency, and accounting category are required.")

        account_id = str(uuid.uuid4())
        account = Account(
            id=account_id,
            name=name,
            currency=currency,
            accounting_category=accounting_category,
            account_number=account_number,
            banking_product_type=banking_product_type,
            available_balance=available_balance,
            credit_limit=credit_limit,
            notes=notes,
            parent_account_id=parent_account_id,
            hidden=hidden,
            placeholder=placeholder
        )
        self.accounts[account_id] = account
        if self.db_session:
            self.db_session.add(account)
            self.db_session.flush()
        return account

    def get_account(self, account_id: str) -> Optional[Account]:
        if self.db_session:
            account = self.db_session.get(Account, account_id)
            if account:
                self.accounts[account_id] = account
            return account
        return self.accounts.get(account_id)

    def get_all_accounts(self) -> List[Account]:
        if self.db_session:
            return self.db_session.scalars(select(Account)).all()
        return list(self.accounts.values())

    def update_account(self, account_id: str, **kwargs: Any) -> Optional[Account]:
        account = self.get_account(account_id)
        if account:
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            if self.db_session:
                self.db_session.add(account)
                self.db_session.flush()
            self.accounts[account_id] = account
            return account
        return None

    def delete_account(self, account_id: str) -> bool:
        account = self.get_account(account_id)
        if account:
            if self.db_session:
                self.db_session.delete(account)
                self.db_session.flush()
            self.accounts.pop(account_id, None)
            return True
        return False

    def search_accounts_by_name(self, name_query: str) -> List[Account]:
        query = name_query.lower()
        if self.db_session:
            accounts = self.db_session.scalars(select(Account)).all()
        else:
            accounts = list(self.accounts.values())
        return [acc for acc in accounts if query in acc.name.lower()]

    # Placeholder methods for balance calculation
    def calculate_running_balance(self, account_id: str) -> float:
        account = self.get_account(account_id)
        return account.available_balance if account else 0.0

    def calculate_reconciled_balance(self, account_id: str) -> float:
        account = self.get_account(account_id)
        return account.available_balance if account else 0.0
