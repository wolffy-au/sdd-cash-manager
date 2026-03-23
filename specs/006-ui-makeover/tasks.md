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

- [ ] T011 [US2] Build `frontend/src/components/reconciliation/SessionControls.tsx` with inputs/buttons wired to `reconciliationStore.commands.fetchSessions` and `fetchUnreconciled`
- [ ] T012 [US2] Implement `frontend/src/components/reconciliation/UnreconciledList.tsx` that virtualizes the transactions list, renders status badges, and updates `reconciliationStore.selectedIds`
- [ ] T013 [US2] Create `frontend/src/features/reconciliation.tsx` to layer session controls, the unreconciled list, and the Difference badge tied to `difference.amount` + `remaining_uncleared`
- [ ] T014 [US2] Add `frontend/tests/ui/reconciliation.spec.ts` that mocks `/reconciliation/sessions/unreconciled`, manipulates checkboxes, and verifies the Difference guidance text updates

**Checkpoint**: Reconciliation panel functions independently with live difference updates.

---

## Phase 5: User Story 3 - Guided Discrepancy Insights (Priority: P3)

**Goal**: Surface contextual guidance when the Difference remains non-zero, including colors, icons, and filter links for UNCLEARED rows.

**Independent Test**: Simulate a non-zero difference, read the guidance panel, and confirm it displays amber/orange badges plus a filter action that toggles the store.

- [ ] T015 [US3] Create `frontend/src/components/guidance/DiscrepancyInsight.tsx` to show difference_status messaging, icons, and a link that filters UNCLEARED rows via `reconciliationStore.commands.applySelection`
- [ ] T016 [US3] Ensure `frontend/src/features/reconciliation.tsx` consumes `DiscrepancyInsight` so guidance text appears immediately when difference > 0 and the badge color shifts
- [ ] T017 [US3] Write `frontend/tests/ui/insight.spec.ts` to assert the guidance panel reacts to `difference_status: under`/`over`, displays instructions, and offers the filter link

**Checkpoint**: Discrepancy insights deliver clear next steps whenever reconciliation is incomplete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, accessibility fixes, and test harness validation across stories.

- [ ] T018 [P] Update `docs/ui-overview.md` (or new docs/ entry) with navigation flows, MVVM responsibilities, and API contract references
- [ ] T019 [P] Confirm keyboard focus order/semitic roles via storybook/playwright helpers (adjust `layout.css` or component props as needed)
- [ ] T020 [P] Run `frontend/npm run test:ui` and document results in `specs/006-ui-makeover/quickstart.md`
- [ ] T021 Review Tailwind/Tsgen configs to ensure badges/status colors meet accessibility contrast requirements and log any adjustments in `specs/006-ui-makeover/research.md`

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
