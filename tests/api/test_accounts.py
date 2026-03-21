"""HTTP tests covering account creation and listing flows (User Story 1)."""

import logging
from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_payload_keys, assert_status

logger = logging.getLogger(__name__) # Initialize logger

REQUIRED_CREATE_KEYS = {"id", "name", "currency", "available_balance", "hidden", "placeholder"}


@pytest.mark.asyncio
async def test_create_and_get_account(api_client: AsyncClient, authenticated_headers: dict[str, str]) -> None:
    """Create an account and then fetch it directly to verify persistence."""
    payload = {
        "name": "Accounts API Test",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "CHECKING",
        "notes": "Created by automated API tests",
        "available_balance": "1000.00",
    }

    post_response = await api_client.post("/accounts", json=payload, headers=authenticated_headers)
    assert_status(post_response, 201)
    resource = post_response.json()
    assert_payload_keys(resource, REQUIRED_CREATE_KEYS)
    assert resource["name"] == payload["name"]
    assert Decimal(str(resource["available_balance"])) == Decimal(payload["available_balance"])

    account_id = resource["id"]
    get_response = await api_client.get(f"/accounts/{account_id}", headers=authenticated_headers)
    assert_status(get_response, 200)
    fetched = get_response.json()
    assert fetched["id"] == account_id
    assert fetched["name"] == payload["name"]
    assert Decimal(str(fetched["available_balance"])) == Decimal(payload["available_balance"])


@pytest.mark.asyncio
async def test_list_accounts_filters(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Verify that listing honors search_term, include_hidden, and include_placeholder."""
    visible = seeded_accounts["visible"]
    hidden = seeded_accounts["hidden"]
    placeholder = seeded_accounts["placeholder"]

    response = await api_client.get(
        "/accounts",
        params={
            "search_term": "visible-account",
            "include_hidden": "true",
            "include_placeholder": "true",
        },
        headers=authenticated_headers,
    )
    assert_status(response, 200)
    payload = response.json()
    assert isinstance(payload, list)

    ids = {entry["id"] for entry in payload}
    assert visible["id"] in ids
    assert hidden["id"] in ids
    assert placeholder["id"] in ids

    hidden_entries = [entry for entry in payload if entry["hidden"] is True]
    placeholder_entries = [entry for entry in payload if entry["placeholder"] is True]
    assert any(entry["id"] == hidden["id"] for entry in hidden_entries)
    assert any(entry["id"] == placeholder["id"] for entry in placeholder_entries)


@pytest.mark.asyncio
async def test_account_merge_reparents_entries(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Merge a child account into a visible target and verify the plan response."""
    target = seeded_accounts["visible"]
    balancing = seeded_accounts["balancing"]

    child_payload = {
        "name": "merge-child",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "CHECKING",
        "available_balance": "0.00",
        "parent_account_id": target["id"],
    }
    child_resp = await api_client.post("/accounts", json=child_payload, headers=authenticated_headers)
    assert_status(child_resp, 201)
    child = child_resp.json()

    transaction_payload = {
        "transfer_from": child["id"],
        "transfer_to": balancing["id"],
        "action": "TRANSFER",
        "amount": "25.00",
        "currency": "USD",
        "description": "Merge entry",
    }
    txn_response = await api_client.post("/transactions/", json=transaction_payload, headers=authenticated_headers)
    assert_status(txn_response, 201)

    merge_payload = {
        "source_account_id": child["id"],
        "target_account_id": target["id"],
        "reparenting_map": {},
        "audit_notes": "API merge test",
        "initiated_by": "tests",
        "metadata": {"reason": "cleanup"},
    }
    merge_response = await api_client.post("/accounts/merge", json=merge_payload, headers=authenticated_headers)
    assert_status(merge_response, 200)
    body = merge_response.json()
    assert body["status"] == "executed"
    assert body["affected_entries_count"] >= 1
    assert body["target_account_id"] == target["id"]

    # Cleanup the placeholder child after merging
    await api_client.delete(f"/accounts/{child['id']}", headers=authenticated_headers)
