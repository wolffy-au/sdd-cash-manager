# Task List: Account Management

**Feature Name**: Account Management
**Generated**: 2026-02-22

## Phases

### Phase 1: Setup

This phase covers the initial project setup and dependency installation.

- [ ] T001 Setup Python project structure (`src/` with `__init__.py` files for packages, `tests/`).
- [ ] T002 Set up virtual environment and install core dependencies (FastAPI, SQLAlchemy, Pydantic, `python-accounting`, `psycopg2-binary`).
- [ ] T003 Configure SQLite database connection and ORM setup.
- [ ] T004 Configure Pytest for testing.

### Phase 2: Foundational Tasks

This phase includes common utilities, base models, and error handling that will be used across the feature.

- [ ] T005 Define base SQLAlchemy models and migration setup (`src/models/base.py`).
- [ ] T006 Implement common utility functions (e.g., for currency handling, date formatting, exception handling) in `src/lib/utils.py`.
- [ ] T007 Define API error handling structure and exceptions in `src/lib/exceptions.py`.

### Phase 3: User Story 1 - Account Creation and Management (P1)

Core functionality for creating, managing, and listing accounts.

- [ ] T010 [US1] Implement AccountService for core CRUD operations (create, read, update, delete) using TDD principles, writing tests before implementation code, in src/services/account_service.py.
- [ ] T011 [US1] Define `Account` model (including `account_number`, `currency`, `accounting_category`, `banking_product_type`, `available_balance`, `credit_limit`, `notes`) in `src/models/account.py`.
- [ ] T012 [US1] Define `AccountingCategory` and `BankingAccountType` enums in `src/models/enums.py`.
- [ ] T013 [US1] Implement basic balance calculation logic (running, reconciled) in `src/services/account_service.py`. This serves as the foundation for historical balance tracking.
- [ ] T014 [US1] Implement account search by name functionality in `src/services/account_service.py`.
- [ ] T015 [US1] Create account API endpoints (POST /accounts, GET /accounts, GET /accounts/{id}, PUT /accounts/{id}, DELETE /accounts/{id}) in `src/api/accounts.py`.
- [ ] T016 [US1] Implement account search API endpoint in `src/api/accounts.py`.
- [ ] T017 [US1] Write unit tests for `Account` model and enums in `tests/unit/test_account_model.py`.
- [ ] T018 [US1] Write unit tests for basic `AccountService` CRUD operations and search in `tests/unit/test_account_service.py`.
- [ ] T019 [US1] Write integration tests for account API endpoints in `tests/integration/test_account_api.py`.

### Phase 4: User Story 3 - Balance Adjustment (P1)

Functionality to manually adjust account balances, creating corresponding transactions. The interface for this functionality must be intuitive, requiring no more than 3 clicks from the account details view, providing real-time validation feedback, and displaying confirmation within 1 second.

- [ ] T020 [US3] Define `Transaction` model (including `effective_date`, `booking_date`, `description`, `amount`, `debit_account_id`, `credit_account_id`, `processing_status`, `reconciliation_status`, `action_type`) in `src/models/transaction.py`.
- [ ] T021 [US3] Define `ProcessingStatus` and `ReconciliationStatus` enums in `src/models/enums.py`.
- [ ] T022 [US3] Implement `TransactionService` for creating and managing transactions in `src/services/transaction_service.py`.
- [ ] T023 [US3] Implement manual balance adjustment logic using TDD principles. This task involves creating a Transaction (referencing T020/T022) and updating account balances, leveraging the logic from T013 and T025/T026. Implementation in `src/services/account_service.py` and `src/services/transaction_service.py`.
- [ ] T025 [US3] Implement historical balance tracking logic using TDD, building upon the basic balance calculation from T013. Write tests before implementation code.
- [ ] T026 [US3] Implement historical balance tracking logic, leveraging the foundation from T013 and T025.
- [ ] T027 [US3] Create API endpoint for manual balance adjustment (e.g., POST /accounts/{id}/adjust_balance) in `src/api/accounts.py`.
- [ ] T028 [US3] Write unit tests for `Transaction` model and enums in `tests/unit/test_transaction_model.py`.
- [ ] T029 [US3] Write unit tests for `TransactionService` and balance adjustment logic in `tests/unit/test_transaction_service.py` and `tests/unit/test_account_service.py`.
- [ ] T030 [US3] Write integration tests for balance adjustment API endpoint in `tests/integration/test_account_api.py`.

### Phase 5: User Story 2 - Hierarchical Account Structure (P2)

Enabling accounts to be organized in a tree-like structure and aggregating group balances.

- [ ] T031 [US2] Update `Account` model to include `parent_account_id` and implement relationship in `src/models/account.py`.
- [ ] T032 [US2] Implement AccountService for hierarchical account creation, retrieval, and balance aggregation using TDD principles, writing tests before implementation code, in src/services/account_service.py.
- [ ] T034 [US2] Implement AccountGroup balance calculation logic by aggregating balances from individual accounts managed by T013, T025, and T026.
- [ ] T035 [US2] Update account API endpoints to support hierarchical structures (e.g., creating sub-accounts) in `src/api/accounts.py`.
- [ ] T036 [US2] Write unit tests for hierarchical account logic in `tests/unit/test_account_service.py`.
- [ ] T037 [US2] Write integration tests for hierarchical account API endpoints in `tests/integration/test_account_api.py`.

### Phase 6: Polish & Cross-Cutting Concerns

Finalization tasks including state management, documentation, and performance optimization.

- [ ] T038 Implement application state management for unsaved changes ("Save/New"), and define/implement clear lifecycles and state transitions for `Account` and `Transaction` entities in `src/lib/state_management.py` and integrate with relevant services/APIs.
- [ ] T039 Add comprehensive docstrings and type hints across the codebase.
- [ ] T040 Refactor and optimize database queries for performance, focusing on those identified as bottlenecks by the performance testing task T041.
- [ ] T041 [Perf Test] Benchmark account creation latency (API endpoint T013), throughput for account listing (API endpoint T013), and scalability of account balance aggregation (T029). Ensure these meet performance goals.
- [ ] T042 Implement logging and monitoring.
- [ ] T043 Add `README.md` with installation and usage instructions.
- [ ] T044 Implement comprehensive input validation and security best practices for all API endpoints and services (`src/api/`, `src/services/`).
- [ ] T046 [Security] Implement JWT authentication for API endpoints.
- [ ] T047 [Security] Implement Role-Based Access Control (RBAC) for API endpoints.
- [ ] T048 [Security] Implement encryption for sensitive data at rest (e.g., sensitive account notes).
- [ ] T049 [Security] Define and implement secure configuration management using environment variables.
- [ ] T050 Define 'core business logic' for the Account Management feature and ensure 100% test coverage with automated reporting.

## Dependencies and Ordering

- **Setup Tasks (T001-T004)** must complete before **Foundational Tasks (T005-T007)**.
- **Foundational Tasks** must complete before **User Story Tasks (T008-T032)**.
- Within User Story phases, the typical order is Models → Services → API Endpoints → Tests.
- User Story 1 (T008-T017) and User Story 3 (T018-T026) are both P1 and should be completed before User Story 2 (T027-T032), which is P2.
- **Polish Tasks (T033-T037)** depend on the completion of all User Story implementation tasks.

## Parallel Opportunities

- **Setup**: T001, T002, T003, T004 can potentially be executed in parallel.
- **Foundational**: T005 and T006 can be worked on in parallel.
- **User Story 1**: T008 (Model), T010 (Service), T015 (API) can be worked on in parallel, with T010 depending on T008, and T015 depending on T010. Tests (T017, T018, T019) can run in parallel once their respective implementation tasks are completed.
- **User Story 3**: Similar parallelization opportunities exist for Models, Services, API, and Tests.
- **User Story 2**: Similar parallelization opportunities exist for Models, Services, API, and Tests.

## Implementation Strategy

- **MVP**: User Story 1 (Account Creation and Management) and User Story 3 (Balance Adjustment).
- **Incremental Delivery**: Implement features phase by phase, starting with setup, then foundational elements, followed by user stories in priority order (P1 then P2), and finally polish.

## Summary

- **Total Tasks**: 37
- **Tasks per User Story**:
    - US1: 10 tasks
    - US3: 9 tasks
    - US2: 6 tasks
- **Parallel Opportunities**: Identified across setup, foundational, and within user story implementation/testing phases.
- **Independent Test Criteria**: Each user story phase is designed to be independently testable.
- **Suggested MVP Scope**: User Story 1 and User Story 3.
- **Format Validation**: All tasks follow the checklist format `- [ ] [TaskID] [P?] [Story?] Description with file path`.
