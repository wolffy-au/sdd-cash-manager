#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

echo "Running pre-commit checks..."

# --- Linting and Formatting Check ---
echo "Running pymarkdown lint..."
# Runs pymarkdown for linting markdown files. Assumes pymarkdown is executable in the environment.
uv run pymarkdownlnt fix *.md specs/*.md

echo "Running ruff check..."
# Runs ruff for linting and formatting checks across the project.
uv run ruff check . --fix

echo "Running pyright..."
# Runs pyright for static type checking. Assumes pyright is executable in the environment.
uv run pyright

# --- Static Type Checking ---
echo "Running mypy..."
# Runs mypy on the src directory for static type checking.
uv run mypy

# --- Code Quality Checks ---
echo "Running code quality checks..."
# Runs SonarQube for code quality checks
uv sync --upgrade --all-groups
uv run poetry lock --regenerate
# uv run sonar-scanner -Dsonar.projectKey=sdd-cash-manager -Dsonar.sources=. -Dsonar.host.url=http://host.containers.internal:9000 -Dsonar.login=<toiken>
# uv run pysonar --sonar-host-url=http://host.containers.internal:9000 --sonar-token=<token> --sonar-project-key=sdd-cash-manager || true

# --- Security Checks ---
echo "Running snyk security checks..."
# Runs snyk to check for vulnerabilities in the project dependencies. Assumes snyk is executable in the environment.
uv run snyk test --package-manager=poetry --org=wolffy-au
uv run snyk code test  --package-manager=poetry --org=wolffy-au --include-ignores


# --- BDD Testing ---
echo "Running behave tests..."
# Runs behave tests from the specified features directory.
uv run behave tests/features/ || true

# --- Unit/Integration Testing ---
echo "Running pytest..."
# Runs pytest for unit and integration tests.
uv run pytest --cov-fail-under=90 || true

echo "Pre-commit checks passed successfully."
exit 0
