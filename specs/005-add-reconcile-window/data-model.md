# Data Model: Reconcile Window

## ReconciliationSession
- **Purpose**: Tracks a statement reconciliation event tied to a single ending balance entry and set of matched transactions.
- **Fields**:
  - `id`: Unique identifier.
  - `statement_date`: Cutoff for transactions eligible for this session (auto derived from previous statement).
  - `ending_balance`: Decimal value entered by the user from the bank statement.
  - `difference`: Computed as `ending_balance - sum(selected_transaction.amount)`; should converge toward $0.00.
  - `state`: Enum (`IN_PROGRESS`, `COMPLETED`, `DISPUTED`) to describe session lifecycle.
  - `created_by` / `created_at`: Auditing metadata.
- **Relationships**:
  - `transactions`: Many-to-many association to `Transaction` with linkage table capturing the order and selection timestamp.
- **Validation**:
  - `ending_balance` must be non-negative and match the statement’s decimal precision.
  - `difference` should be recalculated after every selection; only zero difference allows the state to transition to `COMPLETED`.
- **State transitions**:
  - `IN_PROGRESS` → `COMPLETED` when `difference == 0` and all selected transactions have updated statuses.
  - `IN_PROGRESS` → `DISPUTED` if user flags a mismatch or the Difference remains non-zero despite matching transactions.

## Transaction
- **Purpose**: Represents individual ledger entries; existing fields extended with reconciliation metadata for this feature.
- **Fields** (relevant to reconciliation):
  - `processing_status`: External state (`PENDING`, `COMPLETED`, `FAILED`).
  - `reconciliation_status`: Internal state (`UNCLEARED`, `CLEARED`, `RECONCILED`).
  - `amount`, `date`, `account_id`, `description`, etc.
- **Relationships**:
  - Belongs to an `Account` through `account_id`.
  - Linked to `ReconciliationSession` when a user checks it off.
- **Validation**:
  - Only transactions marked `UNCLEARED`/`CLEARED` and `processing_status` in (`PENDING`, `COMPLETED`) are eligible for selection.
  - Transactions with `processing_status == FAILED` must remain untouched until an external retry updates the status.
- **State transitions**:
  - `UNCLEARED` → `CLEARED` when the transaction is selected in the window.
  - `CLEARED` → `RECONCILED` when the session is finalized (difference hits zero) or when confirmed by user.

## BankStatementSnapshot
- **Purpose**: Represents the external bank statement metadata that drives the reconciliation horizon.
- **Fields**:
  - `closing_date`: Last date included on the statement.
  - `closing_balance`: Decimal matching the ending balance input.
  - `statement_id`: Optional identifier for traceability.
  - `transaction_cutoff`: Date used to filter transactions (`closing_date` + 1 for next cycle).
- **Validation**:
  - `closing_balance` must match `ReconciliationSession.ending_balance` when a new session is created.
- **Usage**:
  - Governs which transactions are considered “since the last statement” via the cutoff.
