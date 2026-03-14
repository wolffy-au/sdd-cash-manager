# API Pytest Suite

This directory holds httpx-based pytest modules that exercise the running `uvicorn src.main:app` API, mimicking Postman coverage with code. Follow the quickstart steps documented in `specs/002-add-api-pytests/quickstart.md`:

1. Activate your virtual environment and install project dependencies.
2. Set `SDD_CASH_MANAGER_SECURITY_ENABLED=true`, `SDD_CASH_MANAGER_JWT_SECRET`, and `SDD_CASH_MANAGER_JWT_ALGORITHM` before running tests.
3. Start the API (`uvicorn src.main:app --reload`).
4. Execute `pytest tests/api` to run the regression suite. Each test seeds deterministic accounts, posts transactions, or verifies validation errors with httpx clients.

Use `pytest -k <pattern>` to run subsets (e.g., `-k balance`), and refer back to this file for environment hygiene.
