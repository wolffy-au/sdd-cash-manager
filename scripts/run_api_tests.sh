#!/usr/bin/env bash
set -euo pipefail

# Ensure deterministic JWT/security configuration when invoking the suite manually.
: "${SDD_CASH_MANAGER_SECURITY_ENABLED:=true}"
: "${SDD_CASH_MANAGER_JWT_SECRET:=sdd-test-secret-32-bytes-long-tt}"
: "${SDD_CASH_MANAGER_JWT_ALGORITHM:=HS256}"

echo "Running API regression suite (tests/api) with pytest..."

# Compose the base pytest command. Prefer `poetry run` when available so `uv.lock` tooling is respected.
if command -v poetry >/dev/null 2>&1; then
  PYTEST_BASE=("uv" "run" "pytest")
else
  PYTEST_BASE=("pytest")
fi

PYTEST_ARGS=("tests/api" "--maxfail=1" "--log-cli-level=INFO" "--durations=5" "-o" "addopts=--verbose --junitxml=build/unit-tests.xml")

RUN_CMD=("${PYTEST_BASE[@]}" "${PYTEST_ARGS[@]}")

# Limit the suite runtime to 5 minutes to catch stuck requests early.
if command -v timeout >/dev/null 2>&1; then
  timeout 300 "${RUN_CMD[@]}"
else
  "${RUN_CMD[@]}"
fi
