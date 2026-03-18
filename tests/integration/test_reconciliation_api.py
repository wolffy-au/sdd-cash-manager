import uuid
from datetime import date  # Add import for date
from decimal import Decimal  # Add import for Decimal
from uuid import UUID  # Keep UUID for type hinting if needed

from fastapi import status
from fastapi.testclient import TestClient

from sdd_cash_manager.database import get_db
from sdd_cash_manager.main import app
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry  # Import model for mocking return

# Mock data
TEST_ACCOUNT_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef"

# Mock db session and services for integration tests
def override_get_db():
    # This mock session needs to be able to provide a query interface
    # For simplicity, let's mock the entire query chain for the test
    mock_session = MagicMock(spec=Session)
    mock_session.query.return_value.filter.return_value.all.return_value = [] # Default empty list for .all()
    return mock_session

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Integration Tests for Reconciliation API Endpoint ---

def test_get_reconciliation_view_success(mock_db_session):
    # Mock a successful response with data
    mock_entries = [
        ReconciliationViewEntry(
            entry_id=uuid.uuid4(),
            account_id=UUID(TEST_ACCOUNT_ID),
            entry_date=date(2026, 3, 31),
            amount=Decimal("500.00"),
            description="Manual balance adjustment",
            is_adjustment=True,
            reconciled_status="PENDING_RECONCILIATION",
            original_transaction_id=uuid.uuid4(), # Mock transaction ID
        ),
        ReconciliationViewEntry(
            entry_id=uuid.uuid4(),
            account_id=UUID(TEST_ACCOUNT_ID),
            entry_date=date(2026, 3, 30),
            amount=Decimal("-100.00"),
            description="Regular transaction",
            is_adjustment=False,
            reconciled_status="CLEARED",
            original_transaction_id=uuid.uuid4(),
        ),
    ]

    # Configure mock_db_session to return mock entries when query is called
    mock_db_session.query.return_value.filter.return_value.all.return_value = mock_entries

    response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 2
    # Check first entry details
    assert data[0]["account_id"] == TEST_ACCOUNT_ID
    assert data[0]["entry_date"] == "2026-03-31"
    assert data[0]["amount"] == "500.00"
    assert data[0]["is_adjustment"] is True
    assert data[0]["reconciled_status"] == "PENDING_RECONCILIATION"
    assert data[0]["original_transaction_id"] is not None
    # Check second entry details
    assert data[1]["amount"] == "-100.00"
    assert data[1]["is_adjustment"] is False
    assert data[1]["reconciled_status"] == "CLEARED"

def test_get_reconciliation_view_no_entries(mock_db_session):
    # Mock no entries found for the account
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == [] # Expect an empty list

def test_get_reconciliation_view_server_error(mock_db_session):
    # Mock a server error during data fetching
    mock_db_session.query.side_effect = Exception("Database connection error")

    response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"detail": "An internal error occurred while fetching reconciliation data."}
