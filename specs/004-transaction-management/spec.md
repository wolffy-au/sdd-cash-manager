# Feature Specification: Transaction Management

## Clarifications
### Session 2026-03-21
- Q: What benchmark defines SC-002’s QuickFill edit reduction target? → A: Run an automated entry script over 1,000 repeat transactions with the same action/currency and compare manual edits before and after QuickFill confirmation (measure form fields unchanged edits to prove the 40% reduction).

**Feature Branch**: `feature/004-transaction-management`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "Create the transaction management features that map to section 2 of PROJECT_SPECIFICATION.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a double-entry transaction (Priority: P1)

A user enters a new transaction in the register view by choosing a source account, a target account, an action (e.g., Buy, Sell, Transfer), date, and amount. The system enforces double-entry, creates mirrored debit/credit entries, and immediately updates every involved account's balance and reconciliation status.

**Why this priority**: Every financial event must retain double-entry integrity before any analysis, so this story is the foundation of the ledger.

**Independent Test**: Submit a transaction payload via the API (or UI helper) with `transfer_from`, `transfer_to`, `action`, and amount, and verify both accounts hold balanced entries and neither side can be persisted without the other.

**Acceptance Scenarios**:

1. **Given** two valid accounts with enough permissions, **When** I submit a transaction request with `transfer_from`, `transfer_to`, `amount`, and `action`, **Then** the system records both debit and credit entries and increments the related accounts' running balances and reconciliation snapshots.
2. **Given** the same transaction, **When** I inspect either account's ledger or hierarchy aggregate, **Then** I see the transaction reflected consistently and the aggregated parent balance recalculates to include both sides.

---

### User Story 2 - Use QuickFill suggestions to accelerate entry (Priority: P2)

While typing a description or memo, the user receives QuickFill templates derived from recent similar transactions (same action and currency). Selecting a template populates the remaining fields (accounts, amounts) but still allows edits before save and does not commit balances until confirmation.

**Why this priority**: Speeds up repetitive entries and reduces input errors for high-frequency operations without blocking manual control.

**Independent Test**: Type keywords that match previous entries, accept the top QuickFill suggestion, then verify that `transfer_from`, `transfer_to`, `action`, and `amount` fields match the template before submission.

**Acceptance Scenarios**:

1. **Given** existing transaction history with matching metadata, **When** I begin entering new data with the same action/currency, **Then** QuickFill surfaces the best match and pre-fills the fields when I pick it.
2. **Given** no suitable historical match, **When** I type a unique description, **Then** QuickFill does not surface stale candidates and manual entry proceeds without interference.

---

### User Story 3 - Clean up duplicates and merge accounts (Priority: P3)

During a data-cleanup session, an admin runs the duplicate detector which lists identical transactions at the account and group level; after review the admin consolidates them into a single canonical row. The admin also merges redundant accounts that share metadata; rails children and ledger rows to the target without altering aggregate balances.

**Why this priority**: Duplicate entries and fragmented accounts erode trust in reports, so the cleanup tools ensure financial accuracy before deeper analysis.

**Independent Test**: Feed the detector with known duplicates, confirm it reports matching pairs for review, then execute a merge and verify only one canonical transaction/account remains while balances stay consistent.

**Acceptance Scenarios**:

1. **Given** two identical transactions in the same account, **When** duplicate cleanup runs, **Then** it flags them for consolidation and prevents destructive deletion of unique entries.
2. **Given** two accounts with matching name/notes/type, **When** I trigger a merge, **Then** child accounts and entries move to the target account and reconciliation metadata/logs record the merge.

---

### Edge Cases

- What happens when one of the accounts involved in a transaction is archived or deleted? The API must reject the submission with a validation error and leave existing balances untouched.
- How does QuickFill behave when the most recent templates share the same keywords but different currencies or actions? The suggestion engine should prioritize exact currency/action matches and fall back to “no match” when ambiguity remains.
- What happens if duplicate detection finds transactions that differ only in metadata such as notes? The detector should surface them for manual review (do not auto-merge) until a human confirms.
- How does the system guard against merging accounts whose hierarchies would exceed the 5-level depth limit? The merge routine must reparent children/flatten as needed or reject the merge if constraints would be violated.
- What happens if duplicate cleanup runs at the same time a new transaction is created? The cleanup job must operate on a snapshot and either retry or abort when a conflict is detected to preserve ledger consistency.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST enforce double-entry accounting for every transaction, requiring `transfer_from` and `transfer_to` accounts, and atomically persisting both debit and credit entries to keep the ledger balanced.
- **FR-002**: Transactions MUST include an `action` (Buy, Sell, Transfer, etc.) and descriptive metadata that persist in both entries and populate QuickFill history for future use.
- **FR-003**: QuickFill MUST derive candidate templates from the most recent similar transactions (same action and currency), surface the highest confidence match in real time, and allow confirmation with a single interaction before any balances change.
- **FR-004**: Duplicate detection MUST run at account and account-group scope, flag identical entries for manual consolidation, and offer a safe merge path that leaves reconciliation balances unchanged.
- **FR-005**: Account merge operations MUST move child accounts, ledger rows, and reconciliation markers from the source to the target account, log the operation, and preserve aggregate balances even across hierarchies.
- **FR-006**: Administrators MUST be able to approve/discard QuickFill templates and duplicate-consolidation suggestions via dedicated workflows so automation can be corrected or tuned.

### Key Entities *(include if feature involves data)*

- **Transaction**: Represents a double-entry transfer with metadata (`action`, `description`, `memo`, `amount`, `currency`, `status`) plus links to both debit and credit accounts and reconciliation state.
- **QuickFillTemplate**: A derived entity composed of historical `action`, account pair, currency, and formatted memo; includes confidence scores and last-used timestamps for ranking.
- **DuplicateCandidate**: Encapsulates a set of matching transactions (accounts, amount, date) and suggests a canonical entry along with reconciliation implications.
- **AccountMergePlan**: Describes source/target accounts, child reparenting, depth-limit validation, and audit metadata for controlled merges.

## Assumptions

- Existing account hierarchy APIs (spec 001) are available to render the register, validate merges, and recalculate aggregates without reimplementation.
- QuickFill reuses the same datastore as the ledger, so it inherits existing performance safeguards rather than introducing a separate service.
- Duplicate detection and merge operations may run asynchronously but must emit deterministic audit logs and provide manual confirmation before altering data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of transaction submissions that pass validation create matching debit and credit rows; any unbalanced payload is rejected before persistence.
- **SC-002**: QuickFill suggestion acceptance requires at most two clicks and reduces manual field edits for repeat entries by at least 40% in benchmark scenarios.
- Benchmark note: measure SC-002 by running an automated entry script over 1,000 repeat transactions with the same action/currency and comparing the number of manual edits before vs after using QuickFill so the 40% reduction is demonstrable.
- **SC-003**: Duplicate detection scans datasets of 1,000 transactions in under 3 seconds and reports only exact matches for manual review.
- **SC-004**: Account merges either succeed with audit logging or leave the source/target untouched, with aggregate balances verifying unchanged totals after the operation.
