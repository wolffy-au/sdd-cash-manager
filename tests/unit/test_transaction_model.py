import uuid
from datetime import datetime, timezone  # uses timezone.utc for timezone-aware inputs
from typing import Any
from unittest.mock import MagicMock

import pytest

from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Entry, Transaction


@pytest.fixture(autouse=True)
def mock_uuid(monkeypatch):
    mock_uuid = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    monkeypatch.setattr(
        "sdd_cash_manager.models.transaction.uuid.uuid4",
        MagicMock(return_value=mock_uuid)
    )


def _build_common_entry_kwargs() -> dict[str, Any]:
    return {
        "transaction_id": "tx-id",
        "account_id": "acc-1",
        "notes": "note",
        "created_at": datetime.now(),
    }


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

    assert transaction.id == str(uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
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

    with pytest.raises(ValueError, match="Description cannot be empty."):
        Transaction(
            effective_date=now,
            booking_date=now,
            description="",
            amount=100.00,
            debit_account_id="acc-debit",
            credit_account_id="acc-credit",
            action_type="Test"
        )

    with pytest.raises(ValueError, match="Debit account ID cannot be empty."):
        Transaction(
            effective_date=now,
            booking_date=now,
            description="Missing Debit",
            amount=100.00,
            debit_account_id="",
            credit_account_id="acc-credit",
            action_type="Test"
        )

    with pytest.raises(ValueError, match="Credit account ID cannot be empty."):
        Transaction(
            effective_date=now,
            booking_date=now,
            description="Missing Credit",
            amount=100.00,
            debit_account_id="acc-debit",
            credit_account_id="",
            action_type="Test"
        )


def test_entry_rejects_negative_amounts() -> None:
    with pytest.raises(ValueError):
        Entry(debit_amount=-1.0, credit_amount=0.0, **_build_common_entry_kwargs())


def test_entry_rejects_simultaneous_debit_and_credit() -> None:
    with pytest.raises(ValueError):
        Entry(debit_amount=50.0, credit_amount=50.0, **_build_common_entry_kwargs())


def test_entry_rejects_zero_amounts() -> None:
    with pytest.raises(ValueError):
        Entry(debit_amount=0.0, credit_amount=0.0, **_build_common_entry_kwargs())


def test_transaction_builds_balanced_entries() -> None:
    transaction = Transaction(
        effective_date=datetime.now(timezone.utc),
        booking_date=datetime.now(timezone.utc),
        description="Adjustment",
        amount=120.0,
        debit_account_id="debit-id",
        credit_account_id="credit-id",
        action_type="ADJUSTMENT"
    )

    assert len(transaction.entries) == 2
    total_debits = sum(entry.debit_amount for entry in transaction.entries)
    total_credits = sum(entry.credit_amount for entry in transaction.entries)
    assert total_debits == total_credits == 120.0


def test_transaction_rejects_unbalanced_entries() -> None:
    entries = [
        Entry(transaction_id="tx", account_id="a", debit_amount=100.0, credit_amount=0.0),
        Entry(transaction_id="tx", account_id="b", debit_amount=0.0, credit_amount=40.0),
    ]
    with pytest.raises(ValueError):
        Transaction(
            effective_date=datetime.now(timezone.utc),
            booking_date=datetime.now(timezone.utc),
            description="Bad",
            amount=100.0,
            debit_account_id="a",
            credit_account_id="b",
            action_type="ADJUSTMENT",
            entries=entries
        )
