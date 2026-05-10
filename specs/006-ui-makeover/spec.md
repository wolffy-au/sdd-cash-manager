# Feature Specification: UI Makeover

**Feature Branch**: `feature/006-ui-makeover`  
**Created**: 2026-03-23  
**Updated**: 2026-05-10  
**Status**: Partially Implemented  
**Input**: User description: "create a ui similar to gnucash ui look but with a much more intuitive feel using the best pattern suited for the project"

## What Was Built

The implementation delivers a GnuCash-inspired ledger workspace with a modern dark/light theme, MVVM-style state management via Zustand, and a context-sensitive toolbar — all without page reloads.

### App Shell (`App.tsx`)

- The reconciliation panel is now **slide-in on demand**: clicking the toolbar "Reconcile" button toggles a side panel; a `✕` button closes it.
- The `LedgerFeature` receives `onReconcile` / `reconcileActive` props so the toolbar button reflects panel state without coupling the feature to the shell.

### Theme System (`layout.css`)

A full CSS custom-property token set covers both dark (default) and light (`prefers-color-scheme: light`) themes:

| Token group | Purpose |
|---|---|
| `--app-*` | Shell background gradient, text, muted text, panel bg/border |
| `--ledger-panel-*` | Account tree and register panel surfaces |
| `--tbl-*` | Table header, row hover/selected, totals footer, text hierarchy |
| `--balance-positive / --balance-negative` | Cyan (dark) / forest green (light) vs red |
| `--ctrl-*`, `--accent` | Inputs, buttons, focus ring |
| `--recon-*` | Reconciliation input and row surfaces |

### Account Tree (`AccountTree.tsx`)

Replaced the recursive div renderer with a **flat-row table** approach:

- Columns: **Account Name**, **Type**, **Account Code**, **Total**
- Hierarchical indent is an inline `width` spacer; expand/collapse is a `▸`/`▾` `<button>` (accessible, stops event propagation).
- Placeholder/group rows render in a distinct muted style; leaf rows show an SVG account icon.
- **Double-click** on a leaf row opens it as a register tab.
- Grand Total footer row spans the name/type/code columns.
- `AccountNode` type extended with `type: string`, `code?: string`, `placeholder?: boolean`.

### Register (`Register.tsx`)

Replaced the `<ul>` + prev/next pagination with a **full table**:

- Columns: **Date**, **Num**, **Description**, **Transfer**, **R** (reconciliation status), **Amount**, **Balance**.
- Reconciliation status displays as `R` (reconciled), `c` (cleared), or blank (uncleared).
- Amounts and balances are formatted with `en-AU` locale (2 dp, absolute value, sign prefix).
- `LedgerRow` type extended with `num?: string`, `transfer?: string`, `reconciled?: 'n' | 'c' | 'y'`, `balance: number`.

### Ledger Feature (`features/ledger.tsx`)

Major rewrite introducing three sub-systems:

1. **Split pane**: tree and register panels separated by a draggable `ledger__divider`; width driven by `useSplitPane`.
2. **Tab bar**: an Accounts tab (permanent) plus closeable per-account Register tabs. Opening a register tab from the tree (double-click or toolbar button) adds a tab; closing it returns focus to Accounts.
3. **Toolbar awareness**: `LedgerToolbar` receives `tabType` and `canActOnSelected`; buttons are disabled/enabled accordingly. Reconcile button is also toggled active to reflect panel state.

Sample data uses a realistic multi-level hierarchy: Assets (Bank × 3, Investments × 2), Equity, Expenses (Groceries, Utilities, Dining, Auto × 2), Income, and Liabilities.

### LedgerToolbar (`components/ledger/LedgerToolbar.tsx`) — new file

Context-sensitive icon toolbar with two variants:

| Tab context | Buttons |
|---|---|
| Accounts | New · Edit · Delete \| Open Register \| Reconcile \| Filter |
| Register | Enter · Blank \| Delete \| Schedule |

Each button uses an inline SVG icon (no icon-font dependency) and a text label below. Disabled state is propagated from `canActOnSelected`. The Reconcile button carries an `--active` modifier class when the reconciliation panel is open.

### TabBar (`components/common/TabBar.tsx`) — new file

Generic tab strip with ARIA `role="tablist"` / `role="tab"` / `aria-selected`. Closeable tabs render a `✕` button that fires `onClose` without triggering `onSelect`.

### useSplitPane (`hooks/useSplitPane.ts`) — new file

Drag-to-resize hook:
- Reads initial width from `localStorage` (key is caller-supplied).
- Clamps to configurable `min` / `max` px.
- Attaches `mousemove` / `mouseup` listeners on `document` and sets `cursor: col-resize` on `body` during drag.
- Persists final width to `localStorage` on `mouseup`.

---

## Remaining Work (from reference screenshots)

Three feature areas visible in the GnuCash reference screenshots (`specs/006-ui-makeover/screenshots/`) are **not yet implemented** and should be treated as the next implementation phase. A fourth area (the Account Hierarchy Setup Wizard) is a stretch goal deferred to a separate feature.

### 1. New / Edit Account Dialog (`account-new-*`, `account-edit-*`)

A modal dialog with three tabs opened from the New and Edit toolbar buttons:

**General tab**
- Account name (text input, required)
- Account code (text input — BSB/account number)
- Description (text input)
- Parent Account — inline tree picker showing the full account hierarchy with expand/collapse
- Account Type — dropdown (Bank, Cash, Asset, Credit Card, Liability, Equity, Income, Expense, Stock, Mutual Fund, Currency, A/Receivable, A/Payable, Trading)
- Security/currency — read-only display + "Select…" button (AUD Australian Dollar default)
- Smallest fraction — dropdown (Use Commodity Value)
- Account Colour — colour swatch + "Default" reset button
- Notes — multi-line text area
- Checkboxes: Placeholder, Hidden, Auto interest transfer, Tax related, Opening balance

**More Properties tab**
- Higher Balance Limit (number input)
- Lower Balance Limit (number input)
- Include sub accounts (checkbox)

**Opening Balance tab** (New Account only)
- Balance (number input, default 0.00)
- Date (date picker, defaults to today)
- Initial Balance Transfer — radio group:
  - Use equity 'Opening Balances' account (default)
  - Select transfer account (reveals account tree picker)

Both New and Edit use the same form; Edit pre-fills all fields from the selected account. The dialog title shows the full account path (e.g. `Assets:Bank and Cash Accounts:W Direct Debits`).

---

### 2. Filter Accounts Dialog (`accounts-filter-*`)

A two-tab modal opened from the Filter toolbar button:

**Account Type tab**
- Checkboxes for every account type: Bank, Cash, Asset, Credit Card, Liability, Stock, Mutual Fund, Currency, Income, Expense, Equity, A/Receivable, A/Payable, Trading
- Select All / Clear All / Default buttons

**Other tab**
- Show hidden accounts (unchecked by default)
- Show zero total accounts (checked by default)
- Show unused accounts (checked by default)

Filter state should be persisted (e.g. `localStorage`) and applied to the account tree view reactively.

---

### 3. Richer Account Tree Columns (`acount-register-2`)

The reference screenshot shows additional columns beyond Name / Type / Account Code / Total:

| Column | Notes |
|---|---|
| Description | Free-text description stored on the account |
| Last Reconcile Date | Date of most recent reconciliation (e.g. `20/11/2025`) |
| Future Minimum | Projected minimum balance |
| C | Account colour — shown as a coloured swatch (orange, green, red) in the row; clicking opens a colour picker |
| H | Hidden flag — checkbox; toggling hides the account from the default view |
| P | Placeholder flag — checkbox; toggling marks the account as a non-transactable group |

The tab bar in that screenshot also shows non-Accounts tabs (Income & Expense, Balance Sheet, Dashboard) opened from a Reports menu — these are separate from the register tabs and represent a future reporting phase.

---

### 4. Account Hierarchy Setup Wizard (`account-hierarchy-*`) ⚠️ Stretch Goal

> **Deferred** — this wizard is a stretch goal and is likely to be implemented as a separate feature once the account CRUD dialog (item 1 above) is stable. It is documented here for reference only and should not block delivery of items 1–3.

A 5-step wizard triggered by "New Account Hierarchy…" for seeding a new book. Steps shown in a left-side progress nav:

1. **New Account Hierarchy Setup** — intro text explaining the wizard
2. **New Book Options** — tabbed settings (Accounts, Budgeting, Business, Counters, Tax); Accounts tab has "Day Threshold for Read-Only Transactions", "Use Trading Accounts", "Use Split Action Field for Number"
3. **Choose Currency** — single dropdown (defaults to AUD Australian Dollar)
4. **Choose accounts to create** — left panel: category list (A Simple Checkbook, Business Accounts, Car Loan, CD and Money Market, Childcare Expenses, Common Accounts, Education Loan, Fixed Assets, …) with checkboxes and language/region pickers; right panel: live preview tree of accounts the selected category will create; category description area; Select All / Clear All buttons; link to GnuCash Account Template Wiki
5. **Setup selected accounts** — flat tree with columns Account Name, Type, Placeholder (checkbox), Opening Balance (editable); placeholder-flagged rows are highlighted
6. **Finish Account Setup** — summary with Apply / Back / Cancel

---

## Clarifications

### Session 2026-05-10

- Q: Should the New/Edit Account dialog save to a backend REST API or local Zustand state only? → A: Backend API (POST /accounts, PATCH /accounts/{id}); UI must refresh automatically via a reactive hook when the server confirms the change.
- Q: Should the Account Hierarchy Setup wizard (FR-009) be built in this cycle or deferred? → A: Deferred — implement FR-008 (dialog) first; wizard is a separate follow-up feature once the CRUD API is stable.
- Q: Does the Filter Accounts dialog filter client-side or re-fetch from the backend? → A: Client-side only — filter applied in React to the already-fetched tree; state persisted to `localStorage`.
- Q: How should the Future Minimum column in FR-011 be calculated? → A: Computed from upcoming scheduled transactions (backend endpoint), but scheduled transactions are deferred — column renders a dash/placeholder until that feature ships.
- Q: Which data-fetching layer should drive the auto-refresh after account saves? → A: React Query (TanStack Query) — `useQuery` for `GET /accounts`, `useMutation` + `invalidateQueries` for `POST`/`PATCH`/`DELETE`.

---

## User Scenarios & Testing

### User Story 1 - Modern Ledger Workspace (Priority: P1)

A finance operator opens the application and immediately sees a GnuCash-inspired account tree and register that feel familiar but emphasize clarity, spacing, and responsive layout.

**Why this priority**: The ledger workspace is the primary entry point; delivering a polished layout first ensures every subsequent workflow feels consistent and intuitive.

**Independent Test**: Load the workspace and verify the tree table, register table, split-pane divider, and tab bar all render; confirm expand/collapse, account selection, and double-click-to-register-tab all work without page reload.

**Acceptance Scenarios**:

1. **Given** the user has multiple accounts, **When** they click a disclosure triangle, **Then** child accounts collapse/expand in place and the selected account row is highlighted while the register panel remains unchanged.
2. **Given** the user double-clicks a leaf account, **When** the action is processed, **Then** a closeable register tab opens and the toolbar switches to register context (Enter/Blank/Delete/Schedule buttons).
3. **Given** the user drags the split-pane divider, **When** they release the mouse, **Then** the new width is persisted to `localStorage` and survives a page refresh.

---

### User Story 2 - Reconciliation Kit (Priority: P2)

An accountant opens the reconcile workspace, sees the unreconciled list, enters a statement balance, checks transactions, and observes the difference updating without modal reloads.

**Why this priority**: Reconciliation is the feature built on the backend; the UI must let users exercise it quickly to prove the workflow end-to-end.

**Independent Test**: Click "Reconcile" in the toolbar with a leaf account selected; confirm the side panel slides in and ReconciliationFeature renders. Close with `✕` and confirm the panel unmounts cleanly.

**Acceptance Scenarios**:

1. **Given** the user selects a leaf account and clicks Reconcile, **When** the action fires, **Then** the reconciliation panel appears alongside the ledger without a full-page reload, and the toolbar Reconcile button shows as active.
2. **Given** the user enters an ending balance and fetches unreconciled, **When** the MVVM command completes, **Then** the list renders with `R`/`c`/blank status indicators and a Difference badge.
3. **Given** the user checks several rows, **When** the selection is applied, **Then** the difference badge updates in real time using `difference_status` and `remaining_uncleared` from the service payload.

---

### User Story 3 - Guided Discrepancy Insights (Priority: P3)

A reviewer watches the difference stay above zero and receives contextual tips while the view model tracks previously reconciled entries.

**Why this priority**: This story enhances confidence and reduces help requests by surfacing meaningful cues when reconciliation is not yet zeroed out.

**Independent Test**: Simulate a difference > 0 and confirm the guidance area updates with iconography, accessible messaging, and a link to filter UNCLEARED rows.

**Acceptance Scenarios**:

1. **Given** the difference remains positive, **When** the reviewer reads the guidance panel, **Then** it offers actionable next steps and the badge is colored orange/amber.

---

### Edge Cases

- Large transaction sets (>1,000 rows): the register table currently renders all rows; virtualization should be added if scroll performance degrades.
- Reconciliation API errors: guidance panel should show a retry prompt; network errors currently fall back to the reconciliation feature's own error handling.
- Missing data (no statement snapshot): layout must not break; empty-state copy should guide the user.
- Split pane on narrow viewports: the `min` clamp (160 px) prevents the tree from disappearing; register panel should remain usable.

---

## Requirements

### Functional Requirements

- **FR-001**: The application MUST render a GnuCash-inspired account tree table (Name / Type / Account Code / Total) and register table (Date / Num / Description / Transfer / R / Amount / Balance) with responsive split-pane layout.
- **FR-002**: The reconcile panel MUST open as a slide-in from the toolbar Reconcile button and bind to view-model commands that call `/reconciliation/sessions`, `/reconciliation/sessions/unreconciled`, and `/reconciliation/sessions/{session_id}/transactions` without full-page reloads.
- **FR-003**: The register MUST display reconciliation status per row (`R`, `c`, blank) and the reconciliation panel MUST surface `difference_status`, `remaining_uncleared`, and guidance text from the backend payload.
- **FR-004**: The interface MUST use an MVVM-inspired pattern (React Query for server state + Zustand for local UI state + hooks) so business logic stays testable outside the DOM and the view updates declaratively. React Query owns account tree data; Zustand owns ephemeral UI state (selected account, register rows, tab list).
- **FR-005**: The toolbar, tab bar, and tree disclosure buttons MUST carry semantic ARIA attributes (`role`, `aria-selected`, `aria-label`) and respect keyboard focus order.
- **FR-006**: The split-pane divider MUST persist its position to `localStorage` and restore it on reload, clamped within configurable min/max bounds.
- **FR-007**: The context-sensitive toolbar MUST switch button sets between Accounts context and Register context and disable inapplicable actions when no leaf account is selected.
- **FR-008**: The New / Edit Account dialog MUST present a three-tab modal (General, More Properties, Opening Balance) with a parent-account tree picker, account type dropdown, currency display, colour selector, placeholder/hidden flags, balance limits, and opening balance with transfer-account selection. Edit mode pre-fills all fields from the selected account. On OK, the dialog MUST call `POST /accounts` (new) or `PATCH /accounts/{id}` (edit) and the account tree MUST refresh automatically via a reactive hook (e.g. React Query invalidation or SWR revalidation) when the backend confirms the change — no manual page reload.
- **FR-009**: ~~A New Account Hierarchy wizard MUST guide users through 5 steps~~ **DEFERRED** — the Account Hierarchy Setup wizard is out of scope for this cycle. It will be specified as a separate feature once the account CRUD API (FR-008) is stable.
- **FR-010**: The Filter Accounts dialog MUST provide an Account Type tab (per-type checkboxes + Select All / Clear All / Default) and an Other tab (show hidden / show zero total / show unused). Filtering MUST be applied client-side to the already-fetched account tree (no backend re-fetch); filter state MUST be persisted to `localStorage` and applied reactively on load and on change.
- **FR-011**: The account tree MUST support additional columns: Description, Last Reconcile Date, Future Minimum, and C/H/P indicator columns (colour swatch, hidden checkbox, placeholder checkbox), with the colour swatch opening an inline colour picker. Future Minimum MUST be computed from scheduled transactions via a backend endpoint; until the Scheduled Transactions feature ships, the column MUST render a `—` placeholder and must not block layout or other columns.

### Key Entities

- **AccountNode**: `{ id, name, type, code?, balance, placeholder?, description?, colour?, hidden?, lastReconcileDate?, futureMinimum?, children? }` — extended to carry account type, optional BSB/account code, display flags, and a flag distinguishing group rows from transactable accounts. Sourced from `GET /accounts` and mutated via `POST /accounts` / `PATCH /accounts/{id}` / `DELETE /accounts/{id}`.
- **LedgerRow**: `{ id, date, num?, description, transfer?, reconciled?, amount, balance }` — extended with transaction number, transfer account, reconciliation flag, and running balance.
- **Ledger Workspace ViewModel** (`useLedgerStore`): exposes `registerRows`, `selectedAccountId`, and `commands` (`expandAccount`, `selectRow`). Account tree data is owned by React Query (`useQuery(['accounts']`) and no longer held in Zustand; mutations invalidate the `accounts` query key to trigger automatic refetch.
- **Reconciliation ViewModel**: manages statement balance input, unreconciled list, selected IDs, and difference insight metadata.
- **useSplitPane**: encapsulates drag state, clamping, and localStorage persistence for the resizable divider.

---

## Implementation Map

| File | Change |
|---|---|
| `frontend/src/App.tsx` | Toggle-driven reconciliation side panel; `onReconcile` / `reconcileActive` props on LedgerFeature |
| `frontend/src/types.ts` | Extended `AccountNode` and `LedgerRow` types |
| `frontend/src/styles/layout.css` | Full CSS token system (dark + light), all new component class definitions |
| `frontend/src/features/ledger.tsx` | Split-pane, tab bar, toolbar wiring, realistic sample data |
| `frontend/src/components/ledger/AccountTree.tsx` | Flat-row table with expand/collapse, icons, Grand Total footer |
| `frontend/src/components/ledger/Register.tsx` | Full table with R-status column, locale-formatted amounts, running balance |
| `frontend/src/components/ledger/LedgerToolbar.tsx` | **New** — SVG icon toolbar, Accounts and Register variants |
| `frontend/src/components/common/TabBar.tsx` | **New** — generic ARIA tab strip with closeable tabs |
| `frontend/src/hooks/useSplitPane.ts` | **New** — drag-to-resize hook with localStorage persistence |

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: At least 90% of pilot users rate the new workspace "intuitive" or "very intuitive" on a quick survey (3 options) after using it for reconciliation tasks.
- **SC-002**: Primary reconciliation workflow (enter balance → check transactions → difference zero) completes in under 3 minutes for 85% of test scenarios.
- **SC-003**: The register and reconcile panels load in under 1 second with up to 250 transactions present (measured in the UI test harness with mock data).
- **SC-004**: Guidance text/visual states reduce help-desk references about "why difference isn't zero" by at least 40% compared to historical logs.

***
