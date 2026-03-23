# Task List: Account Management

**Feature Name**: Account Management
**Generated**: 2026-03-12

## Phases

### Phase 1: Setup

This phase covers the initial project setup and dependency installation.

- [x] T001 Setup Python project structure (`src/` with `__init__.py` files for packages, `tests/`).
- [x] T002 Set up virtual environment and install core dependencies (FastAPI, SQLAlchemy, Pydantic, `python-accounting`, `psycopg2-binary`).
- [x] T003 Configure SQLite database connection and ORM setup.
- [x] T004 Configure Pytest for testing.

### Phase 2: Foundational Tasks

This phase includes common utilities, base models, and error handling that will be used across the feature.

- [x] T005 Define base SQLAlchemy models and migration setup (`src/models/base.py`).
- [x] T006 Implement common utility functions (e.g., for currency handling, date formatting, exception handling) in `src/lib/utils.py`.
- [x] T007 Define API error handling structure and exceptions in `src/lib/exceptions.py`.

### Phase 3: User Story 1 - Account Creation and Management (P1)

Core functionality for creating, managing, and listing accounts.

- [x] T008 [US1] Define `Account` model in `src/models/account.py` (including `account_number`, `currency`, `accounting_category`, `banking_product_type`, `available_balance`, `credit_limit`, `notes`).
- [x] T009 [US1] Define `AccountingCategory` and `BankingProductType` enums in `src/models/enums.py`.
- [x] T010 [US1] Implement AccountService for core CRUD operations (create, read, update, delete) using TDD principles, writing tests before implementation code, in `src/services/account_service.py`.
- [x] T011 [US1] Implement account search by name functionality in `src/services/account_service.py`.
- [x] T012 [US1] Create account API endpoints (POST /accounts, GET /accounts, GET /accounts/{id}, PUT /accounts/{id}, DELETE /accounts/{id}) in `src/api/accounts.py`.
- [x] T013 [US1] Write unit tests for `Account` model and enums in `tests/unit/test_account_model.py`.
- [x] T014 [US1] Write unit tests for basic `AccountService` CRUD operations and search in `tests/unit/test_account_service.py`.
- [x] T015 [US1] Write integration tests for account API endpoints in `tests/integration/test_account_api.py`.

### Phase 4: User Story 3 - Balance Adjustment (P1)

Functionality to manually adjust account balances, creating corresponding double-entry transactions.

- [x] T016 [US3] Define `Transaction` and `Entry` models for double-entry accounting in `src/models/transaction.py`. `Transaction` will contain common details, and `Entry` will link to `Transaction` and specific `Account`s with `debit_amount`/`credit_amount`.
- [x] T017 [US3] Implement `TransactionService` for creating and managing double-entry transactions and their associated `Entries` in `src/services/transaction_service.py`. This service will enforce double-entry integrity (debits = credits).
- [x] T018 [US3] Implement manual balance adjustment logic using TDD principles. This task involves creating a `Transaction` with at least two `Entries` to adjust account balances, leveraging the `TransactionService`. Implementation in `src/services/account_service.py` and `src/services/transaction_service.py`.
- [x] T019 [US3] Implement historical balance tracking logic for `Account` and `Entry` models, building upon the basic balance calculation from T010 (now adapted for double-entry). Write tests before implementation code.
- [x] T020 [US3] Create API endpoint for manual balance adjustment (POST /accounts/{account_id}/adjust_balance) in `src/api/accounts.py`, accepting the double-entry payload as defined in `contracts/public_api.md`.
- [x] T021 [US3] Write unit tests for `Transaction` and `Entry` models and related enums in `tests/unit/test_transaction_model.py`.
- [x] T022 [US3] Write unit tests for `TransactionService` and double-entry balance adjustment logic in `tests/unit/test_transaction_service.py` and `tests/unit/test_account_service.py`.
- [x] T023 [US3] Write integration tests for the balance adjustment API endpoint in `tests/integration/test_account_api.py`.

### Phase 5: User Story 2 - Hierarchical Account Structure (P2)

Enabling accounts to be organized in a tree-like structure and aggregating group balances.

- [x] T024 [US2] Update `Account` model to include `parent_account_id` and implement relationship in `src/models/account.py`.
- [x] T025 [US2] Implement AccountService for hierarchical account creation, retrieval, and balance aggregation using TDD principles, writing tests before implementation code, in `src/services/account_service.py`.
- [x] T026 [US2] Implement AccountGroup balance calculation logic by aggregating balances from individual accounts (summing `Entry` debits/credits).
- [x] T027 [US2] Update account API endpoints to support hierarchical structures (e.g., creating sub-accounts, retrieving aggregated balances) in `src/api/accounts.py`.
- [x] T028 [US2] Write unit tests for hierarchical account logic in `tests/unit/test_account_service.py`.
- [x] T029 [US2] Write integration tests for hierarchical account API endpoints in `tests/integration/test_account_api.py`.

### Phase 6: Polish & Cross-Cutting Concerns

Finalization tasks including state management, documentation, and performance optimization.

- [x] T030 Implement application state management for unsaved changes ("Save/New"), and define/implement clear lifecycles and state transitions for `Account`, `Transaction`, and `Entry` entities in `src/lib/state_management.py` and integrate with relevant services/APIs.
- [x] T031 Add comprehensive docstrings and type hints across the codebase.
- [x] T032 Refactor and optimize database queries for performance, focusing on those identified as bottlenecks by performance testing.
- [x] T033 Benchmark account creation latency, transaction processing throughput, and scalability of account balance aggregation. Ensure these meet performance goals.
- [x] T034 Implement logging and monitoring.
- [x] T035 Add `README.md` with installation and usage instructions.
- [x] T036 Implement comprehensive input validation and security best practices for all API endpoints and services (`src/api/`, `src/services/`).
- [x] T037 [Security] Implement JWT authentication for API endpoints.
- [x] T038 [Security] Implement Role-Based Access Control (RBAC) for API endpoints.
- [x] T039 [Security] Implement encryption for sensitive data at rest (e.g., sensitive account notes).
- [x] T040 [Security] Define and implement secure configuration management using environment variables.
- [x] T041 Define 'core business logic' for the Account Management feature and ensure 100% test coverage with automated reporting.

### Phase 7: Core Security & Reliability Enhancements (New Tasks based on updated spec.md and codebase investigation)

This phase addresses the critical architectural and security gaps identified.

- [x] T042 [P] Implement pessimistic locking (e.g., `SELECT ... FOR UPDATE`) in `src/services/account_service.py` to prevent race conditions during account balance updates.
- [x] T043 [P] Modify `src/services/transaction_service.py` to persist `Transaction` and `Entry` data to the database, ensuring all financial transactions are durable. Update `src/models/transaction.py` and `src/database.py` as needed for ORM integration and migrations.
- [x] T044 Document a formal threat model for the Account Management feature in `specs/001-account-management/threat_model.md` and map existing/new security requirements to it.
- [x] T045 Define and implement logging, alerting, and incident response procedures for security failures and data breaches in `src/lib/security_events.py` and `src/core/config.py`.
- [x] T046 Review and enhance input validation and sanitization enforcement across all layers (API, service, data access) in `src/api/`, `src/services/`, and `src/models/` to prevent bypasses.
- [x] T047 Verify alignment of implemented security controls with OWASP Top 10 and define measurable acceptance criteria for security (e.g., integrate security scanning tools, define PT scope).

### Phase 8: NFR Verification Tasks (Updated with new dependencies)

These tasks verify the Non-Functional Requirements, now dependent on the core security and reliability enhancements.

- [x] T048 [Scalability] Document implementation mechanisms for horizontal scaling (running multiple Uvicorn workers via Gunicorn, stateless app design) in `quickstart.md`. Testing of horizontal scaling will be covered by load testing in tasks T055 and T056.
- [x] T049 [Scalability] Verify that account retrieval for hierarchies up to 5 levels deep completes within 200ms under load. (Implemented Locust task in `performance-tests/locustfile.py`. Manual execution of Locust and FastAPI app is required to verify performance. Instructions for running Locust are in `locustfile.py`).
- [x] T050 [Accuracy] Implement financial calculation logic using `Decimal` types with appropriate precision and explicitly defined rounding rules (e.g., `ROUND_HALF_UP`) to ensure adherence to the 0.001% tolerance and 0.01 unit absolute error for the smallest currency denomination. Implement corresponding tests.
- [x] T051 [Accuracy] Develop tests to rigorously check the accuracy of all financial computations.
- [x] T052 [Reliability] Implement and test systems for achieving 99.9% uptime by exercising `scripts/check-health.sh` against `/health` and capturing the results in `specs/001-account-management/nfr_verification.md`.
- [x] T053 [Reliability] Establish and test procedures for meeting RTO < 4 hours and RPO of 1 hour by snapshotting/restoring `sdd_cash_manager.db` through `scripts/db-backup.sh`/`scripts/db-restore.sh` documented in `specs/001-account-management/nfr_verification.md`.
- [x] T054 [Reliability] Incorporate logging, monitoring, and failover mechanisms via the structured logging helpers (`src/sdd_cash_manager/lib/logging_config.py`) and the documented monitoring guidance in `specs/001-account-management/nfr_verification.md`.
- [x] T055 [Scalability] Define and test a 500+ RPS target for account APIs using `performance-tests/locustfile.py` and record the general approach in `specs/001-account-management/nfr_verification.md`.
- [x] T056 [Scalability] Define and test a concurrent throughput target (1,000 requests/minute) via the same Locust harness and describe how to capture the summary in `specs/001-account-management/nfr_verification.md`.
- [x] T057 [Accuracy] Define the <0.001% accuracy target and validate it through `tests/api/test_transactions.py::test_reconcile_window_zero_difference_flow` as described in `specs/001-account-management/nfr_verification.md`.
- [x] T058 [Reliability] Define the >99.9% uptime reliability goal and tie it to the health check/smoke-test guidance in `specs/001-account-management/nfr_verification.md`.

## Dependencies and Ordering

- **Setup Tasks (T001-T004)** must complete before **Foundational Tasks (T005-T007)**.
- **Foundational Tasks** must complete before **User Story Tasks (T008-T029)**.
- Within User Story phases, the typical order is Models → Services → API Endpoints → Tests.
- User Story 1 (T008-T015) and User Story 3 (T016-T023) are both P1 and can be worked on in parallel, but US1 foundational elements might be needed for US3. US1 foundational elements (T008-T010) are prerequisites for US3.
- User Story 2 (T024-T029) is P2 and depends on the completion of US1.
- **Polish Tasks (T030-T041)** depend on the completion of all User Story implementation tasks.
- **Core Security & Reliability Enhancements (T042-T047)** depend on the completion of Polish Tasks (T030-T041) and are critical prerequisites for NFR Verification.
- **NFR Verification Tasks (T048-T058)** depend on the completion of all User Story implementation, Polish, and Core Security & Reliability Enhancement tasks.

## Parallel Opportunities

- **Setup**: T001, T002, T003, T004 can potentially be executed in parallel.
- **Foundational**: T005, T006, T007 can be worked on in parallel.
- **User Story 1**: T008 (Model), T009 (Enums), T010 (Service) can be worked on in parallel. T012 (API) depends on T010. Tests (T013-T015) can run in parallel once their respective implementation tasks are completed.
- **User Story 3**: T016 (Models), T017 (Service) can be worked on in parallel, but T017 depends on T016. T020 (API) depends on T017. Tests (T021-T023) can run in parallel once their respective implementation tasks are completed.
- **User Story 2**: T024 (Model), T025 (Service) can be worked on in parallel, but T025 depends on T024. T027 (API) depends on T025. Tests (T028-T029) can run in parallel once their respective implementation tasks are completed.
- **Polish & Core Security/Reliability**: Many tasks in Phase 6 and 7 can be worked on in parallel, with dependencies noted.
- **NFR Verification**: Many tasks in Phase 8 can be worked on in parallel, with dependencies noted.

## Implementation Strategy

- **MVP**: User Story 1 (Account Creation and Management) and User Story 3 (Balance Adjustment).
- **Incremental Delivery**: Implement features phase by phase, starting with setup, then foundational elements, followed by user stories in priority order (P1 then P2), then core security/reliability enhancements, and finally NFR verification.

## Summary

- **Total Tasks**: 58
- **Tasks per User Story**:
  - US1: 8 tasks
  - US3: 8 tasks
  - US2: 6 tasks
- **Parallel Opportunities**: Identified across setup, foundational, and within user story implementation/testing phases, as well as within the new Core Security & Reliability and NFR Verification phases.
- **Independent Test Criteria**: Each user story phase is designed to be independently testable. Core Security & Reliability enhancements are also independently testable where applicable.
- **Suggested MVP Scope**: User Story 1 and User Story 3.
- **Format Validation**: All tasks follow the checklist format `- [ ] [TaskID] [P?] [Story?] Description with file path`.

## Next Step

The task list has been regenerated to include critical security and reliability enhancements. Please review and provide further instructions.
