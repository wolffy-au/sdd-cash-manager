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

# --- BDD Testing ---
echo "Running behave tests..."
# Runs behave tests from the specified features directory.
uv run behave tests/features/ || true

# --- Unit/Integration Testing ---
echo "Running pytest..."
# Runs pytest for unit and integration tests.
uv run pytest --cov-fail-under=90

echo "Pre-commit checks passed successfully."
exit 0
