# Feature Specification: Reconcile Window

**Feature Branch**: `005-add-reconcile-window`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "a dedicated “Reconcile Window” where the user matches app records to a bank statement: 1. User workflow: Enter the ending balance from the statement, then see only the unreconciled transactions since the last statement. Check off the ones that appear on the bank statement while watching the “Difference” field update toward zero. 2. Checks and status tracking: Each transaction carries two statuses—processing_status (external state: PENDING, COMPLETED, FAILED) and reconciliation_status (internal state: UNCLEARED, CLEARED, RECONCILED). These statuses drive what appears in the window and how the difference is computed. 3. Outcome goal: The window highlights a dynamic discrepancy value that should reach $0.00 when the statement and app records are fully in sync, confirming that unreconciled transactions have been inspected and properly marked."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Match statement balance (Priority: P1)

A reconciliation specialist opens the Reconcile Window, pastes the ending bank statement balance, reviews the list of unreconciled transactions, and marks the ones that appear on the statement until the displayed difference reaches zero.

**Why this priority**: This is the primary task that confirms the ledger aligns with the bank statement, so it must be stable and testable on its own before any secondary helpers are added.

**Independent Test**: Entering a known ending balance, selecting matching transactions, and verifying the Difference field updates to zero while unchecked items remain available.

**Acceptance Scenarios**:

1. **Given** the last statement closed with a known balance and several UNCLEARED transactions exist, **When** the user enters that ending balance and selects each transaction that appears on the statement, **Then** the Difference field subtracts the total of selected transactions from the ending balance and reaches $0.00 only after every statement item has been checked.
2. **Given** a transaction fails processing_status before reconciliation, **When** the user attempts to select it, **Then** the window prevents selection and surfaces a helper message explaining that FAILED processing_status items cannot be reconciled until they are retried or corrected.

---

### User Story 2 - Surface the correct transaction set (Priority: P2)

Accountants only want to see transactions introduced after the previous statement and those still internally UNCLEARED or CLEARED, while keeping COMPLETED but RECONCILED items hidden.

**Why this priority**: Keeping the list scoped to the right data protects the difference calculation and improves reviewer focus, but it can be validated after the P1 workflow exists.

**Independent Test**: Refresh the window for each statement cycle and verify that only transactions with UNCLEARED or CLEARED reconciliation_status and acceptable processing_status values appear.

**Acceptance Scenarios**:

1. **Given** there are recent transactions marked RECONCILED and earlier UNCLEARED entries, **When** the Reconcile Window loads, **Then** only UNCLEARED and CLEARED transactions generated since the prior statement date are rendered in the list.

---

### User Story 3 - Surface discrepancy insights (Priority: P3)

A supervisor reviews why the difference is not zero after matching known transactions and needs visibility into outstanding or missing items.

**Why this priority**: Understanding unresolved discrepancies improves confidence, but it depends on the core matching experience being in place.

**Independent Test**: Force a scenario where the Difference shows a non-zero value after selecting all available transactions and confirm the interface highlights the gap and offers a summary of remaining UNCLEARED items.

**Acceptance Scenarios**:

1. **Given** the user has selected all visible transactions but the difference remains non-zero, **When** the window renders the discrepancy, **Then** the Difference field is visually emphasized (color or icon) and a message lists next steps, such as reviewing pending transactions or editing the ending balance.

---

### Edge Cases

- What happens when the ending balance entered is lower than the sum of eligible transactions (negative difference)?  
- How does the window behave if the bank statement timeframe overlaps with transactions already marked RECONCILED?  
- How do we recover if the difference is stuck because a transaction flips between CLEARED and UNCLEARED while open?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Reconcile Window MUST require an ending statement balance and use it as the basis for a Difference calculation that subtracts the sum of user-selected, eligible transactions from that balance.
- **FR-002**: The window MUST only list transactions whose reconciliation_status is UNCLEARED or CLEARED and whose processing_status is either PENDING or COMPLETED, excluding FAILED records from selection until their external processing_status becomes eligible.
- **FR-003**: The interface MUST allow users to check off each listed transaction, immediately update its reconciliation_status to CLEARED or RECONCILED depending on whether it is already matched to the statement end, and recalculate the Difference field.
- **FR-004**: The system MUST visually emphasize the Difference field and provide contextual guidance whenever the discrepancy is non-zero, including a count of remaining UNCLEARED transactions.
- **FR-005**: The Reconcile Window MUST persist the reconciliation_status changes once the user confirms their selection so subsequent visits start from the updated state and the remaining Difference reflects unreconciled transactions only.

### Key Entities *(include if feature involves data)*

- **Reconciliation Session**: Represents a user-led attempt to reconcile a statement period, capturing the ending balance, selected transactions, and the calculated discrepancy.
- **Transaction**: Financial records with attributes such as processing_status, reconciliation_status, amount, date, and relationship to parent accounts.
- **Bank Statement Snapshot**: Encapsulates the closing balance, statement period cutoff date, and flags to determine which transactions are considered "since the last statement."

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of reconciliation attempts complete with a Difference of $0.00 within 5 minutes of beginning the session.
- **SC-002**: 100% of transactions marked as selected during a reconciliation session should transition to CLEARED or RECONCILED before the window closes.
- **SC-003**: At least 90% of users report that the Reconcile Window surfaces the next action (e.g., missing transactions or stale statuses) without needing to leave the screen.
- **SC-004**: Support requests citing unexplained discrepancies for reconciled statements drop by 40% compared to the previous quarter.
