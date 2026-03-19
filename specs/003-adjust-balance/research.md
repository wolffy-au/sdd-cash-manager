# Research: Adjust Balance Window

This research brief captures the resolved decisions and working practices that guide the existing implementation of the manual balance adjustment feature.

## Technical Decisions

### Storage & Migration Strategy
- **Decision**: Keep SQLite as the default for local development and automated tests while maintaining Alembic migration scripts so the same models can target PostgreSQL in production.
- **Rationale**: SQLite keeps the iteration cycle fast and requires no external infrastructure, while Alembic lets us promote the schema to PostgreSQL without hand-translating fields or losing double-entry invariants. The database layer is already parameterized by `DATABASE_URL`, so switching to Postgres only requires pointing the environment at a new DSN.
- **Alternatives Considered**: Always running Postgres locally (adds friction for contributors), or committing to SQLite forever (limits scalability and tooling such as CRDB-specific features). Both were rejected in favor of the hybrid approach.

### Performance Goals
- **Decision**: Target a median response time of <200 ms (95th percentile <250 ms) for balance-adjustment requests even when servicing ~100 concurrent adjustments; reconciliation entries must be persisted before responding.
- **Rationale**: Manual balance adjustments are often used during time-boxed reconciliation windows, so latency directly impacts accountants' work. The current service stack (FastAPI + SQLAlchemy + synchronous DB writes) comfortably achieves this when using connection pooling and quantized decimals.
- **Alternatives Considered**: Queueing adjustments for asynchronous processing would complicate traceability and visibility, so we opted for immediate persistence combined with tight validation and double-entry enforcement.

### Security, Audit, and Compliance Constraints
- **Decision**: Enforce JWT authentication with RBAC (`Role.OPERATOR` for adjustments) and log every adjustment attempt via `log_security_event`; always persist `ManualBalanceAdjustment` records even when no ledger transaction is created.
- **Rationale**: Audit trails must capture intent, status, and user identity for compliance. The current libs (`pyjwt`, FastAPI dependencies) provide this with minimal custom code.
- **Alternatives Considered**: Allowing unauthenticated adjustments or skipping zero-difference records would break traceability.

### Scale & Scope
- **Decision**: Design the feature to handle roughly 500 manual adjustments per day per instance, plus 1,000 ledger transactions per minute during peak reconciliation activity.
- **Rationale**: These numbers align with expected workloads for a mid-sized finance team and leave headroom for scaling the transaction service without architectural changes.
- **Alternatives Considered**: Building for tens of thousands of adjustments/day would require sharding and async queues, which is premature for the MVP.

## Technology Best Practices

### FastAPI + SQLAlchemy + python-accounting Integration
- **Decision**: Centralize balance adjustments within `ManualBalanceAdjustmentService`, which calls `TransactionService` to enforce double-entry accounting; the service sets the balancing account (`BALANCING_ACCOUNT_ID`) and quantizes currencies before updating the account's `available_balance`.
- **Rationale**: Encapsulating adjustments in one service ensures ledger invariants are satisfied, reconciliation entries are created immediately via `ReconciliationService`, and the `AdjustmentTransaction` record can be referenced by subsequently generated reconciliation entries or audit logs.
- **Alternatives Considered**: Updating balances directly in the API layer or bypassing `python-accounting` would duplicate logic and make tests harder to reason about.

### Testing & Automation Patterns
- **Decision**: Use pytest with pytest-asyncio and pytest-mock for unit/integration coverage, httpx/AsyncClient for API-level tests, and behave for behavior checks when they are available; rely on fixtures for seeded accounts and cleanup.
- **Rationale**: pytest/AsyncClient provide reliable, fast tests that exercise the FastAPI app in-process. The newly added integration tests (`tests/integration/test_adjustment_api.py`, `tests/integration/test_reconciliation_api.py`, `tests/integration/test_adjustment_reconciliation_flow.py`) demonstrate both positive and edge case flows.
- **Alternatives Considered**: Spinning up a real server for tests was rejected because it slows the feedback loop; mocking at too high a level hides integration issues.

### Documentation & Tooling Consistency
- **Decision**: Capture workflows in `specs/003-adjust-balance/quickstart.md`, and keep the plan/tasks aligned with speckit templates; use the `scripts/pre_commit_checks.sh` pipeline for linting, typing, and tests before merging.
- **Rationale**: Consistent documentation and automated checks help future contributors understand the architecture and ensure the code remains healthy.
- **Alternatives Considered**: Skipping quickstart or manual linting checks would increase onboarding time and risk regressions.

## Operational Observability & Tracing

- **Decision**: Emit structured `SecurityEvent` entries for every manual adjustment, including milliseconds-to-complete metrics and audit metadata (user, account, target balance, difference, status). Zero-difference adjustments still produce `SecurityEvent.SENSITIVE_DATA_ACCESS` entries so downstream reporting and SIEM consumers recognize the intent even without ledger mutations.
- **Rationale**: Having a single, structured log (and the `security.log` file) that couples security, performance, and reconciliation metadata keeps compliance reviewers focused while avoiding the complexity of full distributed tracing.
- **Alternatives Considered**: Introducing OpenTelemetry or custom tracing libraries was rejected because they would add dependencies and increase the workload of audit defenders; the existing logging plus the new security-event payload meets the audited requirements.

## Constitutional & Standards Review

- **Decision**: Evaluate the implementation against the canonical guidance (`TECHNICAL.md`, `GEMINI.md`, `.specify/memory/constitution.md`, `NONFUNCTIONALS.md`, and `PROJECT_CONSTITUTION.md`) before closing the feature, ensuring every new behavior (security logging, RBAC enforcement, instrumentation, and test coverage) aligns with the documented standards.
- **Rationale**: Documenting this review in the research brief provides the explicit traceability auditors expect and marks the feature as consistent with the project’s coding, security, and performance expectations.
- **Alternatives Considered**: Leaving the review implicit risks leaving compliance gaps; the explicit mention ensures future maintainers know where the standard alignment was verified.

## PostgreSQL Migration Strategy

- **Decision**: Keep SQLite as the default for local development while allowing `SDD_CASH_MANAGER_DATABASE_URL` to point at PostgreSQL for production. Maintain Alembic scripts, test them against both engines, and avoid SQLite-only SQL expansions.
- **Plan**:
  1. Make schema changes via Alembic revisions and run the migration against Postgres in CI (`uv run alembic upgrade head --sql` for dry runs or `uv run alembic upgrade head` with a Postgres sandbox).
  2. Validate that `Numeric(18, 2)` columns, UUID PKs, and foreign keys behave identically across SQLite and Postgres (adjust column defaults if Postgres requires explicit `server_default` clauses).
  3. Run the adjustment + reconciliation integration suites (especially `tests/integration/test_adjustment_reconciliation_flow.py`) against a Postgres container or service to confirm concurrency, locking, and reconciliation entries persist as expected.
  4. Update deployment docs so operations teams set `SDD_CASH_MANAGER_DATABASE_URL` to the targeted Postgres DSN and include `uv run alembic upgrade head` as part of deployments.
- **Alternatives Considered**: Shipping the feature on SQLite only would simplify dev flows but leave production deployments underprepared for Postgres’s stricter constraints, so the hybrid approach is the safer compromise.
