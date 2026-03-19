# Feature Specification: Adjust Balance Window

**Feature Branch**: `feature/003-adjust-balance`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "### 1.2 Adjust Balance Window - **Manual Balance Adjustment:** Provides a dedicated window for users to manually adjust an account's balance to a specific value. - **Automated Transaction Creation:** When a new balance is entered, the system automatically creates a new transaction on a specified date. - **Difference Calculation:** The amount of this new transaction is calculated as the difference between the target new balance and the account's existing balance up to the specified date. - **Impact on Records:** This adjustment transaction updates the account's ledger and is reflected in reconciliation views.   - The banking product enum should be updated to expose explicit “TRANSACTION” or “DEPOSIT” symbols if literal matches are required by features or tests (src/sdd_cash_manager/models/enums.py#L12‑#L31).  - The system will differentiate 'running balance' (current state) from 'cleared balance' (posted transactions only) for adjustment and reconciliation purposes, moving away from solely deriving both from available_balance (src/sdd_cash_manager/services/account_service.py#L279‑#L592)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manual balance reconciliation (Priority: P1)

As a reconciler, I need a manual balance adjustment window so I can align an account's total balance with the most recent statement before closing the period.

**Why this priority**: Reconciling balances is a daily bookkeeping task; without this window, the ledger cannot reflect the bank's reported value and auditing is delayed.

**Independent Test**: Trigger the adjustment flow for an account and verify the user can set a target balance, pick an effective date, and submit without any other workflows running.

**Acceptance Scenarios**:

1. **Given** I am on an account detail page with a balance summary, **When** I open the adjustment window and enter a new target balance with an effective date, **Then** the window accepts the value and enables the confirm action.
2. **Given** the window is open for a reconciled account, **When** I submit a new balance, **Then** I see confirmation that the adjustment transaction is scheduled for the chosen date and the ledger will reflect the correction.

---

### User Story 2 - Automated transaction creation (Priority: P2)

As an operator, I want the system to create the balancing transaction automatically so I do not need to manually insert ledger entries after every adjustment.

**Why this priority**: Manual ledger edits risk double-counting; automation guarantees the difference is sourced from the same data I entered.

**Independent Test**: Submit a target balance that differs from the current running balance and verify the system logs a new transaction dated per the window, showing the debit/credit needed to reach the target.

**Acceptance Scenarios**:

1. **Given** the current balance is 8,000 and I request a target of 8,500, **When** I submit the adjustment for March 31, **Then** a transaction dated March 31 appears with an amount of 500.

---

### User Story 3 - Ledger and reconciliation visibility (Priority: P3)

As an auditor, I need this adjustment transaction to be visible in reconciliation views so I can trace the lineage of balance edits.

**Why this priority**: Traceability ensures each manually entered balance change can be defended during reviews even if it happens after a reconciliation cut-off.

**Independent Test**: After performing an adjustment, open the reconciliation panel for the account and confirm the adjustment appears with the chosen effective date and status.

**Acceptance Scenarios**:

1. **Given** a recent balance adjustment exists, **When** I filter reconciliation entries by the effective date, **Then** the adjustment transaction is listed with its amount, the target balance, and the reconciled flag.

---

### Edge Cases

- What happens when the target balance equals the current running balance?  (System should detect zero difference and skip transaction creation while still recording the user confirmation.)
- How does the system behave when the submitted effective date is in the past or future (outside the current reconciliation period)?  (The window should allow any date but surface a non-blocking toast notification when the date falls outside the current statement range.)
- How does permissioning work when a user without adjustment rights tries to open the window?  (The UI control should be disabled (e.g., greyed out) and remain visible, and an audit entry should be logged.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST surface a dedicated manual balance adjustment window directly from each account detail page for users with the appropriate privilege.
- **FR-002**: System MUST allow the user to enter a target balance and an effective date for the adjustment before submitting.
- **FR-003**: When the target balance differs from the account's existing running balance as of the effective date, the system MUST automatically calculate the absolute difference and create a matching transaction the same date.
- **FR-004**: The automatically created transaction MUST debit or credit the account and the balancing ledger entry so that the account's running balance equals the requested target after posting.
- **FR-005**: The adjustment transaction MUST be visible in account reconciliation views with the effective date, amount, and reconciliation status so auditors can confirm the change.
- **FR-006**: System MUST persist a record of every completed adjustment attempt (including zero-difference submissions) for future audit trails, even if no ledger change is required.

### Key Entities *(include if feature involves data)*

- **ManualBalanceAdjustment**: Represents the user-entered target balance, effective date, submitting user, and whether the change replayed existing posted transactions.
- **AdjustmentTransaction**: The autogenerated ledger entry containing the calculated difference, debit/credit accounts, effective date, and reconciliation metadata needed to keep the account running balance aligned.
- **ReconciliationViewEntry**: A read-only projection that surfaces adjustment transactions (with status flags) alongside other cleared transactions within reconciliation filters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a manual balance adjustment start-to-finish (open window, enter data, submit) within 2 minutes with the UI disabling the confirm button until all inputs are valid.
- **SC-002**: Adjustments that change the balance result in an autogenerated transaction whose amount equals the difference between the requested target and the prior running balance with 100% accuracy for amounts down to cents.
- **SC-003**: Every adjustment entry appears in the reconciliation view within five seconds of creation, showing date, difference amount, and a reconciled/cleared flag so auditors can confirm.
- **SC-004**: At least 95% of auditors who review balance adjustments can trace the user, date, and quantified change without needing developer assistance.

## Assumptions

- Manual adjustments are restricted to users who already have access to the account detail page (permissions handled elsewhere).
- The reconciliation view can consume the same ledger records the adjustment transaction writes and reflect them without additional upstream work.
- Zero-difference submissions still count as an adjustment attempt for auditing but do not create new ledger entries.

## Clarifications

### Session 2026-03-16
- Q: How should the system distinguish between 'running balance' and 'cleared balance' for adjustments and reconciliation? → A: Differentiate 'running balance' (current state) from 'cleared balance' (posted transactions only) for adjustment and reconciliation purposes.
- Q: Regarding the `banking product enum` in `src/sdd_cash_manager/models/enums.py`, the spec mentions a potential need to add symbols like "TRANSACTION" or "DEPOSIT" if literal matches are required. Should these symbols be explicitly added to the enum to support specific transaction types if they are referenced literally in requirements or tests? → A: Add specific symbols for transaction types if referenced literally.
- Q: For the performance and auditability success criteria (SC-003 and SC-004), should we add specific load conditions or define explicit metrics for "developer assistance" to make them more robust and testable under varying conditions? → A: No, the current criteria are sufficient for the MVP.
- Q: Regarding users without adjustment rights, should the UI control for manual balance adjustment be hidden entirely, or should it be disabled (e.g., greyed out) while still visible? → A: Disabled - The control should be visible but unclickable/greyed out.

## Implementation status

- **Running-balance calculation** – `ManualBalanceAdjustmentService` now consumes `AccountService.calculate_running_balance_as_of`, so the difference honors the submitted `effective_date` instead of mutating the current `available_balance`.
- **Ledger posting** – Adjustments are routed through `TransactionService.create_transaction`, which generates balanced `Entry` rows, updates the account’s `available_balance`, and materializes the accompanying `AdjustmentTransaction`.
- **Reconciliation visibility** – Each adjustment invokes `ReconciliationService.create_reconciliation_entry_from_transaction`, ensuring reconciliation records backed by the adjustment metadata exist before the API response is returned.
- **Authorization/audit logging** – The endpoint enforces `Role.OPERATOR` with `require_role`, injects the JWT `subject` into the payload, and records structured logs for every attempt so the UI can disable the control for unauthorized roles.
- **Testing coverage** – Unit and integration suites now cover the adjustment/reconciliation services and API layers; the remaining risk areas are captured below.

## Outstanding work

- **Full-stack reconciliation smoke test** – Add an end-to-end regression that posts to `/accounts/{account_id}/adjust-balance`, verifies the resulting `Transaction` and `Entry` rows exist, and confirms `/accounts/{account_id}/reconciliation` surfaces the new `ReconciliationViewEntry`.
- **Permission and audit scenarios** – Create API tests (and/or assertions against `security_events`) that prove the endpoint returns 403 for unauthorized callers and that audit logs capture those rejections so the UI can safely grey-out the control.
- **Zero-difference traceability** – Extend the reconciliation suite to prove zero-difference adjustments still persist `ManualBalanceAdjustment` records (status `ZERO_DIFFERENCE`) and surface the audit entry without creating ledger transactions.
- **Documentation clarity** – Record the distinction between running-balance snapshots and cleared balances so future UI, reporting, or reconciliation work can reuse the existing helpers without uncertainty.
