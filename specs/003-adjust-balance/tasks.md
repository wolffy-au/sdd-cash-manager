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

- [ ] T001 Create project structure per implementation plan (`src/api`, `src/models`, `src/services`, `tests/unit`, `tests/integration`).
- [ ] T002 Set up Python 3.11 environment and install dependencies: FastAPI, SQLAlchemy, Pydantic, python-accounting, pytest, Alembic.
- [ ] T003 Configure database connection for SQLite, with a strategy for PostgreSQL extensibility (refer to `research.md`).
- [ ] T004 Initialize Alembic for database migrations.
- [ ] T005 Set up basic FastAPI application structure (`main.py`, `api/`, `models/`, `services/`).

---

## Phase 3: User Story 1 - Manual Balance Reconciliation (P1)

**Goal**: As a reconciler, I need a manual balance adjustment window so I can align an account's total balance with the most recent statement before closing the period.

**Independent Test Criteria**: Trigger the adjustment flow for an account and verify the user can set a target balance, pick an effective date, and submit without any other workflows running.

- [ ] T010 [P] [US1] Implement `ManualBalanceAdjustment` SQLAlchemy model in `src/sdd_cash_manager/models/adjustment.py`.
- [ ] T011 [P] [US1] Implement `ManualBalanceAdjustment` Pydantic schema for request/response in `src/sdd_cash_manager/schemas/adjustment.py`.
- [ ] T012 [P] [US1] Implement `ManualBalanceAdjustmentService` in `src/sdd_cash_manager/services/adjustment_service.py` to handle creation, validation (target balance >= 0), and persistence.
- [ ] T013 [P] [US1] Implement FastAPI endpoint for manual balance adjustment (e.g., POST /accounts/{account_id}/adjust-balance) in `src/sdd_cash_manager/api/v1/endpoints/adjustment.py`.
- [ ] T014 [P] [US1] Add validation for `effective_date` (past/present/future) and surface warnings if outside the current statement range (non-blocking toast notification) in API endpoint or service layer.
- [ ] T015 [P] [US1] Write unit tests for `ManualBalanceAdjustmentService` and Pydantic schemas.
- [ ] T016 [P] [US1] Write integration tests for the manual balance adjustment API endpoint.

---

## Phase 4: User Story 2 - Automated Transaction Creation (P2)

**Goal**: As an operator, I want the system to create the balancing transaction automatically so I do not need to manually insert ledger entries after every adjustment.

**Independent Test Criteria**: Submit a target balance that differs from the current running balance and verify the system logs a new transaction dated per the window, showing the debit/credit needed to reach the target.

- [ ] T017 [P] [US2] Update `ManualBalanceAdjustment` model/service to trigger transaction creation upon successful adjustment.
- [ ] T018 [P] [US2] Implement `AdjustmentTransaction` SQLAlchemy model in `src/sdd_cash_manager/models/adjustment.py`.
- [ ] T019 [P] [US2] Implement `AdjustmentTransaction` Pydantic schema in `src/sdd_cash_manager/schemas/adjustment.py`.
- [ ] T020 [P] [US2] Update `AdjustmentService` (or related service) to create `AdjustmentTransaction` based on calculated difference and effective date.
- [ ] T021 [P] [US2] Implement logic to update `ManualBalanceAdjustment.created_transaction_id` and `ManualBalanceAdjustment.status` upon successful transaction creation.
- [ ] T022 [P] [US2] Update `banking product enum` to include 'ADJUSTMENT_DEBIT' and 'ADJUSTMENT_CREDIT' as per spec clarification.
- [ ] T023 [P] [US2] Write unit tests for `AdjustmentTransaction` model and creation logic.
- [ ] T024 [P] [US2] Write integration tests for the automated transaction creation flow.
- [ ] T036 [P] [US2] Ensure `ManualBalanceAdjustmentService` determines the current running balance as of the submitted `effective_date` (using account history/ledger snapshots) rather than relying on a mutable `account.running_balance`.
- [ ] T037 [P] [US2] Route adjustment posting through `TransactionService`/ledger entries to persist true debit/credit rows, update balances, and link the resulting `AdjustmentTransaction` to the `ManualBalanceAdjustment`.
- [ ] T038 [P] [US3] After the adjustment transaction posts, invoke `ReconciliationService.create_reconciliation_entry_from_transaction` so `ReconciliationViewEntry` immediately reflects the change for `/accounts/{account_id}/reconciliation`.
- [ ] T039 [P] [US1/US2] Replace the placeholder permission stub in `src/sdd_cash_manager/api/v1/endpoints/adjustment.py` with JWT/`require_role` enforcement, disable the control for unauthorized roles, and log each adjustment attempt for auditing.

---

## Phase 5: User Story 3 - Ledger and Reconciliation Visibility (P3)

**Goal**: As an auditor, I need this adjustment transaction to be visible in reconciliation views so I can trace the lineage of balance edits.

**Independent Test Criteria**: After performing an adjustment, open the reconciliation panel for the account and confirm the adjustment appears with the chosen effective date and status.

- [ ] T025 [P] [US3] Implement `ReconciliationViewEntry` model/schema (or adapt existing reconciliation views) in `src/sdd_cash_manager/models/reconciliation.py` and `src/sdd_cash_manager/schemas/reconciliation.py`.
- [ ] T026 [P] [US3] Develop logic to populate `ReconciliationViewEntry` with data from `AdjustmentTransaction`, ensuring `is_adjustment` flag and `reconciled_status` are correctly set.
- [ ] T027 [P] [US3] Implement API endpoint to fetch reconciliation view data (e.g., GET /accounts/{account_id}/reconciliation).
- [ ] T028 [P] [US3] Write unit tests for reconciliation view population logic.
- [ ] T029 [P] [US3] Write integration tests for fetching reconciliation data including adjustment entries.

---

## Phase 6: Polish & Cross-Cutting Concerns

These tasks address broader quality attributes and final checks.

- [ ] T030 [P] Implement permissioning logic: disable adjustment control for users without rights, log audit entry. (Edge Case handling)
- [ ] T031 [P] Refine performance of balance calculation and transaction creation if benchmarks exceed targets (refer to `research.md` for goals).
- [ ] T032 [P] Implement comprehensive logging and tracing for adjustment and transaction creation flows.
- [ ] T033 [P] Add detailed documentation (docstrings, README updates) for new modules and endpoints.
- [ ] T034 [P] Conduct a final review against `GEMINI.md` (Constitution) and `TECHNICAL.md` (Coding Standards).
- [ ] T035 [P] Prepare for database migration strategy from SQLite to PostgreSQL (refer to `research.md`).
- [ ] T040 [P] Add unit/integration tests that cover: effective-date based difference calculation, ledger transaction creation, reconciliation entry persistence, zero-difference audit records, and permission enforcement for adjustments.
- [ ] T041 [P] Ensure reconciliation API tests validate that the newly created reconciliation entries appear with the adjustment metadata (date, amount, `is_adjustment`, reconciled flag).
- [ ] T042 [P] Add tests that simulate unauthorized users attempting to adjust a balance so the disabled control and 403 behavior are validated alongside audit logging.

---

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
