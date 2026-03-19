import uuid
from datetime import date  # Add import for date
from decimal import Decimal  # Add import for Decimal
from unittest.mock import MagicMock, patch
from uuid import UUID  # Keep UUID for type hinting if needed

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sdd_cash_manager.database import get_db
from sdd_cash_manager.main import app
from sdd_cash_manager.models.enums import ReconciliationStatus
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry  # Import model for mocking return

# Mock data
TEST_ACCOUNT_ID = "a1b2c3d4-e5f6-7890-1234-567890abcdef"

def build_mock_db_session() -> Session:
    mock_session = MagicMock(spec=Session)
    mock_session.query.return_value.filter.return_value.all.return_value = []
    return mock_session

@pytest.fixture(autouse=True)
def override_get_db(mock_db_session):
    def _override():
        yield mock_db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def mock_db_session() -> Session:
    return build_mock_db_session()

client = TestClient(app)

# --- Integration Tests for Reconciliation API Endpoint ---

def test_get_reconciliation_view_success(mock_db_session):
    mock_entries = [
        ReconciliationViewEntry(
            entry_id=uuid.uuid4(),
            account_id=UUID(TEST_ACCOUNT_ID),
            entry_date=date(2026, 3, 31),
            amount=Decimal("500.00"),
            description="Manual balance adjustment",
            is_adjustment=True,
            reconciled_status=ReconciliationStatus.PENDING_RECONCILIATION.value,
            original_transaction_id=uuid.uuid4(), # Mock transaction ID
        ),
        ReconciliationViewEntry(
            entry_id=uuid.uuid4(),
            account_id=UUID(TEST_ACCOUNT_ID),
            entry_date=date(2026, 3, 30),
            amount=Decimal("-100.00"),
            description="Regular transaction",
            is_adjustment=False,
            reconciled_status=ReconciliationStatus.RECONCILED.value,
            original_transaction_id=uuid.uuid4(),
        ),
    ]

    with patch(
        "sdd_cash_manager.api.v1.endpoints.reconciliation.ReconciliationService"
    ) as MockReconciliationService:
        mock_service = MagicMock()
        mock_service.get_reconciliation_entries_for_account.return_value = mock_entries
        MockReconciliationService.return_value = mock_service

        response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 2
        # Check first entry details
        assert data[0]["account_id"] == TEST_ACCOUNT_ID
        assert data[0]["entry_date"] == "2026-03-31"
        assert data[0]["amount"] == "500.00"
        assert data[0]["is_adjustment"] is True
        assert data[0]["reconciled_status"] == ReconciliationStatus.PENDING_RECONCILIATION.value
        assert data[0]["original_transaction_id"] is not None
        # Check second entry details
        assert data[1]["amount"] == "-100.00"
        assert data[1]["is_adjustment"] is False
        assert data[1]["reconciled_status"] == ReconciliationStatus.RECONCILED.value

        MockReconciliationService.assert_called_once_with(mock_db_session)
        mock_service.get_reconciliation_entries_for_account.assert_called_once_with(UUID(TEST_ACCOUNT_ID))

def test_get_reconciliation_view_no_entries(mock_db_session):
    with patch(
        "sdd_cash_manager.api.v1.endpoints.reconciliation.ReconciliationService"
    ) as MockReconciliationService:
        mock_service = MagicMock()
        mock_service.get_reconciliation_entries_for_account.return_value = []
        MockReconciliationService.return_value = mock_service

        response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

        MockReconciliationService.assert_called_once_with(mock_db_session)
        mock_service.get_reconciliation_entries_for_account.assert_called_once_with(UUID(TEST_ACCOUNT_ID))

def test_get_reconciliation_view_server_error(mock_db_session):
    with patch(
        "sdd_cash_manager.api.v1.endpoints.reconciliation.ReconciliationService"
    ) as MockReconciliationService:
        mock_service = MagicMock()
        mock_service.get_reconciliation_entries_for_account.side_effect = Exception("Database connection error")
        MockReconciliationService.return_value = mock_service

        response = client.get(f"/accounts/{TEST_ACCOUNT_ID}/reconciliation")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "An internal error occurred while fetching reconciliation data."}

        MockReconciliationService.assert_called_once_with(mock_db_session)
        mock_service.get_reconciliation_entries_for_account.assert_called_once_with(UUID(TEST_ACCOUNT_ID))
