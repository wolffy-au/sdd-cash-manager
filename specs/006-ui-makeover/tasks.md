---

description: "Task list template for feature implementation"
---

# Tasks: UI Makeover

**Input**: Design documents from `/specs/006-ui-makeover/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Vitest (component/unit) and Playwright (flows) cover MVVM hooks and UI journeys. These run via `frontend/npm run test:ui`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the frontend workspace, tooling, and style system.

- [x] T001 Create `frontend/package.json` with React 18, Vite, Tailwind, Zustand/xState, Axios, Vitest, and Playwright dependencies
- [x] T002 Add `frontend/tailwind.config.js`, `frontend/postcss.config.js`, and global styles in `frontend/src/styles/layout.css` per the MVVM layout plan
- [x] T003 [P] Establish tooling scripts (`frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/tests/ui/playwright.config.ts`) and editor settings so linting/testing run consistently

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the MVVM glue, API wiring, and virtualization hooks required by every story.

- [x] T004 [P] Implement `frontend/src/stores/ledgerStore.ts` and `frontend/src/stores/reconciliationStore.ts` with the fields/commands defined in the data model (selectedAccountId, registerRows, statementBalance, unreconciled, difference, statusFlags)
- [x] T005 [P] Create `frontend/src/services/apiClient.ts` that wraps `/accounts`, `/reconciliation/sessions`, `/reconciliation/sessions/unreconciled`, and `/reconciliation/sessions/{session_id}/transactions` APIs and normalizes the Difference payload
- [x] T006 [P] Build helper abstractions (`frontend/src/hooks/useVirtualizedList.ts`, `frontend/src/hooks/useReconciliationViewModel.ts`) plus layout helpers (responsive panels in `layout.css`) to keep the MVVM stores decoupled from rendering details

**Checkpoint**: With stores, API wiring, and virtualization hooks in place, user stories can now be implemented independently.

---

## Phase 3: User Story 1 - Modern Ledger Workspace (Priority: P1) 🎯 MVP

**Goal**: Deliver a desktop-friendly ledger workspace with a GnuCash-inspired tree, register, and breadcrumb that expose MVVM commands without page reloads.

**Independent Test**: Load `frontend/src/features/ledger.tsx`, expand accounts, select register rows, and verify the tree highlights + register updates without reloading.

- [x] T007 [US1] Build `frontend/src/components/ledger/AccountTree.tsx` to render the hierarchical account tree, animate expansions, and call `ledgerStore.commands.expandAccount`
- [x] T008 [US1] Implement `frontend/src/components/ledger/Register.tsx` using `useVirtualizedList` to render register rows and invoke `ledgerStore.commands.selectRow`
- [x] T009 [US1] Create `frontend/src/features/ledger.tsx` that assembles the tree, register, and breadcrumb panels while binding focus order and keyboard navigation per FR-005
- [x] T010 [US1] Add `frontend/tests/ui/ledger.spec.ts` (Playwright/Vitest) to verify account expansion, row selection, and MVVM binding updates

**Checkpoint**: The ledger workspace stands alone with working tree/register interactions.

---

## Phase 4: User Story 2 - Reconciliation Kit (Priority: P2)

**Goal**: Enable statement balance input, fetching unreconciled transactions, and real-time Difference updates without modal reloads.

**Independent Test**: Trigger `frontend/src/features/reconciliation.tsx`, hit `/sessions/unreconciled`, select rows, and assert the Difference badge updates via the store.

- [x] T011 [US2] Build `frontend/src/components/reconciliation/SessionControls.tsx` with inputs/buttons wired to `reconciliationStore.commands.fetchSessions` and `fetchUnreconciled`
- [x] T012 [US2] Implement `frontend/src/components/reconciliation/UnreconciledList.tsx` that virtualizes the transactions list, renders status badges, and updates `reconciliationStore.selectedIds`
- [x] T013 [US2] Create `frontend/src/features/reconciliation.tsx` to layer session controls, the unreconciled list, and the Difference badge tied to `difference.amount` + `remaining_uncleared`
- [x] T014 [US2] Add `frontend/tests/ui/reconciliation.spec.ts` that mocks `/reconciliation/sessions/unreconciled`, manipulates checkboxes, and verifies the Difference guidance text updates

**Checkpoint**: Reconciliation panel functions independently with live difference updates.

---

## Phase 5: User Story 3 - Guided Discrepancy Insights (Priority: P3)

**Goal**: Surface contextual guidance when the Difference remains non-zero, including colors, icons, and filter links for UNCLEARED rows.

**Independent Test**: Simulate a non-zero difference, read the guidance panel, and confirm it displays amber/orange badges plus a filter action that toggles the store.

- [x] T015 [US3] Create `frontend/src/components/guidance/DiscrepancyInsight.tsx` to show difference_status messaging, icons, and an action that highlights UNCLEARED rows via `reconciliationStore.commands.applySelection`.
- [x] T016 [US3] Ensure `frontend/src/features/reconciliation.tsx` consumes `DiscrepancyInsight` so guidance text appears immediately when difference > 0 and the panel color shifts to alert the user.
- [x] T017 [US3] Write `frontend/tests/ui/insight.spec.ts` to assert the guidance panel reacts to `difference_status: under`, updates the remaining count, and offers a filter button that selects UNCLEARED rows

**Checkpoint**: Discrepancy insights deliver clear next steps whenever reconciliation is incomplete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, accessibility fixes, and test harness validation across stories.

- [x] T018 [P] Update `docs/ui-overview.md` (or new docs entry) with navigation flows, MVVM responsibilities, API contract references, and the new discrepancy guidance story so testers can trace the full workflow
- [x] T019 [P] Validate keyboard focus order and semantic roles through Playwright knobs and adjust `frontend/src/styles/layout.css` so badges and guidance buttons meet contrast/hover expectations
- [x] T020 [P] Run `frontend/npm run test:ui` and document the three passing suites (ledger, reconciliation, insight) inside `specs/006-ui-makeover/quickstart.md`
- [x] T021 Review Tailwind/TypeScript configs to ensure badges/status colors meet accessibility contrast requirements and describe the decisions in `specs/006-ui-makeover/research.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)**: Prepares tooling/configuration; no prior dependencies
- **Foundational (Phase 2)**: Depends on Setup completion and unlocks user stories
- **User Stories (Phases 3–5)**: Require Phase 2 completion; can progress in priority order (US1 → US2 → US3) or in parallel
- **Polish (Phase 6)**: Requires all user stories to be feature-complete

### User Story Dependencies
- **US1 (P1)**: Starts after Phase 2; no dependencies on other stories
- **US2 (P2)**: Starts after Phase 2; depends on API wiring and stores but not on US1
- **US3 (P3)**: Starts after Phase 2; depends on US2 for difference metadata but exposes independent guidance

### Within Each Story
- Component tests (Playwright/Vitest) run before implementation leftovers
- Virtualized components precede feature wiring
- Guidance logic hooks into existing stores before display

### Parallel Opportunities
1. Phase 1 tasks: T001–T003 can be assigned to different engineers (package setup, tooling, styles)
2. Foundational tasks: T004–T006 operate on distinct files (stores, services, hooks) and can proceed concurrently
3. Across stories: US1/US2/US3 feature implementations (T007–T017) can run in parallel once stores/services exist
4. Testing tasks (T010, T014, T017) are independent Playwright/Vitest suites and can run together

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Run Phase 1 + Phase 2 to prepare the MVVM/store/API layers
2. Complete Phase 3 (US1) with ledger tree/register + verification tests
3. Validate US1 functionality via `frontend/tests/ui/ledger.spec.ts`
4. Ship MVP before adding US2/US3

### Incremental Delivery
1. Foundation ready (Phases 1–2)
2. Deliver US1 → Demo + Test → Deploy
3. Deliver US2 → Test + Deploy
4. Deliver US3 → Test + Deploy

### Parallel Team Strategy
- Developer A: waveform ledger UI (US1)
- Developer B: reconciliation kit + Difference badge (US2)
- Developer C: discrepancy insights/filters (US3)
- QA: Playwright/Vitest suites per story

---

## Phase 7: React Query Foundation (Blocking Prerequisites for FR-008/010/011)

**Purpose**: Replace static sample data with live API data via React Query; build the tree utility and hook layer all remaining user stories depend on.

**⚠️ CRITICAL**: Phases 8–10 cannot begin until this phase is complete.

- [ ] T022 Install @tanstack/react-query v5 in `frontend/package.json` and wrap the root with `QueryClientProvider` in `frontend/src/main.tsx`
- [ ] T023 [P] Create `frontend/src/services/accountsApi.ts` — typed Axios wrappers for `GET /accounts/?include_hidden=true&include_placeholder=true`, `POST /accounts/`, `PUT /accounts/{id}`, `DELETE /accounts/{id}`; add request interceptor reading `localStorage['auth-token']` and attaching `Authorization: Bearer` header
- [ ] T024 [P] Write Vitest unit tests in `frontend/src/lib/buildAccountTree.test.ts` FIRST (TDD) — cover: flat list → tree assembly, category sort order (ASSET→LIABILITY→EQUITY→REVENUE→EXPENSE then name), leaf `type` from `banking_product_type`, placeholder `type` from `accounting_category`, missing parent gracefully ignored
- [ ] T025 Create `frontend/src/lib/buildAccountTree.ts` — pure O(n) utility mapping `AccountResponse[]` to `AccountNode[]` hierarchy; all T024 tests must pass
- [ ] T026 [P] Write Vitest unit tests in `frontend/src/hooks/useAccounts.test.ts` FIRST (TDD) — cover: `useQuery` returns `AccountNode[]`; `useCreateAccount` calls POST and invalidates `['accounts']` cache; `useUpdateAccount` calls PUT with only changed fields; `useDeleteAccount` calls DELETE and invalidates cache on success
- [ ] T027 Create `frontend/src/hooks/useAccounts.ts` — `useQuery(['accounts'])` wrapping `accountsApi.getAccounts()` + `buildAccountTree()`; `useCreateAccount` / `useUpdateAccount` / `useDeleteAccount` mutations each calling `invalidateQueries({ queryKey: ['accounts'] })` on success; all T026 tests must pass
- [ ] T028 [P] Update `frontend/src/types.ts` — extend `AccountNode` with `parentId`, `hidden`, `notes`, `currency`, `colour?`, `lastReconcileDate?`, `futureMinimum?`; add `AccountFormData` type (all dialog fields per `data-model.md`); add `FilterState` type (`accountTypes: Set<string>`, `showHidden`, `showZeroTotal`, `showUnused` booleans)
- [ ] T029 Update `frontend/src/stores/ledgerStore.ts` — remove `accountTree` field (now owned by React Query); add `accountDialogOpen: boolean`, `accountDialogMode: 'create' | 'edit'`, `filterDialogOpen: boolean`, `deleteDialogOpen: boolean`; retain `selectedAccountId`, `registerRows`, tab list, and other existing UI state
- [ ] T030 Update `frontend/src/features/ledger.tsx` — call `useAccounts()` instead of static `sampleAccounts`; render shimmer/skeleton rows when `isLoading`; render an error banner with retry when `isError`
- [ ] T031 Create `frontend/src/components/common/Modal.tsx` — focus-trapped accessible dialog wrapper; `role="dialog"`, `aria-modal="true"`; Tab/Shift+Tab cycling through focusable children via `useRef` + `keydown`; Escape calls `onClose`; accepts `title`, `children`, `footer`, `onClose` props; no external library

**Checkpoint**: App fetches live account data from `GET /accounts/`; tree renders real data; `Modal.tsx` ready for all dialogs.

---

## Phase 8: User Story 4 - New / Edit / Delete Account Dialog (Priority: P1) 🎯

**Goal**: Deliver FR-008 — a 3-tab modal for creating and editing accounts backed by POST/PUT `/accounts/`, with auto-refresh via React Query cache invalidation.

**Independent Test**: Click New → fill Account Name → OK → assert `POST /accounts/` called and new row appears in tree without page reload. Click Edit with account selected → assert all fields pre-filled. Click Delete → confirm → assert `DELETE /accounts/{id}` called and row removed.

- [ ] T032 [P] [US4] Create `frontend/src/hooks/useAccountColours.ts` — reads/writes `localStorage['account-colours']` as `Record<accountId, string>`; exports `getColour(id)`, `setColour(id, value)`, `resetColour(id)`
- [ ] T033 [P] [US4] Create `frontend/src/components/common/ColourSwatch.tsx` — renders `<input type="color">` alongside a coloured square preview using `useAccountColours`; includes a "Default" button calling `resetColour(accountId)`; zero external dependencies
- [ ] T034 [P] [US4] Write Vitest component tests in `frontend/src/components/ledger/AccountDialog.spec.tsx` FIRST (TDD) — cover: name required validation blocks submit; invalid currency code rejected; edit mode pre-fills name, code, notes from `AccountNode`; OK in create mode calls `useCreateAccount` with correct `AccountFormData` → API payload mapping; OK in edit mode calls `useUpdateAccount` with only changed fields; mutation error displayed inline
- [ ] T035 [US4] Create `frontend/src/components/ledger/AccountDialog.tsx` — 3-tab `Modal.tsx` dialog (General / More Properties / Opening Balance); General tab: name input (required, 1–100 chars, alphanumeric + `. , - _ ( ) & '`), code input (optional), description textarea, parent-account scrollable tree picker with expand/collapse, account type dropdown (AccountingCategory + BankingProductType per `data-model.md`), currency read-only field + Select button (AUD default), `ColourSwatch`, notes textarea, placeholder/hidden checkboxes; More Properties tab: `higherBalanceLimit` / `lowerBalanceLimit` number inputs; Opening Balance tab (create mode only): balance number input (≥0, 2 dp), date picker (today default), transfer radio group (equity account vs. select account); validate all fields before submit; call `useCreateAccount` or `useUpdateAccount`; display mutation errors inline; all T034 tests must pass
- [ ] T036 [US4] Create `frontend/src/components/ledger/DeleteConfirmDialog.tsx` — `Modal.tsx`-based single-step confirmation; shows "Delete account: {name}?" with the full account name; OK fires `useDeleteAccount(selectedAccountId)`; inline error if mutation fails; Cancel / Escape closes without action
- [ ] T037 [US4] Update `frontend/src/features/ledger.tsx` — wire New button to open `AccountDialog` in create mode; wire Edit button to open `AccountDialog` in edit mode passing selected `AccountNode` as initial data; wire Delete button to open `DeleteConfirmDialog`; read/write `accountDialogOpen`, `accountDialogMode`, `deleteDialogOpen` from `ledgerStore`; keep Edit and Delete toolbar buttons disabled when `selectedAccountId` is null or selected account is a placeholder

**Checkpoint**: Full create/edit/delete account CRUD workflow functional; tree auto-refreshes after each mutation without page reload.

---

## Phase 9: User Story 5 - Filter Accounts Dialog (Priority: P2)

**Goal**: Deliver FR-010 — a 2-tab client-side filter dialog with per-type checkboxes and other flags; filter state persisted to `localStorage` and applied reactively.

**Independent Test**: Click Filter → uncheck Expense type → Apply → assert Expense rows disappear from tree → reload page → assert filter still applied from `localStorage['account-filter']`.

- [ ] T038 [P] [US5] Create `frontend/src/hooks/useFilterState.ts` — reads `FilterState` from `localStorage['account-filter']` (JSON, with fallback to defaults); exports `filterState` and `setFilter(patch: Partial<FilterState>)`; defaults: all `AccountingCategory` types enabled, `showHidden=false`, `showZeroTotal=true`, `showUnused=true`
- [ ] T039 [US5] Create `frontend/src/components/ledger/FilterDialog.tsx` — 2-tab `Modal.tsx` dialog; Account Type tab: one checkbox per `AccountingCategory` mapped to display label (Asset / Liability / Equity / Income / Expense) plus Select All / Clear All / Default buttons; Other tab: Show hidden accounts / Show zero total accounts / Show unused accounts checkboxes; Apply writes to `useFilterState` and closes; Cancel discards in-progress changes
- [ ] T040 [US5] Update `frontend/src/features/ledger.tsx` — after `buildAccountTree()` result, apply `filterTree(nodes, filterState)` that: excludes `hidden=true` when `!showHidden`; excludes zero-balance accounts (no children with balance) when `!showZeroTotal`; excludes no-transaction accounts when `!showUnused`; excludes accounts whose `accounting_category` is not in `accountTypes`; always preserves placeholder parents whose children pass; wire Filter toolbar button to open `FilterDialog` (`filterDialogOpen` in `ledgerStore`); tree rerenders reactively on `filterState` change without page reload

**Checkpoint**: Account tree filters reactively; filter state survives page reload.

---

## Phase 10: User Story 6 - Richer Account Tree Columns (Priority: P3)

**Goal**: Deliver FR-011 — add Description, Last Reconcile Date, Future Minimum (—), and C/H/P indicator columns to the account tree table.

**Independent Test**: Account tree displays 6 new columns; Description shows `account.notes`; Future Minimum column always shows `—`; clicking a C cell opens the colour picker and the swatch updates immediately; H checkbox toggles hidden via `PUT /accounts/{id}`.

- [ ] T041 [US6] Update `frontend/src/components/ledger/AccountTree.tsx` — add Description column (renders `account.notes` or empty); add Last Reconcile Date column (renders `account.lastReconcileDate` as locale date string or `—` if undefined); add Future Minimum column (always renders `—`, stub for Scheduled Transactions API); add C column (`ColourSwatch` per row, reads/writes `localStorage['account-colours']` via `useAccountColours`); add H column (checkbox bound to `account.hidden`, `onChange` calls `useUpdateAccount({ hidden: !account.hidden })`); add P column (readonly checkbox displaying `account.placeholder`)

**Checkpoint**: All FR-011 columns visible and interactive; tree layout stable with 10 total columns; Future Minimum gracefully renders `—`.

---

## Phase 11: Polish & E2E Tests

**Purpose**: End-to-end verification of all new CRUD and filter functionality; update existing test files for React Query compatibility.

- [ ] T042 [P] Write Playwright E2E test in `frontend/tests/ui/accounts-crud.spec.ts` — create: click New, fill name/type, OK, assert new row in tree; edit: select row, click Edit, change name, OK, assert row updated in tree; delete: select row, click Delete, confirm, assert row removed; all mutations occur without page reload
- [ ] T043 [P] Write Playwright E2E test in `frontend/tests/ui/accounts-filter.spec.ts` — open Filter, uncheck one type, Apply, assert matching rows hidden; reopen Filter, click Default, Apply, assert all rows visible; reload page and assert filter persists from `localStorage`
- [ ] T044 [P] Update `frontend/src/App.spec.tsx` and `frontend/src/features/ledger.spec.tsx` — wrap renders in `QueryClientProvider`; mock `accountsApi` with `vi.mock` to prevent real HTTP calls in unit tests

---

## Dependencies & Execution Order (Phases 7–11)

### Phase Dependencies
- **Phase 7 (Foundation)**: Must complete before Phases 8–10; T022 must complete before T023–T031 can begin
- **Phase 8 (US4)**: Depends on Phase 7; T031 (Modal.tsx) must exist before T035 and T039
- **Phase 9 (US5)**: Depends on Phase 7 + T031 (Modal.tsx); independent of Phase 8
- **Phase 10 (US6)**: Depends on Phase 7 + T032 (useAccountColours) + T033 (ColourSwatch); independent of Phases 8–9
- **Phase 11 (E2E)**: Depends on Phases 8–10 being feature-complete

### User Story Dependencies
- **US4 (P1)**: Starts after Phase 7; no dependency on US5 or US6
- **US5 (P2)**: Starts after Phase 7; no dependency on US4 or US6
- **US6 (P3)**: Starts after Phase 7 + T032/T033; no dependency on US4 or US5

### Parallel Opportunities (Phases 7–11)
1. After T022 completes: T023, T024, T026, T028 target different files — run in parallel
2. T025 (implementation) follows T024 (tests); T027 (implementation) follows T026 (tests)
3. After T031 (Modal.tsx) completes: T032, T033, T034, T038 are all parallel
4. T042, T043, T044 are independent suites — run in parallel in Phase 11

---

## Parallel Example: Phase 8 (US4)

```bash
# After Phase 7 completes, launch in parallel:
Task: "Create useAccountColours.ts — T032"
Task: "Create ColourSwatch.tsx — T033"
Task: "Write AccountDialog.spec.tsx (TDD) — T034"

# Then sequentially:
Task: "Create AccountDialog.tsx (make T034 pass) — T035"
Task: "Create DeleteConfirmDialog.tsx — T036"
Task: "Wire dialogs into features/ledger.tsx — T037"
```

---

## Implementation Strategy (Phases 7–11)

### MVP First (React Query + Account CRUD)
1. Complete Phase 7 — app shows live API data
2. Complete Phase 8 (US4) — full create/edit/delete CRUD
3. **STOP and VALIDATE**: Confirm CRUD round-trips with real backend before continuing
4. Add Phase 9 (US5 filter) and Phase 10 (US6 richer columns) incrementally

### Incremental Delivery
1. Phase 7 complete → live data from `GET /accounts/`
2. Phase 8 complete → full CRUD → demo to stakeholders
3. Phase 9 complete → filter → improved account navigation
4. Phase 10 complete → richer columns → matches GnuCash reference screenshots
5. Phase 11 complete → E2E coverage → production-ready

### Parallel Team Strategy (Phases 8–10)
- Developer A: US4 — AccountDialog + DeleteConfirmDialog (T032–T037)
- Developer B: US5 — FilterDialog + filter logic (T038–T040)
- Developer C: US6 — richer AccountTree columns (T041)
- QA: E2E suites after each story (T042–T044)

---
