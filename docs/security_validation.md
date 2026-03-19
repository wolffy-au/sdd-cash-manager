# Security and Validation Practices

This document records the end-to-end validation and security controls applied to the Account Management feature as part of Phase 6 polish.

## Input Validation

- Pydantic models (`AccountCreatePayload`, `AccountUpdatePayload`, `BalanceAdjustmentPayload`) enforce:
  - Strict string constraints (length, allowed characters, control-character filtering).
  - ISO 4217 currency codes with explicit `CurrencyField` helpers.
  - Enumerated `AccountingCategory`, `BankingProductType`, and `ActionType` values, raising `HTTPException` when unsupported values are supplied.
  - Decimal quantization and rounding via `_quantize_amount` to avoid floating-point drift.
- `AccountService` re-validates enums and currencies before persistence and squeezes numeric inputs through `quantize_currency` (see `src/sdd_cash_manager/lib/utils.py`). Hidden/placeholder filters also guard batch operations.

## Security Guards

- Authentication and RBAC (Roles: `viewer`, `operator`, `admin`) live in `src/sdd_cash_manager/lib/auth.py`. FastAPI endpoints invoke `require_role` so that all CRUD and adjustment operations only succeed when JWT authentication is enabled (`SDD_CASH_MANAGER_SECURITY_ENABLED=true`). The default is `false` to keep the dev/test suites green.
- JWTs are signed with `SDD_CASH_MANAGER_JWT_SECRET`/`SDD_CASH_MANAGER_JWT_ALGORITHM`, and helper `create_access_token` makes it trivial to generate tokens for integration tests or deploying clients.
- Endpoints log the calling subject when provided (`logger.info(... user=%s)`) to provide an audit trail.

## Sensitive Data Handling

- Account `notes` are encrypted before being persisted when `AccountService` operates against a database-backed session (`_use_db`). Encryption uses Fernet with a SHA-256-derived key from `SDD_CASH_MANAGER_ENCRYPTION_KEY` (see `src/sdd_cash_manager/lib/encryption.py`). API responses decrypt notes via `AccountService.decrypt_notes` so clients still see plaintext.
- The database layer logs session lifecycle events (opening/closing) and table creation, making it easier to correlate suspicious activity with specific services.

## Observability & Benchmarks

- Structured logs are enabled through `src/sdd_cash_manager/lib/logging_config.py`, honoring `SDD_CASH_MANAGER_LOG_LEVEL`. Every request path logs context and outcomes, including validation failures and unexpected errors.
- The benchmarking script (`scripts/benchmark_account_workflow.py`) exercises account creation, balance adjustments, and hierarchy queries. Running it before/after query tuning or schema changes shows whether latency targets remain acceptable.

## Manual Adjustment Auditing & Tracing

- The manual adjustment endpoint logs `SecurityEvent.SENSITIVE_DATA_ACCESS` (or `SecurityEvent.SYSTEM_ALERT` when errors occur) to `security.log`, capturing the requesting user, account ID, duration in milliseconds, and the difference between the submitted and running balances.
- Adjustments trace the start-to-finish flow through `ManualBalanceAdjustmentService`, which records both zero-difference and completed adjustments before creating reconciliation entries, so auditors can see the full lineage without replaying double-entry rows.
- Performance monitoring relies on the duration metadata emitted with each adjustment audit record; if sustained spikes appear, the service is instrumented to highlight the combination of validation, transaction posting, and reconciliation persistence that contribute to the latency budget.
