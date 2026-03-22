---
description: "Task list for implementing the Reconcile Window feature"
---

# Tasks: Reconcile Window

**Input**: Design documents from `/specs/005-add-reconcile-window/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the repo with the documented stack before touching feature code.

- [x] T001 Create `.python-version` pinned to `3.12` so contributors can install the same interpreter (root).
- [x] T002 [P] Add `pytest-httpx>=0.24.0,<1.0.0` to the `[tool.poetry.dependencies.tests]` group in `pyproject.toml` to support httpx-based integration scenarios (pyproject.toml).
- [x] T003 [P] Extend `tests/api/README.md` with a reconciliation quickstart step that lists the new `pytest tests/api/test_transactions.py::test_reconcile_window_flow -v` command and the required JWT env vars (tests/api/README.md).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the data and service foundation that every user story relies on.

- [ ] T004 Create `src/sdd_cash_manager/models/reconciliation_session.py` to persist statement metadata, ending balance, difference, and lifecycle state for each reconciliation attempt (models directory).
- [ ] T005 Export `ReconciliationSession` and the new `BankStatementSnapshot` models from `src/sdd_cash_manager/models/__init__.py` so other modules can import them consistently (models/__init__.py).
- [ ] T006 Extend `src/sdd_cash_manager/models/enums.py` with `ProcessingStatus.COMPLETED`, `ReconciliationStatus.UNCLEARED`, `ReconciliationStatus.CLEARED`, and helper functions so the service layer can filter status values matching the feature spec (models/enums.py).
- [ ] T007 Add `src/sdd_cash_manager/models/bank_statement_snapshot.py` with fields for `closing_date`, `closing_balance`, `statement_id`, and `transaction_cutoff` to capture the horizon of each statement window (models directory).
- [ ] T008 Expand `src/sdd_cash_manager/services/reconciliation_service.py` with helper methods that query `Transaction` rows filtered by the new statuses, persist `ReconciliationSession` records, and recalculate the Difference as selections are applied (services/reconciliation_service.py).

---

## Phase 3: User Story 1 - Match statement balance (Priority: P1) 🎯 MVP

**Goal**: Let the user enter a statement ending balance, route selected transactions through the Reconcile Window, and drive the Difference field to zero while persisting status transitions.

**Independent Test**: Enter a known ending balance via `POST /reconciliation/sessions`, select the transactions shown by the unreconciled endpoint, and verify that the Difference response reaches $0.00 and each transaction flips to `CLEARED`/`RECONCILED` without touching FAILED rows.

### Implementation Tasks
- [ ] T009 [US1] Create `src/sdd_cash_manager/schemas/reconciliation_schema.py` with Pydantic models for the session creation request/response, the transaction selection payload, and the difference response documented in `contracts/reconcile.yaml` (schemas/reconciliation_schema.py).
- [ ] T010 [US1] Enhance `ReconciliationService` in `src/sdd_cash_manager/services/reconciliation_service.py` with `create_session`, `apply_selected_transactions`, and difference-calculation helpers that persist `ReconciliationSession` records and update transaction statuses from `UNCLEARED` → `CLEARED`/`RECONCILED` (services/reconciliation_service.py).
- [ ] T011 [US1] Implement the `POST /reconciliation/sessions` route in `src/sdd_cash_manager/api/reconciliation.py`, wiring the request schema to the service, enforcing JWT auth, and returning the initial Difference payload (api/reconciliation.py).
- [ ] T012 [US1] Implement the `POST /reconciliation/sessions/{session_id}/transactions` route in `src/sdd_cash_manager/api/reconciliation.py` so selected transaction IDs update reconciliation_status, recalc the Difference, and persist the new state (api/reconciliation.py).
- [ ] T013 [US1] Append a focused scenario to `tests/api/test_transactions.py` that posts an ending balance, selects matching UNCLEARED transactions, and asserts the service returns `difference == 0` and statuses `CLEARED`/`RECONCILED` without touching FAILED records (tests/api/test_transactions.py).

### Parallel execution example (US1)
- Run the schema file creation (T009) in parallel with the service wiring (T010) because they touch different modules and the schema just defines DTOs used by the new routes.
- While the API routes (T011/T012) wait for service helpers, the integration test (T013) can be drafted independently since it only calls the contracts described in `contracts/reconcile.yaml`.

---

## Phase 4: User Story 2 - Surface the correct transaction set (Priority: P2)

**Goal**: Return only UNCLEARED/CLEARED transactions created since the prior statement and exclude FAILED rows so the Difference calculation works from a clean data set.

**Independent Test**: Fetch `GET /reconciliation/sessions/unreconciled` after a statement cutoff, then assert the payload contains only UNCLEARED or CLEARED transactions whose processing_status is `PENDING` or `COMPLETED`, and it omits any FAILED rows or already RECONCILED entries.

### Implementation Tasks
- [ ] T014 [US2] Extend `schemas/reconciliation_schema.py` with the `TransactionSummary` schema used by `/sessions/unreconciled`, including status fields defined in the contract (schemas/reconciliation_schema.py).
- [ ] T015 [US2] Add `get_unreconciled_transactions` to `ReconciliationService` so it filters by the configured statement cutoff, ignores FAILED processing_status values, and returns the DTOs shown in the contract (services/reconciliation_service.py).
- [ ] T016 [US2] Implement the `GET /reconciliation/sessions/unreconciled` endpoint in `src/sdd_cash_manager/api/reconciliation.py`, injecting the facility to load the latest `BankStatementSnapshot` or the most recent session to determine the cutoff (api/reconciliation.py).
- [ ] T017 [US2] Add a test case in `tests/api/test_transactions.py` that creates CLEARED/UNCLEARED transactions before and after a cutoff, calls `/sessions/unreconciled`, and asserts only the allowed statuses and time windows appear (tests/api/test_transactions.py).

### Parallel execution example (US2)
- Schema updates (T014) and the service filter (T015) can advance in parallel because one defines the DTO while the other defines how rows map to it.
- Endpoint wiring (T016) can proceed once service helpers exist, while the new test (T017) can be authored concurrently to validate both the service and the API contract.

---

## Phase 5: User Story 3 - Surface discrepancy insights (Priority: P3)

**Goal**: Highlight when the Difference remains non-zero, display remaining UNCLEARED counts, and surface actionable messaging so supervisors understand outstanding reconciliation work.

**Independent Test**: Call `POST /reconciliation/sessions/{session_id}/transactions` with a subset of matching IDs so the Difference stays non-zero, then verify the response includes `difference_status`, `remaining_uncleared`, and a guidance message describing the next steps.

### Implementation Tasks
- [ ] T018 [US3] Add the extended `DifferenceResponse` schema fields (`difference_status`, `remaining_uncleared`, `guidance`) to `schemas/reconciliation_schema.py` per the contract (schemas/reconciliation_schema.py).
- [ ] T019 [US3] Update `ReconciliationService.apply_selected_transactions` so it calculates the difference sign, computes the count of remaining UNCLEARED transactions, and returns the guidance metadata used by the response (services/reconciliation_service.py).
- [ ] T020 [US3] Modify the `POST /reconciliation/sessions/{session_id}/transactions` route to include the enriched difference response declared in the contract and to surface the guidance text when the difference is not zero (api/reconciliation.py).
- [ ] T021 [US3] Add an integration test in `tests/api/test_transactions.py` that leaves a non-zero difference and asserts the response contains `difference_status != balanced`, a positive `remaining_uncleared`, and the textual guidance (tests/api/test_transactions.py).

### Parallel execution example (US3)
- Schema evolution (T018) and service logic (T019) can progress side-by-side because they touch different files but converge on the same response shape.
- The endpoint update (T020) and supporting integration test (T021) can be developed together once the service returns the enriched payload.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tie documentation, verification, and walkthrough steps together after all stories land.

- [ ] T022 [P] Refresh `specs/005-add-reconcile-window/quickstart.md` to reference the new reconciliation endpoints, the targeted `test_transactions` task, and the difference insight messaging so contributors have a single onboarding reference (specs/005-add-reconcile-window/quickstart.md).
- [ ] T023 Run `scripts/run_api_tests.sh` to exercise the new reconciliation endpoints and capture the result in project logs (scripts/run_api_tests.sh).

---

## Dependencies & Execution Order

### Phase Dependencies
- Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3/4/5 (User Stories) → Phase 6 (Polish).

### User Story Dependencies
- US1 (P1, Match statement balance) has no upstream story dependencies once the foundation is ready.
- US2 (P2, Surface correct transaction set) depends on the foundational infrastructure but can run in parallel with US1 once T004–T008 complete.
- US3 (P3, Surface discrepancy insights) depends on US1’s session lifecycle but can execute concurrently afterward because it reuses the same routes with richer responses.

### Story Completion Graph
```
US1   US2   US3
 |     |     |
 └─────┴─────┘  (all depend on Phase 2 and share the foundational service)
```

### Parallel Opportunities
- Setup tasks T002/T003 can be executed in parallel since they touch different docs (pyproject and README).
- Service/schema work for each story can proceed in parallel when they touch distinct modules, as highlighted under each story’s parallel example.
- User stories themselves (US1, US2, US3) can run in parallel after Phase 2 completes because they implement different endpoints and validation flows.

## Implementation Strategy

### MVP First (Story 1 Only)
1. Complete Phase 1 & 2 to pin the environment, models, and service helpers (T001–T008).
2. Deliver Story 1 (T009–T013), then validate via the new tests before merging.
3. Accept the feature as an MVP once Story 1 passes regression and captures the zero-difference workflow.

### Incremental Delivery
1. After MVP, add Story 2 (T014–T017) to expose the filtered transaction list and confirm the API contract.
2. Follow with Story 3 (T018–T021) to enrich the difference response and provide discrepancy guidance.
3. After each story, run the dedicated integration tests and the polish phase (T022–T023) to keep docs and validation scripts in sync.

### Parallel Team Strategy
1. Developers A/B can split Schema/Service work per story while Developer C drafts matching integration tests and documentation updates.
2. Once foundational models (T004–T007) exist, the API/router wires in earnest while tests are authored independently.
