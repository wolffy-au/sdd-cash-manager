# Quickstart: Reconcile Window

1. **Prepare the environment.** Ensure Python 3.12 is active and install dependencies via `pip install -r requirements.txt` or `poetry install`. The project already uses FastAPI + SQLAlchemy, so the current dependency files cover the reconciliation modules.
2. **Configure JWT/security.** Export the values noted in `tests/api/README.md` (`SDD_CASH_MANAGER_SECURITY_ENABLED=true`, `SDD_CASH_MANAGER_JWT_SECRET`, `SDD_CASH_MANAGER_JWT_ALGORITHM`) so the reconciliation endpoints authenticate like the rest of the API.
3. **Target the reconciliation tests.** Run the focused suite with:
   ```bash
   pytest tests/api/test_transactions.py -k reconcile_window -v
   ```
   This includes the zero-difference flow, the filtered unreconciled payload, and the new difference insight metadata.
4. **Verify the full API surface.** After landing the reconciliation routes, run `scripts/run_api_tests.sh` (the same script invoked by the pre-commit hook) to exercise the entire FastAPI suite with coverage and confirm no regressions.
5. **Review contracts and models.** Keep `specs/005-add-reconcile-window/contracts/reconcile.yaml` handy; it defines the `/reconciliation/sessions` endpoints and the `DifferenceResponse` payload used by the UI.
6. **Reference the new endpoints in docs.** Mention `/reconciliation/sessions`, `/reconciliation/sessions/unreconciled`, and `/reconciliation/sessions/{session_id}/transactions` whenever you describe the reconciliation workflow so contributors can connect the UI behavior with the backend validation.
