from datetime import datetime
from decimal import Decimal  # Import Decimal
from typing import Optional
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db  # Assuming get_db is available
from sdd_cash_manager.lib.auth import Role, create_access_token
from sdd_cash_manager.main import app  # Assuming app is FastAPI instance in main.py
from sdd_cash_manager.models.adjustment import (  # Import models for assertions
    AdjustmentTransaction,
    ManualBalanceAdjustment,
)
from sdd_cash_manager.models.enums import BankingProductType
from sdd_cash_manager.schemas.adjustment import ManualBalanceAdjustmentCreate

# Mock data
TEST_ACCOUNT_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
TEST_USER_ID = "f0e9d8c7-b6a5-4321-0987-654321fedcba"

def auth_headers(subject: str = TEST_USER_ID) -> dict[str, str]:
    token = create_access_token(subject=subject, roles=[Role.OPERATOR])
    return {"Authorization": f"Bearer {token}"}

# Mock AccountService and ManualBalanceAdjustmentService for integration tests
# We'll patch these services when they are called by the API endpoint

class MockAccount:
    def __init__(self, id: UUID, running_balance: Decimal) -> None:
        self.id = id
        self.running_balance = running_balance

class MockAccountService:
    def get_account(self, account_id: UUID) -> Optional[MockAccount]:
        if str(account_id) == TEST_ACCOUNT_ID:
            return MockAccount(id=account_id, running_balance=Decimal("1000.00"))
        return None

class MockManualBalanceAdjustmentService:
    def __init__(self, db_session: Session) -> None:
        self.db = db_session
        self.account_service = MockAccountService()

    def create_adjustment(self, account_id: UUID, adjustment_data: ManualBalanceAdjustmentCreate) -> ManualBalanceAdjustment:
        account = self.account_service.get_account(account_id)
        if not account:
            raise ValueError("Account not found")

        difference = adjustment_data.target_balance - account.running_balance

        transaction = None
        if difference != Decimal("0"):
            transaction_type = BankingProductType.ADJUSTMENT_DEBIT if difference > Decimal("0") else BankingProductType.ADJUSTMENT_CREDIT
            transaction = AdjustmentTransaction(
                transaction_id=uuid4(),
                account_id=account_id,
                effective_date=adjustment_data.effective_date,
                amount=abs(difference),
                transaction_type=transaction_type,
                description="Manual balance adjustment",
                created_at=datetime.utcnow(),
            )
            account.running_balance += difference

        adjustment = ManualBalanceAdjustment(
            id=1,
            account_id=account_id,
            target_balance=adjustment_data.target_balance,
            effective_date=adjustment_data.effective_date,
            submitted_by_user_id=adjustment_data.submitted_by_user_id,
            adjustment_attempt_timestamp=datetime.utcnow(),
            created_transaction_id=transaction.transaction_id if transaction else None,
            status="COMPLETED" if transaction else "ZERO_DIFFERENCE"
        )

        return adjustment


# Mock db session for integration tests
def build_mock_db_session() -> Session:
    mock_session = MagicMock(spec=Session)
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.refresh.return_value = None
    return mock_session

@pytest.fixture
def mock_db_session() -> Session:
    return build_mock_db_session()

def override_get_db():
    yield build_mock_db_session()

app.dependency_overrides[get_db] = override_get_db

# Patch services used by the API endpoint
@pytest.fixture(autouse=True)
def patch_services():
    with patch('sdd_cash_manager.api.v1.endpoints.adjustment.ManualBalanceAdjustmentService') as mock_service_cls:
        mock_service_instance = MockManualBalanceAdjustmentService(build_mock_db_session())
        mock_service_cls.return_value = mock_service_instance
        yield

client = TestClient(app)

# --- Integration Tests for API Endpoint ---

def test_create_manual_balance_adjustment_integration_success():
    payload = {
        "target_balance": "1500.00",
        "effective_date": "2026-03-31",
        "submitted_by_user_id": TEST_USER_ID,
    }

    response = client.post(
        f"/accounts/{TEST_ACCOUNT_ID}/adjust-balance",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["account_id"] == TEST_ACCOUNT_ID
    assert data["target_balance"] == "1500.00"
    assert data["effective_date"] == "2026-03-31"
    assert data["submitted_by_user_id"] == TEST_USER_ID
    assert data["status"] == "COMPLETED"
    assert data["created_transaction_id"] is not None

def test_create_manual_balance_adjustment_integration_zero_difference():
    payload = {
        "target_balance": "1000.00", # Same as mock account's running balance
        "effective_date": "2026-03-31",
        "submitted_by_user_id": TEST_USER_ID,
    }

    response = client.post(
        f"/accounts/{TEST_ACCOUNT_ID}/adjust-balance",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "ZERO_DIFFERENCE"
    assert data["created_transaction_id"] is None

def test_create_manual_balance_adjustment_integration_account_not_found():
    payload = {
        "target_balance": "1500.00",
        "effective_date": "2026-03-31",
        "submitted_by_user_id": TEST_USER_ID,
    }

    # Mock the service to raise ValueError for account not found
    with patch.object(MockManualBalanceAdjustmentService, "create_adjustment", side_effect=ValueError("Account with id {} not found".format(UUID(int=99)))):
        response = client.post(
            f"/accounts/{UUID(int=99)}/adjust-balance",
            json=payload,
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        expected_detail = f"Account with id {UUID(int=99)} not found"
        assert response.json() == {"detail": expected_detail}

def test_create_manual_balance_adjustment_integration_server_error():
    payload = {
        "target_balance": "1500.00",
        "effective_date": "2026-03-31",
        "submitted_by_user_id": TEST_USER_ID,
    }

    # Mock the service to raise a generic exception
    with patch.object(MockManualBalanceAdjustmentService, "create_adjustment", side_effect=Exception("Database connection error")):
        response = client.post(
            f"/accounts/{TEST_ACCOUNT_ID}/adjust-balance",
            json=payload,
            headers=auth_headers(),
        )
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "An internal error occurred during balance adjustment."}

def test_create_manual_balance_adjustment_invalid_date_validation_error():
    # Pydantic validation for effective_date occurs before service call
    payload = {
        "target_balance": "1500.00",
        "effective_date": "2027-03-31", # Date outside the expected range
        "submitted_by_user_id": TEST_USER_ID,
    }

    response = client.post(
        f"/accounts/{TEST_ACCOUNT_ID}/adjust-balance",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation error
    assert "Effective date must be within a reasonable range" in response.text

def test_create_manual_balance_adjustment_invalid_balance_validation_error():
    # Pydantic validation for target_balance (ge=0)
    payload = {
        "target_balance": "-100.00", # Invalid negative balance
        "effective_date": "2026-03-31",
        "submitted_by_user_id": TEST_USER_ID,
    }

    response = client.post(
        f"/accounts/{TEST_ACCOUNT_ID}/adjust-balance",
        json=payload,
        headers=auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation error
    assert "greater than or equal to 0" in response.text
