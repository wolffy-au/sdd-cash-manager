# Feature Specification: UI Makeover

**Feature Branch**: `feature/006-ui-makeover`  
**Created**: 2026-03-23  
**Status**: Draft  
**Input**: User description: "create a ui similar to gnucash ui look but with a much more intuitive feel using the best pattern suited for the project"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modern Ledger Workspace (Priority: P1)
A finance operator opens the application and immediately sees a GnuCash-inspired side tree, register list, and breadcrumb that feel familiar but emphasize clarity, spacing, and responsive layout.

**Why this priority**: The ledger workspace is the primary entry point; delivering a polished layout first ensures every subsequent workflow feels consistent and intuitive.

**Independent Test**: Load the new workspace and verify the tree, register, and detail panels render, respond to reorders, and expose MVVM-driven commands for selecting an account.

**Acceptance Scenarios**:

1. **Given** the user has multiple accounts, **When** they expand a master account, **Then** the tree smoothly animates and highlights the active account while the register refreshes without a page reload.
2. **Given** the user clicks a register row, **When** the row is selected, **Then** related panels (detail, status) update via view-model bindings and the MVVM command remains decoupled from the view layer.

---

### User Story 2 - Reconciliation Kit (Priority: P2)
An accountant opens the reconcile workspace, sees the unreconciled list, enters a statement balance, checks transactions, and observes the difference updates without modal reloads.

**Why this priority**: Reconciliation is the feature we just built on the backend; the UI must let users exercise it quickly to prove the workflow end-to-end.

**Independent Test**: Trigger the reconcile panel, call `/reconciliation/sessions`, `/sessions/unreconciled`, select some IDs, and confirm the difference field updates in real time (mock data is acceptable for UI tests).

**Acceptance Scenarios**:

1. **Given** the user enters an ending balance, **When** they click the “Fetch Unreconciled” button, **Then** the MVVM command hits `/reconciliation/sessions/unreconciled` and renders the list with stacked statuses and a Difference badge.
2. **Given** the user checks several rows, **When** the selection is applied, **Then** the difference badge uses the service payload to show `difference_status`, `remaining_uncleared`, and textual guidance.

---

### User Story 3 - Guided Discrepancy Insights (Priority: P3)
A reviewer watches the difference stay above zero and receives contextual tips (e.g., “Review missing transactions”) while the view model keeps track of previously reconciled entries.

**Why this priority**: This story enhances confidence and reduces help requests by surfacing meaningful cues when reconciliation isn’t zeroed out yet.

**Independent Test**: Simulate a difference > 0 and confirm the guidance area updates with iconography, accessible messaging, and a link to filter UNCLEARED rows.

**Acceptance Scenarios**:

1. **Given** the difference remains positive, **When** the reviewer reads the guidance panel, **Then** it offers next steps and colors the badge orange/amber.

---

### Edge Cases

- What happens when the MVVM command receives a large (>1,000) transaction set; does virtualization keep the register responsive?
- How does the UI behave when reconciliation APIs return empty lists or network errors (e.g., guidance panel shows retry)?
- How is missing data (e.g., no statement snapshot) communicated without breaking layout?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST render a familiar ledger tree + register layout inspired by GnuCash but refreshed with clearer typography, spacing, and responsive panels.
- **FR-002**: The reconcile workspace MUST bind buttons to view-model commands that call `/reconciliation/sessions`, `/reconciliation/sessions/unreconciled`, and `/reconciliation/sessions/{session_id}/transactions` without causing full-page reloads.
- **FR-003**: The UI MUST highlight statuses (UNCLEARED/CLEARED/RECONCILED) and the dynamic Difference status/guidance from the backend payload in concise badges or toast messages.
- **FR-004**: The interface MUST adopt an MVVM-inspired pattern (observables or hooks + reducers) so business logic stays testable outside of the DOM and the view updates declaratively.
- **FR-005**: Navigation components (e.g., tabs, sidebar) MUST preserve keyboard focus order and semantic roles to stay accessible while mirroring the existing GnuCash structure.

### Key Entities *(include if feature involves data)*

- **Ledger Workspace ViewModel**: Encapsulates the selected account, register rows, and actions (expand tree, filter transactions) while exposing observable state for the view to render.
- **Reconciliation ViewModel**: Manages statement balance input, unreconciled list, selected transaction IDs, and difference insight metadata bound to the guidance component.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of pilot users rate the new workspace “intuitive” or “very intuitive” on a quick survey (3 options) after using it for reconciliation tasks.
- **SC-002**: Primary reconciliation workflow (enter balance → check transactions → difference zero) completes in under 3 minutes for 85% of test scenarios.
- **SC-003**: The register and reconcile panels load in under 1 second with up to 250 transactions present (measured in the UI test harness with mock data).
- **SC-004**: Guidance text/visual states reduce help-desk references about “why difference isn’t zero” by at least 40% compared to historical logs (or by showing the guidance in the UI so users can self-serve).

***
