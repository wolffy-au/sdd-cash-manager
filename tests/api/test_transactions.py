"""HTTP tests covering transaction and hierarchy behaviors (User Story 2)."""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from sdd_cash_manager.services.transaction_service import BALANCING_ACCOUNT_ID
from tests.api.helpers import assert_payload_keys, assert_status


@pytest.mark.asyncio
async def test_perform_balance_adjustment_credit_persists_to_db(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Post an adjustment and assert the transaction is recorded with completed entries."""
    target_account = seeded_accounts["visible"]
    amount = Decimal("150.00")
    payload = {
        "amount": str(amount),
        "action_type": "CREDIT",
        "description": "Automated credit adjustment",
    }

    response = await api_client.post(
        f"/accounts/{target_account['id']}/adjustment",
        json=payload,
        headers=authenticated_headers,
    )
    assert_status(response, 201)
    transaction = response.json()
    assert transaction["status"] == "COMPLETED"
    entries = transaction.get("entries", [])
    assert isinstance(entries, list)
    recorded_amounts = {str(entry.get("amount")) for entry in entries}
    assert payload["amount"] in recorded_amounts
    assert BALANCING_ACCOUNT_ID in {entry.get("account_id") for entry in entries}
    assert target_account["id"] in {entry.get("account_id") for entry in entries}
    assert_payload_keys(transaction, {"transaction_id", "status", "entries"})


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

    adjustment_payload = {
        "amount": str(adjustment_amount),
        "action_type": "CREDIT",
        "description": "Balance check adjustment",
    }

    post_resp = await api_client.post(
        f"/accounts/{target_account['id']}/adjustment",
        json=adjustment_payload,
        headers=authenticated_headers,
    )
    assert_status(post_resp, 201)

    balance_resp = await api_client.get(
        f"/accounts/{target_account['id']}/balance", headers=authenticated_headers
    )
    assert_status(balance_resp, 200)
    balance_body = balance_resp.json()
    updated_balance = Decimal(str(balance_body["available_balance"]))
    assert updated_balance == initial_balance + adjustment_amount
