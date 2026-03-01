# Data Model: Account Management

This document outlines the core data entities and their relationships for the Account Management feature, based on the feature specification and research findings.

## Core Entities

### 1. Account

Represents a financial account within the system.

*   **Attributes:**
    *   `id` (str): Unique identifier for the account.
    *   `name` (String): The name of the account (e.g., "Checking Account", "Savings").
    *   `account_number` (String): The primary account number.
    *   `currency` (String): The currency of the account (e.g., "AUD").
    *   `accounting_category` (Enum): The classification of the account. Must be one of:
        *   `ASSET` (Asset Accounts: Bank, Cash, Portfolio, Mutual Fund, General Asset)
        *   `LIABILITY` (Liability Accounts: Credit Card, General Liability)
        *   `EQUITY` (Equity Accounts: For representing ownership)
        *   `INCOME` (Income Accounts: For tracking sources of revenue)
        *   `EXPENSE` (Expense Accounts: For tracking expenditures)
    *   `banking_product_type` (Enum): The classification of the account according to banking product types. Must be one of:
        * `TRANSACTION` (This type generally refers to accounts used for day-to-day banking, payments, and frequent monetary transactions. Examples include checking accounts or current accounts.)
        * `DEPOSIT` (This type typically covers accounts where funds are held, often with the purpose of saving or earning interest. Examples include savings accounts, term deposits, or high-yield savings accounts.)
        * `CREDIT_CARD` (This classification is for revolving credit facilities, such as credit card accounts, that allow users to borrow money up to a certain limit.)
        * `LOAN` (This type represents accounts where money has been borrowed and needs to be repaid, such as personal loans, mortgages, or car loans.)
        * `OTHER` (This is a general category for any banking product or account type that does not fit into the more specific )classifications listed above.
    *   `available_balance` (Decimal/Float): The readily available balance.
    *   `credit_limit` (Decimal/Float, Nullable): The credit limit for credit accounts.
    *   `parent_account_id` (str, Nullable): Foreign key referencing the `id` of the parent account for hierarchical organization. Null if it's a top-level account.
    *   `notes` (Text, Nullable): Additional textual information or remarks about the account.
    *   `running_balance` (Decimal/Float): The current balance reflecting all entered transactions.
    *   `reconciled_balance` (Decimal/Float): The balance reflecting only transactions that have been cleared or formally reconciled.
    *   `created_at` (DateTime): Timestamp of account creation.
    *   `updated_at` (DateTime): Timestamp of last account update.

*   **Relationships:**
    *   One-to-Many: An Account can have many child accounts (`parent_account_id` links to `Account.id`).
    *   Many-to-One: An Account can belong to one parent account (`parent_account_id` references `Account.id`).
    *   One-to-Many: An Account can have many associated Transactions.

*   **Validation Rules:**
    *   `name`: Must be a non-empty string. Should ideally be unique within its parent account's scope or at the top level.
    *   `account_number`: Must be a non-empty string.
    *   `currency`: Must be a valid currency code.
    *   `accounting_category`: Must be one of the defined `AccountingCategoryType` enumeration values.
    *   `banking_product_type`: Must be one of the defined `BankingAccountType` enumeration values.
    *   `available_balance`: Must be a valid numerical type.
    *   `credit_limit`: Must be a valid numerical type if present.
    *   `running_balance` & `reconciled_balance`: Must be valid numerical types.
    *   `parent_account_id`: If present, must reference an existing `Account.id`.

### 2. Transaction

Represents a financial movement between accounts.

*   **Attributes:**
    *   `id` (str): Unique identifier for the transaction.
    *   `effective_date` (Date/DateTime): The date the transaction effectively impacts the balance.
    *   `booking_date` (Date/DateTime): The date the transaction was recorded.
    *   `description` (String): A brief description of the transaction.
    *   `merchant_name` (String, Nullable): Name of the merchant or payee.
    *   `payee_details` (String, Nullable): Additional details about the payee.
    *   `amount` (Decimal/Float): The monetary value of the transaction.
    *   `debit_account_id` (UUID/Integer): Foreign key referencing the `id` of the account debited.
    *   `credit_account_id` (UUID/Integer): Foreign key referencing the `id` of the account credited.
    *   `processing_status` (Enum): The status of the transaction as processed by the bank. Must be one of:
        *   `PENDING`
        *   `COMPLETED`
        *   `FAILED`
    *   `reconciliation_status` (Enum): Indicates if the transaction has been reconciled within the application. Values could be: `UNCLEARED`, `CLEARED`, `RECONCILED`.
    *   `memo` (Text, Nullable): Additional details or reference for the transaction.
    *   `action_type` (Enum, Nullable): Specifies the type of transaction, e.g., `ADJUSTMENT`, `TRANSFER`, `PAYMENT`, `INVOICE`.
    *   `created_at` (DateTime): Timestamp of transaction creation.
    *   `updated_at` (DateTime): Timestamp of last transaction update.

*   **Relationships:**
    *   Many-to-One: A Transaction is associated with two Accounts (debit and credit).

*   **Validation Rules:**
    *   `effective_date` and `booking_date`: Must be valid date/datetime values.
    *   `description`, `merchant_name`, `payee_details`: Must be strings.
    *   `amount`: Must be a valid numerical type.
    *   `debit_account_id` & `credit_account_id`: Must be present and reference valid, existing `Account.id`s.
    *   `processing_status`: Must be one of the defined `ProcessingStatus` enumeration values.
    *   `reconciliation_status`: Must be one of the defined `ReconciliationStatus` enumeration values.
    *   `action_type`: Must be a valid type if provided.

### 3. Account Group Balance (Implicit Entity/Concept)

Represents the aggregated balance of a parent account and its sub-accounts. This is not a separate table but a calculated view or property derived from child accounts.

*   **Attributes:**
    *   `account_id` (str): The ID of the parent account.
    *   `consolidated_running_balance` (Decimal/Float): Sum of running balances of all its child accounts.
    *   `consolidated_reconciled_balance` (Decimal/Float): Sum of reconciled balances of all its child accounts.

*   **Calculation:** The consolidated balances are derived by summing the respective balances of all accounts that list the group account as their parent (directly or indirectly through multiple levels of hierarchy).

### 4. Application State (Conceptual)

Tracks the state of unsaved changes for accounts.

*   **Attributes:**
    *   `has_unsaved_changes` (Boolean): True if modifications have been made to account data without being saved.
    *   `is_new_state` (Boolean): True if the current data represents a new, unsaved entity.

*   **Note:** This is a conceptual entity related to user interaction and workflow management, rather than a persistent data model.

## State Transitions

*   **Account:**
    *   A new account is created in a "new" state with zero balances.
    *   An existing account's balances are updated by new transactions.
    *   An account can be deleted.
*   **Transaction:**
    *   Transactions are created, linked to debit and credit accounts.
    *   Transactions can be marked as `UNCLEARED`, `CLEARED`, or `RECONCILED`.
*   **Balance Adjustment:**
    *   Triggered by the "Adjust Balance" window.
    *   Creates a new `Transaction` record representing the difference between the old and new balance.
    *   Updates the `running_balance` and `reconciled_balance` of the affected account(s).
    *   This adjustment transaction itself will have a `status` and `action_type`.

## Historical Balances

The system maintains historical running balances for each transaction. This implies that as transactions are added or modified, a historical ledger of account balances at any given point in time can be reconstructed. This is typically managed by storing transaction details and recalculating balances, or by maintaining a ledger table that records balance changes.
