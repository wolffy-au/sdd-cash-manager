# Tasks: API Pytest Coverage with httpx

**Input**: Design documents from `/specs/002-add-api-pytests/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the dedicated API test surface so pytest/httpx exercises the real service.

- [x] T001 Create `tests/api/` package with `__init__.py` and placeholder for pytest modules
- [x] T002 Add `tests/api/conftest.py` that configures an `httpx.AsyncClient` pointing at `http://127.0.0.1:8000` and reads `SDD_CASH_MANAGER_SECURITY_ENABLED`, `SDD_CASH_MANAGER_JWT_SECRET`, and `SDD_CASH_MANAGER_JWT_ALGORITHM`
- [x] T003 Document the pytest execution steps described in `specs/002-add-api-pytests/quickstart.md` within `tests/api/README.md` so contributors know how to run the suite

---

-## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Provide deterministic fixtures, JWT helpers, and cleanup logic required before any user story tests start.

- [x] T004 Create `tests/api/fixtures.py` that seeds visible, hidden, placeholder accounts plus the balancing account (`BALANCING_ACCOUNT_ID`) and exposes teardown hooks
- [x] T005 Implement `tests/api/jwt_utils.py` to issue short-lived tokens matching the app’s authentication settings for use within each test
- [x] T006 Add `tests/api/helpers.py` with utilities to assert HTTP status/payload combinations and to reset the SQLite test database after each scenario

**Checkpoint**: Deterministic state and auth helpers are available for every user story so tests remain isolated.

---

## Phase 3: User Story 1 - Verify core account flows (Priority: P1)

**Goal**: Validate account creation, retrieval, and filtering behavior via pytest/httpx so regressions in fundamental account flows are caught early.  
**Independent Test**: Run `pytest tests/api/test_accounts.py::test_create_and_get_account` followed by `pytest tests/api/test_accounts.py::test_list_accounts_filters` against a running API; both should pass independently.

### Tests for User Story 1

- [x] T007 [P] [US1] Add creation test in `tests/api/test_accounts.py` that posts `/accounts` with valid payload and asserts `201 Created`, returned fields, and later GET `/accounts/{id}`
- [x] T008 [P] [US1] Add listing/filter test in `tests/api/test_accounts.py` that fetches `/accounts` with `search_term`, `include_hidden`, `include_placeholder` and validates response filtering

### Implementation for User Story 1

- [x] T009 [US1] Ensure `tests/api/conftest.py` exposes fixtures to provide seeded accounts used by the creation/list tests
- [x] T010 [US1] Validate response assertions (status + required payload keys) using helpers from `tests/api/helpers.py`

**Checkpoint**: Story 1 demonstrates account creation/listing flow and is independently runnable.

---

## Phase 4: User Story 2 - Verify transactional summaries and hierarchies (Priority: P2)

**Goal**: Confirm that posting balance adjustments updates hierarchy balances and that responses remain consistent.  
**Independent Test**: Run `pytest tests/api/test_transactions.py::test_post_adjustment_updates_balances` and `pytest tests/api/test_transactions.py::test_balance_endpoint_reflects_adjustments` independently after foundational fixtures.

### Tests for User Story 2

- [x] T011 [P] [US2] Add balance adjustment test in `tests/api/test_transactions.py` that POSTs `/accounts/{id}/adjustment` and asserts `status == COMPLETED` plus transaction entries
- [x] T012 [P] [US2] Add POST-adjustment follow-up test in `tests/api/test_transactions.py` that GETs `/accounts/{id}/balance` for both accounts and compares totals before/after

### Implementation for User Story 2

- [x] T013 [US2] Use fixtures from `tests/api/fixtures.py` to prepare accounts with predictable balances and pass their IDs to the transaction tests
- [x] T014 [US2] Assert both HTTP contract expectations (status/payload shape) and business rules (balancing account adjustments) using `tests/api/helpers.py`

**Checkpoint**: Transaction and hierarchy tests run independently ensuring double-entry invariants stay intact.

---

## Phase 5: User Story 3 - Detect invalid payload handling (Priority: P3)

**Goal**: Exercise validation and authentication failure paths so clients see consistent error messages.  
**Independent Test**: Run `pytest tests/api/test_validation.py::test_missing_fields_returns_422` and `pytest tests/api/test_validation.py::test_unauthorized_request_returns_401` separately.

### Tests for User Story 3

- [x] T015 [P] [US3] Add invalid payload test in `tests/api/test_validation.py` posting incomplete `/accounts` bodies and asserting `422 Unprocessable Entity` plus documented error detail arrays
- [x] T016 [P] [US3] Add authentication test in `tests/api/test_validation.py` that omits or mangles the JWT and confirms a `401 Not authenticated` response

### Implementation for User Story 3

- [x] T017 [US3] Leverage `tests/api/jwt_utils.py` to craft both valid and invalid tokens for the validation tests
- [x] T018 [US3] Ensure error expectations cover both HTTP status and schema detail fields via `tests/api/helpers.py`

**Checkpoint**: Validation story makes sure malformed data and auth failures are traceable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Document usage, clean up, and ensure the suite integrates with the CI flow.

- [x] T019 [P] Update `README.md` or `docs/api-tests.md` with the quickstart steps from `specs/002-add-api-pytests/quickstart.md`
- [x] T020 [P] Add CI job or script entry (e.g., `scripts/run_api_tests.sh`) that runs `pytest tests/api` and enforces timeout/logging behavior
- [x] T021 [P] Run `pytest tests/api` locally, capture logs, and commit any necessary fixture tweaks for flakiness based on real output
- [ ] T022 [P] Tag tests/API tasks in AGENTS.md or other tooling so tooling knows the new suite exists

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: No dependencies; establishes directory and doc structure.
- **Foundational (Phase 2)**: Depends on Setup; must finish before any user story tasks start.
- **User Stories (Phase 3+)**: Each story depends on Foundational completion but not on each other; they can run in parallel once base fixtures exist.
- **Polish (Phase 6)**: Depends on all user stories to be implemented for accurate documentation and CI hooks.

### Story Dependencies

- **User Story 1 (P1)**: Core flows and MVP; start immediately after Phase 2.
- **User Story 2 (P2)**: Hierarchy/transaction tests; can run concurrently with US1 once fixtures ready.
- **User Story 3 (P3)**: Validation flows; independent once fixtures exist.

## Parallel Execution Examples

### User Story 1

- Model & fixture updates (`tests/api/fixtures.py`) can land in parallel with contract assertions (`tests/api/tests_accounts.py`) because they touch different files.
- Spawn `pytest tests/api/test_accounts.py::test_create_and_get_account` and `pytest tests/api/test_accounts.py::test_list_accounts_filters` simultaneously: they share fixtures but can run concurrently due to cleanup hooks.

### User Story 2

- Balance adjustment POST and balance GET tests can execute together (`tests/api/test_transactions.py` tasks) since they operate on different endpoints and only read shared fixtures.

### User Story 3

- Invalid payload and unauthorized response tests run in `tests/api/test_validation.py` and can execute in parallel once JWT helper gets updated.

## Implementation Strategy

### MVP First (User Story 1)

1. Finish Phase 1 + Phase 2 so infrastructure, fixtures, and JWT helpers exist.
2. Complete Phase 3 (US1) tests for account creation/listing plus helpers to make them reliable.
3. Validate the suite runs via `pytest tests/api/test_accounts.py` before expanding to US2 or US3.

### Incremental Delivery

1. Add US2 after US1 is stable, focusing on transaction adjustments and hierarchy checks.
2. Introduce US3 once core business flows are secured, covering validation and auth errors.
3. Each story adds independent coverage without regressing earlier tests.

### Parallel Team Strategy

- Developer A: Hooks (setup/conftest)  
- Developer B: Story 1 tests  
- Developer C: Story 2/3 tests  
