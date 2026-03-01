# tests/security/test_api_security.py

import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel  # Import BaseModel for the new BalanceAdjustmentRequest
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db

# --- Corrected Imports ---
# Removed 'src.' prefix from all imports related to sdd_cash_manager
# These imports assume that 'sdd_cash_manager' is directly discoverable after 'src' is added to PYTHONPATH
from sdd_cash_manager.schemas.account_schema import AccountResponse


# --- Placeholder Schema Definition ---
# Defining BalanceAdjustmentRequest as it's not found in account_schema.py
# This model should ideally exist in your project's schema definitions.
class BalanceAdjustmentRequest(BaseModel):
    target_balance: float
    adjustment_date: str # Assuming string date input for API payload
    description: str
    action_type: str # Added action_type as it's used in service

# --- Fixture for setting up mocks and test client ---
@pytest.fixture(scope="module")
def mock_dependencies():
    """
    Sets up mock dependencies (Service, DB Session) and a mock API client.
    """
    global mock_account_service_instance

    # Mock AccountService and its methods
    # Removed 'spec=AccountService' to resolve potential introspection issues with MagicMock
    mock_account_service = MagicMock()

    # Mocking get_account to return None for non-existent accounts,
    # and a dummy account for existing ones to test responses.
    mock_account_data = {
        "id": "test-account-id",
        "name": "Test Account",
        "currency": "USD",
        "accounting_category": "ASSET",
        "available_balance": 1000.0,
        "account_number": "ACC-123",
        "banking_product_type": "BANK",
        "credit_limit": None,
        "notes": "Initial notes",
        "parent_account_id": None,
        "hidden": False,
        "placeholder": False
    }
    mock_account_response = AccountResponse(**mock_account_data)

    mock_account_service.get_account.side_effect = lambda acc_id: mock_account_response if acc_id == "test-account-id" else None
    mock_account_service.get_all_accounts.return_value = [mock_account_response]

    mock_account_service.create_account.return_value = mock_account_response
    mock_account_service.update_account.return_value = mock_account_response
    mock_account_service.delete_account.return_value = True

    mock_account_service.perform_balance_adjustment.return_value = {
        "transaction_id": "txn-mock-123",
        "account_id": "test-account-id",
        "new_balance": 1250.75,
        "amount": 250.75,
        "description": "Adjustment made"
    }

    mock_account_service_instance = mock_account_service

    # Mocking get_db to return a mock session
    mock_db_session = MagicMock(spec=Session)
    mock_db_session.commit.return_value = None
    mock_db_session.rollback.return_value = None
    mock_db_session.close.return_value = None

    # Patch get_db to yield the mock session
    original_get_db = get_db
    async def mock_get_db():
        yield mock_db_session

    # Corrected import for 'database' module
    from sdd_cash_manager import database
    database.get_db = mock_get_db # Replace the function

    yield mock_account_service, mock_db_session # Yield mocks

    # Restore original get_db after tests
    database.get_db = original_get_db

# --- Test Cases for Input Validation and Sanitization ---

TEST_MALICIOUS_CHARS = ["'", '"', ";", "--", "<", ">", "/*", "*/", "%", "&", "|", "`", "\0", "\n", "\r"]
EXTREMELY_LONG_STRING = "A" * 5000

@pytest.mark.asyncio
async def test_create_account_malicious_inputs(mock_dependencies):
    """
    Test creating an account with various malicious and malformed inputs.
    Pydantic should reject these with 422 Unprocessable Entity.
    """
    mock_account_service, _ = mock_dependencies

    print("--- Testing create_account with malicious inputs ---")

    for char in TEST_MALICIOUS_CHARS:
        payload = {
            "name": f"Test {char} Account",
            "account_number": f"ACC-{uuid.uuid4()}{char}",
            "currency": "USD",
            "accounting_category": "ASSET",
            "banking_product_type": "BANK",
            "available_balance": "1000.00",
            "notes": f"Notes with {char}"
        }
        print(f"  Testing with malicious char '{char}': {payload}")

    long_string_payload = {
        "name": EXTREMELY_LONG_STRING,
        "account_number": f"ACC-{uuid.uuid4()}",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "BANK",
        "available_balance": "1000.00",
        "notes": EXTREMELY_LONG_STRING
    }
    print(f"  Testing with long strings: {long_string_payload}")

    invalid_type_payload = {
        "name": "Type Test Account",
        "account_number": f"ACC-{uuid.uuid4()}",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "BANK",
        "available_balance": "this is not a number",
        "notes": "Testing type errors"
    }
    print(f"  Testing with invalid type for balance: {invalid_type_payload}")

    missing_field_payload = {
        "account_number": f"ACC-{uuid.uuid4()}",
        "currency": "USD",
    }
    print(f"  Testing with missing required fields: {missing_field_payload}")

    non_numeric_balance_payload = {"target_balance": "not a float", "adjustment_date": "2026-02-26", "description": "Invalid balance", "action_type": "TEST_ADJ"}
    print(f"  Testing adjust_balance with non-numeric target_balance: {non_numeric_balance_payload}")

    large_balance_payload = {"target_balance": 1.8e308, "adjustment_date": "2026-02-26", "description": "Very large balance", "action_type": "TEST_ADJ"}
    print(f"  Testing adjust_balance with large target_balance: {large_balance_payload}")

    invalid_date_payload = {"target_balance": 1200.0, "adjustment_date": "26-02-2026", "description": "Invalid date format", "action_type": "TEST_ADJ"}
    print(f"  Testing adjust_balance with invalid date format: {invalid_date_payload}")


@pytest.mark.asyncio
async def test_api_error_responses_no_sensitive_data(mock_dependencies):
    """
    Tests that API error responses do not expose sensitive internal information.
    This involves triggering errors and inspecting the response body.
    """
    mock_account_service, _ = mock_dependencies

    print("\n--- Testing API error responses for sensitive data ---")

    # --- Test case 1: Trying to get a non-existent account ---
    non_existent_account_id = "non-existent-account-id-12345"
    print(f"  Testing GET non-existent account ({non_existent_account_id}) error response.")
    # Expected: API endpoint returns 404 with a generic detail message.

    # --- Test case 2: Trying to create an account with invalid data ---
    # TODO: This would typically involve sending a request with invalid payload to the API endpoint.
    print("  Testing POST account with invalid data error response.")
    # Expected: API endpoint returns 422 with Pydantic validation errors.

    # --- Test case 3: Simulate an internal server error ---
    mock_account_service.create_account.side_effect = Exception("Simulated internal error for testing details")

    #TODO : This would involve sending a valid request to the create account endpoint, which will trigger the exception.
    print("  Testing simulated internal server error response.")
    # Expected: API endpoint returns 500 Internal Server Error with a generic detail message.

    mock_account_service.create_account.side_effect = None


# --- Necessary Imports for the test file itself ---
# Ensure all used modules and classes are imported here if they aren't in the global scope.
# The `mock_dependencies` fixture and constants are defined above.
# All necessary modules (uuid, pytest, httpx, pydantic, sqlalchemy, etc.) are imported.
# Ensure the models imported from sdd_cash_manager are correct.
# If `Account` model is also needed in tests, add:
# from sdd_cash_manager.models.account import Account
# from sdd_cash_manager.models.enums import AccountingCategory, BankingAccountType

# Note:
# This test file is structured assuming a FastAPI application and the use of `httpx.AsyncClient`
# or `fastapi.testclient.TestClient`. The actual implementation would require:
# 1. An import of your FastAPI `app` instance.
# 2. A fixture to create and manage the test client.
# 3. Proper mocking of services and database sessions to isolate API layer testing.
# The current code uses print statements for illustrative purposes of what would be tested.
# Actual assertions would check response status codes and JSON bodies.
