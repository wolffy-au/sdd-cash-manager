# Data Model: Adjust Balance Window

This document outlines the data model for the 'Adjust Balance Window' feature, detailing key entities, their attributes, relationships, and validation rules.

## Entities

### ManualBalanceAdjustment

Represents a user's request to manually adjust an account's balance.

*   **Attributes**:
    *   `account_id` (UUID): The identifier of the account being adjusted. (Required)
    *   `target_balance` (Decimal): The desired new balance for the account. (Required, >= 0)
    *   `effective_date` (Date): The date on which this adjustment should take effect. (Required)
    *   `submitted_by_user_id` (UUID): The identifier of the user who initiated the adjustment. (Required)
    *   `adjustment_attempt_timestamp` (DateTime): Timestamp when the adjustment was submitted. (Required, auto-generated)
    *   `created_transaction_id` (UUID, Nullable): Reference to the `AdjustmentTransaction` created, if any.
    *   `status` (Enum): Status of the adjustment (e.g., 'PENDING', 'COMPLETED', 'ZERO_DIFFERENCE').
*   **Relationships**:
    *   Belongs to an `Account`.
    *   Associated with a `User`.
    *   May create an `AdjustmentTransaction`.
*   **Validation Rules**:
    *   `target_balance` must be non-negative.
    *   `effective_date` can be in the past, present, or future, but warnings will be surfaced if outside the current statement range.
    *   `submitted_by_user_id` must reference a valid user.

### AdjustmentTransaction

Represents the automatically generated ledger entry to facilitate the balance adjustment.

*   **Attributes**:
    *   `transaction_id` (UUID): Unique identifier for the transaction. (Required, PK)
    *   `account_id` (UUID): The account to which this transaction applies. (Required)
    *   `effective_date` (Date): The date the transaction is effective. (Required)
    *   `amount` (Decimal): The calculated difference amount to be debited or credited. (Required)
    *   `transaction_type` (Enum): Type of transaction (e.g., 'ADJUSTMENT_DEBIT', 'ADJUSTMENT_CREDIT'). (Required)
    *   `description` (String): A brief description of the transaction (e.g., "Manual balance adjustment"). (Required)
    *   `reconciliation_metadata` (JSON/Dict, Nullable): Data related to reconciliation status.
    *   `created_at` (DateTime): Timestamp of transaction creation. (Required, auto-generated)
*   **Relationships**:
    *   Belongs to an `Account`.
    *   May be linked from a `ManualBalanceAdjustment`.
*   **Validation Rules**:
    *   `amount` is calculated as the difference between the target balance and the account's running balance as of `effective_date`.
    *   `transaction_type` must be consistent with the debit/credit needed to reach the target balance.

### ReconciliationViewEntry

A read-only projection for displaying reconciliation data, including adjustment transactions.

*   **Attributes**:
    *   `entry_id` (UUID): Unique identifier for the reconciliation entry. (Required, PK)
    *   `account_id` (UUID): The account associated with this entry. (Required)
    *   `entry_date` (Date): The date of the entry. (Required)
    *   `amount` (Decimal): The transaction amount. (Required)
    *   `description` (String): Description of the transaction. (Required)
    *   `is_adjustment` (Boolean): Flag indicating if this entry is from a balance adjustment. (Required)
    *   `reconciled_status` (Enum): Status of reconciliation (e.g., 'CLEARED', 'PENDING', 'UNCLEARABLE'). (Required)
    *   `original_transaction_id` (UUID, Nullable): Reference to the original transaction if this is a projection.
*   **Relationships**:
    *   Represents data derived from `AdjustmentTransaction` and other ledger entries.
*   **Validation Rules**:
    *   `reconciled_status` reflects the state of the transaction in the reconciliation process.
    *   `is_adjustment` flag should be true for entries originating from `ManualBalanceAdjustment`.

## Data Model Assumptions

*   `Account` entity exists with `id`, `running_balance` (as of current date), and potentially methods to retrieve balance as of a specific date.
*   `User` entity exists with `id`.
*   The `banking product enum` (mentioned in spec.md) will be updated to include 'ADJUSTMENT_DEBIT' and 'ADJUSTMENT_CREDIT' types if literal matching is required.
*   The reconciliation view can consume and display `AdjustmentTransaction` data, reflecting its status.
*   Date handling should consider timezones appropriately, especially for `effective_date` and timestamps.

## Relationships Summary

*   `ManualBalanceAdjustment` (1) --(*) `AdjustmentTransaction` (optional)
*   `ManualBalanceAdjustment` (1) --(*) `User` (1)
*   `Account` (1) --(*) `ManualBalanceAdjustment`
*   `Account` (1) --(*) `AdjustmentTransaction`
*   `Account` (1) --(*) `ReconciliationViewEntry`
*   `ReconciliationViewEntry` may represent data from `AdjustmentTransaction`.
