import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from sdd_cash_manager.models.adjustment import AdjustmentTransaction
from sdd_cash_manager.models.reconciliation import ReconciliationViewEntry
from sdd_cash_manager.schemas.reconciliation import ReconciliationViewEntryCreate # Assuming this schema will be used by the service
from sdd_cash_manager.services.reconciliation_service import ReconciliationService

# Mock data
TEST_ACCOUNT_ID = UUID(int=1)

# Mock db session
@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.refresh.return_value = None
    mock_session.query.return_value.filter.return_value.all.return_value = [] # Default for fetching
    return mock_session

# --- Tests for ReconciliationService ---

def test_create_reconciliation_entry_from_transaction(mock_db_session):
    # Mock data for an AdjustmentTransaction
    mock_transaction = AdjustmentTransaction(
        transaction_id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        effective_date=date(2026, 3, 31),
        amount=Decimal("500.00"),
        transaction_type="ADJUSTMENT_DEBIT",
        description="Manual balance adjustment",
        created_at=datetime.utcnow(),
        reconciliation_metadata=None,
    )

    # Instantiate the service with the mock db session
    reconciliation_service = ReconciliationService(mock_db_session)

    # Call the method to create reconciliation entry
    created_entry = reconciliation_service.create_reconciliation_entry_from_transaction(
        account_id=TEST_ACCOUNT_ID,
        transaction=mock_transaction
    )

    # Assertions
    assert isinstance(created_entry, ReconciliationViewEntry)
    assert created_entry.account_id == TEST_ACCOUNT_ID
    assert created_entry.entry_date == mock_transaction.effective_date
    assert created_entry.amount == mock_transaction.amount
    assert created_entry.description == mock_transaction.description
    assert created_entry.is_adjustment is True
    assert created_entry.reconciled_status == "PENDING_RECONCILIATION"
    assert created_entry.original_transaction_id == mock_transaction.transaction_id
    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()
    mock_db_session.commit.assert_called_once()

def test_create_reconciliation_entry_from_transaction_with_metadata(mock_db_session):
    # Mock data for an AdjustmentTransaction with metadata
    mock_transaction = AdjustmentTransaction(
        transaction_id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        effective_date=date(2026, 4, 1),
        amount=Decimal("200.00"),
        transaction_type="ADJUSTMENT_CREDIT",
        description="Another adjustment",
        reconciliation_metadata={"source": "manual_entry"},
        created_at=datetime.utcnow(),
    )

    reconciliation_service = ReconciliationService(mock_db_session)
    created_entry = reconciliation_service.create_reconciliation_entry_from_transaction(
        account_id=TEST_ACCOUNT_ID,
        transaction=mock_transaction
    )

    assert created_entry.reconciliation_metadata == {"source": "manual_entry"}
    assert created_entry.is_adjustment is True
    assert created_entry.reconciled_status == "PENDING_RECONCILIATION"
    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()
    mock_db_session.commit.assert_called_once()

def test_create_reconciliation_entry_sqlalchemy_error(mock_db_session):
    mock_transaction = AdjustmentTransaction(
        transaction_id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        effective_date=date(2026, 3, 31),
        amount=Decimal("500.00"),
        transaction_type="ADJUSTMENT_DEBIT",
        description="Manual balance adjustment",
        created_at=datetime.utcnow(),
    )

    mock_db_session.add.side_effect = SQLAlchemyError("Mock DB error")

    reconciliation_service = ReconciliationService(mock_db_session)

    with pytest.raises(RuntimeError, match="Failed to create reconciliation entry"):
        reconciliation_service.create_reconciliation_entry_from_transaction(
            account_id=TEST_ACCOUNT_ID,
            transaction=mock_transaction
        )

    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()
    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()

def test_create_reconciliation_entry_unexpected_error(mock_db_session):
    mock_transaction = AdjustmentTransaction(
        transaction_id=uuid4(),
        account_id=TEST_ACCOUNT_ID,
        effective_date=date(2026, 3, 31),
        amount=Decimal("500.00"),
        transaction_type="ADJUSTMENT_DEBIT",
        description="Manual balance adjustment",
        created_at=datetime.utcnow(),
    )

    mock_db_session.add.side_effect = Exception("Some other error")

    reconciliation_service = ReconciliationService(mock_db_session)

    with pytest.raises(RuntimeError, match="An unexpected error occurred"):
        reconciliation_service.create_reconciliation_entry_from_transaction(
            account_id=TEST_ACCOUNT_ID,
            transaction=mock_transaction
        )

    mock_db_session.add.assert_called_once()
    mock_db_session.flush.assert_called_once()
    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()
