# Implementation Plan: Transaction Management

**Branch**: `004-transaction-management` | **Date**: 2026-03-21 | **Spec**: `specs/004-transaction-management/spec.md`
**Input**: Feature specification from `/specs/004-transaction-management/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Deliver the transaction management capabilities outlined in the feature spec by enforcing atomic double-entry persistence, surfacing QuickFill templates drawn from recent action/currency history, and supporting duplicate detection plus account merge tools while reusing the existing FastAPI/SQLAlchemy ledger stack and test harness.

## Technical Context

**Language/Version**: Python 3.12.13 (project targets >=3.10,<3.13)  
**Primary Dependencies**: FastAPI 0.128+, SQLAlchemy 2.0.x, httpx for API tests, pytest/pytest-asyncio/behave, python-accounting helpers, and existing JWT/auth utilities.  
**Storage**: SQLAlchemy-backed relational store – SQLite during local/testing and PostgreSQL in production (via existing `database.py` session management).  
**Testing**: `pytest` drives unit, integration, and API suites under `tests/`, behave covers placeholder BDD checks, plus `uv`-managed dependency updates via `uv.lock`.  
**Target Platform**: Linux containerized server running FastAPI (`uvicorn`) inside the repository’s standard devcontainer/CI environments.  
**Project Type**: Web service backend with HTTP APIs for account/transaction management.  
**Performance Goals**: QuickFill latency within ~200ms while typing, duplicate-detection scans 1,000 transactions in <3 seconds with deterministic snapshots, and pytest coverage stays ≥90%.  
**Constraints**: Maintain double-entry atomicity, validate hierarchy depth (≤5 levels) during merges, require structured audit logging for QuickFill/merge/duplicate actions, and reject operations affecting archived/deleted accounts.  
**Scale/Scope**: Operates over existing ledger datasets (~1k transactions per detection run) and reuses spec 001 account hierarchy services instead of rebuilding them.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

All constitution principles are satisfied: double-entry/state transitions follow the Constitution’s state management guidance, unit/integration testing aligns with the testing standard, audit/logging updates meet security requirements, and QuickFill/duplicate flows preserve the user experience and performance mandates.

## Project Structure

### Documentation (this feature)

```text
specs/004-transaction-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── transaction-management-api.md
│   └── transaction-management.yaml
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
│   │   ├── transaction_service.py
│   │   └── adjustment_service.py
│   ├── models/
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── quickfill_template.py
│   │   ├── duplicate_candidate.py
│   │   └── account_merge_plan.py
│   ├── schemas/
│   │   ├── account_schema.py
│   │   └── transaction_schema.py
│   ├── lib/
│   │   ├── auth.py
│   │   └── security_events.py
│   ├── core/
│   │   └── config.py
│   └── database.py
tests/
├── unit/
├── api/
│   ├── test_accounts.py
│   ├── test_transactions.py
│   ├── test_quickfill.py
│   ├── test_duplicates.py
│   └── conftest.py
└── integration/
```

**Structure Decision**: Continue with the existing single-backend layout under `src/sdd_cash_manager` plus `tests/api`/`tests/unit`. Feature-specific logic sits in `services/transaction_service.py`, new models in `models/`, and HTTP coverage via `tests/api/*.py`, matching the documented structure in AGENTS instructions.

## Complexity Tracking

> No constitution violations detected; no additional justifications required.
