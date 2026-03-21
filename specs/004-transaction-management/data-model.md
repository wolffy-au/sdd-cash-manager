# Data Model: Transaction Management

## Transaction
- **Fields**: `id`, `transfer_from_account_id`, `transfer_to_account_id`, `action`, `description`, `memo`, `amount`, `currency`, `status`, `created_at`, `updated_at`, `reconciliation_status`.
- **Relationships**: Each transaction links to two `Account` entries (debit + credit). The ledger records balanced `Entry` rows under the hood via the existing double-entry infrastructure.
- **Validation**: Ensure `transfer_from` ≠ `transfer_to`, both accounts exist and are active, amount > 0, currency in ISO 4217, and hierarchy depth limits maintainable post-transaction.
- **State transitions**: `status` flows from `draft` → `posted` once both entries persist; `reconciliation_status` ties into reconciliation entries created per transaction.

## QuickFillTemplate
- **Fields**: `id`, `action`, `currency`, `transfer_from_account_id`, `transfer_to_account_id`, `amount`, `memo`, `confidence_score`, `history_count`, `last_used_at`, `source_transaction_id`.
- **Derivation**: Generated from historical transactions meeting the same action/currency pairing; recency and frequency drive `confidence_score`.
- **Usage**: QuickFill suggestions return the fields above (excluding `source_transaction_id`) to pre-populate new transaction forms.

## DuplicateCandidate
- **Fields**: `candidate_id`, `account_id`, `matching_transaction_ids`, `amount`, `date`, `description`, `confidence`, `scope` (`account` or `account_group`).
- **Relationships**: Ties to the set of `Transaction` records it flags; reconciliation metadata is referenced to ensure balances remain stable.
- **Validation**: Only includes entries where accounts, amount, and date match exactly; optional metadata differences are surfaced for manual review.
- **Lifecycle**: A candidate enters `review` state until an admin either consolidates or dismisses it; consolidation merges entries (ensuring double-entry) and logs audit metadata.

## AccountMergePlan
- **Fields**: `plan_id`, `source_account_id`, `target_account_id`, `reparenting_map` (child account → new parent), `affected_entries_count`, `audit_notes`, `initiated_by`, `status` (`pending`, `validated`, `executed`, `rejected`).
- **Behavior**: Validates that moving the hierarchy maintains the ≤5 depth constraint; ensures child accounts, ledger rows, and reconciliation markers are reassigned to the target.
- **Audit**: Logs before/after balances for both source and target along with metadata (operator, timestamp).

## Validation & Guardrails
- QuickFill templates are only activated after an admin approves them, requiring explicit `status` toggles in the template metadata.
- Duplicate detection snapshots operate on a query-time copy of the transactions to prevent concurrent mutation conflicts.
- Merge operations leverage `AccountHierarchy` helpers from spec 001 to recompute aggregates post-transfer.
