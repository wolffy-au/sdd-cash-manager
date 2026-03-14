# Quickstart: Running the API Pytest Suite

1. **Prepare the environment**
   - Activate your virtualenv (e.g., `source .venv/bin/activate`).
   - Install project deps if needed: `pip install -r requirements.txt` or rely on `uv` tooling already configured.
   - Ensure the local API is running (`uvicorn src.main:app --reload`) and reachable at `http://127.0.0.1:8000`.

2. **Set required environment variables**
   - `SDD_CASH_MANAGER_SECURITY_ENABLED=true` (enforce JWT auth during tests).
   - `SDD_CASH_MANAGER_JWT_SECRET=your_test_secret` and `SDD_CASH_MANAGER_JWT_ALGORITHM=HS256` (match what the fixtures expect for token creation).
   - Optionally override `SDD_CASH_MANAGER_DATABASE_URL` if you want tests to run against a different DB.

3. **Run the pytest module**

   ```bash
   pytest tests/api
   ```

   Tests use httpx clients, seed deterministic accounts, and clean up after each scenario.
   The fixtures enforce deterministic connect/read/write httpx timeouts so slow or hung servers surface as failures (FR-007).

4. **Interpret results**
   - Passing suite: all acceptance criteria (account creation, hierarchy balance, validation errors) verified.
   - Failing test: inspect the httpx response payload traced by pytest logs; failure indicates regression in the corresponding endpoint or fixture setup.

5. **Optional**
   - To reproduce specific scenarios, invoke individual tests with `pytest tests/api/test_accounts.py::test_xyz`.
   - Use `-k` filters to run subsets (e.g., `pytest tests/api -k balance`).

## Current suite files

Reference the key test modules when contributing: `tests/api/conftest.py`, `tests/api/test_accounts.py`, and the supporting helpers under `tests/api/`. No additional files are required for the API regression suite at this time.
