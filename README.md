
# sdd-cash-manager Development Setup

This document outlines the steps to set up the development environment for the sdd-cash-manager project.

## Prerequisites

- Python 3.11
- pip
- virtualenv (or equivalent)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd sdd-cash-manager
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Upgrade pip:**
    ```bash
    pip install --upgrade pip
    ```

4.  **Install core dependencies:**
    ```bash
    pip install fastapi uvicorn sqlalchemy psycopg2-binary python-accounting pydantic
    ```

5.  **Configure Database:**
    The project is configured to use SQLite for development purposes. The database connection string is defined in `src/core/config.py`. For production, a PostgreSQL database will be used with the `psycopg2-binary` driver.

    *Note: Ensure you have the necessary database drivers installed if switching from SQLite.*

6.  **Run Tests:**
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
