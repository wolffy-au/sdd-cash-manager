# Quickstart: Transaction Management Feature

1. **Start the API** (default FastAPI local server):
   ```bash
   uv run uvicorn src.main:app --reload
   ```
2. **Run the existing test suite to verify this feature**:
   ```bash
   pytest tests/api -k "transaction" -v
   ```
3. **Seed data for QuickFill**: use `tests/api/fixtures.seeded_accounts` to create accounts and run a few sample transactions via `POST /transactions` with different `action` values.
4. **Trigger duplicate detection manually**:
   ```bash
   uv run python -m scripts.run_duplicate_detection
   ```
   (This script will scan accounts/groups and write candidates to `build/duplicates.json`.)
5. **Run merge scenario**: issue `POST /accounts/{id}/merge` with the `target_account_id` of the desired canonical account and verify balances through `GET /accounts/{target_account_id}`.
