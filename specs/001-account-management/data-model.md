# Data Model: Account Management

This document outlines the data model for the Account Management feature, based on the requirements specified in `spec.md` and derived from the implementation plan.

## Entities

### Account

Represents a financial account within the system.

| Field Name              | Type    | Constraints                                                                    | Description                                                                                                                  |
| :---------------------- | :------ | :----------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------- |
| `id`                    | UUID    | Primary Key                                                                    | Unique identifier for the account.                                                                                           |
| `account_number`        | String  | Unique, Not Null                                                               | Unique account number.                                                                                                       |
| `name`                  | String  | Not Null                                                                       | User-friendly name for the account.                                                                                          |
| `currency`              | String  | Not Null, e.g., "USD", "EUR"                                                   | Currency code for the account balance.                                                                                       |
| `accounting_category`   | Enum    | Not Null, FK to `AccountingCategoryType`                                       | Categorizes the account for accounting purposes (e.g., Asset, Liability, Equity, Revenue, Expense).                           |
| `banking_product_type`  | Enum    | Not Null, FK to `BankingAccountType`                                           | Type of banking product (e.g., Checking, Savings, Credit Card).                                                              |
| `available_balance`     | Decimal | Not Null, Default: 0.00                                                        | The readily available balance, which may differ from the running balance due to holds or pending transactions.               |
| `credit_limit`          | Decimal | Optional                                                                       | The credit limit for accounts like credit cards.                                                                             |
| `notes`                 | Text    | Optional                                                                       | Any additional notes or descriptions for the account.                                                                        |
| `parent_account_id`     | UUID    | Foreign Key to `Account.id`, Optional                                          | Identifier of the parent account in a hierarchical structure. If null, it's a top-level account.                             |
| `created_at`            | DateTime| Not Null, Default: CURRENT_TIMESTAMP                                           | Timestamp when the account was created.                                                                                      |
| `updated_at`            | DateTime| Not Null, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP             | Timestamp when the account was last updated.                                                                                 |

### Transaction

Represents a financial transaction.

| Field Name                     | Type    | Constraints                                                    | Description                                                                                                                                                                                                                                                                                                                                                       |
| :----------------------------- | :------ | :------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                           | UUID    | Primary Key                                                    | Unique identifier for the transaction.                                                                                                                                                                                                                                                                                                                            |
| `effective_date`               | Date    | Not Null                                                       | The date the transaction is intended to be effective.                                                                                                                                                                                                                                                                                                             |
| `booking_date`                 | Date    | Not Null                                                       | The date the transaction is booked in the system.                                                                                                                                                                                                                                                                                                                 |
| `description`                  | String  | Not Null                                                       | A brief description of the transaction.                                                                                                                                                                                                                                                                                                                           |
| `amount`                       | Decimal | Not Null                                                       | The monetary value of the transaction. Positive for credits (income/deposits) and negative for debits (expenses/withdrawals).                                                                                                                                                                                                                                     |
| `debit_account_id`             | UUID    | Foreign Key to `Account.id`, Not Null                          | The account from which funds are debited.                                                                                                                                                                                                                                                                                                                         |
| `credit_account_id`            | UUID    | Foreign Key to `Account.id`, Not Null                          | The account to which funds are credited.                                                                                                                                                                                                                                                                                                                          |
| `processing_status`            | Enum    | Not Null, FK to `ProcessingStatus`                             | The current status of the transaction processing (e.g., Pending, Processed, Failed).                                                                                                                                                                                                                                                                              |
| `reconciliation_status`        | Enum    | Not Null, FK to `ReconciliationStatus`                         | The status of the transaction regarding reconciliation with external statements (e.g., Unreconciled, Reconciled).                                                                                                                                                                                                                                                 |
| `action_type`                  | String  | Not Null, e.g., "adjustment", "transfer", "payment"            | Categorizes the type of action performed by the transaction.                                                                                                                                                                                                                                                                                                      |
| `running_balance_after_transaction` | Decimal | Not Null                                                       | The running balance of the primary account (e.g., debit account for a withdrawal) *after* this transaction has been applied. This helps in reconstructing account balances.                                                                                                                                                                                             |
| `created_at`                   | DateTime| Not Null, Default: CURRENT_TIMESTAMP                           | Timestamp when the transaction was created.                                                                                                                                                                                                                                                                                                                       |

## Enums

### `AccountingCategoryType`

Used to categorize accounts for accounting purposes.

-   `Asset`
-   `Liability`
-   `Equity`
-   `Revenue`
-   `Expense`

### `BankingAccountType`

Used to specify the type of banking product.

-   `Checking`
-   `Savings`
-   `CreditCard`
-   `Loan`
-   `Investment`

### `ProcessingStatus`

Indicates the status of transaction processing.

-   `Pending`
-   `Processed`
-   `Failed`

### `ReconciliationStatus`

Indicates the status of transaction reconciliation.

-   `Unreconciled`
-   `Reconciled`

## Relationships

-   **Account to Account**: A one-to-many relationship where an `Account` can have many child `Account`s, and each child `Account` has one `parent_account_id` referencing its parent `Account`.
-   **Transaction to Account**: Each `Transaction` involves two accounts: a `debit_account_id` and a `credit_account_id`, establishing a many-to-one relationship from `Transaction` to `Account` for each role.

## Terminology Definitions (from Spec)

-   **Running Balance**: The current balance reflecting all entered transactions. Stored as `running_balance_after_transaction` on the `Transaction` entity.
-   **Reconciled Balance**: The balance reflecting only transactions that have been cleared or formally reconciled against external statements. (Note: This is typically an attribute of the `Account` and derived/maintained by logic, not directly stored per transaction in this model).
-   **Available Balance**: The readily available balance, which may differ from the running balance due to holds or pending transactions. Stored directly on the `Account` entity.
-   **Account Group**: An `Account` used to aggregate the balances of its child accounts, creating a hierarchical view. Achieved via the `parent_account_id` relationship.
