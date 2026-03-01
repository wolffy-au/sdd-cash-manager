import uuid
from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from sdd_cash_manager.database import get_db
from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base  # Import Base for metadata.create_all
from sdd_cash_manager.services.account_service import (
    AccountService,  # Used for direct db interaction in tests if needed
)

# --- Fixtures ---

@pytest.fixture(scope="module")
def event_loop():
    """Redefine event_loop fixture for pytest-asyncio."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def override_get_db():
    """
    Provides an in-memory SQLite database session for testing.
    """
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Clean up tables after test

        # Remove the test database file after tests
        import os
        if os.path.exists("./test.db"):
            os.remove("./test.db")

@pytest.fixture(scope="function")
async def async_client(override_get_db: Session):
    """
    Provides an httpx.AsyncClient to make requests to a test FastAPI app.
    The test app includes the account router and has dependencies overridden
    for a real, in-memory database session.
    """
    from sdd_cash_manager.api.accounts import router as account_router

    test_app = FastAPI()
    test_app.include_router(account_router, prefix="/api")
    test_app.dependency_overrides[get_db] = lambda: override_get_db

    with TestClient(test_app) as client:
        yield client

# --- Test Cases ---

@pytest.mark.asyncio
async def test_create_account_success(async_client: TestClient, override_get_db: Session):
    """
    Tests successful creation of a new account.
    """
    print("\n--- Testing create_account_success ---")

    account_data_input = {
        "name": "New Integration Account",
        "account_number": f"ACC-INT-{uuid.uuid4()}",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "BANK",
        "available_balance": 500.75,
        "notes": "Created via integration test"
    }

    response = async_client.post("/api/accounts", json=account_data_input)

    assert response.status_code == 201 # Assuming 201 Created

    response_data = response.json()
    assert "id" in response_data
    assert response_data["name"] == account_data_input["name"]
    assert response_data["account_number"] == account_data_input["account_number"]
    assert response_data["available_balance"] == account_data_input["available_balance"]

    # Verify that the account is actually in the database
    account_service = AccountService(override_get_db)
    db_account = account_service.get_account(response_data["id"])
    assert db_account is not None
    assert db_account.name == account_data_input["name"]
    assert db_account.account_number == account_data_input["account_number"]
    assert db_account.available_balance == account_data_input["available_balance"]

@pytest.mark.asyncio
async def test_get_all_accounts(async_client: TestClient, override_get_db: Session):
    """
    Tests retrieving all accounts.
    """
    print("\n--- Testing get_all_accounts ---")

    # Create a couple of accounts directly in the database for testing
    account_service = AccountService(override_get_db)
    account1 = account_service.create_account(
        name="Account One",
        currency="USD",
        accounting_category="ASSET"
    )
    account2 = account_service.create_account(
        name="Account Two",
        currency="EUR",
        accounting_category="LIABILITY"
    )

    response = async_client.get("/api/accounts")

    assert response.status_code == 200
    response_data = response.json()

    assert isinstance(response_data, list)
    assert len(response_data) == 2

    # Check if the created accounts are in the response
    response_ids = {acc["id"] for acc in response_data}
    assert account1.id in response_ids
    assert account2.id in response_ids

@pytest.mark.asyncio
async def test_get_account_by_id_success(async_client: TestClient, override_get_db: Session):
    """
    Tests retrieving a specific account by its ID.
    """
    print("\n--- Testing get_account_by_id_success ---")

    # Create an account directly in the database
    account_service = AccountService(override_get_db)
    created_account = account_service.create_account(
        name="Account for Get Test",
        currency="GBP",
        accounting_category="ASSET",
        account_number="GET-ACC-001"
    )

    response = async_client.get(f"/api/accounts/{created_account.id}")

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == created_account.id
    assert response_data["name"] == created_account.name
    assert response_data["account_number"] == created_account.account_number

@pytest.mark.asyncio
async def test_get_account_by_id_not_found(async_client: TestClient):
    """
    Tests retrieving a non-existent account, expecting a 404.
    """
    print("\n--- Testing get_account_by_id_not_found ---")

    non_existent_id = str(uuid.uuid4())

    response = async_client.get(f"/api/accounts/{non_existent_id}")

    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Account not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_account_success(async_client: TestClient, override_get_db: Session):
    """
    Tests successfully updating an existing account.
    """
    print("\n--- Testing update_account_success ---")

    # Create an account to update
    account_service = AccountService(override_get_db)
    created_account = account_service.create_account(
        name="Account to Update",
        currency="CAD",
        accounting_category="EXPENSE"
    )

    update_data_input = {
        "name": "Updated Account Name",
        "available_balance": 999.99,
        "notes": "Updated notes for integration test"
    }

    response = async_client.put(f"/api/accounts/{created_account.id}", json=update_data_input)

    assert response.status_code == 200
    response_data = response.json()

    assert response_data["id"] == created_account.id
    assert response_data["name"] == update_data_input["name"]
    assert response_data["available_balance"] == update_data_input["available_balance"]
    assert response_data["notes"] == update_data_input["notes"]

    # Verify update in the database
    db_account = override_get_db.query(Account).filter(Account.id == created_account.id).first()
    assert db_account.name == update_data_input["name"]
    assert db_account.available_balance == update_data_input["available_balance"]

@pytest.mark.asyncio
async def test_delete_account_success(async_client: TestClient, override_get_db: Session):
    """
    Tests successfully deleting an account.
    """
    print("\n--- Testing delete_account_success ---")

    # Create an account to delete
    account_service = AccountService(override_get_db)
    created_account = account_service.create_account(
        name="Account to Delete",
        currency="AUD",
        accounting_category="REVENUE"
    )

    response = async_client.delete(f"/api/accounts/{created_account.id}")

    assert response.status_code == 204

    # Verify deletion from the database
    db_account = override_get_db.query(Account).filter(Account.id == created_account.id).first()
    assert db_account is None

@pytest.mark.asyncio
async def test_perform_balance_adjustment_success(async_client: TestClient, override_get_db: Session):
    """
    Tests performing a balance adjustment for an account.
    """
    print("\n--- Testing perform_balance_adjustment_success ---")

    # Create an account
    account_service = AccountService(override_get_db)
    initial_balance = 100.00
    created_account = account_service.create_account(
        name="Account for Adjustment",
        currency="USD",
        accounting_category="ASSET",
        available_balance=initial_balance
    )

    target_balance = 150.00
    adjustment_payload_input = {
        "target_balance": target_balance,
        "adjustment_date": datetime.now().isoformat(),
        "description": "Integration test adjustment",
        "action_type": "MANUAL_ADJUST"
    }

    response = async_client.post(
        f"/api/accounts/{created_account.id}/adjust_balance",
        json=adjustment_payload_input
    )

    assert response.status_code == 200
    response_data = response.json()

    assert "transaction_id" in response_data
    assert response_data["account_id"] == created_account.id
    assert response_data["new_balance"] == target_balance

    # Verify account balance update in the database
    db_account = override_get_db.query(Account).filter(Account.id == created_account.id).first()
    assert db_account.available_balance == target_balance

@pytest.mark.asyncio
async def test_create_account_validation_error(async_client: TestClient):
    """
    Tests account creation with invalid data, expecting a 422 error.
    """
    print("\n--- Testing create_account_validation_error ---")

    invalid_payload_input = {
        "name": "Invalid Account",
        "currency": "USD",
        "accounting_category": "ASSET",
        "available_balance": "not a float" # Invalid type
    }

    response = async_client.post("/api/accounts", json=invalid_payload_input)

    assert response.status_code == 422
    response_data = response.json()
    detail_str = str(response_data["detail"])
    assert "Input should be a valid number" in detail_str

@pytest.mark.asyncio
async def test_update_account_not_found(async_client: TestClient):
    """
    Tests updating a non-existent account, expecting a 404.
    """
    print("\n--- Testing update_account_not_found ---")

    non_existent_id = str(uuid.uuid4())
    update_data_input = {
        "name": "Attempted Update",
        "available_balance": 100.0
    }

    response = async_client.put(f"/api/accounts/{non_existent_id}", json=update_data_input)

    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Account not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_account_not_found(async_client: TestClient):
    """
    Tests deleting a non-existent account, expecting a 404.
    """
    print("\n--- Testing delete_account_not_found ---")

    non_existent_id = str(uuid.uuid4())

    response = async_client.delete(f"/api/accounts/{non_existent_id}")

    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Account not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_perform_balance_adjustment_not_found(async_client: TestClient):
    """
    Tests performing a balance adjustment on a non-existent account, expecting a 400.
    """
    print("\n--- Testing perform_balance_adjustment_not_found ---")

    non_existent_account_id = str(uuid.uuid4())
    adjustment_payload_input = {
        "target_balance": 1500.0,
        "adjustment_date": datetime.now().isoformat(),
        "description": "Adjustment on non-existent account",
        "action_type": "TEST_ADJ"
    }

    response = async_client.post(
        f"/api/accounts/{non_existent_account_id}/adjust_balance",
        json=adjustment_payload_input
    )

    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Account with ID" in response.json()["detail"]
    assert "not found." in response.json()["detail"]


@pytest.mark.asyncio
async def test_perform_balance_adjustment_validation_error(async_client: TestClient):
    """
    Tests balance adjustment with invalid input data, expecting a 422.
    """
    print("\n--- Testing perform_balance_adjustment_validation_error ---")

    # This test no longer needs a created account, as validation happens before service call
    account_id_for_adjustment = str(uuid.uuid4()) # A dummy ID is fine here

    invalid_payload_input = {
        "target_balance": "not a float", # Invalid type
        "adjustment_date": "26-02-2026", # Invalid format
        "description": "Invalid adjustment data",
        "action_type": "TEST_ADJ"
    }

    response = async_client.post(
        f"/api/accounts/{account_id_for_adjustment}/adjust_balance",
        json=invalid_payload_input
    )

    assert response.status_code == 422
    response_data = response.json()
    detail_str = str(response_data["detail"])
    assert "Input should be a valid number" in detail_str
    assert "invalid character in year" in detail_str
