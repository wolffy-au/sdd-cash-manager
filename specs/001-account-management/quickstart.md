# Quickstart Guide: Account Management

This guide provides a quick start for setting up and interacting with the Account Management feature of the sdd-cash-manager system.

## Prerequisites

- Python 3.11 or higher
- `uv` package manager installed (`pip install --upgrade uv`)

## Project Setup

1. **Clone the repository**:

    ```bash
    git clone <repository_url>
    cd sdd-cash-manager
    ```

2. **Set up virtual environment and install dependencies**:

    ```bash
    uv venv create --python 3.11
    uv venv shell  # Activate the virtual environment
    uv sync --upgrade --all-groups
    ```

3. **Database Setup**:
    The system uses SQLite for the MVP. The database will be initialized upon the first run of the application. For production, consider PostgreSQL.

## Running the Application

The sdd-cash-manager is a FastAPI application. You can run it using `uvicorn` (which is typically installed as a dependency of FastAPI).

1. **Navigate to the `src` directory**:

    ```bash
    cd src
    ```

2. **Run the FastAPI application**:

    ```bash
    uvicorn sdd_cash_manager.main:app --reload
    ```

    *(Note: You might need to adjust `sdd_cash_manager.main:app` based on the actual entry point of the application.)*

## API Endpoints

The Account Management feature exposes the following API endpoints:

### Accounts

- **Create Account**: `POST /accounts`
  - **Request Body**: JSON payload defining account details (name, currency, types, initial balance, etc.).
  - **Response**: Created account object with its ID.
- **Get Accounts**: `GET /accounts`
  - **Response**: List of all accounts.
- **Get Account by ID**: `GET /accounts/{id}`
  - **Response**: Specific account object.
- **Update Account**: `PUT /accounts/{id}`
  - **Request Body**: JSON payload with updated account details.
  - **Response**: Updated account object.
- **Delete Account**: `DELETE /accounts/{id}`
  - **Response**: Success message or status code.
- **Search Accounts**: `GET /accounts/search?name={account_name}`
  - **Response**: List of accounts matching the partial name (case-insensitive).
- **Adjust Balance**: `POST /accounts/{id}/adjust_balance`
  - **Request Body**: JSON payload with adjustment amount, reason, and target date.
  - **Response**: Confirmation of adjustment and updated account state.

## Further Information

For more detailed information on development, testing, and architecture, please refer to:

- `TECHNICAL.md`
- `.specify/memory/constitution.md`
- `PROJECT_CONSTITUTION.md`
- `PROJECT_SPECIFICATION.md`
- `NONFUNCTIONALS.md`

## Next Steps

- Proceed to Phase 2: Design & Contracts.
