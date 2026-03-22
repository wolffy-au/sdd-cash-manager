"""HTTP tests covering transaction and hierarchy behaviors (User Story 2)."""

import logging
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient

from sdd_cash_manager.database import SessionLocal
from sdd_cash_manager.models.enums import ProcessingStatus, ReconciliationStatus
from sdd_cash_manager.models.transaction import Transaction
from tests.api.helpers import assert_payload_keys, assert_status

logger = logging.getLogger(__name__)  # Initialize logger


@pytest.mark.asyncio
async def test_perform_balance_adjustment_credit_persists_to_db(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Post an adjustment and assert the transaction is recorded with completed entries."""
    target_account = seeded_accounts["visible"]
    initial_balance = Decimal(str(target_account["available_balance"]))
    target_balance = initial_balance + Decimal("150.00")
    adjustment_date = date.today().isoformat()
    payload = {
        "target_balance": str(target_balance),
        "adjustment_date": adjustment_date,
        "description": "Automated credit adjustment",
        "action_type": "ADJUSTMENT",
    }

    response = await api_client.post(
        f"/accounts/{target_account['id']}/adjustment",
        json=payload,
        headers=authenticated_headers,
    )
    assert_status(response, 200)
    transaction = response.json()
    assert transaction["account_id"] == target_account["id"]
    assert Decimal(str(transaction["new_balance"])) == target_balance
    adjustment_amount = target_balance - initial_balance
    assert Decimal(str(transaction["amount"])) == adjustment_amount
    assert transaction["processing_status"] == "Posted"
    assert transaction["reconciliation_status"] == "Pending Reconciliation"
    assert_payload_keys(
        transaction,
        {
            "transaction_id",
            "account_id",
            "new_balance",
            "amount",
            "processing_status",
            "reconciliation_status",
        },
    )


@pytest.mark.asyncio
async def test_balance_endpoint_reflects_adjustments(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Verify that hierarchy balance changes after an adjustment."""
    target_account = seeded_accounts["visible"]
    initial_balance = Decimal(str(target_account["available_balance"]))
    adjustment_amount = Decimal("75.00")
    target_balance = initial_balance + adjustment_amount
    adjustment_date = date.today().isoformat()

    adjustment_payload = {
        "target_balance": str(target_balance),
        "adjustment_date": adjustment_date,
        "description": "Balance check adjustment",
        "action_type": "ADJUSTMENT",
    }

    post_resp = await api_client.post(
        f"/accounts/{target_account['id']}/adjustment",
        json=adjustment_payload,
        headers=authenticated_headers,
    )
    assert_status(post_resp, 200)

    get_resp = await api_client.get(
        f"/accounts/{target_account['id']}", headers=authenticated_headers
    )
    assert_status(get_resp, 200)
    account_body = get_resp.json()
    updated_balance = Decimal(str(account_body["available_balance"]))
    assert updated_balance == target_balance
    assert Decimal(str(account_body["hierarchy_balance"])) == target_balance


@pytest.mark.asyncio
async def test_record_transaction_updates_both_accounts(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """POST /transactions/ should create balanced entries and refresh the affected balances."""
    source_account = seeded_accounts["visible"]
    target_account = seeded_accounts["balancing"]
    amount = Decimal("125.50")

    payload = {
        "transfer_from": source_account["id"],
        "transfer_to": target_account["id"],
        "action": "Transfer",
        "amount": str(amount),
        "currency": "USD",
        "description": "Test double-entry transaction",
        "memo": "API quick entry",
        "date": date.today().isoformat(),
    }

    response = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
    assert_status(response, 201)
    body = response.json()
    assert_payload_keys(body, {"transaction_id", "amount", "entries", "processing_status", "reconciliation_status", "notes"})
    assert Decimal(str(body["amount"])) == amount
    assert body["processing_status"] == "Posted"
    assert body["reconciliation_status"] == "Pending Reconciliation"
    assert body["notes"] == "API quick entry"

    entries = body["entries"]
    assert len(entries) == 2
    debit_entry = next(entry for entry in entries if entry["account_id"] == source_account["id"])
    credit_entry = next(entry for entry in entries if entry["account_id"] == target_account["id"])
    assert Decimal(str(debit_entry["debit_amount"])) == amount
    assert Decimal(str(debit_entry["credit_amount"])) == Decimal("0")
    assert Decimal(str(credit_entry["credit_amount"])) == amount
    assert Decimal(str(credit_entry["debit_amount"])) == Decimal("0")

    source_resp = await api_client.get(f"/accounts/{source_account['id']}", headers=authenticated_headers)
    assert_status(source_resp, 200)
    new_source_balance = Decimal(str(source_resp.json()["available_balance"]))
    assert new_source_balance == Decimal(str(source_account["available_balance"])) - amount

    target_resp = await api_client.get(f"/accounts/{target_account['id']}", headers=authenticated_headers)
    assert_status(target_resp, 200)
    new_target_balance = Decimal(str(target_resp.json()["available_balance"]))
    assert new_target_balance == Decimal(str(target_account["available_balance"])) + amount


@pytest.mark.asyncio
async def test_reconcile_window_zero_difference_flow(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Ensure adding transactions to a reconciliation session drives the Difference to zero."""
    source = seeded_accounts["visible"]
    target = seeded_accounts["balancing"]
    amount = Decimal("45.00")

    payload = {
        "transfer_from": source["id"],
        "transfer_to": target["id"],
        "action": "Recon Test",
        "amount": str(amount),
        "currency": "USD",
        "description": "Reconcile test transaction",
        "memo": "Reconcile flow",
        "date": date.today().isoformat(),
    }

    creation_resp = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
    assert_status(creation_resp, 201)
    transaction = creation_resp.json()
    transaction_id = transaction["transaction_id"]

    with SessionLocal() as session:
        txn = session.get(Transaction, transaction_id)
        assert txn is not None
        txn.processing_status = ProcessingStatus.COMPLETED
        txn.reconciliation_status = ReconciliationStatus.UNCLEARED
        session.add(txn)
        session.commit()

    session_payload = {
        "statement_date": date.today().isoformat(),
        "ending_balance": str(amount),
    }
    session_resp = await api_client.post(
        "/reconciliation/sessions",
        json=session_payload,
        headers=authenticated_headers,
    )
    assert_status(session_resp, 200)
    session_body = session_resp.json()
    assert session_body["difference"] == str(amount)
    assert session_body["state"] == "IN_PROGRESS"

    unreconciled_resp = await api_client.get(
        "/reconciliation/sessions/unreconciled",
        headers=authenticated_headers,
    )
    assert_status(unreconciled_resp, 200)
    entries_payload = unreconciled_resp.json()
    entries = entries_payload.get("transactions", [])
    print("DEBUG ENTRIES", entries_payload)
    assert any(entry["id"] == transaction_id for entry in entries)

    update_resp = await api_client.post(
        f"/reconciliation/sessions/{session_body['id']}/transactions",
        json={"transaction_ids": [transaction_id]},
        headers=authenticated_headers,
    )
    assert_status(update_resp, 200)
    diff_body = update_resp.json()
    assert Decimal(str(diff_body["difference"])) == Decimal("0")
    assert diff_body["difference_status"] == "balanced"
    assert diff_body["remaining_uncleared"] == 0


@pytest.mark.asyncio
async def test_unreconciled_transactions_endpoint_filters_by_cutoff_and_status(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Ensure the unreconciled endpoint respects cutoff dates and status filters."""
    source = seeded_accounts["visible"]
    target = seeded_accounts["balancing"]
    today = date.today()
    older_date = today - timedelta(days=5)

    async def create_txn(txn_date: date) -> str:
        payload = {
            "transfer_from": source["id"],
            "transfer_to": target["id"],
            "action": "Recon Filter Test",
            "amount": "10.00",
            "currency": "USD",
            "description": "Filtered transaction",
            "memo": "Reconcile filter",
            "date": txn_date.isoformat(),
        }
        response = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
        assert_status(response, 201)
        body = response.json()
        return str(body["transaction_id"])

    old_transaction_id = await create_txn(older_date)
    recent_transaction_id = await create_txn(today)
    failed_transaction_id = await create_txn(today)

    with SessionLocal() as session:
        for txn_id, processing_status, reconciliation_status in [
            (old_transaction_id, ProcessingStatus.COMPLETED, ReconciliationStatus.RECONCILED),
            (recent_transaction_id, ProcessingStatus.COMPLETED, ReconciliationStatus.UNCLEARED),
            (failed_transaction_id, ProcessingStatus.FAILED, ReconciliationStatus.UNCLEARED),
        ]:
            transaction = session.get(Transaction, txn_id)
            assert transaction is not None
            transaction.processing_status = processing_status
            transaction.reconciliation_status = reconciliation_status
            session.add(transaction)
        session.commit()

    session_payload = {
        "statement_date": today.isoformat(),
        "ending_balance": "0.00",
    }
    session_resp = await api_client.post("/reconciliation/sessions", json=session_payload, headers=authenticated_headers)
    assert_status(session_resp, 200)

    unreconciled_resp = await api_client.get("/reconciliation/sessions/unreconciled", headers=authenticated_headers)
    assert_status(unreconciled_resp, 200)
    payload = unreconciled_resp.json()
    transactions = payload.get("transactions", [])
    assert len(transactions) == 1
    listed_txn = transactions[0]
    assert listed_txn["id"] == recent_transaction_id
    assert listed_txn["processing_status"] == ProcessingStatus.COMPLETED.value
    assert listed_txn["reconciliation_status"] == ReconciliationStatus.UNCLEARED.value
