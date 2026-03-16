# Implementation Plan: Adjust Balance Window

**Branch**: `003-adjust-balance` | **Date**: 2026-03-16 | **Spec**: `/workspaces/sdd-cash-manager/specs/003-adjust-balance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

The feature allows manual adjustment of account balances, creating an automated transaction for the difference, and ensuring visibility in reconciliation views. The implementation will use Python 3.11 with FastAPI, SQLAlchemy, Pydantic, and python-accounting, with SQLite as the initial database.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic, python-accounting  
**Storage**: SQLite (for MVP, extensible to PostgreSQL) - **NEEDS CLARIFICATION**: Strategy for database extensibility/migration.
**Testing**: pytest  
**Target Platform**: Linux server  
**Project Type**: Web Service/API  
**Performance Goals**: API responsiveness (general expectation, specific targets to be defined in Phase 1 if needed)  
**Constraints**: Standard web service constraints (to be defined in Phase 1 if needed)  
**Scale/Scope**: (to be defined in Phase 1 if needed)

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
