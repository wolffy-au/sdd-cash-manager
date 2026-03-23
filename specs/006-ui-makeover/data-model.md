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
