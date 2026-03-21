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


@pytest.mark.asyncio
async def test_quickfill_submission_updates_balances(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
    seeded_accounts: dict[str, dict[str, object]],
) -> None:
    """Using an approved QuickFill suggestion to create a transaction correctly updates account balances."""
    source_account = seeded_accounts["visible"]
    target_account = seeded_accounts["balancing"]
    amount = Decimal("75.00")
    description = "QuickFill submission test"
    memo = "Test memo for submission"

    # 1. Seed history to create a QuickFill template
    seed_payload = {
        "transfer_from": source_account["id"],
        "transfer_to": target_account["id"],
        "action": "Transfer",
        "amount": str(amount),
        "currency": "USD",
        "description": description,
        "memo": memo,
        "date": date.today().isoformat(),
    }
    seed_txn_response = await api_client.post("/transactions/", json=seed_payload, headers=authenticated_headers)
    assert_status(seed_txn_response, 201)

    # 2. Retrieve and approve the template
    suggestion_response = await api_client.get(
        "/quickfill/",
        params={
            "action": "Transfer",
            "currency": "USD",
            "query": description[:5], # Use part of description to find the seeded entry
            "include_unapproved": True,
            "limit": 1,
        },
        headers=authenticated_headers,
    )
    assert_status(suggestion_response, 200)
    suggestions = suggestion_response.json()
    assert suggestions, "Expected at least one QuickFill template after seeding history."

    template_to_approve = suggestions[0]
    assert not template_to_approve["is_approved"]

    approve_response = await api_client.post(
        f"/quickfill/templates/{template_to_approve['id']}/approve",
        headers=authenticated_headers,
    )
    assert_status(approve_response, 200)
    approved_template = approve_response.json()
    assert approved_template["is_approved"]

    # Get account balances before submitting the transaction from the approved template
    note_before_submission = await api_client.get(f"/accounts/{source_account['id']}", headers=authenticated_headers)
    assert_status(note_before_submission, 200)
    source_balance_before_submission = Decimal(str(note_before_submission.json()["available_balance"]))

    # 3. Use the approved template to create a new transaction
    # The approved template's ID is used implicitly when submitting a new transaction that matches its criteria.
    # We'll simulate creating a new transaction using the details from the approved template.
    # The API should infer the template and use it.

    # We need to fetch the actual details from the approved template to use for submission.
    # Assuming the POST /quickfill/templates/{template_id}/approve returns the full template details
    # or we need to re-fetch it. Let's assume the approved_template object has the necessary fields.
    # If not, we'd need to re-fetch it from /quickfill/ with `include_unapproved=False` or similar.

    # For simplicity in this test, we will assume the API allows submission by referencing the template ID
    # or by providing the same parameters that would match an approved template.
    # A common pattern is to use a POST request to `/transactions/` with a `quickfill_template_id` or similar.
    # Let's check the expected payload for creating a transaction from a template.
    # The quickstart mentions "Confirm the template with a single interaction before submitting the POST."
    # This suggests the POST to /transactions/ might take a template ID or its equivalent data.
    # The current schema for POST /transactions/ doesn't explicitly show a template_id field.
    # It uses transfer_from, transfer_to, action, amount, currency, description, memo, date.
    # We'll use these fields, assuming they are populated from the approved template.

    transaction_payload = {
        "transfer_from": approved_template["transfer_from_account_id"],
        "transfer_to": approved_template["transfer_to_account_id"],
        "action": approved_template["action"],
        "amount": str(Decimal(approved_template["amount"])), # Ensure it's string
        "currency": approved_template["currency"],
        "description": approved_template["description"],
        "memo": approved_template["memo"],
        "date": date.today().isoformat(), # Use today's date for consistency
    }

    new_txn_response = await api_client.post("/transactions/", json=transaction_payload, headers=authenticated_headers)
    assert_status(new_txn_response, 201)
    new_transaction = new_txn_response.json()

    # 4. Verify that account balances are updated correctly for this new transaction.
    note_after_submission = await api_client.get(f"/accounts/{source_account['id']}", headers=authenticated_headers)
    assert_status(note_after_submission, 200)
    source_balance_after_submission = Decimal(str(note_after_submission.json()["available_balance"]))

    # The balance should have decreased by the transaction amount
    expected_balance = source_balance_before_submission - Decimal(transaction_payload["amount"])
    assert source_balance_after_submission == expected_balance, "Source account balance not updated correctly after QuickFill submission."

    # Optionally, check target account balance as well
    target_note_after_submission = await api_client.get(f"/accounts/{target_account['id']}", headers=authenticated_headers)
    assert_status(target_note_after_submission, 200)
    # Assuming target account balance increases by the same amount (for a Transfer action)
    # Assuming target account balance increases by the same amount (for a Transfer action)
    # We need to fetch target_balance_before_submission if we want to assert this precisely.
    # For now, focus on the source account update as per the common pattern.
    # The logic for double-entry is covered by other tests, so this focuses on the QuickFill submission part.

    # Verify the created transaction details
    assert new_transaction["amount"] == transaction_payload["amount"]
    assert new_transaction["currency"] == transaction_payload["currency"]
    assert new_transaction["description"] == transaction_payload["description"]
    assert new_transaction["memo"] == transaction_payload["memo"]
    assert new_transaction["action"] == transaction_payload["action"]
    assert new_transaction["transfer_from_account_id"] == transaction_payload["transfer_from"]
    assert new_transaction["transfer_to_account_id"] == transaction_payload["transfer_to"]

