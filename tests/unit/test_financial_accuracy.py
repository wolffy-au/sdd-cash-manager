from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sdd_cash_manager.lib.utils import quantize_currency
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.enums import AccountingCategory
from sdd_cash_manager.models.transaction import Entry
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import BALANCING_ACCOUNT_ID, TransactionService


@pytest.fixture(scope="function")
def db_session():
    # Use a named in-memory database for shared access
    engine = create_engine("sqlite:///file:test_financial_accuracy_db?mode=memory&cache=shared")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def account_service(db_session):
    return AccountService(db_session=db_session)


@pytest.fixture
def transaction_service(db_session, account_service):
    service = TransactionService(db_session=db_session)
    service.set_account_service(account_service)
    return service


@pytest.fixture
def setup_accounts_for_accuracy(db_session, account_service):
    acc1 = account_service.create_account(
        name="Accuracy Account 1",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        available_balance=Decimal("1000.1234")
    )
    acc2 = account_service.create_account(
        name="Accuracy Account 2",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        available_balance=Decimal("500.5678")
    )
    # Ensure balancing account exists
    balancing_acc = account_service.create_account(
        name="Balancing Account",
        currency="USD",
        accounting_category=AccountingCategory.EQUITY,
        available_balance=Decimal("0.00"),
        id=BALANCING_ACCOUNT_ID
    )
    db_session.commit()
    return acc1, acc2, balancing_acc


def test_quantize_currency_accuracy():
    """Test the currency quantization helper for precision."""
    assert quantize_currency(Decimal("100.123")) == Decimal("100.12")
    assert quantize_currency(Decimal("100.125")) == Decimal("100.13") # ROUND_HALF_UP
    assert quantize_currency(Decimal("100.127")) == Decimal("100.13")
    assert quantize_currency(Decimal("100.000")) == Decimal("100.00")
    assert quantize_currency(Decimal("0.001")) == Decimal("0.00")
    assert quantize_currency(Decimal("0.005")) == Decimal("0.01")
    assert quantize_currency(Decimal("-100.123")) == Decimal("-100.12")
    assert quantize_currency(Decimal("-100.125")) == Decimal("-100.13") # ROUND_HALF_UP for negative


def test_transaction_service_ensure_double_entry_accuracy():
    """Test that _ensure_double_entry rigorously checks for exact balance."""
    # Balanced entries
    balanced_entries = [
        Entry(transaction_id=None, account_id="acc1", debit_amount=Decimal("100.00"), credit_amount=Decimal("0.00")),
        Entry(transaction_id=None, account_id="acc2", debit_amount=Decimal("0.00"), credit_amount=Decimal("100.00")),
    ]
    TransactionService()._ensure_double_entry(balanced_entries) # Should not raise

    # Unbalanced entries
    unbalanced_entries = [
        Entry(transaction_id=None, account_id="acc1", debit_amount=Decimal("100.00"), credit_amount=Decimal("0.00")),
        Entry(transaction_id=None, account_id="acc2", debit_amount=Decimal("0.00"), credit_amount=Decimal("99.99")),
    ]
    with pytest.raises(ValueError, match="Transaction entries must balance."):
        TransactionService()._ensure_double_entry(unbalanced_entries)

    # Very small imbalance (should still raise)
    small_imbalance_entries = [
        Entry(transaction_id=None, account_id="acc1", debit_amount=Decimal("100.00002"), credit_amount=Decimal("0.00")),
        Entry(transaction_id=None, account_id="acc2", debit_amount=Decimal("0.00"), credit_amount=Decimal("100.00000")),
    ]
    with pytest.raises(ValueError, match="Transaction entries must balance."):
        TransactionService()._ensure_double_entry(small_imbalance_entries)


def test_perform_balance_adjustment_accuracy(transaction_service, account_service, db_session, setup_accounts_for_accuracy):
    acc1, _, _ = setup_accounts_for_accuracy

    # Adjust balance to a new quantized value
    target_balance = Decimal("1050.55")
    adjustment_date = datetime.now(timezone.utc)

    transaction = transaction_service.perform_balance_adjustment(
        account_id=acc1.id,
        target_balance=target_balance,
        adjustment_date=adjustment_date,
        description="Precise adjustment",
        action_type="ADJUSTMENT"
    )
    db_session.commit()

    assert transaction is not None
    assert transaction.amount == Decimal("50.43") # The difference after quantization of initial balance

    updated_account = account_service.get_account(acc1.id)
    assert updated_account.available_balance == target_balance # Final balance should be exact target


def test_get_account_hierarchy_balance_accuracy(account_service, db_session):
    # Create a hierarchy
    root = account_service.create_account(
        name="Root", currency="USD", accounting_category=AccountingCategory.ASSET, available_balance=Decimal("100.00")
    )
    child1 = account_service.create_account(
        name="Child1", currency="USD", accounting_category=AccountingCategory.ASSET, parent_account_id=root.id, available_balance=Decimal("50.50")
    )
    child2 = account_service.create_account(
        name="Child2", currency="USD", accounting_category=AccountingCategory.ASSET, parent_account_id=root.id, available_balance=Decimal("25.25")
    )
    grandchild = account_service.create_account(
        name="Grandchild", currency="USD", accounting_category=AccountingCategory.ASSET, parent_account_id=child1.id, available_balance=Decimal("10.10")
    )
    db_session.commit()

    expected_total = root.available_balance + child1.available_balance + child2.available_balance + grandchild.available_balance
    expected_total_quantized = quantize_currency(expected_total)

    hierarchy_balance = account_service.get_account_hierarchy_balance(root.id)
    assert hierarchy_balance == expected_total_quantized
