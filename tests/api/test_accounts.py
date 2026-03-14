"""HTTP tests covering account creation and listing flows (User Story 1)."""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_payload_keys, assert_status

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
