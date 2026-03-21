# sdd-cash-manager Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-20

## Active Technologies
- Python 3.12 (project targets >=3.10,<3.13 and Ruff is configured for py312). + FastAPI for the API surface, SQLAlchemy 2.0 for ORM/models, httpx/pytest/pytest-asyncio for testing, python-accounting utilities, and existing jwt/security helpers. (004-transaction-management)
- Ledger data persists via SQLAlchemy (SQLite for dev/tests, Postgres in production). (004-transaction-management)

- Python 3.12 + FastAPI, SQLAlchemy, python-accounting, httpx, pytest, pytest-asyncio (004-transaction-management)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 004-transaction-management: Added Python 3.12 (project targets >=3.10,<3.13 and Ruff is configured for py312). + FastAPI for the API surface, SQLAlchemy 2.0 for ORM/models, httpx/pytest/pytest-asyncio for testing, python-accounting utilities, and existing jwt/security helpers.

- 004-transaction-management: Added Python 3.12 + FastAPI, SQLAlchemy, python-accounting, httpx, pytest, pytest-asyncio

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
