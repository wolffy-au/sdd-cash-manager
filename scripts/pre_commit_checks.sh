#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -euo pipefail

echo "Running pre-commit checks..."

# --- Static Type Checking ---
echo "Running mypy..."
# Runs mypy on the src directory for static type checking.
poetry run mypy src/

echo "Running pyright..."
# Runs pyright for static type checking. Assumes pyright is executable in the environment.
poetry run pyright

# --- Linting and Formatting Check ---
echo "Running ruff check..."
# Runs ruff for linting and formatting checks across the project.
poetry run ruff check .

# --- BDD Testing ---
echo "Running behave tests..."
# Runs behave tests from the specified features directory.
poetry run behave tests/features/

# --- Unit/Integration Testing ---
echo "Running pytest..."
# Runs pytest for unit and integration tests.
poetry run pytest

echo "Pre-commit checks passed successfully."
exit 0
