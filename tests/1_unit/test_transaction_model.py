import uuid
from datetime import datetime
from unittest.mock import MagicMock  # Added this import

import pytest

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Transaction


# Mocking uuid.uuid4 for deterministic IDs
@pytest.fixture(autouse=True)
def mock_uuid(monkeypatch):
    mock_uuid = uuid.UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
    monkeypatch.setattr('sdd_cash_manager.models.transaction.uuid.uuid4',
                        MagicMock(return_value=mock_uuid))

def test_transaction_model_creation():
    now = datetime.now()
    transaction = Transaction(
        effective_date=now,
        booking_date=now,
        description="Test Transaction",
        amount=100.50,
        debit_account_id="acc-debit-123",
        credit_account_id="acc-credit-456",
        action_type="Test Action",
        notes="Some test notes"
    )

    assert transaction.id == str(uuid.UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'))
    assert transaction.effective_date == now
    assert transaction.booking_date == now
    assert transaction.description == "Test Transaction"
    assert transaction.amount == 100.50
    assert transaction.debit_account_id == "acc-debit-123"
    assert transaction.credit_account_id == "acc-credit-456"
    assert transaction.processing_status == ProcessingStatus.PENDING
    assert transaction.reconciliation_status == ReconciliationStatus.PENDING_RECONCILIATION
    assert transaction.action_type == "Test Action"
    assert transaction.notes == "Some test notes"

def test_transaction_model_defaults():
    now = datetime.now()
    transaction = Transaction(
        effective_date=now,
        booking_date=now,
        description="Default Test",
        amount=-50.00,
        debit_account_id="acc-debit-abc",
        credit_account_id="acc-credit-xyz",
        action_type="Default"
    )
    assert transaction.id is not None
    assert transaction.processing_status == ProcessingStatus.PENDING
    assert transaction.reconciliation_status == ReconciliationStatus.PENDING_RECONCILIATION
    assert transaction.notes is None

def test_transaction_model_enums():
    now = datetime.now()
    transaction = Transaction(
        effective_date=now,
        booking_date=now,
        description="Enum Test",
        amount=200.00,
        debit_account_id="acc-debit-789",
        credit_account_id="acc-credit-012",
        processing_status=ProcessingStatus.POSTED,
        reconciliation_status=ReconciliationStatus.RECONCILED,
        action_type="Test"
    )
    assert isinstance(transaction.processing_status, ProcessingStatus)
    assert transaction.processing_status.value == "Posted"
    assert isinstance(transaction.reconciliation_status, ReconciliationStatus)
    assert transaction.reconciliation_status.value == "Reconciled"

def test_transaction_model_required_fields_missing():
    now = datetime.now()
    # Test missing description
    with pytest.raises(ValueError, match="Description cannot be empty."): # Changed to ValueError
        Transaction(
            effective_date=now,
            booking_date=now,
            description="", # Pass empty string
            amount=100.00,
            debit_account_id="acc-debit",
            credit_account_id="acc-credit",
            action_type="Test"
        )
    # Test missing debit_account_id
    with pytest.raises(ValueError, match="Debit account ID cannot be empty."): # Changed to ValueError
        Transaction(
            effective_date=now,
            booking_date=now,
            description="Missing Debit",
            amount=100.00,
            debit_account_id="", # Pass empty string
            credit_account_id="acc-credit",
            action_type="Test"
        )
    # Test missing credit_account_id
    with pytest.raises(ValueError, match="Credit account ID cannot be empty."): # Changed to ValueError
        Transaction(
            effective_date=now,
            booking_date=now,
            description="Missing Credit",
            amount=100.00,
            debit_account_id="acc-debit",
            credit_account_id="", # Pass empty string
            action_type="Test"
        )
