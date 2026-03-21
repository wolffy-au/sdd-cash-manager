"""API tests covering duplicate detection and consolidation (US3)."""

from decimal import Decimal

import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_status


def _transaction_payload(debit_account: str, credit_account: str) -> dict[str, object]:
    return {
        "transfer_from": debit_account,
        "transfer_to": credit_account,
        "action": "TRANSFER",
        "amount": "50.00",
        "currency": "USD",
        "description": "Duplicate candidate generation",
        "memo": "auto-duplicate",
    }


@pytest.mark.asyncio
async def test_duplicate_candidate_merge(api_client: AsyncClient, authenticated_headers: dict[str, str], seeded_accounts: dict[str, dict[str, object]]) -> None:
    """Create identical transactions, list the candidate, and merge so only one transaction remains."""
    visible = seeded_accounts["visible"]
    balancing = seeded_accounts["balancing"]

    payload = _transaction_payload(str(visible["id"]), str(balancing["id"]))
    first_response = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
    second_response = await api_client.post("/transactions/", json=payload, headers=authenticated_headers)
    assert_status(first_response, 201)
    assert_status(second_response, 201)

    duplicates_response = await api_client.get(
        "/accounts/duplicates/",
        params={"account_id": str(visible["id"])},
        headers=authenticated_headers,
    )
    assert_status(duplicates_response, 200)
    candidates = duplicates_response.json()
    assert candidates, "Expected at least one duplicate candidate"

    candidate = candidates[0]
    merge_response = await api_client.post(
        "/accounts/duplicates/merge",
        json={"candidate_id": candidate["candidate_id"]},
        headers=authenticated_headers,
    )
    assert_status(merge_response, 200)
    merge_payload = merge_response.json()
    assert merge_payload["status"] == "merged"
    assert Decimal(str(merge_payload["before_balance"])) == Decimal(str(merge_payload["after_balance"]))
    assert merge_payload["removed_transaction_ids"], "Duplicate merge should report removed IDs"
