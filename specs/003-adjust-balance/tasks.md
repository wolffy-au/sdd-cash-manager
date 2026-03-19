# Tasks: Adjust Balance Window

**Branch**: `003-adjust-balance` | **Date**: 2026-03-16 | **Spec**: `/workspaces/sdd-cash-manager/specs/003-adjust-balance/spec.md`

## Summary

This document outlines the actionable tasks required to implement the 'Adjust Balance Window' feature. Tasks are organized by user story priority and include setup, foundational components, and user-specific implementations.

## Implementation Strategy

*   **MVP First**: Focus on User Story 1 (P1) as the minimum viable product, followed by P2 and P3.
*   **Incremental Delivery**: Each user story phase should deliver a complete, independently testable increment.
*   **Parallelization**: Tasks marked with `[P]` can be executed in parallel if resources allow and dependencies are met.

---

## Phase 1: Setup

These tasks cover initial project setup and environment configuration.

- [x] T001 Create project structure per implementation plan (`src/api`, `src/models`, `src/services`, `tests/unit`, `tests/integration`).
- [x] T002 Set up Python 3.11 environment and install dependencies: FastAPI, SQLAlchemy, Pydantic, python-accounting, pytest, Alembic.
- [x] T003 Configure database connection for SQLite, with a strategy for PostgreSQL extensibility (refer to `research.md`).
- [x] T004 Initialize Alembic for database migrations.
- [x] T005 Set up basic FastAPI application structure (`main.py`, `api/`, `models/`, `services/`).

---

## Phase 3: User Story 1 - Manual Balance Reconciliation (P1)

**Goal**: As a reconciler, I need a manual balance adjustment window so I can align an account's total balance with the most recent statement before closing the period.

**Independent Test Criteria**: Trigger the adjustment flow for an account and verify the user can set a target balance, pick an effective date, and submit without any other workflows running.

- [x] T010 [P] [US1] Implement `ManualBalanceAdjustment` SQLAlchemy model in `src/sdd_cash_manager/models/adjustment.py`.
- [x] T011 [P] [US1] Implement `ManualBalanceAdjustment` Pydantic schema for request/response in `src/sdd_cash_manager/schemas/adjustment.py`.
- [x] T012 [P] [US1] Implement `ManualBalanceAdjustmentService` in `src/sdd_cash_manager/services/adjustment_service.py` to handle creation, validation (target balance >= 0), and persistence.
- [x] T013 [P] [US1] Implement FastAPI endpoint for manual balance adjustment (e.g., POST /accounts/{account_id}/adjust-balance) in `src/sdd_cash_manager/api/v1/endpoints/adjustment.py`.
- [x] T014 [P] [US1] Add validation for `effective_date` (past/present/future) and surface warnings if outside the current statement range (non-blocking toast notification) in API endpoint or service layer.
- [x] T015 [P] [US1] Write unit tests for `ManualBalanceAdjustmentService` and Pydantic schemas.
- [x] T016 [P] [US1] Write integration tests for the manual balance adjustment API endpoint.

---

## Phase 4: User Story 2 - Automated Transaction Creation (P2)

**Goal**: As an operator, I want the system to create the balancing transaction automatically so I do not need to manually insert ledger entries after every adjustment.

**Independent Test Criteria**: Submit a target balance that differs from the current running balance and verify the system logs a new transaction dated per the window, showing the debit/credit needed to reach the target.

- [x] T017 [P] [US2] Update `ManualBalanceAdjustment` model/service to trigger transaction creation upon successful adjustment.
- [x] T018 [P] [US2] Implement `AdjustmentTransaction` SQLAlchemy model in `src/sdd_cash_manager/models/adjustment.py`.
- [x] T019 [P] [US2] Implement `AdjustmentTransaction` Pydantic schema in `src/sdd_cash_manager/schemas/adjustment.py`.
- [x] T020 [P] [US2] Update `AdjustmentService` (or related service) to create `AdjustmentTransaction` based on calculated difference and effective date.
- [x] T021 [P] [US2] Implement logic to update `ManualBalanceAdjustment.created_transaction_id` and `ManualBalanceAdjustment.status` upon successful transaction creation.
- [x] T022 [P] [US2] Update `banking product enum` to include 'ADJUSTMENT_DEBIT' and 'ADJUSTMENT_CREDIT' as per spec clarification.
- [x] T023 [P] [US2] Write unit tests for `AdjustmentTransaction` model and creation logic.
- [x] T024 [P] [US2] Write integration tests for the automated transaction creation flow.
- [x] T036 [P] [US2] Ensure `ManualBalanceAdjustmentService` determines the current running balance as of the submitted `effective_date` (using account history/ledger snapshots) rather than relying on a mutable `account.running_balance`.
- [x] T037 [P] [US2] Route adjustment posting through `TransactionService`/ledger entries to persist true debit/credit rows, update balances, and link the resulting `AdjustmentTransaction` to the `ManualBalanceAdjustment`.
- [x] T038 [P] [US3] After the adjustment transaction posts, invoke `ReconciliationService.create_reconciliation_entry_from_transaction` so `ReconciliationViewEntry` immediately reflects the change for `/accounts/{account_id}/reconciliation`.
- [x] T039 [P] [US1/US2] Replace the placeholder permission stub in `src/sdd_cash_manager/api/v1/endpoints/adjustment.py` with JWT/`require_role` enforcement, disable the control for unauthorized roles, and log each adjustment attempt for auditing.

---

## Phase 5: User Story 3 - Ledger and Reconciliation Visibility (P3)

**Goal**: As an auditor, I need this adjustment transaction to be visible in reconciliation views so I can trace the lineage of balance edits.

**Independent Test Criteria**: After performing an adjustment, open the reconciliation panel for the account and confirm the adjustment appears with the chosen effective date and status.

- [x] T025 [P] [US3] Implement `ReconciliationViewEntry` model/schema (or adapt existing reconciliation views) in `src/sdd_cash_manager/models/reconciliation.py` and `src/sdd_cash_manager/schemas/reconciliation.py`.
- [x] T026 [P] [US3] Develop logic to populate `ReconciliationViewEntry` with data from `AdjustmentTransaction`, ensuring `is_adjustment` flag and `reconciled_status` are correctly set.
- [x] T027 [P] [US3] Implement API endpoint to fetch reconciliation view data (e.g., GET /accounts/{account_id}/reconciliation).
- [x] T028 [P] [US3] Write unit tests for reconciliation view population logic.
- [x] T029 [P] [US3] Write integration tests for fetching reconciliation data including adjustment entries.

---

## Phase 6: Polish & Cross-Cutting Concerns

These tasks address broader quality attributes and final checks.

 - [x] T030 [P] Implement permissioning logic: disable adjustment control for users without rights, log audit entry. (Edge Case handling)
 - [x] T031 [P] Refine performance of balance calculation and transaction creation if benchmarks exceed targets (refer to `research.md` for goals).
 - [x] T032 [P] Implement comprehensive logging and tracing for adjustment and transaction creation flows.
 - [x] T033 [P] Add detailed documentation (docstrings, README updates) for new modules and endpoints.
 - [x] T034 [P] Conduct a final review against `GEMINI.md` (Constitution) and `TECHNICAL.md` (Coding Standards).
 - [x] T035 [P] Prepare for database migration strategy from SQLite to PostgreSQL (refer to `research.md`).
- [x] T040 [P] Add unit/integration tests that cover: effective-date based difference calculation, ledger transaction creation, reconciliation entry persistence, zero-difference audit records, and permission enforcement for adjustments.
- [x] T041 [P] Ensure reconciliation API tests validate that the newly created reconciliation entries appear with the adjustment metadata (date, amount, `is_adjustment`, reconciled flag).
- [x] T042 [P] Add tests that simulate unauthorized users attempting to adjust a balance so the disabled control and 403 behavior are validated alongside audit logging.

---

## Phase 7: Alignment Tasks

These tasks capture the remaining alignment work that surfaced during the reconciliation between the specification and the current code base.

- [x] T050 Fix `tests/integration/test_adjustment_api.py` to import `datetime`, `Session`, and `MagicMock`, ensuring the manual adjustment API tests run without `NameError` before executing their service mocks. (`tests/integration/test_adjustment_api.py`)
- [x] T051 Fix `tests/integration/test_reconciliation_api.py` to import `Session` and `MagicMock` so the reconciliation view tests can construct mock DB sessions without failing at import time. (`tests/integration/test_reconciliation_api.py`)

## Phase 8: Documentation & QA Alignment

With the feature code stabilized, these deliverables ensure the supporting artifacts (plan, research, quickstart, and test reporting) describe the implementation and verification status accurately.

- [x] T060 Update `plan.md` to capture the Python 3.12 stack, SQLite/PostgreSQL migration strategy, exact dependencies, performance targets, and scale assumptions for the adjustment feature.
- [x] T061 Replace the previous research TODOs with a decision log that covers the chosen storage strategy, performance goals, security/audit constraints, scale assumptions, and the FastAPI+SQLAlchemy+python-accounting integration pattern.
- [x] T062 Publish `quickstart.md` that shows how to spin up the API, call `/accounts/{account_id}/adjust-balance`, and run the relevant integration/unit suites.
- [x] T063 Document the targeted regression tests that prove the manual adjustment, zero-difference audit trail, reconciliation entry persistence, and RBAC protections (`uv run pytest tests/integration/test_adjustment_api.py tests/integration/test_reconciliation_api.py tests/integration/test_adjustment_reconciliation_flow.py tests/unit/test_reconciliation.py tests/unit/test_auth_events.py` and any additional suites).

## Dependencies

The user stories must be completed in the following order:
1.  US1
2.  US2
3.  US3

Setup and Foundational tasks must be completed before any user story tasks.

## Parallel Execution Opportunities

Tasks marked with `[P]` within the same phase are candidates for parallel execution, provided their specific file path dependencies are met and they do not block other critical path items.

## Implementation Strategy

*   **MVP Scope**: User Story 1 (Manual Balance Reconciliation) forms the MVP.
*   **Incremental Delivery**: Subsequent stories (US2, US3) build upon the MVP.
*   **Cross-Cutting Concerns**: Polish and auditability tasks (Phase 6) should be addressed iteratively but finalized before release.
