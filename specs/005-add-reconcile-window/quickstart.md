# Quickstart: Reconcile Window

1. **Prepare the environment.** Ensure Python 3.12 is active and install dependencies via `pip install -r requirements.txt` or `poetry install`. The project already uses FastAPI + SQLAlchemy, so the current dependency files cover the reconciliation modules.
2. **Configure JWT/security.** Export the values noted in `tests/api/README.md` (`SDD_CASH_MANAGER_SECURITY_ENABLED=true`, `SDD_CASH_MANAGER_JWT_SECRET`, `SDD_CASH_MANAGER_JWT_ALGORITHM`) so the reconciliation endpoints authenticate like the rest of the API.
3. **Target the reconciliation tests.** Run the focused suite with:
   ```bash
   pytest tests/api/test_transactions.py -k reconcile_window -v
   ```
   This exercise covers the zero-difference session, the filtered unreconciled payload, and the difference-insight metadata (`difference_status`, `remaining_uncleared`, guidance text) so you can validate both balanced and outstanding cases.
4. **Exercise the entire API surface.** Run `scripts/run_api_tests.sh` (the same script invoked by the pre-commit hook) to smoke-test every FastAPI route, capture structured logs, and ensure the reconciliation helpers coexist with the rest of the suite.
5. **Review contracts and docs.** Keep `specs/005-add-reconcile-window/contracts/reconcile.yaml` open; it defines `/reconciliation/sessions`, `/reconciliation/sessions/unreconciled`, and `/reconciliation/sessions/{session_id}/transactions` along with the enriched `DifferenceResponse` fields that feed the UI guidance text.
6. **Reference the endpoints in UI documentation.** When describing the Reconcile Window, highlight the three reconciliation endpoints so contributors can trace how selecting UNCLEARED transactions updates `DifferenceResponse` to zero (or surfaces `difference_status != balanced` when the discrepancy remains).
