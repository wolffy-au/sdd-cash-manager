# Implementation Plan: Transaction Management

**Branch**: `004-transaction-management` | **Date**: 2026-03-21 | **Spec**: `specs/004-transaction-management/spec.md`
**Input**: Feature specification from `/specs/004-transaction-management/spec.md`

**Note**: This template is maintained by the `/speckit.plan` workflow. See `.specify/templates/plan-template.md` for the execution process.

## Summary

Deliver the transaction management capabilities outlined in the spec by enforcing double-entry persistence, modeling QuickFill templates from recent history, and adding duplicate-detection plus account-merge flows while building on the existing FastAPI/SQLAlchemy ledger stack.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12 (project targets >=3.10,<3.13 and Ruff is configured for py312).  
**Primary Dependencies**: FastAPI for the API surface, SQLAlchemy 2.0 for ORM/models, httpx/pytest/pytest-asyncio for testing, python-accounting utilities, and existing jwt/security helpers.  
**Storage**: Ledger data persists via SQLAlchemy (SQLite for dev/tests, Postgres in production).  
**Testing**: pytest suite for unit, integration, and API tests; httpx AsyncClient in `tests/api`.  
**Target Platform**: Linux server/container hosting the FastAPI app.  
**Project Type**: Web service/backend.  
**Performance Goals**: Duplicate detection must scan 1,000 transactions within 3 seconds; QuickFill template lookup should respond within the interaction window (<200ms ideally while typing).  
**Constraints**: Maintain double-entry atomicity, respect the 5-level hierarchy depth limit when reparenting accounts, and ensure any merge/cleanup operations leave reconciliation balances unchanged.  
**Scale/Scope**: Operates on the existing ledger dataset (~1k historical transactions per scan) and reuses shared account hierarchy APIs from earlier specs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: Align with the constitution’s emphasis on readability, modularity, and SOLID principles (use `TECHNICAL.md` conventions for structure and naming).  
- **Testing Standards**: All new behavior must be covered by unit + integration tests (matching the constitution’s 100% coverage aim for core logic).  
- **User Experience Consistency**: QuickFill and cleanup flows must provide clear, actionable responses and preserve the mental model already established by the FastAPI endpoints.  
- **Performance**: Duplicate detection target (1k transactions in <3s) and QuickFill latency (<200ms) are directly derived from the specification.  
- **Security**: Validate inputs, require proper auth (reuse existing JWT helpers), and log audit events for merges/cleanup operations.  
- **State Management**: Double-entry enforcement, duplicate cleanup snapshots, and merge state transitions all must track entity lifecycles per constitution expectations.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/sdd_cash_manager/
├── api/                # FastAPI router endpoints (accounts, transactions)
├── services/           # Business logic (account_service, transaction_service)
├── models/             # SQLAlchemy entities and enums
├── schemas/            # Pydantic DTOs (accounts, transactions)
├── lib/                # Shared primitives (auth, encryption, logging)
├── core/               # Config management
└── database.py         # Session management

tests/
├── unit/               # Legacy unit tests covering models/services
├── api/                # httpx-backed integration tests
└── (future) contract/   # contract-focused tests when needed
```

**Structure Decision**: Continue leveraging the single backend project layout centered around `src/sdd_cash_manager`. Transactions, QuickFill, duplicate detection, and merge logic will extend `services/transaction_service.py` (and related helpers) while reusing existing models/schemas. Integration tests live under `tests/api` to cover the new endpoints, with `tests/unit` ensuring service invariants.

## Complexity Tracking

> No constitution violations were identified; all gates remain satisfied.
