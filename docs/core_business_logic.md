# Core Business Logic for Account Management

This document captures the essential flows that define the `001-account-management` feature and links them to validation, persistence, and testing artifacts.

## Account Lifecycle
- `src/sdd_cash_manager/api/accounts.py` orchestrates the HTTP surface, sanitizing inputs via `AccountCreatePayload`, `AccountUpdatePayload`, and helpers such as `_sanitize_search_term`, `_validate_name_value`, and `_ensure_parent_account_exists`.
- `AccountService` (`src/sdd_cash_manager/services/account_service.py`) owns creation, updates, hierarchical linkage, and balance snapshots. Each public method performs enum validation, quantizes currency via `lib/utils.py`, commits through SQLAlchemy sessions, and tracks history for debugging or auditing.
- The service emits snapshots (`AccountBalanceSnapshot`) so downstream observers can reconstruct historical balances during debugging or reporting.

## Double-Entry Transactions & Balance Adjustments
- `TransactionService` (`src/sdd_cash_manager/services/transaction_service.py`) enforces double-entry integrity with `_ensure_double_entry` and indexes entries per account. It owns transaction creation, status updates, and the balancing logic invoked by the `/accounts/{id}/adjust_balance` endpoint.
- API-level helpers assemble sanitized payloads, log each adjustment (`lib/logging_config.py`), and bubble user errors (e.g., `ValueError` when the target equals the current balance) as HTTP 400 responses with descriptive detail.

## Hierarchies & Aggregation
- Accounts may link to parents via `parent_account_id` in `src/sdd_cash_manager/models/account.py`, and `AccountService.get_all_accounts` applies optional `hidden`, `placeholder`, and search filters to present aggregated hierarchies. This method is also used by the API list endpoint when materializing responses.
- `AccountService.get_account_hierarchy_balance` computes the aggregate for an account plus descendants (using a recursive CTE when backed by the database and an in-memory walk otherwise), and `AccountResponse` now includes a `hierarchy_balance` field so clients can immediately consume parent-group totals without replaying entries.
- Hierarchical consistency is validated before deletions or updates so orphaned placeholders cannot be removed without clearing children first.

## Validation & Observability
- Input validation lives at multiple layers: FastAPI/Pydantic models guard shapes and character sets, while services re-validate enums and numeric precision through `AccountService._quantize_value`.
- Observability now includes structured logging from `lib/logging_config.py`, which reads `SDD_CASH_MANAGER_LOG_LEVEL` and is used across API handlers and database session scaffolding (`src/sdd_cash_manager/database.py`) to record lifecycle events.

## Testing & Coverage
- Unit tests such as `tests/unit/test_account_model.py`, `tests/unit/test_account_service.py`, `tests/unit/test_transaction_model.py`, and `tests/unit/test_transaction_service.py` exercise entity invariants and service behaviors.
- Integration tests (`tests/integration/test_account_api.py`) exercise the FastAPI router, verifying the JSON contract, filtering, and balance adjustment endpoint semantics.
- Running `pytest --cov=sdd_cash_manager --cov-report=term-missing` (already used in `scripts/pre_commit_checks.sh`) produces coverage reports in `build/coverage-reports` and ensures that the above flows remain covered. The current report (91.94%) is tracked as the baseline; the goal is to drive it toward 100% by adding guards/tests in the remaining Phase 6 tasks.

## Next Steps
- Extend the coverage signal to confirm core logic for JWT/RBAC, encryption, and security hardening once those modules exist.
- Use the structured logger and the coverage reports mentioned above to verify that every new rule added for Phase 6 (docstrings, validation, observability) gets an automated regression test alongside it.
