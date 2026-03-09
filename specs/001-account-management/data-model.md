# Data Model

This document outlines the primary data entities, their fields, relationships, and validation rules based on the feature specification, updated for double-entry accounting.

## Entities

### Account

Represents a financial account within the system.

- **Fields**:
  - `id`: UUID (Primary Key) - Unique identifier for the account.
  - `name`: String (max_length=100) - Human-readable name for the account. Specific allowed characters: alphanumeric, spaces, `.`, `,`, `-`, `_`, `(`, `)`, `&`, `'`.
  - `currency`: String (3 uppercase letters) - ISO 4217 currency code. Must be in an allowed list (e.g., 'USD', 'EUR').
  - `accounting_category`: Enum (`AccountingCategory`) - Defines the accounting role of the account (e.g., Asset, Liability, Equity, Revenue, Expense).
  - `banking_product_type`: Enum (`BankingProductType`) - Defines the banking nature of the account (e.g., Checking, Savings, Credit Card, Loan).
  - `account_number`: Optional String (max_length=50) - User-provided account number, can contain alphanumeric and hyphens.
  - `available_balance`: Decimal (max_digits=18, decimal_places=2, ge=0) - The balance readily available for use. Quantized to 0.01 units of the smallest currency denomination. This will be calculated based on committed entries.
  - `credit_limit`: Optional Decimal (max_digits=18, decimal_places=2, ge=0) - The credit limit associated with the account (e.g., for credit cards). Quantized to 0.01.
  - `notes`: Optional String (max_length=500) - User-added notes for the account. Specific allowed characters: alphanumeric, spaces, `.`, `,`, `-`, `_`, `(`, `)`, `&`, `'`.
  - `parent_account_id`: Optional UUID - Foreign key referencing the `id` of another `Account` to establish a hierarchical structure. Must reference an existing account.
  - `hidden`: Boolean - Flag to indicate if the account is hidden from primary views.
  - `placeholder`: Boolean - Flag to indicate if the account is a placeholder or not yet fully configured.
  - `created_at`: DateTime - Timestamp of account creation.
  - `updated_at`: DateTime - Timestamp of last account update.

- **Relationships**:
  - Hierarchical: An account can have a `parent_account_id` linking it to another `Account`, forming a tree structure.
  - Has many `Entries` through `Transaction`.

- **State**:
  - Accounts can have states related to visibility (`hidden`) and readiness (`placeholder`).
  - The system must manage "unsaved changes" indicating a transient state before persistence.

### Transaction

Represents a complete financial event that affects at least two accounts (a debit and a credit).

- **Fields**:
  - `id`: UUID (Primary Key) - Unique identifier for the transaction event.
  - `transaction_date`: DateTime/Date - The date the transaction occurred.
  - `description`: String (min_length=1, max_length=255) - A description of the overall transaction. Specific allowed characters: alphanumeric, spaces, `.`, `,`, `-`, `_`, `(`, `)`, `&`, `'`.
  - `created_at`: DateTime - Timestamp of transaction creation.
  - `updated_at`: DateTime - Timestamp of last transaction update.

- **Relationships**:
  - Has many `Entries`.

### Entry

Represents a single debit or credit line item within a `Transaction`.

- **Fields**:
  - `id`: UUID (Primary Key) - Unique identifier for the entry.
  - `transaction_id`: UUID (Foreign Key to `Transaction.id`) - Links the entry to its parent transaction.
  - `account_id`: UUID (Foreign Key to `Account.id`) - The account affected by this entry.
  - `debit_amount`: Decimal (max_digits=18, decimal_places=2, ge=0) - The amount debited to the account. Quantized to 0.01 units of the smallest currency denomination.
  - `credit_amount`: Decimal (max_digits=18, decimal_places=2, ge=0) - The amount credited to the account. Quantized to 0.01 units of the smallest currency denomination.
  - *(Note: For a valid double-entry system, for each transaction, the sum of all `debit_amount`s must equal the sum of all `credit_amount`s. This model assumes one of `debit_amount` or `credit_amount` is zero for a given entry.)*
  - `running_balance_after`: Decimal - The account's running balance *after* this specific entry is applied.
  - `running_balance_before`: Decimal - The account's running balance *before* this specific entry is applied.
  - `reconciled_balance_after`: Decimal - The account's reconciled balance *after* this entry is applied.
  - `reconciled_balance_before`: Decimal - The account's reconciled balance *before* this entry is applied.

## Validation Rules Summary

Comprehensive validation rules are defined for inputs to API endpoints, enforced primarily through Pydantic schemas and FastAPI. Key rules include:

- **String Lengths**: Max lengths for names, descriptions, notes, etc.
- **Character Restrictions**: Certain characters are forbidden in sensitive string fields to prevent injection and ensure data integrity.
- **Numeric Constraints**: Amounts and balances are Decimals with specific digit counts, precision, and minimum values (e.g., `ge=0`). Quantization to 0.01 units for currency precision.
- **Enum Types**: Fields like `accounting_category`, `banking_product_type`, and `action_type` must conform to predefined enum values.
- **UUID Format**: IDs and foreign keys must be valid UUIDs.
- **Existence Checks**: `parent_account_id` must reference an existing account. `transaction_id` must reference an existing transaction, and `account_id` must reference an existing account for `Entry`.
- **ISO 4217**: Currency codes must adhere to this standard.
- **Double-Entry Integrity**: The sum of debit amounts must equal the sum of credit amounts for all entries within a single transaction.

## State Transitions

- **Account**: States include active, hidden, placeholder. Management of unsaved changes is a transient state before persistence.
- **Transaction**: Transactions and their associated entries are generally considered immutable once recorded. They define historical balance states.

## Relationships

- **Account Hierarchy**: Accounts can be parent to other accounts via `parent_account_id`.
- **Transaction-Entry Link**: Each `Entry` belongs to one `Transaction`.
- **Entry-Account Link**: Each `Entry` affects one `Account`.
