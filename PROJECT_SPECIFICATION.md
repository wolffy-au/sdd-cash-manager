# GnuCash (X-Accountant Business Feature Specification (v1.0.11 Review - Dec 1997)

This document outlines the key business features and input/output formats of GnuCash (formerly X-Accountant) , based on a review of the codebase at tag 1.0.11 and related documentation available before December 11, 1997. The focus is on functionality from a user's perspective, with some architectural insights for context.

## 1. Account Management

### 1.1 Core Account Functionality

- **Multiple Accounts:** Users can create and manage an arbitrary number of financial accounts.
- **Account Types:** Supports predefined account classifications for both banking product type and accounting category, which influence how balances are calculated:
  - **Banking Product Types:**: Reflects the nature of the financial product aligned with industry standards.
    - **TRANSACTION:** A record of any financial event or movement of funds.
    - **DEPOSIT:** An amount of money placed into an account.
    - **CREDIT_CARD:** A card that allows users to borrow money for purchases, with a repayment obligation.
    - **LOAN:** Money borrowed that must be repaid, usually with interest.
    - **OTHER:** A miscellaneous category for banking products that do not fit other classifications.
  - **Accounting Category Types:** Supports predefined account classifications, which influence how balances are calculated (e.g., monetary vs. share-based for investment accounts):
    - **Asset Accounts:** Bank, Cash, Portfolio, Mutual Fund, General Asset.
    - **Liability Accounts:** Credit Card, General Liability.
    - **Equity Accounts:** For representing ownership.
    - **Income Accounts:** For tracking sources of revenue.
    - **Expense Accounts:** For tracking expenditures.
- **Balances:** Each account maintains multiple balance types for comprehensive financial tracking:
  - **Running Balance:** Reflects all entered transactions.
  - **Reconciled Balance:** Reflects only transactions that have been cleared or formally reconciled.
  - **Available Balance:** Indicates the funds readily available for use.
  - **Credit Limit:** Applicable for credit-related accounts, indicating the maximum amount that can be borrowed.
- **Historical Running Balances:** The system maintains historical running balances (both overall and cleared) for each transaction within an account, allowing for chronological analysis and accurate balance progression.
- **Account Notes:** Each account can have associated textual notes for additional information.
- **Hierarchical Accounts (Sub-accounts):** Accounts can be organized into a tree-like structure, allowing master accounts to group related detail accounts (e.g., "Assets" > "Cash On Hand" > "Checking Account"). This facilitates categorization and aggregation.
- **Account Group Balances:** Parent account groups maintain a consolidated balance reflecting the sum of all accounts within their hierarchy.
- **Search Accounts by Name:** Provides the ability to locate accounts by their name.
- **Application State Management (Save/New):** The system tracks whether changes have been made to the account data, prompting users to save unsaved work and managing "new" (empty) data states.

### 1.3 Adjust Balance Window

- **Manual Balance Adjustment:** Provides a dedicated window for users to manually adjust an account's balance to a specific value.
- **Automated Transaction Creation:** When a new balance is entered, the system automatically creates a new transaction on a specified date.
- **Difference Calculation:** The amount of this new transaction is calculated as the difference between the target new balance and the account's existing balance up to the specified date.
- **Impact on Records:** This adjustment transaction updates the account's ledger and is reflected in reconciliation views.

## 2. Transaction Management

### 2.1 Transaction Entry

- **Register/Ledger Window:** The primary interface for entering and viewing transactions.
- **QuickFill:** Automates transaction entry by suggesting and completing description fields based on previously entered transactions.
- **Double-Entry Support:**
  - The system supports the double-entry accounting methodology.
  - Every transaction involves two accounts: one account is debited, and another is credited with an equal amount. This ensures transactional balance across the ledger.
  - Transactions are conceptually "transfers" between accounts.
  - Changes to a double-entry transaction in one view are automatically propagated to all linked accounts and views.
  - **Note:** Double-entry is currently optional; users can create single-entry ("dangling") transactions. (A future goal is to allow forced double-entry).
- **Transaction Categorization:** Transactions are categorized by linking them to specific Income/Expense accounts.

### 2.2 Transaction Details & Features

- **Transaction Actions:** Transactions can be associated with specific actions (e.g., "Buy", "Sell"), indicating the nature of the transaction.
- **Transfer Specification:** Users explicitly select "Transfer From" and "Transfer To" accounts for double-entry transactions.
- **Stock Transactions:** Handled within individual stock accounts or a specialized "Portfolio Ledger" for grouped stock accounts. This ledger uses a two-line display for debited/credited accounts and amounts.

### 2.3 Data Integrity & Maintenance

- **Duplicate Transaction Consolidation (Account-level):** The system includes functionality to identify and remove duplicate transactions within a single account based on a comprehensive match of key transaction fields (credit/debit accounts, reconciled status, date, number, description, memo, action, amount, and share price).
- **Global Duplicate Transaction Consolidation (Group-level):** Extends the duplicate transaction consolidation to identify and remove duplicates across all accounts within an account group.
- **Account Merging/Consolidation:** Provides the ability to merge accounts that share the same name, description, notes, and type. This operation consolidates their child accounts and transactions into a single account.

## 3. Reconciliation

### 3.1 Account Reconciliation Process

- **Reconcile Window:** A dedicated interface for matching application records with bank statements.
- **Process Flow:**
    1. User enters the ending balance from a bank statement.
    2. The system displays all unreconciled transactions since the last statement.
    3. User checks off transactions that appear on the bank statement.
    4. A "Difference" field dynamically shows the discrepancy, aiming for $0.00 at completion.
- **Transaction Statuses:** Transactions have distinct status types:
  - **`processing_status`:** Reflects the external status from the bank or payment processor. Values include `PENDING`, `COMPLETED`, `FAILED`.
  - **`reconciliation_status`:** Reflects the internal status within the application for user reconciliation. Values include `UNCLEARED`, `CLEARED`, `RECONCILED`.

## 4. Reporting

### 4.1 Standard Reports

- **Balance Sheet:** Presents a snapshot of financial position at a specific time, showing Assets, Liabilities, and Equity. The sum of Assets should equal the sum of Liabilities and Equity.
- **Profit and Loss Statement (P&L):** Reports financial performance over a period, detailing Income and Expenses. Calculates total profit or loss (Income - Expenses).
- **General Ledger View:** Allows viewing transactions from a master account and all its sub-accounts in a single register window, providing a comprehensive overview. (Noted as more complex, recommended for accounting experts).

## 5. Investment Tracking

- **Stock & Mutual Fund Portfolios:** Users can track investments either by creating individual accounts for each stock/fund or by grouping them into a portfolio account.
- **Portfolio Ledger:** A specialized transaction entry and viewing interface for portfolios, designed to handle stock purchases and sales with specific display conventions (e.g., two-line entries, distinct treatment for money/share exchanges).

## 6. Input/Output (I/O) Formats

### 6.1 Current I/O Capabilities

- **Native File Format:** GnuCash uses its own proprietary file format for data storage, which has evolved through several versions:
  - **Version 1:** Original format.
  - **Version 2:** Introduced support for double-entry transactions.
  - **Version 3:** Added support for transaction "actions" (e.g., Buy, Sell).
  - **Version 4:** Incorporated "account groups" (hierarchical accounts).
  The file format is designed for cross-platform compatibility.

- **Quicken QIF Import:** Supports importing Quicken Version 3.0 QIF files.
  - Allows merging imported data with existing GnuCash data.
  - Includes duplicate transaction detection and removal based on comprehensive matching criteria.
  - Imports all accounts and categories from the QIF file, even if empty.

### 6.2 Future I/O Goals (for context on intended direction)

- **Abstracted Data Interface & Loadable Modules:** A design goal to allow dynamic loading of data from diverse sources (e.g., stock-quote websites, online banking, SQL databases).
- **SQL I/O:** Direct integration with SQL databases for data storage and retrieval.
- **Quicken QIF Export:** Ability to export data to Quicken QIF format.
- **Comma-separated utf-8 File Format:** Support for a human-readable and easily manipulable plain text format for data exchange.

## 7. User Interface & Presentation

### 7.1 Core Display and Interaction

- **Formatted Currency & Share Display:** The application provides robust formatting for displaying monetary amounts (with currency symbols and appropriate decimal precision) and share amounts (with a "shrs" suffix and appropriate decimal precision), handling negative values appropriately.

## 8. Data Entry & Validation

- **Input Validation (Dates & Amounts):** Basic input validation is performed for critical data fields such as dates (ensuring valid format) and amounts (ensuring valid numerical input).
