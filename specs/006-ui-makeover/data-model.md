# Data Model: UI Makeover

## Ledger Workspace ViewModel
| Field | Type | Description |
|---|---|---|
| `selectedAccountId` | string | ID of the highlighted account in the tree; null when no selection |
| `accountTree` | Array<AccountNode> | Hierarchical tree entries (name, balance, children) used to render the side panel |
| `registerRows` | Array<LedgerRow> | Virtualized slice of transactions matching the selection and filters |
| `isLoading` | boolean | Indicates when ledger data is being fetched |
| `commands` | { expandAccount(id), selectRow(id), reorderTree(direction) } | MVVM commands invoked by UI controls |

### Validation & Constraints
- The tree fetches only once per session unless accounts mutate.
- Register rows rely on backend paging; virtualization only renders the visible slice.
- Focus order preserves tree → register → detail panel to satisfy accessibility constraints.

## Reconciliation ViewModel
| Field | Type | Description |
|---|---|---|
| `activeSessionId` | string | Current reconciliation session identifier from `/reconciliation/sessions` |
| `statementBalance` | number | User-entered ending balance tied to `Difference` calculations |
| `unreconciled` | Array<ReconcileRow> | List of transactions returned from `/sessions/unreconciled` filtered by statuses |
| `selectedIds` | Set<string> | IDs checked in the UI; used to compute the `difference` when the user applies selections |
| `difference` | { amount, remaining_uncleared, difference_status } | Backend-provided object summarizing discrepancy and textual guidance |
| `statusFlags` | { pending: number, completed: number, failed: number } | Mirrors `processing_status` values for UI badges |
| `commands` | { fetchSessions(), fetchUnreconciled(), applySelection() } | MVVM commands triggered from buttons and badges |

### State Transitions
1. `fetchSessions()` sets `activeSessionId` and clears previous `selectedIds`.
2. `fetchUnreconciled()` populates `unreconciled` and `difference`; statuses determine badge colors (UNCLEARED=amber, RECONCILED=green).
3. `applySelection()` toggles entries in `selectedIds`, recalculates `difference`, and updates guidance text; the view model prevents selecting rows already marked `RECONCILED`.

## Supporting Entities from Backend Contracts
- **ReconciliationTransaction**: { id, description, amount, status: UNCLEARED|CLEARED|RECONCILED, date, processing_status }
- **DifferencePayload**: { amount, difference_status, remaining_uncleared, guidance_text }

The frontend binds these entities to MVVM stores so components stay declarative while still reflecting real-time statuses.

---

## Phase 2 Entities (2026-05-10 — remaining work)

## AccountNode (extended)

The TypeScript type used throughout the frontend. Built client-side from `AccountResponse[]`.

| Field | Type | Source |
|---|---|---|
| `id` | `string` | `AccountResponse.id` |
| `name` | `string` | `AccountResponse.name` |
| `type` | `string` | `banking_product_type` (leaf) or `accounting_category` (placeholder) |
| `code` | `string \| undefined` | `AccountResponse.account_number` |
| `balance` | `number` | `AccountResponse.hierarchy_balance` (includes children) |
| `placeholder` | `boolean` | `AccountResponse.placeholder` |
| `hidden` | `boolean` | `AccountResponse.hidden` |
| `notes` | `string \| undefined` | `AccountResponse.notes` (displayed as Description) |
| `currency` | `string` | `AccountResponse.currency` |
| `parentId` | `string \| undefined` | `AccountResponse.parent_account_id` |
| `colour` | `string \| undefined` | `localStorage['account-colours'][id]` — frontend only |
| `lastReconcileDate` | `string \| undefined` | Reconciliation API — deferred; renders `—` |
| `futureMinimum` | `number \| undefined` | Scheduled Transactions API — deferred; renders `—` |
| `children` | `AccountNode[]` | Assembled by `buildAccountTree` |

### Validation rules
- `balance` is always `hierarchy_balance` (inclusive of subtree), not `available_balance`.
- Placeholder accounts cannot be selected as register targets (toolbar buttons disabled).
- `colour` defaults to `undefined`; the C column cell renders empty (no swatch) until set.

---

## AccountFormData

Represents the New/Edit dialog form state before submission.

| Field | Type | Maps to API field |
|---|---|---|
| `name` | `string` | `name` |
| `accountCode` | `string` | `account_number` |
| `notes` | `string` | `notes` |
| `parentAccountId` | `string \| null` | `parent_account_id` |
| `accountingCategory` | `AccountingCategory` | `accounting_category` |
| `bankingProductType` | `BankingProductType` | `banking_product_type` |
| `currency` | `string` | `currency` (default: `'AUD'`) |
| `placeholder` | `boolean` | `placeholder` |
| `hidden` | `boolean` | `hidden` |
| `openingBalance` | `number` | `available_balance` (new accounts only) |
| `openingBalanceDate` | `string` | Used to create opening balance transaction (future) |
| `higherBalanceLimit` | `number \| null` | Frontend-only for now (no backend field) |
| `lowerBalanceLimit` | `number \| null` | Frontend-only for now (no backend field) |

### Validation rules
- `name` required; 1–100 chars; alphanumeric + `. , - _ ( ) & '` only.
- `accountCode` optional; alphanumeric + dashes only.
- `currency` must be one of: USD, EUR, GBP, CAD, AUD, JPY, CHF, NZD, SGD, CNY.
- `parentAccountId` must reference an existing account when provided.

---

## FilterState

Persisted to `localStorage['account-filter']`.

| Field | Type | Default |
|---|---|---|
| `accountTypes` | `Set<string>` | All types enabled |
| `showHidden` | `boolean` | `false` |
| `showZeroTotal` | `boolean` | `true` |
| `showUnused` | `boolean` | `true` |

### Filter application logic
1. Exclude `hidden === true` accounts when `showHidden` is false.
2. Exclude accounts with `balance === 0` (and no children with balance) when `showZeroTotal` is false.
3. Exclude accounts with no transactions recorded when `showUnused` is false.
4. Exclude accounts whose `accounting_category` is not in `accountTypes`.
5. Always show placeholder/group rows whose children pass the filter (to preserve tree structure).

---

## AccountingCategory enum (backend → frontend mapping)

| Backend value | Display label |
|---|---|
| `ASSET` | Asset |
| `LIABILITY` | Liability |
| `EQUITY` | Equity |
| `REVENUE` | Income |
| `EXPENSE` | Expense |

## BankingProductType enum (backend → frontend mapping)

| Backend value | Display label |
|---|---|
| `BANK` | Bank |
| `CREDIT_CARD` | Credit Card |
| `LOAN` | Loan |
| `CASH` | Cash |
| `INVESTMENT` | Mutual Fund / Investment |
| `OTHER` | Other |
