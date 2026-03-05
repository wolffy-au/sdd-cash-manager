# Quickstart Guide: Account Management

This guide provides the steps to set up and run the Account Management API locally.

## Prerequisites

*   **Python 3.11**: Ensure you have Python 3.11 or later installed.
*   **pip**: Python's package installer.
*   **Git**: For cloning the repository.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd sdd-cash-manager
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *(On Windows, use `.venv\Scripts\activate`)*

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt  # Assumes a requirements.txt exists, or use pyproject.toml
    # Or, if using Poetry/other package managers:
    # poetry install
    # pip install -e . # For editable install if src/ is the main package
    ```
    *Based on the context, `pyproject.toml` is present, so `pip install -e .` might be appropriate for an editable install.*
    ```bash
    pip install -e .
    ```

4.  **Database Setup (for MVP using SQLite)**:
    The application is configured to use SQLite for the MVP. Database schema initialization may be handled by ORM migrations (e.g., Alembic) or automatically on first run, depending on implementation. If using Alembic, you would typically run:
    ```bash
    alembic upgrade head
    ```
    *(Note: Specific migration commands depend on the chosen ORM setup.)*

## Running the API

The application is built as an API using FastAPI. The server can typically be run using `uvicorn`.

1.  **Run the development server**:
    ```bash
    uvicorn src.sdd_cash_manager.api.main:app --reload
    ```
    *(Note: The exact entry point `src.sdd_cash_manager.api.main:app` will depend on the project's final structure. Adjust if necessary.)*

    The API will be available at `http://localhost:8000`.

## API Documentation

You can access the automatically generated interactive API documentation (Swagger UI) at:
`http://localhost:8000/docs`

## Next Steps

-   Explore the API documentation to understand available endpoints.
-   Refer to `specs/001-account-management/spec.md` for detailed feature requirements.
-   Consult `specs/001-account-management/plan.md` for implementation details.
