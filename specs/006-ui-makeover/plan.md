# Implementation Plan: UI Makeover

**Branch**: `006-ui-makeover` | **Date**: 2026-05-10 | **Spec**: [../spec.md](../spec.md)
**Input**: Feature specification from `/specs/006-ui-makeover/spec.md`

## Summary

Deliver the remaining UI Makeover work on top of the already-shipped GnuCash-inspired ledger workspace (split-pane, tab bar, toolbar, dark/light theme). The three remaining deliverables are:

1. **New / Edit / Delete Account dialog** (FR-008) — a three-tab modal (`AccountDialog`) backed by `POST /accounts/`, `PUT /accounts/{id}`, `DELETE /accounts/{id}`; auto-refreshes the tree via React Query `invalidateQueries` on success. Requires a React Query migration to replace static sample data first.
2. **Filter Accounts dialog** (FR-010) — client-side-only 2-tab filter dialog (type checkboxes + other flags), filter state persisted to `localStorage` and applied reactively.
3. **Richer account tree columns** (FR-011) — Description / Last Reconcile Date / Future Minimum (placeholder `—`) / C / H / P columns added to the account tree table.

The Account Hierarchy Setup wizard (FR-009) is a **stretch goal deferred** to a separate feature cycle once the CRUD API is stable.

## Technical Context

**Language/Version**: TypeScript 5.3 (frontend) — Python 3.12 FastAPI backend exists and is not modified in this cycle
**Primary Dependencies**: React 18.3, Vite 5, Zustand 5.0 (UI state only), `@tanstack/react-query` v5 (server state), Axios 1.15 (HTTP + JWT interceptor), Tailwind CSS 3.4, Vitest 1.4, @testing-library/react 15, Playwright 1.48
**Storage**: PostgreSQL via FastAPI (account persistence); `localStorage` for account colours (`account-colours`), filter state (`account-filter`), split-pane width (`ledger-split-px`)
**Testing**: Vitest + React Testing Library (unit/component — TDD); Playwright (E2E flows)
**Target Platform**: Modern desktop browsers (Chromium, Firefox, Safari)
**Project Type**: Web application — frontend only in this cycle
**Performance Goals**: Account tree populates in <1 s; client-side filter applies in <100 ms; React Query cache eliminates redundant fetches on tab switches
**Constraints**: ARIA-accessible modal dialogs with focus trap; keyboard focus order preserved; no page reloads on mutations; Future Minimum column renders `—` gracefully until Scheduled Transactions ships
**Scale/Scope**: Dozens of accounts; up to 250 register rows per session

## Constitution Check

*GATE: Code Quality (I), Testing (II), UX Consistency (III), Performance (IV), Security (V), State Management (VI)*

| Gate | Status | Evidence |
|---|---|---|
| I. Code Quality | ✅ PASS | `buildAccountTree` pure utility; `useAccounts` hook isolates fetch logic; components stay focused (dialog tabs are separate sub-components); functions kept under 30 lines |
| II. Testing Standards | ✅ PASS (TDD required) | Vitest tests for `buildAccountTree`, form validation, and `useAccounts` mutations written BEFORE implementation; Playwright E2E covers create/edit/delete/filter flows |
| III. UX Consistency | ✅ PASS | Dialog tabs match GnuCash reference screenshots; filter dialog follows established 2-tab pattern; error messages include actionable resolution copy |
| IV. Performance | ✅ PASS | React Query caches `GET /accounts`; tree build is O(n); client-side filter is O(n) — instant for typical account counts; all operations async |
| V. Security | ✅ PASS | All form inputs validated client-side before submission; backend is authoritative; JWT Bearer token via Axios interceptor; token not logged |
| VI. State Management | ✅ PASS | Clear lifecycle: create → cache invalidation → refetch → render; React Query owns server state; Zustand owns ephemeral UI state; no cross-contamination |

> No constitution violations detected. Complexity tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-ui-makeover/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entity definitions
├── quickstart.md        # Dev setup guide
├── contracts/           # API contracts
│   └── accounts.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
frontend/src/
├── components/
│   ├── common/
│   │   ├── TabBar.tsx              ← existing
│   │   ├── Modal.tsx               ← NEW: focus-trapped accessible dialog wrapper
│   │   └── ColourSwatch.tsx        ← NEW: <input type="color"> + coloured swatch
│   └── ledger/
│       ├── AccountTree.tsx         ← UPDATE: add Description/LastReconcile/FutureMin/C/H/P columns
│       ├── AccountDialog.tsx       ← NEW: New/Edit 3-tab modal (General/More Properties/Opening Balance)
│       ├── DeleteConfirmDialog.tsx ← NEW: single-action confirmation modal for delete
│       ├── FilterDialog.tsx        ← NEW: Filter Accounts 2-tab modal
│       ├── LedgerToolbar.tsx       ← existing
│       └── Register.tsx            ← existing
├── features/
│   ├── ledger.tsx                  ← UPDATE: wire React Query, dialog open state, filter state
│   └── reconciliation.tsx          ← existing
├── hooks/
│   ├── useAccounts.ts              ← NEW: useQuery + useMutation wrappers for /accounts
│   ├── useAccountColours.ts        ← NEW: localStorage colour map CRUD
│   ├── useFilterState.ts           ← NEW: localStorage filter state CRUD
│   ├── useSplitPane.ts             ← existing
│   ├── useVirtualizedList.ts       ← existing (keep; unused by new table)
│   └── useReconciliationViewModel.ts ← existing
├── lib/
│   └── buildAccountTree.ts         ← NEW: flat AccountResponse[] → AccountNode tree
├── services/
│   └── accountsApi.ts              ← NEW: axios GET/POST/PUT/DELETE wrappers + JWT interceptor
├── stores/
│   ├── ledgerStore.ts              ← UPDATE: remove accountTree (now React Query); keep selectedAccountId, registerRows, tab list, dialog open flags
│   └── reconciliationStore.ts      ← existing
└── types.ts                        ← UPDATE: extend AccountNode; add AccountFormData, FilterState
```

**Structure Decision**: Frontend-only web application (`frontend/src/`). Server state lives in React Query (`useAccounts`); UI state (selected account, active tabs, dialog open flags, filter prefs) lives in Zustand (`ledgerStore`). New utilities (`buildAccountTree`, `accountsApi`) are kept in dedicated `lib/` and `services/` directories so they remain independently testable.

## Implementation Sequence

The work is ordered to keep the app runnable at every step:

1. **Install React Query** — add `@tanstack/react-query` to `package.json`; wrap app in `QueryClientProvider`.
2. **`accountsApi.ts`** — Axios wrappers for all four account endpoints; add JWT interceptor.
3. **`buildAccountTree.ts`** — pure utility + Vitest unit tests (TDD first).
4. **`useAccounts.ts`** — `useQuery` + three `useMutation` hooks + tests.
5. **`types.ts`** update — extend `AccountNode`; add `AccountFormData`, `FilterState`.
6. **`ledgerStore.ts`** update — remove `accountTree`; add dialog open flags; `LedgerFeature` now calls `useAccounts` directly.
7. **`LedgerFeature`** update — replace static sample data with real query; show loading/error states.
8. **`Modal.tsx`** — focus-trapped accessible dialog wrapper (used by all three dialogs).
9. **`AccountDialog.tsx`** + **`ColourSwatch.tsx`** + **`useAccountColours.ts`** — 3-tab New/Edit form wired to `useMutation`; inline validation.
10. **`DeleteConfirmDialog.tsx`** — single confirmation step; fires delete mutation.
11. **`AccountTree.tsx`** update — add Description, Last Reconcile Date, Future Minimum (`—`), C/H/P columns; wire `useAccountColours`.
12. **`useFilterState.ts`** + **`FilterDialog.tsx`** — 2-tab filter form wired to `useFilterState`; `localStorage` persistence.
13. **Toolbar wiring** — connect New/Edit/Delete/Filter buttons in `LedgerFeature`.
14. **E2E tests** — Playwright flows for create, edit, delete, filter.

> FR-009 (Account Hierarchy Setup Wizard) is a stretch goal and is explicitly excluded from this sequence. It will be specified as a separate feature.

## Complexity Tracking

> No constitution violations detected; complexity table not required.
