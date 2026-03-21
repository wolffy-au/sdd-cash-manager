"""API tests for QuickFill suggestions (User Story 2)."""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_status


@pytest.mark.asyncio
async def test_quickfill_suggestion_and_approval_workflow(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Creating a transaction seeds QuickFill history without mutating balances during lookups."""
    source_account = seeded_accounts["visible"]
    target_account = seeded_accounts["balancing"]
    amount = Decimal("50.00")

    payload = {
        "transfer_from": source_account["id"],
        "transfer_to": target_account["id"],
        "action": "Transfer",
        "amount": str(amount),
        "currency": "USD",
        "description": "QuickFill seed entry",
        "memo": "API suggestion test",
        "date": date.today().isoformat(),
    }

    txn_response = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
    assert_status(txn_response, 201)

    note_before = await api_client.get(f"/accounts/{source_account['id']}", headers=authenticated_headers)
    assert_status(note_before, 200)
    source_balance_before = Decimal(str(note_before.json()["available_balance"]))

    suggestion_response = await api_client.get(
        "/quickfill/",
        params={
            "action": "Transfer",
            "currency": "USD",
            "query": "API",
            "include_unapproved": True,
            "limit": 1,
        },
        headers=authenticated_headers,
    )
    assert_status(suggestion_response, 200)
    suggestions = suggestion_response.json()
    assert suggestions, "Expected at least one QuickFill template after seeding history."

    candidate = suggestions[0]
    assert not candidate["is_approved"]

    post_suggestion_balance = await api_client.get(f"/accounts/{source_account['id']}", headers=authenticated_headers)
    assert_status(post_suggestion_balance, 200)
    assert Decimal(str(post_suggestion_balance.json()["available_balance"])) == source_balance_before

    approve_response = await api_client.post(
        f"/quickfill/templates/{candidate['id']}/approve",
        headers=authenticated_headers,
    )
    assert_status(approve_response, 200)
    approved_template = approve_response.json()
    assert approved_template["is_approved"]

    refreshed_suggestions = await api_client.get(
        "/quickfill/",
        params={"action": "Transfer", "currency": "USD", "query": "API", "limit": 1},
        headers=authenticated_headers,
    )
    assert_status(refreshed_suggestions, 200)
    public_candidates = refreshed_suggestions.json()
    assert public_candidates
    assert public_candidates[0]["id"] == candidate["id"]
