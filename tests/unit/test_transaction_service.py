import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.enums import AccountingCategory, ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.quickfill_template import QuickFillTemplate
from sdd_cash_manager.models.transaction import Entry, Transaction
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import BALANCING_ACCOUNT_ID, TransactionService


# Mocking uuid.uuid4 for deterministic IDs
@pytest.fixture(autouse=True)
def mock_uuid(monkeypatch):
    uuids_list = [
        uuid.UUID('00000000-0000-0000-0000-000000000001'), # Acc1 in setup
        uuid.UUID('00000000-0000-0000-0000-000000000002'), # Acc2 in setup
        uuid.UUID('00000000-0000-0000-0000-000000000003'), # Balancing Acc in setup
        uuid.UUID('00000000-0000-0000-0000-000000000004'), # Tx in test_create_transaction_persists_to_db
        uuid.UUID('00000000-0000-0000-0000-000000000005'), # Entry 1 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000006'), # Entry 2 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000007'), # Tx in test_get_transaction_from_db
        uuid.UUID('00000000-0000-0000-0000-000000000008'), # Entry 1 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000009'), # Entry 2 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000010'), # Tx1 in test_get_transactions_by_account_from_db
        uuid.UUID('00000000-0000-0000-0000-000000000011'), # Entry 1 for Tx1
        uuid.UUID('00000000-0000-0000-0000-000000000012'), # Entry 2 for Tx1
        uuid.UUID('00000000-0000-0000-0000-000000000013'), # Tx2 in test_get_transactions_by_account_from_db
        uuid.UUID('00000000-0000-0000-0000-000000000014'), # Entry 1 for Tx2
        uuid.UUID('00000000-0000-0000-0000-000000000015'), # Entry 2 for Tx2
        uuid.UUID('00000000-0000-0000-0000-000000000016'), # Tx3 in test_get_transactions_by_account_from_db
        uuid.UUID('00000000-0000-0000-0000-000000000017'), # Tx in test_update_transaction_status_persists_to_db
        uuid.UUID('00000000-0000-0000-0000-000000000018'), # Entry 1 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000019'), # Entry 2 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000020'), # Tx in test_perform_balance_adjustment_credit_persists_to_db
        uuid.UUID('00000000-0000-0000-0000-000000000021'), # Entry 1 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000022'), # Entry 2 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000023'), # Tx in test_perform_balance_adjustment_debit_persists_to_db
        uuid.UUID('00000000-0000-0000-0000-000000000024'), # Entry 1 for above Tx
        uuid.UUID('00000000-0000-0000-0000-000000000025'), # Entry 2 for above Tx
    ]
    monkeypatch.setattr(uuid, 'uuid4', MagicMock(side_effect=uuids_list))


@pytest.fixture(scope="function")
def db_session():
    # Use a named in-memory database for shared access
    db_file = Path("file:test_db_tx")
    engine = create_engine(f"sqlite:///{db_file}?mode=memory&cache=shared")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        if db_file.exists():
            db_file.unlink()


@pytest.fixture
def account_service(db_session):
    return AccountService(db_session=db_session)


@pytest.fixture
def transaction_service(db_session, account_service):
    service = TransactionService(db_session=db_session)
    service.set_account_service(account_service)
    return service


@pytest.fixture
def setup_accounts(db_session, account_service):
    acc1 = account_service.create_account(
        name="Checking Account",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        available_balance=Decimal("1000.00")
    )
    acc2 = account_service.create_account(
        name="Savings Account",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        available_balance=Decimal("500.00")
    )
    # Create a balancing account for adjustments
    account_service.delete_account(BALANCING_ACCOUNT_ID)
    balancing_acc = account_service.create_account(
        name="Balancing Account",
        currency="USD",
        accounting_category=AccountingCategory.EQUITY, # or appropriate category
        available_balance=Decimal("0.00"),
        id=BALANCING_ACCOUNT_ID # Use the predefined ID
    )
    db_session.commit()
    return acc1, acc2, balancing_acc

def test_acquire_session_uses_factory():
    sentinel = MagicMock()
    service = TransactionService(session_factory=lambda: sentinel)
    session, should_close = service._acquire_session()
    assert session is sentinel
    assert should_close is True

def test_validate_string_field_min_length():
    with pytest.raises(ValueError, match="field must be at least 2 characters long."):
        TransactionService._validate_string_field("x", "field", min_length=2)

def test_validate_string_field_allowed_chars():
    with pytest.raises(ValueError, match="contains invalid characters"):
        TransactionService._validate_string_field(
            "abc-123",
            "field",
            allowed_chars_regex=r"[A-Za-z0-9]+"
        )


def test_get_transaction_without_db_session_raises():
    service = TransactionService()
    with pytest.raises(
        RuntimeError,
        match="TransactionService must be used with a database session to get transactions."
    ):
        service.get_transaction("txn-id")


def test_get_transaction_requires_active_session():
    service = TransactionService(session_factory=lambda: MagicMock())
    service.db_session = None
    with pytest.raises(
        ValueError,
        match="Database session is required to retrieve transactions."
    ):
        service.get_transaction("txn-id")


class _FailingSession:
    def add(self, _):
        raise RuntimeError("forced failure")

    def flush(self):
        pass

    def refresh(self, _):
        pass

    def close(self):
        pass


def test_transaction_service_acquire_session_without_db_raises(monkeypatch):
    service = TransactionService()
    monkeypatch.setattr(
        "sdd_cash_manager.services.transaction_service.log_critical_application_error",
        lambda *args, **kwargs: None
    )
    with pytest.raises(
        RuntimeError,
        match="Failed to acquire database session for transaction service due to unexpected error."
    ):
        service._acquire_session()


@pytest.mark.parametrize(
    "scenario, expected_match",
    [
        ("same_accounts", "Debit and credit accounts cannot be the same."),
        ("non_positive_amount", "Transaction amount must be greater than zero."),
        ("missing_action_type", "Debit account ID, credit account ID, and action type are required."),
    ]
)
def test_create_transaction_validation_errors(transaction_service, setup_accounts, scenario, expected_match):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    if scenario == "same_accounts":
        debit_id = acc1.id
        credit_id = acc1.id
        amount = Decimal("100.00")
        action_type = "Test"
    elif scenario == "non_positive_amount":
        debit_id = acc1.id
        credit_id = acc2.id
        amount = Decimal("0.00")
        action_type = "Test"
    else:
        debit_id = acc1.id
        credit_id = acc2.id
        amount = Decimal("10.00")
        action_type = ""

    with pytest.raises(ValueError, match=expected_match):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="Validation Scenario",
            amount=amount,
            debit_account_id=debit_id,
            credit_account_id=credit_id,
            action_type=action_type
        )


def test_ensure_double_entry_raises_when_unbalanced(transaction_service):
    entries = [
        Entry(transaction_id=None, account_id="acc-1", debit_amount=Decimal("100.00"), credit_amount=Decimal("0.0")),
        Entry(transaction_id=None, account_id="acc-2", debit_amount=Decimal("0.0"), credit_amount=Decimal("50.00"))
    ]
    with pytest.raises(ValueError, match="Transaction entries must balance."):
        transaction_service._ensure_double_entry(entries)


def test_create_transaction_persists_to_db(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)
    amount = Decimal("150.75")

    transaction = transaction_service.create_transaction(
        effective_date=now,
        booking_date=now,
        description="Test Deposit",
        amount=amount,
        debit_account_id=acc1.id,
        credit_account_id=acc2.id,
        action_type="Deposit"
    )
    db_session.commit()

    # Verify transaction is in DB
    retrieved_tx = db_session.get(Transaction, transaction.id)
    assert retrieved_tx is not None
    assert retrieved_tx.id == transaction.id
    assert retrieved_tx.description == "Test Deposit"
    assert retrieved_tx.amount == amount

    # Verify entries are in DB
    retrieved_entries = db_session.scalars(
        select(Entry).where(Entry.transaction_id == transaction.id)
    ).all()
    assert len(retrieved_entries) == 2
    assert any(e.account_id == acc1.id and e.debit_amount == amount for e in retrieved_entries)
    assert any(e.account_id == acc2.id and e.credit_amount == amount for e in retrieved_entries)


def test_create_transaction_session_failure(monkeypatch):
    monkeypatch.setattr(
        "sdd_cash_manager.services.transaction_service.log_critical_application_error",
        lambda *args, **kwargs: None
    )
    service = TransactionService(session_factory=lambda: cast(Session, _FailingSession()))
    now = datetime.now(timezone.utc)
    with pytest.raises(RuntimeError, match="Failed to create transaction"):
        service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="Should fail",
            amount=Decimal("100.00"),
            debit_account_id="acc-debit",
            credit_account_id="acc-credit",
            action_type="Test"
        )


def test_get_transaction_from_db(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)
    transaction = transaction_service.create_transaction(
        effective_date=now,
        booking_date=now,
        description="Fetch Test",
        amount=Decimal("200.00"),
        debit_account_id=acc1.id,
        credit_account_id=acc2.id,
        action_type="Transfer"
    )
    db_session.commit()

    retrieved_tx = transaction_service.get_transaction(transaction.id)
    assert retrieved_tx is not None
    assert retrieved_tx.id == transaction.id
    assert retrieved_tx.description == "Fetch Test"

    assert transaction_service.get_transaction(str(uuid.uuid4())) is None


def test_get_transactions_by_account_requires_db():
    service = TransactionService()
    with pytest.raises(
        RuntimeError,
        match="TransactionService must be used with a database session to get transactions by account."
    ):
        service.get_transactions_by_account("acc-1")


def test_get_transactions_by_account_session_error(monkeypatch):
    monkeypatch.setattr(
        "sdd_cash_manager.services.transaction_service.log_critical_application_error",
        lambda *args, **kwargs: None
    )

    class _BadScaler:
        def scalars(self, _):
            raise RuntimeError("boom")

        def close(self):
            pass

    service = TransactionService(session_factory=lambda: cast(Session, _BadScaler()))
    with pytest.raises(
        RuntimeError,
        match="Failed to retrieve transactions for account acc-1"
    ):
        service.get_transactions_by_account("acc-1")


def test_get_transactions_by_account_from_db(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    tx1 = transaction_service.create_transaction(now, now, "Tx1", Decimal("100.00"), acc1.id, acc2.id, "Type1")
    tx2 = transaction_service.create_transaction(now, now, "Tx2", Decimal("50.00"), acc2.id, acc1.id, "Type2")
    tx3 = transaction_service.create_transaction(now, now, "Tx3", Decimal("25.00"), acc1.id, acc2.id, "Type3",
                                                 entries=[Entry(transaction_id=None, account_id=acc1.id, debit_amount=Decimal("25.00"), credit_amount=Decimal("0.0")),
                                                          Entry(transaction_id=None, account_id=acc2.id, debit_amount=Decimal("0.0"), credit_amount=Decimal("25.00"))]) # Balanced entries
    db_session.commit()

    txs_for_acc1 = transaction_service.get_transactions_by_account(acc1.id)
    assert len(txs_for_acc1) == 3
    assert {tx.id for tx in txs_for_acc1} == {tx1.id, tx2.id, tx3.id}

    txs_for_acc2 = transaction_service.get_transactions_by_account(acc2.id)
    assert len(txs_for_acc2) == 3
    assert {tx.id for tx in txs_for_acc2} == {tx1.id, tx2.id, tx3.id}


def test_update_transaction_status_requires_db():
    service = TransactionService()
    with pytest.raises(
        RuntimeError,
        match="TransactionService must be used with a database session to update transaction status."
    ):
        service.update_transaction_status("txn-id", processing_status=ProcessingStatus.POSTED)


def test_update_transaction_status_persists_to_db(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)
    transaction = transaction_service.create_transaction(
        effective_date=now,
        booking_date=now,
        description="Status Update Test",
        amount=Decimal("300.00"),
        debit_account_id=acc1.id,
        credit_account_id=acc2.id,
        action_type="Test"
    )
    db_session.commit()

    transaction_service.update_transaction_status(
        transaction.id,
        processing_status=ProcessingStatus.POSTED,
        reconciliation_status=ReconciliationStatus.RECONCILED
    )
    db_session.commit()

    retrieved_tx = db_session.get(Transaction, transaction.id)
    assert retrieved_tx is not None
    assert retrieved_tx.processing_status == ProcessingStatus.POSTED
    assert retrieved_tx.reconciliation_status == ReconciliationStatus.RECONCILED

    # Test updating only one status
    transaction_service.update_transaction_status(
        transaction.id,
        processing_status=ProcessingStatus.FAILED
    )
    db_session.commit()

    retrieved_tx_partially = db_session.get(Transaction, transaction.id)
    assert retrieved_tx_partially is not None
    assert retrieved_tx_partially.processing_status == ProcessingStatus.FAILED
    assert retrieved_tx_partially.reconciliation_status == ReconciliationStatus.RECONCILED


def test_perform_balance_adjustment_credit_persists_to_db(transaction_service, account_service, db_session, setup_accounts):
    acc1, _, balancing_acc = setup_accounts
    initial_balance = account_service.get_account(acc1.id).available_balance
    target_balance = initial_balance + Decimal("250.75") # Increase balance
    adjustment_date = datetime(2026, 2, 25, 10, 0, 0, tzinfo=timezone.utc)
    description = "Customer Payment Received"

    transaction = transaction_service.perform_balance_adjustment(
        account_id=acc1.id,
        target_balance=target_balance,
        adjustment_date=adjustment_date,
        description=description,
        action_type="Customer Payment"
    )
    db_session.commit()

    assert transaction is not None
    assert transaction.amount == Decimal("250.75")
    assert transaction.debit_account_id == balancing_acc.id # Debited from balancing account
    assert transaction.credit_account_id == acc1.id # Credited to acc1
    assert transaction.processing_status == ProcessingStatus.POSTED

    # Verify transaction and entries are in DB
    retrieved_tx = db_session.get(Transaction, transaction.id)
    assert retrieved_tx is not None
    assert retrieved_tx.description == f"{description} for account {acc1.name}"
    assert retrieved_tx.amount == Decimal("250.75")

    retrieved_entries = db_session.scalars(
        select(Entry).where(Entry.transaction_id == transaction.id)
    ).all()
    assert len(retrieved_entries) == 2
    assert any(e.account_id == balancing_acc.id and e.debit_amount == Decimal("250.75") for e in retrieved_entries)
    assert any(e.account_id == acc1.id and e.credit_amount == Decimal("250.75") for e in retrieved_entries)

    # Verify account balance was updated in DB
    updated_account = db_session.get(Account, acc1.id)
    assert updated_account.available_balance == target_balance


def test_perform_balance_adjustment_debit_persists_to_db(transaction_service, account_service, db_session, setup_accounts):
    _, acc2, balancing_acc = setup_accounts
    initial_balance = account_service.get_account(acc2.id).available_balance
    target_balance = initial_balance - Decimal("250.00") # Decrease balance
    adjustment_date = datetime(2026, 2, 25, 11, 0, 0, tzinfo=timezone.utc)
    description = "Customer Refund Issued"

    transaction = transaction_service.perform_balance_adjustment(
        account_id=acc2.id,
        target_balance=target_balance,
        adjustment_date=adjustment_date,
        description=description,
        action_type="Customer Refund"
    )
    db_session.commit()

    assert transaction is not None
    assert transaction.amount == Decimal("250.00")
    assert transaction.debit_account_id == acc2.id # Debited from acc2
    assert transaction.credit_account_id == balancing_acc.id # Credited to balancing account
    assert transaction.processing_status == ProcessingStatus.POSTED

    # Verify transaction and entries are in DB
    retrieved_tx = db_session.get(Transaction, transaction.id)
    assert retrieved_tx is not None
    assert retrieved_tx.description == f"{description} for account {acc2.name}"
    assert retrieved_tx.amount == Decimal("250.00")

    retrieved_entries = db_session.scalars(
        select(Entry).where(Entry.transaction_id == transaction.id)
    ).all()
    assert len(retrieved_entries) == 2
    assert any(e.account_id == acc2.id and e.debit_amount == Decimal("250.00") for e in retrieved_entries)
    assert any(e.account_id == balancing_acc.id and e.credit_amount == Decimal("250.00") for e in retrieved_entries)

    # Verify account balance was updated in DB
    updated_account = db_session.get(Account, acc2.id)
    assert updated_account.available_balance == target_balance


def test_perform_balance_adjustment_no_change_persists(transaction_service, account_service, db_session, setup_accounts):
    acc1, _, _ = setup_accounts
    initial_balance = account_service.get_account(acc1.id).available_balance

    transaction = transaction_service.perform_balance_adjustment(
        account_id=acc1.id,
        target_balance=initial_balance,
        adjustment_date=datetime.now(timezone.utc),
        description="No change needed",
        action_type="No Change"
    )
    db_session.commit()

    assert transaction is None # No transaction should be created

    # Verify no transaction was created in DB
    txs = db_session.scalars(select(Transaction)).all()
    assert len(txs) == 0

    # Verify account balance was not updated (remains initial_balance)
    updated_account = db_session.get(Account, acc1.id)
    assert updated_account.available_balance == initial_balance


def test_perform_balance_adjustment_no_net_change_returns_none(
    transaction_service,
    account_service,
    setup_accounts
):
    acc1, _, _ = setup_accounts
    current_balance = account_service.get_account(acc1.id).available_balance

    result = transaction_service.perform_balance_adjustment(
        account_id=acc1.id,
        target_balance=current_balance,
        adjustment_date=datetime.now(timezone.utc),
        description="No net change",
        action_type="No Change"
    )

    assert result is None


def test_create_transaction_string_field_validation_description(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    # Test description too long
    with pytest.raises(ValueError, match="description cannot exceed 255 characters."):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="a" * 256,
            amount=Decimal("10.00"),
            debit_account_id=acc1.id,
            credit_account_id=acc2.id,
            action_type="Test"
        )
    db_session.rollback()

    # Test description with forbidden characters
    with pytest.raises(ValueError, match="description contains forbidden characters"):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="Description <Script>",
            amount=Decimal("10.00"),
            debit_account_id=acc1.id,
            credit_account_id=acc2.id,
            action_type="Test"
        )
    db_session.rollback()


def test_create_transaction_string_field_validation_notes(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    # Test notes too long
    with pytest.raises(ValueError, match="notes cannot exceed 500 characters."):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="Valid Description",
            amount=Decimal("10.00"),
            debit_account_id=acc1.id,
            credit_account_id=acc2.id,
            action_type="Test",
            notes="a" * 501
        )
    db_session.rollback()

    # Test notes with forbidden characters
    with pytest.raises(ValueError, match="notes contains forbidden characters"):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description="Valid Description",
            amount=Decimal("10.00"),
            debit_account_id=acc1.id,
            credit_account_id=acc2.id,
            action_type="Test",
            notes="Notes with <script>"
        )
    db_session.rollback()


def test_perform_balance_adjustment_account_not_found_raises_error(transaction_service, db_session):
    with pytest.raises(ValueError, match="Account with ID non-existent-id not found."):
        transaction_service.perform_balance_adjustment(
            account_id="non-existent-id",
            target_balance=Decimal("100.00"),
            adjustment_date=datetime.now(timezone.utc),
            description="Should fail",
            action_type="Fail Test"
        )
    # Ensure no transaction was created if account not found
    db_session.rollback() # Rollback any pending operations
    txs = db_session.scalars(select(Transaction)).all()
    assert len(txs) == 0


def test_perform_balance_adjustment_no_account_service_raises_error(db_session):
    service = TransactionService(db_session=db_session)
    # Ensure account_service is not set
    service.account_service = None

    with pytest.raises(RuntimeError, match="AccountService is not set."):
        service.perform_balance_adjustment(
            account_id="acc-mock-1",
            target_balance=Decimal("100.00"),
            adjustment_date=datetime.now(timezone.utc),
            description="Should fail",
            action_type="Test Failure"
        )
    db_session.rollback() # Rollback any pending operations


def test_perform_balance_adjustment_update_account_missing(transaction_service, account_service, db_session, setup_accounts, monkeypatch):
    acc1, _, _ = setup_accounts
    target_balance = account_service.get_account(acc1.id).available_balance + Decimal("50.00")
    monkeypatch.setattr(account_service, "update_account", MagicMock(return_value=None))

    with pytest.raises(ValueError, match=f"Account with ID {acc1.id} not found."):
        transaction_service.perform_balance_adjustment(
            account_id=acc1.id,
            target_balance=target_balance,
            adjustment_date=datetime.now(timezone.utc),
            description="Missing update",
            action_type="Adjust"
        )
    db_session.rollback()


def test_perform_balance_adjustment_unexpected_error(transaction_service, account_service, db_session, setup_accounts, monkeypatch):
    acc1, _, _ = setup_accounts
    target_balance = account_service.get_account(acc1.id).available_balance + Decimal("25.00")
    monkeypatch.setattr(
        "sdd_cash_manager.services.transaction_service.log_critical_application_error",
        lambda *args, **kwargs: None
    )
    monkeypatch.setattr(account_service, "record_balance_snapshot", MagicMock(side_effect=TypeError("boom")))

    with pytest.raises(RuntimeError, match=f"Failed to perform balance adjustment for account {acc1.id}"):
        transaction_service.perform_balance_adjustment(
            account_id=acc1.id,
            target_balance=target_balance,
            adjustment_date=datetime.now(timezone.utc),
            description="Unexpected failure",
            action_type="Adjust"
        )
    db_session.rollback()


def test_quickfill_candidate_created_after_transaction(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    transaction_service.create_transaction(
        effective_date=now,
        booking_date=now,
        description="QuickFill seed entry",
        amount=Decimal("75.00"),
        debit_account_id=acc1.id,
        credit_account_id=acc2.id,
        action_type="Repeat",
        currency="USD",
        notes="memo quickfill",
    )
    db_session.commit()

    template = db_session.scalars(select(QuickFillTemplate)).one()
    assert template.action == "Repeat"
    assert template.history_count == 1
    assert template.source_transaction_id is not None
    assert not template.is_approved


def test_quickfill_history_increments_and_can_be_approved(transaction_service, db_session, setup_accounts):
    acc1, acc2, _ = setup_accounts
    now = datetime.now(timezone.utc)

    for offset in range(2):
        transaction_service.create_transaction(
            effective_date=now,
            booking_date=now,
            description=f"QuickFill repetition {offset}",
            amount=Decimal("80.00"),
            debit_account_id=acc1.id,
            credit_account_id=acc2.id,
            action_type="Batch",
            currency="USD",
            notes="memo quickfill",
        )
    db_session.commit()

    template = db_session.scalars(select(QuickFillTemplate)).one()
    assert template.history_count == 2
    approved_template = transaction_service.approve_quickfill_template(template.id, approved_by="tester")
    assert approved_template.is_approved
    assert approved_template.approved_at is not None
    assert approved_template.confidence_score > Decimal("0")
