"""HTTP tests covering transaction and hierarchy behaviors (User Story 2)."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_payload_keys, assert_status


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
