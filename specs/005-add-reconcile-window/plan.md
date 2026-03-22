# Implementation Plan: Reconcile Window

**Branch**: `005-add-reconcile-window` | **Date**: 2026-03-22 | **Spec**: specs/005-add-reconcile-window/spec.md
**Input**: Feature specification from `/specs/005-add-reconcile-window/spec.md`

## Summary
Define the backend support for the Reconcile Window so the UI can accept an ending bank balance, surface only UNCLEARED/CLEARED transactions that match the last statement, and advance the Difference field toward $0.00 while persisting reconciliation_status transitions.

## Technical Context
**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI, SQLAlchemy, python-accounting helpers, pytest/httpx for integration tests, jose- or JWT-backed auth utilities already in `lib`
**Storage**: SQLite (development/tests) via SQLAlchemy sessions; existing models (Account, Transaction) persist the reconciled state and can be extended to store statement metadata.
**Testing**: pytest with httpx.AsyncClient, seeded fixtures for accounts/balancing, and jwt_utils to simulate authenticated api calls
**Target Platform**: Linux-hosted FastAPI service (backend API)
**Project Type**: Web-service backend (FastAPI + SQLAlchemy)
**Performance Goals**: Keep reconciliation queries and difference calculations under ~200 ms for statement batches up to a few hundred rows to satisfy the constitution’s responsiveness expectation while keeping the UI snappy.
**Constraints**: Filters must honor `processing_status` + `reconciliation_status`, the Difference calculation must reflect only the selected set of transactions, and the UI must block FAILED items until their upstream processing_status clears.
**Scale/Scope**: Designed for statement cycles with up to ~10k transactions by relying on SQL filters scoped to the statement cutover date, paging when necessary, and pre-fetching only UNCLEARED/CLEARED rows.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Financial Data Accuracy (VII): Difference derives from the ending bank balance minus the requested matching rows, enforcing audited status transitions (UNCLEARED → CLEARED/RECONCILED) so ledger invariants hold.
- Security Practices (V): The endpoints only mark transactions when their `processing_status` allows it and authenticated access passes through the existing JWT guard to prevent unauthorized reconciliation actions.
- State Management (VI): The plan defines explicit transitions between UNCLEARED, CLEARED, and RECONCILED statuses and documents how they are surfaced to the UI, ensuring predictable workflows.

*Post-design re-check*: The constitution gates remain satisfied after defining the data model, API contracts, and quickstart guidance, as no new dependencies or state transitions violate the core principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-add-reconcile-window/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── reconcile.yaml
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── sdd_cash_manager/
│   ├── api/
│   │   └── accounts.py
│   ├── services/
│   │   ├── account_service.py
│   │   └── transaction_service.py
│   ├── models/
│   │   ├── account.py
│   │   └── transaction.py
│   ├── schemas/
│   │   ├── account_schema.py
│   │   └── transaction_schema.py
│   ├── lib/
│   │   ├── auth.py
│   │   └── logging_config.py
│   ├── core/
│   │   └── config.py
│   └── database.py
└── filesystem helpers (scripts/ and docs/ as needed)
tests/
├── api/
│   ├── conftest.py
│   ├── fixtures.py
│   ├── jwt_utils.py
│   ├── helpers.py
│   ├── test_accounts.py
│   ├── test_transactions.py
│   └── test_validation.py
scripts/
└── run_api_tests.sh
```

**Structure Decision**: Reuse the existing FastAPI/SQLAlchemy service layout under `src/sdd_cash_manager` for the reconciliation endpoints and services; the tests already live in `tests/api`, so the new integration scenarios will live there alongside the current fixtures.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | No constitution violations identified | N/A |
