#!/usr/bin/env bash
set -euo pipefail

# Ensure deterministic JWT/security configuration when invoking the suite manually.
: "${SDD_CASH_MANAGER_SECURITY_ENABLED:=true}"
: "${SDD_CASH_MANAGER_JWT_SECRET:=sdd-test-secret-32-bytes-long-tt}"
: "${SDD_CASH_MANAGER_JWT_ALGORITHM:=HS256}"

echo "Running API regression suite (tests/api) with pytest..."

# Compose the base pytest command. Prefer `uv run` when available so `uv.lock` tooling is respected.
if command -v uv >/dev/null 2>&1; then
  PYTEST_CMD="uv run pytest"
else
  PYTEST_CMD="pytest"
fi

RUN_CMD="${PYTEST_CMD} tests/api --maxfail=1 --log-cli-level=INFO --durations=5"

# Limit the suite runtime to 5 minutes to catch stuck requests early.
if command -v timeout >/dev/null 2>&1; then
  timeout 300 $RUN_CMD
else
  $RUN_CMD
fi
