# Public API Contract

This document outlines the public interface contract for the Account Management library. It details the primary classes, methods, and their expected signatures, serving as a guide for integration and usage.

## Core Components

### `AccountManager` Class

This class will likely serve as the main entry point for interacting with the account management system.

*   **Initialization:**
    ```python
    class AccountManager:
        def __init__(self, storage_config: dict):
            # Initializes the manager, potentially with database connection details or other storage configurations.
            pass
    ```
*   **Account Operations:**
    *   `create_account(name: str, accounting_category: AccountCategoryType, banking_product_type: BankingProductType, parent_id: Optional[str] = None, notes: Optional[str] = None, currency: str = 'AUD', account_number: Optional[str] = None, credit_limit: Optional[Decimal] = None) -> Account`
    *   `get_account(account_id: str) -> Optional[Account]`
    *   `list_accounts(parent_id: Optional[str] = None) -> List[Account]`
    *   `update_account(account_id: str, name: Optional[str] = None, notes: Optional[str] = None, currency: Optional[str] = None, account_number: Optional[str] = None, credit_limit: Optional[Decimal] = None) -> Account`
    *   `delete_account(account_id: str) -> bool`
    *   `adjust_balance(account_id: str, new_balance: Decimal, adjustment_date: datetime, booking_date: datetime = None) -> Transaction`
*   **Balance Operations:**
    *   `get_account_balance(account_id: str, balance_type: str = 'running') -> Decimal` (balance_type can be 'running', 'reconciled', or 'available')
    *   `reconcile_account(account_id: str, reconciliation_date: datetime)`
*   **Search:**
    *   `search_accounts_by_name(name: str) -> List[Account]`

### `Account` Class

Represents a financial account.

*   **Attributes:**
    *   `id: str`
    *   `name: str`
    *   `account_number: Optional[str]`
    *   `currency: str`
    *   `accounting_category: AccountCategoryType` (Enum)
    *   `banking_product_type: BankingProductType` (Enum)
    *   `available_balance: Decimal`
    *   `credit_limit: Optional[Decimal]`
    *   `parent_id: Optional[str]`
    *   `notes: Optional[str]`
    *   `running_balance: Decimal`
    *   `reconciled_balance: Decimal`
    *   `created_at: datetime`
    *   `updated_at: datetime`

### `Transaction` Class

Represents a financial transaction.

*   **Attributes:**
    *   `id: str`
    *   `effective_date: datetime`
    *   `booking_date: datetime`
    *   `description: str`
    *   `merchant_name: Optional[str]`
    *   `payee_details: Optional[str]`
    *   `amount: Decimal`
    *   `debit_account_id: str`
    *   `credit_account_id: str`
    *   `processing_status: ProcessingStatus` (Enum)
    *   `reconciliation_status: ReconciliationStatus` (Enum)
    *   `memo: Optional[str]`
    *   `action_type: Optional[ActionType]` (Enum)
    *   `created_at: datetime`
    *   `updated_at: datetime`


### Enums

*   `AccountCategoryType`: `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`
    *   *Asset Accounts*: Bank, Cash, Portfolio, Mutual Fund, General Asset.
    *   *Liability Accounts*: Credit Card, General Liability.
    *   *Equity Accounts*: For representing ownership.
    *   *Income Accounts*: For tracking sources of revenue.
    *   *Expense Accounts*: For tracking expenditures.
*   `BankingProductType`: `TRANSACTION`, `DEPOSIT`, `CREDIT_CARD`, `LOAN`, `OTHER`
    *   *Transaction*: Checking/Current accounts.
    *   *Deposit*: Savings, Term Deposits, High-Yield Savings.
    *   *Credit Card*: Revolving credit facilities.
    *   *Loan*: Borrowed money needing repayment.
    *   *Other*: General category.
*   `ReconciliationStatus`: `UNCLEARED` (Not yet matched against bank statement), `CLEARED` (Matched against bank statement), `RECONCILED` (Account balance fully reconciled)
*   `ActionType`: `ADJUSTMENT` (Manual balance change), `TRANSFER` (Funds moved between accounts), `PAYMENT` (Funds outflow), `INVOICE` (Funds inflow/revenue)
*   `ProcessingStatus`: `PENDING` (Awaiting processing), `COMPLETED` (Successfully processed), `FAILED` (Processing error)

## Notes on Usage

*   Error handling will be consistent, utilizing a structured JSON response format with defined error codes and messages, as per `TECHNICAL.md`. Specific exceptions will be raised and mapped to these error responses.
*   Implementation will use `decimal.Decimal` for precise financial calculations, `datetime.date` for date fields, and native `list` for collections, aligning with `TECHNICAL.md`'s guidance on type accuracy and native type preference.
*   The `storage_config` for `AccountManager` will be a connection string, that supports both SQLite and PostgreSQL as the chosen primary storage solutions.
*   Detailed documentation for each method, including edge cases and specific return types, will be crucial for usability.
*   Diagrams for documentation will be created using PlantUML and C4-Plantuml, adhering to `TECHNICAL.md`.
