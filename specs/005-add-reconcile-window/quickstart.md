# Quickstart: Reconcile Window

1. **Prepare the environment.** Ensure Python 3.12 is active and install dependencies (for example via `pip install -r requirements.txt`). The project already uses FastAPI + SQLAlchemy, so existing dependency files will cover new modules.
2. **Set the JWT + security variables.** The API tests expect `SDD_CASH_MANAGER_SECURITY_ENABLED=true`, `SDD_CASH_MANAGER_JWT_SECRET`, and `SDD_CASH_MANAGER_JWT_ALGORITHM` to be set as described in `tests/api/README.md`.
3. **Focus on reconciliation tests.** Run the targeted suite with:  
   ```bash
   pytest tests/api/test_transactions.py::test_reconcile_window_flow -v
   ```
   This file will be expanded to cover the new reconciliation endpoints once implemented.
4. **Run the script for the full API surface.** Use `scripts/run_api_tests.sh` to verify the entire FastAPI surface works after adding the reconciliation endpoints and services.
5. **Review contracts.** Reference `specs/005-add-reconcile-window/contracts/reconcile.yaml` when implementing the new endpoints to keep request/response shapes stable.
6. **Document findings.** Update this quickstart file with any new environment tweaks or frequently required commands related to reconciliation.
