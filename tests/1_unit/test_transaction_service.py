import uuid
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.services.transaction_service import TransactionService


# Mocking uuid.uuid4 for deterministic IDs
@pytest.fixture(autouse=True)
def mock_uuid(monkeypatch):
    uuids = [
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd01'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd02'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd03'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd04'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd05'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd06'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd07'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd08'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd09'),
        uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd10'),
    ]
    monkeypatch.setattr(
        'sdd_cash_manager.services.transaction_service.uuid.uuid4', MagicMock(side_effect=uuids))

# Mock AccountService for testing TransactionService independently
@pytest.fixture
def mock_account_service():
    mock_service = MagicMock()
    # Mock accounts with initial balances
    mock_account_1_id = "acc-mock-1"
    mock_account_2_id = "acc-mock-2"
    mock_account_1 = Account(id=mock_account_1_id, name="Mock Checking", currency="USD", accounting_category="Asset", available_balance=1000.0)
    mock_account_2 = Account(id=mock_account_2_id, name="Mock Liability", currency="USD", accounting_category="Liability", available_balance=-500.0, credit_limit=1000.0)

    # Mock get_account to return specific accounts based on ID
    mock_service.get_account.side_effect = lambda acc_id: {
        mock_account_1_id: mock_account_1,
        mock_account_2_id: mock_account_2
    }.get(acc_id)

    # Correctly mock update_account to allow assertion methods
    mock_service.update_account = MagicMock(return_value=mock_account_1) # Default return value, can be adjusted by specific tests

    # The internal mock_update_account function from before is no longer needed
    # If specific update behavior is needed, it can be set on mock_service.update_account.side_effect

    return mock_service

def test_transaction_service_create_transaction(mock_account_service):
    service = TransactionService()
    service.set_account_service(mock_account_service)

    now = datetime.now()
    debit_acc_id = "acc-mock-1"
    credit_acc_id = "acc-mock-2"

    transaction = service.create_transaction(
        effective_date=now,
        booking_date=now,
        description="Initial Transaction",
        amount=150.75,
        debit_account_id=debit_acc_id,
        credit_account_id=credit_acc_id,
        action_type="Initial Entry"
    )

    assert transaction.id == str(uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddd01')) # From fixture mock
    assert transaction.effective_date == now
    assert transaction.booking_date == now
    assert transaction.description == "Initial Transaction"
    assert transaction.amount == 150.75
    assert transaction.debit_account_id == debit_acc_id
    assert transaction.credit_account_id == credit_acc_id
    assert transaction.processing_status == ProcessingStatus.PENDING
    assert transaction.reconciliation_status == ReconciliationStatus.PENDING_RECONCILIATION
    assert transaction.action_type == "Initial Entry"
    assert len(service.transactions) == 1
    assert service.transactions[transaction.id] == transaction

def test_transaction_service_create_transaction_required_fields():
    service = TransactionService()
    now = datetime.now()
    with pytest.raises(ValueError, match="Description, debit account ID, credit account ID, and action type are required."):
        service.create_transaction(now, now, "", 100.0, "d", "c", "type")
    with pytest.raises(ValueError, match="Description, debit account ID, credit account ID, and action type are required."):
        service.create_transaction(now, now, "Desc", 100.0, "", "c", "type")
    with pytest.raises(ValueError, match="Description, debit account ID, credit account ID, and action type are required."):
        service.create_transaction(now, now, "Desc", 100.0, "d", "", "type")
    with pytest.raises(ValueError, match="Description, debit account ID, credit account ID, and action type are required."):
        service.create_transaction(now, now, "Desc", 100.0, "d", "c", "")

def test_transaction_service_create_transaction_same_account():
    service = TransactionService()
    now = datetime.now()
    with pytest.raises(ValueError, match="Debit and credit accounts cannot be the same."):
        service.create_transaction(now, now, "Same Account", 100.0, "acc1", "acc1", "Transfer")

def test_transaction_service_get_transaction():
    service = TransactionService()
    now = datetime.now()
    tx = service.create_transaction(now, now, "Get Tx", 50.0, "d", "c", "Get")
    retrieved_tx = service.get_transaction(tx.id)
    assert retrieved_tx is not None
    assert retrieved_tx.id == tx.id

    assert service.get_transaction("non-existent-id") is None

def test_transaction_service_get_transactions_by_account():
    service = TransactionService()
    now = datetime.now()
    acc1_id = "acc-mock-1"
    acc2_id = "acc-mock-2"

    tx1 = service.create_transaction(now, now, "Tx 1", 100.0, acc1_id, acc2_id, "Transfer")
    tx2 = service.create_transaction(now, now, "Tx 2", 50.0, acc2_id, acc1_id, "Transfer")
    tx3 = service.create_transaction(now, now, "Tx 3", 25.0, acc1_id, "other-acc", "Payment")

    txs_for_acc1 = service.get_transactions_by_account(acc1_id)
    assert len(txs_for_acc1) == 3
    assert tx1 in txs_for_acc1
    assert tx2 in txs_for_acc1
    assert tx3 in txs_for_acc1

    txs_for_acc2 = service.get_transactions_by_account(acc2_id)
    assert len(txs_for_acc2) == 2
    assert tx1 in txs_for_acc2
    assert tx2 in txs_for_acc2

    txs_for_non_existent = service.get_transactions_by_account("non-existent-id")
    assert len(txs_for_non_existent) == 0

def test_transaction_service_update_transaction_status(mock_account_service): # Added mock_account_service as it's used in perform_balance_adjustment
    service = TransactionService()
    service.set_account_service(mock_account_service) # Set the dependency

    now = datetime.now()
    tx = service.create_transaction(now, now, "Update Status", 75.0, "d", "c", "Update")

    updated_tx = service.update_transaction_status(
        tx.id,
        processing_status=ProcessingStatus.POSTED,
        reconciliation_status=ReconciliationStatus.RECONCILED
    )
    assert updated_tx is not None
    assert updated_tx.processing_status == ProcessingStatus.POSTED
    assert updated_tx.reconciliation_status == ReconciliationStatus.RECONCILED

    # Test updating only one status
    updated_tx_partially = service.update_transaction_status(
        tx.id,
        processing_status=ProcessingStatus.FAILED
    )
    assert updated_tx_partially is not None
    assert updated_tx_partially.processing_status == ProcessingStatus.FAILED
    assert updated_tx_partially.reconciliation_status == ReconciliationStatus.RECONCILED # Should remain unchanged

    # Test updating non-existent transaction
    non_existent_update = service.update_transaction_status("non-existent-id", processing_status=ProcessingStatus.POSTED)
    assert non_existent_update is None

def test_transaction_service_perform_balance_adjustment_credit(mock_account_service):
    service = TransactionService()
    service.set_account_service(mock_account_service)

    account_id = "acc-mock-1" # Mock Checking account with balance 1000.0
    target_balance = 1250.75 # Increase balance
    adjustment_date = datetime(2026, 2, 25, 10, 0, 0)
    description = "Customer Payment Received"

    transaction = service.perform_balance_adjustment(
        account_id=account_id,
        target_balance=target_balance,
        adjustment_date=adjustment_date,
        description=description,
        action_type="Customer Payment"
    )

    assert transaction is not None
    assert transaction.amount == 250.75 # Difference is 1250.75 - 1000.0 = 250.75
    # Credit to the account means debit from balancing account
    assert transaction.debit_account_id == "balancing-account-id"
    assert transaction.credit_account_id == account_id
    assert transaction.effective_date == adjustment_date
    assert transaction.action_type == "Customer Payment"
    assert transaction.description == f"{description} for account Mock Checking"
    assert transaction.processing_status == ProcessingStatus.POSTED
    assert transaction.reconciliation_status == ReconciliationStatus.PENDING_RECONCILIATION

    # Verify account balance was updated by the service mock
    # The mock_account_service.update_account is called, so we check the mock object state.
    mock_account_service.update_account.assert_called_once()
    mock_account_service.update_account.assert_called_with(account_id, available_balance=target_balance)

def test_transaction_service_perform_balance_adjustment_debit(mock_account_service):
    service = TransactionService()
    service.set_account_service(mock_account_service)

    account_id = "acc-mock-2" # Mock Liability account with balance -500.0
    target_balance = -750.00 # Decrease balance (make it more negative)
    adjustment_date = datetime(2026, 2, 25, 11, 0, 0)
    description = "Customer Refund Issued"

    transaction = service.perform_balance_adjustment(
        account_id=account_id,
        target_balance=target_balance,
        adjustment_date=adjustment_date,
        description=description,
        action_type="Customer Refund"
    )

    assert transaction is not None
    assert transaction.amount == 250.00 # Difference is |-750.00 - (-500.00)| = |-250.00| = 250.00
    # Debit to the account means credit to balancing account
    assert transaction.debit_account_id == account_id
    assert transaction.credit_account_id == "balancing-account-id"
    assert transaction.effective_date == adjustment_date
    assert transaction.action_type == "Customer Refund"
    assert transaction.description == f"{description} for account Mock Liability"
    assert transaction.processing_status == ProcessingStatus.POSTED
    assert transaction.reconciliation_status == ReconciliationStatus.PENDING_RECONCILIATION

    # Verify account balance was updated
    mock_account_service.update_account.assert_called_once()
    mock_account_service.update_account.assert_called_with(account_id, available_balance=target_balance)

def test_transaction_service_perform_balance_adjustment_no_change(mock_account_service):
    service = TransactionService()
    service.set_account_service(mock_account_service)

    account_id = "acc-mock-1"
    # Get current balance from mock account
    mock_account = mock_account_service.get_account(account_id)
    current_balance = mock_account.available_balance if mock_account else 0.0

    # Target balance is the same as current balance
    transaction = service.perform_balance_adjustment(
        account_id=account_id,
        target_balance=current_balance,
        adjustment_date=datetime.now(),
        description="No change needed",
        action_type="No Change"
    )

    assert transaction is None # No transaction should be created
    # Verify account balance was not updated (no call to mock_account_service.update_account)
    mock_account_service.update_account.assert_not_called()

def test_transaction_service_perform_balance_adjustment_account_not_found(mock_account_service):
    service = TransactionService()
    service.set_account_service(mock_account_service)

    with pytest.raises(ValueError, match="Account with ID non-existent-id not found."):
        service.perform_balance_adjustment(
            account_id="non-existent-id",
            target_balance=100.0,
            adjustment_date=datetime.now(),
            description="Should fail",
            action_type="Fail Test"
        )

def test_transaction_service_perform_balance_adjustment_no_account_service():
    service = TransactionService()
    # Ensure account_service is not set
    service.account_service = None

    with pytest.raises(RuntimeError, match="AccountService is not set."):
        service.perform_balance_adjustment(
            account_id="acc-mock-1",
            target_balance=100.0,
            adjustment_date=datetime.now(),
            description="Should fail",
            action_type="Test Failure" # Added missing argument
        )
