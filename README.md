
# sdd-cash-manager Development Setup

This document outlines the steps to set up the development environment for the sdd-cash-manager project.

## Prerequisites

- Python 3.11
- pip
- virtualenv (or equivalent)

## Installation

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd sdd-cash-manager
    ```

2. **Set up a virtual environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3. **Upgrade pip:**

    ```bash
    pip install --upgrade pip
    ```

4. **Install core dependencies:**

  ```bash
  pip install fastapi uvicorn sqlalchemy psycopg2-binary python-accounting pydantic
  ```

## Configuration

The project uses `pydantic`-backed settings to drive environment-specific values.
You can override the defaults by exporting these variables before running the app:

- `SDD_CASH_MANAGER_DATABASE_URL` – SQLAlchemy URL for the application's database (default: `sqlite:///./sdd_cash_manager.db`).
- `SDD_CASH_MANAGER_DATABASE_ECHO` – Enable SQLAlchemy logging when debugging (default `false`).
- `SDD_CASH_MANAGER_LOG_LEVEL` – Default log level consumed by the structured logger (`INFO`, `DEBUG`, etc.).
- `SDD_CASH_MANAGER_JWT_SECRET` and `SDD_CASH_MANAGER_JWT_ALGORITHM` – Placeholders for the future JWT authentication layer.
- `SDD_CASH_MANAGER_ENCRYPTION_KEY` – Symmetric key used when encrypting sensitive account metadata at rest.
- `SDD_CASH_MANAGER_SECURITY_ENABLED` – Toggle JWT/RBAC enforcement (`false` by default for local development).

Settings are automatically loaded from a `.env` file in the project root when present.

1. **Configure Database:**
    The project is configured to use SQLite for development purposes. The database connection string is defined in `src/core/config.py`. For production, a PostgreSQL database will be used with the `psycopg2-binary` driver.

    *Note: Ensure you have the necessary database drivers installed if switching from SQLite.*

2. **Run Tests:**
    All tests can be run using pytest:

    ```bash
    pytest
    ```

## Running the Application

The application can be run using uvicorn:

```bash
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## Benchmarking

Use `python scripts/benchmark_account_workflow.py` to gather average timings for account creation, balance adjustments, and hierarchy queries. The script runs against an in-memory SQLite database and prints the per-operation latency so you can compare before/after tuning.
