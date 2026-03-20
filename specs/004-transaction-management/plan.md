# Implementation Plan: Transaction Management

**Branch**: `004-transaction-management` | **Date**: 2026-03-20 | **Spec**: [specs/004-transaction-management/spec.md](spec.md)
**Input**: Feature specification from `/specs/004-transaction-management/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implementation focuses on three pillars: (1) enforce double-entry transaction creation for the ledger, (2) surface QuickFill templates derived from the most recent action/currency combinations, and (3) provide cleanup tools for duplicate transactions and account merges so balances stay reliable. The plan reuses the existing FastAPI/SQLAlchemy stack, taps into the established account hierarchy services, and adds admin workflows for template approvals and candidate resolution.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, SQLAlchemy, python-accounting, httpx, pytest, pytest-asyncio  
**Storage**: SQLite (disk-backed locally, in-memory for tests)  
**Testing**: `pytest tests/api` via httpx + pytest-asyncio, supplemented by `scripts/pre_commit_checks.sh` for lint/security gates  
**Target Platform**: Linux-based API service (CLI-friendly)  
**Project Type**: Web service / backend API  
**Performance Goals**: 1000 transactions per minute (≈16.7 TPS) target; account queries and balance propagation should stay below 100 ms p95  
**Constraints**: Maintain atomic double-entry, honor 5-level hierarchy max depth, and keep duplicate detection under ~3 seconds for datasets with 1k transactions  
**Scale/Scope**: Single-tenant deployment anticipating up to 1k active accounts and 10k historical transactions per user in this iteration

## Constitution Check

*GATE: All work must respect the SpecKit Constitution, especially:*  
- **Financial Data Accuracy (VII)**: Double-entry enforcement, duplicate safeguards, and merge tooling keep balances trustworthy.  
- **Security Practices (V)**: Admin-facing flows for template approvals and cleanup inherit the JWT-based RBAC guardrails and audit logs.  
- **State Management (VI)**: Snapshot-based duplicate detection and merge workflows provide predictable state transitions and logging.  

No constitution violations are introduced by this plan.

## Project Structure

### Documentation (this feature)

```text
specs/004-transaction-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── transaction-management.yaml
└── tasks.md          # created later via /speckit.tasks
```

### Source Code (repository root)

```text
src/sdd_cash_manager/
├── api/              # FastAPI endpoints (accounts, transactions)
├── services/         # Business logic (account_service, transaction_service)
├── models/           # SQLAlchemy entities
├── schemas/          # Pydantic DTOs
├── lib/              # Helpers (auth, encryption, logging)
└── core/             # Config and startup

tests/
├── api/              # httpx-based integration tests
├── integration/      # higher-level reconciliation flows
└── unit/             # model/service unit tests
```

**Structure Decision**: Continue leveraging the existing FastAPI + SQLAlchemy code under `src/sdd_cash_manager` and the API-focused test directories; no additional top-level projects are needed.
