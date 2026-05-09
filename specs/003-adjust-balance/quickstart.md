# Quickstart: Adjust Balance Window

This guide helps contributors explore the manual balance adjustment feature, run the relevant tests, and validate reconciliation visibility.

## Prerequisites
1. Install Python 3.12 and ensure the interpreter is available as `python`.  
2. Install `uv` via `pip install --user uv` (used for dependency management and running scripts).  
3. Ensure `uv` has synced the project dependencies (see the Setup section).

## Setup
1. Create or activate the project virtual environment (e.g., `python -m venv .venv && source .venv/bin/activate`).  
2. From the repository root, bootstrap dependencies:
   ```bash
   poetry sync --upgrade --all-groups
   ```
3. The feature prefers SQLite for local development. No additional DB setup is required unless you want to point `DATABASE_URL` at PostgreSQL.

## Running the API
Start the FastAPI server to exercise the endpoints manually or with HTTP clients:
```bash
poetry run uvicorn sdd_cash_manager.main:app --reload --host 0.0.0.0 --port 8000
```
- Authenticate using a JWT that conveys the `operator` role (see `tests/integration/test_adjustment_api.py` for an example of `create_access_token`).  
- POST `/accounts/{account_id}/adjust-balance` with a JSON payload containing `target_balance`, `effective_date`, and `submitted_by_user_id`.  
- GET `/accounts/{account_id}/reconciliation` to confirm the new reconciliation entry.

## Testing the Feature
Run the dedicated integration and unit tests that exercise manual adjustments and reconciliation persistence:
```bash
poetry run pytest tests/integration/test_adjustment_api.py tests/integration/test_reconciliation_api.py \
  tests/integration/test_adjustment_reconciliation_flow.py tests/unit/test_reconciliation.py tests/unit/test_auth_events.py
```
- These tests demonstrate sanctioned adjustments, zero-difference behavior, RBAC enforcement, and that reconciliation data reflects adjustments.
- Use `poetry run pytest --last-failed` during iteration to rerun only failing cases.

## Verification and Troubleshooting
- Use `scripts/pre_commit_checks.sh` to run formatting, linting, static typing, and the full test suite before shipping a change (this script already reruns the commands above).  
- If a manual adjustment does not create a reconciliation entry, confirm that the `ManualBalanceAdjustmentService` persisted `AdjustmentTransaction`/`ManualBalanceAdjustment` rows and that `ReconciliationService.create_reconciliation_entry_from_transaction` executed without rolling back.  
- For JWT configuration, verify `SDD_CASH_MANAGER_JWT_SECRET` and `SDD_CASH_MANAGER_JWT_ALGORITHM` align between the test helpers (`tests/integration/test_accounts.py`) and the app config (`src/sdd_cash_manager/core/config.py`).
- Audit the adjustment via `security.log`; each entry captures the requesting user, account, difference, status, and duration so you can spot slow requests or unauthorized attempts.  
- To test the PostgreSQL-ready path, point `SDD_CASH_MANAGER_DATABASE_URL` at a Postgres instance and rerun the adjustment & reconciliation suites (`poetry run pytest tests/integration/test_adjustment_reconciliation_flow.py`), ensuring Alembic migrations are up-to-date.
