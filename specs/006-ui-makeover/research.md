# Research: UI Makeover

## Decision: Frontend as React + Vite single-page app
**Rationale**: React 18 with Vite delivers fast hot reload, tree-shaking, and integrates easily with MVVM-style hooks/stores we need for the ledger/reconciliation flows. The tooling has mature virtualization components (e.g., react-virtual) and good accessibility support.
**Alternatives considered**: SvelteKit for built-in reactivity (more recent but smaller ecosystem) and Angular for built-in structure (heavier bundle). React scored higher due to existing team familiarity and ecosystem speed.

## Decision: MVVM-inspired state via Zustand/xState stores
**Rationale**: The spec demands observable view models decoupled from the DOM, so we centralize ledger/reconciliation state in focused stores and expose commands to components rather than letting them manage individual API calls.
**Alternatives considered**: Managing state purely with React Context (too noisy for virtualization) or Redux Toolkit (boilerplate-heavy) — Zustand/xState blend gives clarity and minimal ceremony.

## Decision: Virtualized ledger/register lists + badges for statuses
**Rationale**: To keep the UI responsive with 250+ rows, virtualization keeps render counts low and the Difference badge refresh remains under the 1s load budget. Badges ingest backend statuses (UNCLEARED/CLEARED/RECONCILED) to fulfill FR-003.
**Alternatives considered**: Pagination (slows browsing and breaks GNucash feel) and server-side rendering (not necessary for interactive matching). Virtualization with incremental loading satisfies responsiveness requirements.

## Decision: Accessible discrepancy guidance panel
**Rationale**: The non-zero Difference experience now communicates the remaining UNCLEARED count with icons, copy, and a consistent accent bar so auditors immediately understand what action to take. High contrast outlines (`insight-under`, `insight-over`) plus the `Highlight UNCLEARED rows` action keep the component legible at small sizes.
**Alternatives considered**: Using tooltips or plain badges (dropped because they lacked context) or relying on modal dialogs (too interruptive). The lightweight panel stays in the flow and backs its color decisions with the Tailwind contrast checks recorded in layout.css.

---

## Phase 2 Decisions (2026-05-10 — remaining work)

## Decision: React Query v5 for server state

**Decision**: Add `@tanstack/react-query` v5 alongside Zustand. `useQuery(['accounts'])` owns the account tree; `useMutation` + `invalidateQueries` drives auto-refresh after creates/updates/deletes.

**Rationale**: The backend already has full CRUD. React Query's cache + invalidation model is the idiomatic answer to "refresh after mutation" — no manual refetch calls, built-in loading/error states, deduplication of concurrent requests.

**Alternatives considered**: SWR (lighter but less ergonomic mutation API); raw fetch + Zustand actions (works but requires hand-rolling caching, deduplication, invalidation).

---

## Decision: Backend API — all endpoints already exist

**Decision**: No new backend work required. All account CRUD is live in `src/sdd_cash_manager/api/accounts.py`.

| Operation | Endpoint | Method | Auth Role |
|---|---|---|---|
| List accounts | `/accounts/` | GET | VIEWER |
| Create account | `/accounts/` | POST | OPERATOR |
| Update account | `/accounts/{id}` | PUT (patch semantics) | OPERATOR |
| Delete account | `/accounts/{id}` | DELETE | OPERATOR |

`AccountResponse` fields: `id`, `name`, `currency`, `accounting_category`, `banking_product_type`, `account_number`, `available_balance`, `hierarchy_balance`, `credit_limit`, `notes`, `parent_account_id`, `hidden`, `placeholder`.

Fields **not** in backend (frontend-only or deferred): `colour` (localStorage), `lastReconcileDate` (reconciliation API, deferred), `futureMinimum` (scheduled transactions, deferred — renders `—`).

---

## Decision: Tree building — client-side, O(n)

**Decision**: `buildAccountTree(accounts: AccountResponse[]): AccountNode[]` — pure utility in `src/lib/buildAccountTree.ts`.

**Algorithm**: (1) Map `id → AccountNode`; (2) attach each node to its parent's `children` array; (3) return root nodes sorted by category order (ASSET → LIABILITY → EQUITY → REVENUE → EXPENSE) then name.

**Type mapping**: `type` column = `banking_product_type` for leaf accounts; `accounting_category` for placeholder/group rows. `code` = `account_number`.

---

## Decision: Account colour — localStorage only

**Decision**: Colour is a display preference not stored in the backend. `localStorage['account-colours']` holds `Record<accountId, string>` (CSS colour value). `useAccountColours()` hook reads/writes it. `ColourSwatch` uses `<input type="color">` — no library.

---

## Decision: Authentication — Axios interceptor

**Decision**: An Axios request interceptor reads `localStorage['auth-token']` and attaches `Authorization: Bearer {token}`. If no token, requests return 401 which `useAccounts` surfaces as an error state.

**Note**: Proper auth UI is a separate feature. This is a minimum viable wire-up.

---

## Decision: Filter dialog — client-side, localStorage

**Decision**: Filter state (`FilterState`) is applied in React to the already-fetched account list — no backend re-fetch. State persisted to `localStorage['account-filter']` and rehydrated on app load.

**Filter dimensions**: account type checkboxes (ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE + banking product subtypes); show hidden (default false); show zero total (default true); show unused (default true).

---

## Decision: Modal / focus trap — no external library

**Decision**: Generic `Modal.tsx` wrapper with manual focus trap using `useRef` + `keydown` handler cycling `Tab`/`Shift+Tab` within the dialog. `Escape` closes. `role="dialog"` + `aria-modal="true"`.

**Rationale**: Avoids adding Radix/HeadlessUI for a single use case.
