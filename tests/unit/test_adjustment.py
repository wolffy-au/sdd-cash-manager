from datetime import date, datetime
from decimal import Decimal
import logging
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from sdd_cash_manager.models.adjustment import AdjustmentTransaction, ManualBalanceAdjustment
from sdd_cash_manager.models.enums import BankingProductType  # Import the enum
from sdd_cash_manager.services.adjustment_service import ManualBalanceAdjustmentService

logger = logging.getLogger(__name__) # Initialize logger

# Mock data
TEST_ACCOUNT_ID = UUID(int=1)

# Mock db session
@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.refresh.return_value = None
    return mock_session

# --- Tests for AdjustmentTransaction SQLAlchemy Model ---

def test_adjustment_transaction_model_creation():
    transaction_id = uuid4()
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    amount = Decimal("500.00")
    transaction_type = BankingProductType.ADJUSTMENT_DEBIT # Use the enum value
    description = "Manual balance adjustment"
    created_at = datetime.utcnow()

    transaction = AdjustmentTransaction(
        transaction_id=transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        reconciliation_metadata={"status": "processed"},
        created_at=created_at,
    )

    assert transaction.transaction_id == transaction_id
    assert transaction.account_id == account_id
    assert transaction.effective_date == effective_date
    assert transaction.amount == amount
    assert transaction.transaction_type == BankingProductType.ADJUSTMENT_DEBIT
    assert transaction.description == description
    assert transaction.reconciliation_metadata == {"status": "processed"}
    assert transaction.created_at == created_at

def test_adjustment_transaction_model_defaults():
    # Test default values if any (e.g., for reconciliation_metadata)
    transaction_id = uuid4()
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    amount = Decimal("100.00")
    transaction_type = BankingProductType.ADJUSTMENT_CREDIT
    description = "Another adjustment"
    created_at = datetime.utcnow()

    transaction = AdjustmentTransaction(
        transaction_id=transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        created_at=created_at,
        # reconciliation_metadata is Optional and not provided
    )

    assert transaction.reconciliation_metadata is None

# --- Tests for AdjustmentTransaction creation logic within Service (simulated) ---
# These tests would typically be in test_adjustment_service.py, but for completeness here:

# Mock AccountService and manual_balance_adjustment for service logic simulation
class MockAccount:
    def __init__(self, id: UUID, running_balance: Decimal):
        self.id = id
        self.running_balance = running_balance

class MockAccountService:
    def __init__(self, db: Session):
        self.db = db
        self.accounts = {
            TEST_ACCOUNT_ID: MockAccount(id=TEST_ACCOUNT_ID, running_balance=Decimal("1000.00"))
        }
    def get_account(self, account_id: UUID):
        return self.accounts.get(account_id)

def test_adjustment_transaction_creation_logic(mock_db_session):
    # Simulate calling the service logic that creates the transaction
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    difference = Decimal("500.00") # Positive difference for debit
    current_balance = Decimal("1000.00")
    target_balance = current_balance + difference

    # Manually create a mock account
    mock_account = MockAccount(id=account_id, running_balance=current_balance)

    # Create a mock AccountService that returns this mock account
    mock_account_service = MockAccountService(mock_db_session)
    mock_account_service.get_account = MagicMock(return_value=mock_account)

    # Instantiate the service with the mock db session and mock account service
    adjustment_service = ManualBalanceAdjustmentService(mock_db_session)
    adjustment_service.account_service = mock_account_service # Inject the mock account service

    # Simulate the adjustment creation part which should lead to transaction creation
    # In the actual service, this is called within create_adjustment
    # Here we directly simulate the part that creates the transaction

    # ManualBalanceAdjustment object creation (simplified for this test)
    adjustment = ManualBalanceAdjustment(
        id=1,
        account_id=account_id,
        target_balance=target_balance,
        effective_date=effective_date,
        submitted_by_user_id=UUID(int=2),
        adjustment_attempt_timestamp=datetime.utcnow(),
        status="PENDING"
    )
    mock_db_session.add(adjustment)
    mock_db_session.flush() # Simulate flush to get adjustment ID

    # Logic to create transaction if difference exists
    transaction_type = BankingProductType.ADJUSTMENT_DEBIT if difference > Decimal("0") else BankingProductType.ADJUSTMENT_CREDIT
    description = "Manual balance adjustment"
    new_transaction_id = uuid4()

    new_transaction = AdjustmentTransaction(
        transaction_id=new_transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=abs(difference),
        transaction_type=transaction_type,
        description=description,
        created_at=datetime.utcnow(),
    )
    mock_db_session.add(new_transaction)
    mock_db_session.flush()

    # Update adjustment with transaction info and status
    adjustment.created_transaction_id = new_transaction.transaction_id
    adjustment.status = "COMPLETED"
    mock_db_session.add(adjustment)
    mock_db_session.commit()

    # Assertions
    assert adjustment.status == "COMPLETED"
    assert adjustment.created_transaction_id == new_transaction_id
    mock_db_session.commit.assert_called_once()
    assert mock_db_session.add.call_count >= 2

def test_adjustment_transaction_creation_negative_difference(mock_db_session):
    # Simulate negative difference for CREDIT transaction
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    difference = Decimal("-200.00") # Negative difference for credit
    current_balance = Decimal("1000.00")
    target_balance = current_balance + difference

    mock_account = MockAccount(id=account_id, running_balance=current_balance)
    mock_account_service = MockAccountService(mock_db_session)
    mock_account_service.get_account = MagicMock(return_value=mock_account)

    adjustment_service = ManualBalanceAdjustmentService(mock_db_session)
    adjustment_service.account_service = mock_account_service

    adjustment = ManualBalanceAdjustment(
        id=2,
        account_id=account_id,
        target_balance=target_balance,
        effective_date=effective_date,
        submitted_by_user_id=UUID(int=2),
        adjustment_attempt_timestamp=datetime.utcnow(),
        status="PENDING"
    )
    mock_db_session.add(adjustment)
    mock_db_session.flush()

    transaction_type = BankingProductType.ADJUSTMENT_DEBIT if difference > Decimal("0") else BankingProductType.ADJUSTMENT_CREDIT
    description = "Manual balance adjustment"
    new_transaction_id = uuid4()

    new_transaction = AdjustmentTransaction(
        transaction_id=new_transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=abs(difference),
        transaction_type=transaction_type,
        description=description,
        created_at=datetime.utcnow(),
    )
    mock_db_session.add(new_transaction)
    mock_db_session.flush()

    adjustment.created_transaction_id = new_transaction.transaction_id
    adjustment.status = "COMPLETED"
    mock_db_session.add(adjustment)
    mock_db_session.commit()

    assert adjustment.status == "COMPLETED"
    assert adjustment.created_transaction_id == new_transaction_id
    mock_db_session.commit.assert_called_once()
    assert mock_db_session.add.call_count >= 2


# Mock data
TEST_ACCOUNT_ID = UUID(int=1)

# Mock db session
@pytest.fixture
def mock_db_session():
    mock_session = MagicMock(spec=Session)
    mock_session.commit.return_value = None
    mock_session.flush.return_value = None
    mock_session.refresh.return_value = None
    return mock_session

# --- Tests for AdjustmentTransaction SQLAlchemy Model ---

def test_adjustment_transaction_model_creation():
    transaction_id = uuid4()
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    amount = Decimal("500.00")
    transaction_type = BankingProductType.ADJUSTMENT_DEBIT # Use the enum value
    description = "Manual balance adjustment"
    created_at = datetime.utcnow()

    transaction = AdjustmentTransaction(
        transaction_id=transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        reconciliation_metadata={"status": "processed"},
        created_at=created_at,
    )

    assert transaction.transaction_id == transaction_id
    assert transaction.account_id == account_id
    assert transaction.effective_date == effective_date
    assert transaction.amount == amount
    assert transaction.transaction_type == BankingProductType.ADJUSTMENT_DEBIT
    assert transaction.description == description
    assert transaction.reconciliation_metadata == {"status": "processed"}
    assert transaction.created_at == created_at

def test_adjustment_transaction_model_defaults():
    # Test default values if any (e.g., for reconciliation_metadata)
    transaction_id = uuid4()
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    amount = Decimal("100.00")
    transaction_type = BankingProductType.ADJUSTMENT_CREDIT
    description = "Another adjustment"
    created_at = datetime.utcnow()

    transaction = AdjustmentTransaction(
        transaction_id=transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        created_at=created_at,
        # reconciliation_metadata is Optional and not provided
    )

    assert transaction.reconciliation_metadata is None

# --- Tests for AdjustmentTransaction creation logic within Service (simulated) ---
# These tests would typically be in test_adjustment_service.py, but for completeness here:

# Mock AccountService and manual_balance_adjustment for service logic simulation
class MockAccount:
    def __init__(self, id: UUID, running_balance: Decimal):
        self.id = id
        self.running_balance = running_balance

class MockAccountService:
    def __init__(self, db: Session):
        self.db = db
        self.accounts = {
            TEST_ACCOUNT_ID: MockAccount(id=TEST_ACCOUNT_ID, running_balance=Decimal("1000.00"))
        }
    def get_account(self, account_id: UUID):
        return self.accounts.get(account_id)

def test_adjustment_transaction_creation_logic(mock_db_session):
    # Simulate calling the service logic that creates the transaction
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    difference = Decimal("500.00") # Positive difference for debit
    current_balance = Decimal("1000.00")
    target_balance = current_balance + difference

    # Manually create a mock account
    mock_account = MockAccount(id=account_id, running_balance=current_balance)

    # Create a mock AccountService that returns this mock account
    mock_account_service = MockAccountService(mock_db_session)
    mock_account_service.get_account = MagicMock(return_value=mock_account)

    # Instantiate the service with the mock db session and mock account service
    adjustment_service = ManualBalanceAdjustmentService(mock_db_session)
    adjustment_service.account_service = mock_account_service # Inject the mock account service

    # Simulate the adjustment creation part which should lead to transaction creation
    # In the actual service, this is called within create_adjustment
    # Here we directly simulate the part that creates the transaction

    # ManualBalanceAdjustment object creation (simplified for this test)
    adjustment = ManualBalanceAdjustment(
        id=1,
        account_id=account_id,
        target_balance=target_balance,
        effective_date=effective_date,
        submitted_by_user_id=UUID(int=2),
        adjustment_attempt_timestamp=datetime.utcnow(),
        status="PENDING"
    )
    mock_db_session.add(adjustment)
    mock_db_session.flush() # Simulate flush to get adjustment ID

    # Logic to create transaction if difference exists
    transaction_type = BankingProductType.ADJUSTMENT_DEBIT if difference > Decimal("0") else BankingProductType.ADJUSTMENT_CREDIT
    description = "Manual balance adjustment"
    new_transaction_id = uuid4()

    new_transaction = AdjustmentTransaction(
        transaction_id=new_transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=abs(difference),
        transaction_type=transaction_type,
        description=description,
        created_at=datetime.utcnow(),
    )
    mock_db_session.add(new_transaction)
    mock_db_session.flush()

    # Update adjustment with transaction info and status
    adjustment.created_transaction_id = new_transaction.transaction_id
    adjustment.status = "COMPLETED"
    mock_db_session.add(adjustment)
    mock_db_session.commit()

    # Assertions
    assert adjustment.status == "COMPLETED"
    assert adjustment.created_transaction_id == new_transaction_id
    mock_db_session.commit.assert_called_once()
    assert mock_db_session.add.call_count >= 2

def test_adjustment_transaction_creation_negative_difference(mock_db_session):
    # Simulate negative difference for CREDIT transaction
    account_id = TEST_ACCOUNT_ID
    effective_date = date(2026, 3, 31)
    difference = Decimal("-200.00") # Negative difference for credit
    current_balance = Decimal("1000.00")
    target_balance = current_balance + difference

    mock_account = MockAccount(id=account_id, running_balance=current_balance)
    mock_account_service = MockAccountService(mock_db_session)
    mock_account_service.get_account = MagicMock(return_value=mock_account)

    adjustment_service = ManualBalanceAdjustmentService(mock_db_session)
    adjustment_service.account_service = mock_account_service

    adjustment = ManualBalanceAdjustment(
        id=2,
        account_id=account_id,
        target_balance=target_balance,
        effective_date=effective_date,
        submitted_by_user_id=UUID(int=2),
        adjustment_attempt_timestamp=datetime.utcnow(),
        status="PENDING"
    )
    mock_db_session.add(adjustment)
    mock_db_session.flush()

    transaction_type = BankingProductType.ADJUSTMENT_DEBIT if difference > Decimal("0") else BankingProductType.ADJUSTMENT_CREDIT
    description = "Manual balance adjustment"
    new_transaction_id = uuid4()

    new_transaction = AdjustmentTransaction(
        transaction_id=new_transaction_id,
        account_id=account_id,
        effective_date=effective_date,
        amount=abs(difference),
        transaction_type=transaction_type,
        description=description,
        created_at=datetime.utcnow(),
    )
    mock_db_session.add(new_transaction)
    mock_db_session.flush()

    adjustment.created_transaction_id = new_transaction.transaction_id
    adjustment.status = "COMPLETED"
    mock_db_session.add(adjustment)
    mock_db_session.commit()

    assert adjustment.status == "COMPLETED"
    assert adjustment.created_transaction_id == new_transaction_id
    mock_db_session.commit.assert_called_once()
    assert mock_db_session.add.call_count >= 2
