# NFR Verification: Account Management

This reference captures how the Account Management feature satisfies the remaining non-functional requirements (reliability, scalability, accuracy) and documents the concrete verification steps we run before closing those tasks.

## Reliability (T052, T053, T054, T058)

| Target | Measurement | Verification |
|--------|-------------|--------------|
| 99.9% uptime | Health-check endpoint (`GET /health`) | Run `scripts/check-health.sh` against the live service (five consecutive `200` responses by default). Automate this check in CI or a monitoring job for each deployment to detect outages more than ~43 minutes/month.
| RTO < 4h / RPO 1h | Database snapshot & restore | Use `scripts/db-backup.sh` to snapshot `sdd_cash_manager.db`, then run `scripts/db-restore.sh /path/to/backup` to rehydrate the database and confirm the service can start within a few minutes. Document the latest successful backup filename in deployment runbooks so the recovery point is known.
| Logging & monitoring | Structured logs + human-readable console output | `src/sdd_cash_manager/lib/logging_config.py` configures every logger to emit the format in `SDD_CASH_MANAGER_LOG_FORMAT` (default `%(asctime)s - %(name)s - %(levelname)s - %(message)s`). Forwarding these logs to log aggregators (ELK, Splunk, etc.) unlocks alerting and failover coverage. Include the JSON health-check output in your monitoring dashboard to trigger alerts on failure.
| Reliability target (>99.9% uptime) | Automated smoke tests | Add `scripts/run_api_tests.sh` and `scripts/check-health.sh` to the deployment pipeline; document their success in release notes to prove reliability.

## Scalability (T055, T056)

- **High throughput target (T055):** Aim for 500+ RPS across critical account endpoints (POST `/accounts`, GET `/accounts`). Use `performance-tests/locustfile.py` by running `locust -f performance-tests/locustfile.py --host=http://127.0.0.1:8000 --headless -u 200 -r 20 --run-time 1m`. Inspect the generated HTML and CLI summary to confirm 500 RPS with acceptable latencies.
- **Scalability target (T056):** Support at least 1,000 concurrent account-oriented requests per minute. The same Locust scenario above can be extended: increase `-u` to 1000 and monitor for < 200ms p95 latency. Capture the summary in `build/locust-report.txt` for archival.

## Accuracy (T057)

- **Accuracy target:** Maintain a decimal error rate below 0.001% and absolute rounding control at the smallest currency denomination. All financial operations use `Decimal` with `ROUND_HALF_UP` (see `src/sdd_cash_manager/lib/utils.py` and `src/sdd_cash_manager/services/account_service.py`). Verification is provided by `tests/api/test_transactions.py::test_reconcile_window_zero_difference_flow`, which asserts that reconciling curated entries yields exactly zero difference even when rounding is required.
- **Verification command:** `pytest tests/api/test_transactions.py::test_reconcile_window_zero_difference_flow -k reconcile_window` ensures the difference between ledger entries stays at $0.00 across edge cases.

## Additional Notes

- Ship `scripts/check-health.sh`, `scripts/db-backup.sh`, and `scripts/db-restore.sh` with your deployment scripts so production operators can run them manually or in automation loops.
- Mention these verification commands in release notes whenever the reliability/scalability story is promoted.

