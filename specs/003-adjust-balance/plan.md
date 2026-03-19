# Implementation Plan: Adjust Balance Window

**Branch**: `003-adjust-balance` | **Date**: 2026-03-16 | **Spec**: `/workspaces/sdd-cash-manager/specs/003-adjust-balance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

The feature allows manual adjustment of account balances, creating an automated transaction for the difference, and ensuring visibility in reconciliation views. The implementation will use Python 3.12 with FastAPI, SQLAlchemy, Pydantic, and python-accounting, with SQLite as the initial database.

## Technical Context

**Language/Version**: Python 3.12 (minimum supported runtime for the branch and CI agents).  
**Primary Dependencies**: FastAPI 0.128+, SQLAlchemy 2.0+, Pydantic 2.0+, python-accounting 1.0+, httpx 0.27+ (testing), pyjwt 2.9+, and `uv` for dependency and task orchestration.  
**Storage**: SQLite for local development and tests, with Alembic-managed migration scripts prepared so the same models can target PostgreSQL (production pattern) without rewrites.  
**Testing**: pytest (unit/integration), pytest-asyncio, pytest-mock, pytest-cov, behave, and httpx/AsyncClient for API exercises.  
**Target Platform**: Linux containers or virtual machines running Python 3.12 with SQLite for local/dev and PostgreSQL for production deployments.  
**Project Type**: Web Service / REST API that enforces double-entry accounting invariants via services and database transactions.  
**Performance Goals**: The manual adjustment endpoint should respond under 200 ms (95th percentile < 250 ms) when servicing ~100 concurrent adjustment requests, with reconciliation entry persistence completing before the API responds.  
**Constraints**: JWT+RBAC enforced at the endpoint, atomic transaction creation (double-entry) to keep ledgers balanced, quantized currency math to 2 decimal places, and audit-friendly persistence of every adjustment attempt.  
**Scale/Scope**: MVP supports ~500 manual adjustments/day per instance, with leaderboards submitting ~1k ledger transactions/minute during busy reconciliation windows; the pipeline must stay responsive while writing reconciliation entries immediately after adjustment. 

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: Adheres to SOLID principles; functions have clear purpose. (Assumed, requires verification during implementation).
- **Testing Standards**: Unit and integration tests required. TDD approach to be followed. (Assumed, requires verification during implementation).
- **User Experience Consistency**: (N/A for backend API feature, but relevant for API contract).
- **Performance Requirements**: Operations exceeding 200ms must be asynchronous or justified. (Assumed, requires verification during implementation).
- **Security Practices**: Adheres to OWASP, CWE, CERT. (Assumed, requires verification during implementation).
- **State Management and Workflow Integrity**: Clear lifecycles and state transitions for entities. (The `ManualBalanceAdjustment` and `AdjustmentTransaction` entities will require clear state definitions).

## Project Structure

### Documentation (this feature)

```text
specs/003-adjust-balance/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── api/
└── lib/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Option 1: Single project. The existing structure under `src/sdd_cash_manager/` appears to follow this pattern. We will likely add to `src/sdd_cash_manager/api/` for endpoints, `src/sdd_cash_manager/services/` for business logic, and `src/sdd_cash_manager/models/` for Pydantic/SQLAlchemy models. Tests will go into `tests/unit/` and `tests/integration/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| SQLite to PostgreSQL extensibility | Allows for future scaling and more robust data handling beyond MVP. | Direct SQLite integration is simpler for MVP but lacks inherent scalability and advanced features required for potential future growth. |
| Integration of python-accounting library | Provides robust financial logic essential for accurate balance adjustments and transaction creation. | Re-implementing complex accounting logic from scratch would be time-consuming, error-prone, and deviate from the DRY principle. |
| FastAPI with SQLAlchemy/Pydantic | Standard, efficient, and well-supported stack for building Python APIs. | Using a less established framework or manual ORM mapping would increase complexity and maintenance overhead. |
