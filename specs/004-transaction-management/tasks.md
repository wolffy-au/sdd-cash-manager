---
description: "Task list for implementing transaction management"
---

# Tasks: Transaction Management

**Input**: plan.md, spec.md, research.md, data-model.md, contracts/
**Prerequisites**: plan.md defines the architecture; contracts/ enumerate the API surface.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 [P] Add QuickFill history and duplicate-scan settings (retention window, max batch size) to `src/sdd_cash_manager/core/config.py`
- [X] T002 [P] Extend `src/sdd_cash_manager/lib/security_events.py` with structured audit events for transaction creation, QuickFill suggestion approval, duplicate merges, and account merges

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 [P] Create `src/sdd_cash_manager/models/quickfill_template.py` with the SQLAlchemy entity that tracks action, currency, accounts, confidence_score, and timestamps
- [x] T004 [P] Create `src/sdd_cash_manager/models/duplicate_candidate.py` that stores matching transaction ids, account scope, amount, date, and suggested canonical entry
- [x] T005 [P] Create `src/sdd_cash_manager/models/account_merge_plan.py` to capture source/target accounts, reparenting map, status, and audit metadata
- [x] T006 [P] Expand `src/sdd_cash_manager/schemas/transaction_schema.py` with QuickFillTemplateResponse, DuplicateCandidateResponse, and AccountMergePlanRequest/Response DTOs matching the new models
- [x] T007 [P] Update `src/sdd_cash_manager/services/transaction_service.py` to include helper functions for ranking QuickFill candidates, scanning duplicate sets, and validating merges against the hierarchy depth constraint

---

## Phase 3: User Story 1 - Record a double-entry transaction (Priority: P1) 🎯 MVP

**Goal**: Persist balanced debit/credit entries, update reconciliation snapshots, and surface HTTP errors for invalid payloads.  
**Independent Test**: POST `/transactions/` and inspect both accounts plus reconciliation state to confirm double-entry persistence and updated balances.

### Tests for User Story 1
- [x] T008 [US1] Add an API integration test in `tests/api/test_transactions.py` that submits a transaction payload and verifies that both accounts store matching debit/credit entries and balances update atomically

### Implementation for User Story 1
- [x] T009 [US1] Implement transaction creation logic in `src/sdd_cash_manager/services/transaction_service.py`, enforcing double-entry atomicity, hierarchy validation, and reconciliation snapshot updates
- [x] T010 [US1] Expose `POST /transactions/` in `src/sdd_cash_manager/api/accounts.py`, wiring it to `TransactionService` and returning the new entries via `schemas.transaction_schema.TransactionResponse`
- [x] T011 [US1] Add request/response schema enhancements in `src/sdd_cash_manager/schemas/transaction_schema.py` to reflect the double-entry payload and response shape for the new endpoint

---

## Phase 4: User Story 2 - Use QuickFill suggestions to accelerate entry (Priority: P2)

**Goal**: Surface QuickFill templates derived from recent entries, allow single-interaction confirmation, and support admin approvals.  
**Independent Test**: Query `/quickfill/?action=...&currency=...` after seeding similar history and verify the high-confidence template plus acceptance path.

### Tests for User Story 2
- [ ] T012 [US2] Add an integration test in `tests/api/test_quickfill.py` that creates matching transactions, retrieves a QuickFill suggestion, and confirms acceptance updates nothing until submission

### Implementation for User Story 2
- [ ] T013 [US2] Implement QuickFill candidate derivation, confidence scoring, and approval flag checks inside `src/sdd_cash_manager/services/transaction_service.py`
- [ ] T014 [US2] Add QuickFill endpoints (`GET /quickfill/`, `POST /quickfill/templates/{template_id}/approve`) in `src/sdd_cash_manager/api/accounts.py`, leveraging the new schemas and logging approvals via `security_events`

---

## Phase 5: User Story 3 - Clean up duplicates and merge accounts (Priority: P3)

**Goal**: Detect identical entries for manual consolidation and move children/entries during account merges without touching aggregate balances.  
**Independent Test**: Seed duplicates, call `/duplicates/merge`, and run `/accounts/merge`, verifying audit logs plus untouched totals.

### Tests for User Story 3
- [x] T015 [US3] Add `tests/api/test_duplicates.py` that exercises duplicate detection listing and merge approval while confirming reconciliation snapshots stay constant
- [x] T016 [US3] Extend `tests/api/test_accounts.py` to cover account merge validation (depth check) and audit logging

### Implementation for User Story 3
- [x] T017 [US3] Implement duplicate detection scan, merge consolidation logic, and account reparenting helpers in `src/sdd_cash_manager/services/transaction_service.py` and `src/sdd_cash_manager/services/account_service.py`
- [x] T018 [US3] Add duplicate/merge endpoints (`GET /duplicates/`, `POST /duplicates/merge`, `POST /accounts/merge`) in `src/sdd_cash_manager/api/accounts.py`, emitting structured responses plus audit events

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T019 [P] Update `specs/004-transaction-management/quickstart.md` with any adjustments discovered during implementation and verify each step still describes a reproducible flow
- [ ] T020 Review `docs/api-tests` (if exists) or add notes in `README.md` to reflect the new transaction, QuickFill, and duplicate endpoints so testers know how to exercise them
- [ ] T021 [P] Run the full pytest suite (`pytest tests/api -v`) to confirm no regression and to capture coverage info for the new flows

---

## Dependencies & Execution Order

1. **Phase 1 (Setup)** tasks can run immediately and in parallel.  
2. **Phase 2 (Foundational)** depends on Phase 1 and must finish before any story begins.  
3. **Phase 3+ (User Stories)** depend on Phase 2 but can run in priority order (US1 → US2 → US3) or in parallel once Phase 2 completes.  
4. **Phase 6 (Polish)** occurs after all user stories finish and ties up documentation/tests.

### Story Dependencies
- US1 (P1) is the MVP and must be implemented/tested before US2/US3 rely on shared services.  
- US2 (P2) builds on US1’s transaction persistence but remains independently testable.  
- US3 (P3) can run concurrently after Phase 2 but should wait for the merge helpers that may reuse US1’s services.

### Parallel Opportunities
- Tasks marked `[P]` (T001, T002, T003, T004, T005, T006, T007, T019, T021) can run in parallel because they touch distinct files or docs.  
- Once Phase 2 is done, US1, US2, and US3 phases can be assigned to separate developers for concurrent implementation/testing.

### Implementation Strategy
1. Finish Phase 1+2 to prepare config/models/schemas.  
2. Deliver US1 first (MVP) and validate via its independent test before enabling QuickFill and duplicates.  
3. Complete US2 and US3 sequentially or in parallel, each with its own tests and API checks.  
4. Polish docs/test run in Phase 6 to confirm everything matches the quickstart.
