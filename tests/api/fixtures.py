"""Seed and cleanup helpers for API pytest sessions."""

from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator, cast

import pytest
from httpx import AsyncClient, HTTPStatusError

from sdd_cash_manager.services.transaction_service import BALANCING_ACCOUNT_ID

DEFAULT_ACCOUNT_BASE = {
    "currency": "USD",
    "accounting_category": "ASSET",
    "banking_product_type": "CHECKING",
    "available_balance": "0.00",
}


async def _create_account(client: AsyncClient, headers: dict[str, str], **overrides: object) -> dict[str, object]:
    payload = {
        "name": f"seed-{uuid.uuid4()}",
        "notes": "Seeded for API pytest suite",
        **DEFAULT_ACCOUNT_BASE,
        **overrides,
    }
    response = await client.post("/accounts", json=payload, headers=headers)
    response.raise_for_status()
    data: dict[str, object] = response.json()
    return data


async def _cleanup_accounts(client: AsyncClient, headers: dict[str, str], account_ids: list[str]) -> None:
    for account_id in account_ids:
        try:
            await client.delete(f"/accounts/{account_id}", headers=headers)
        except Exception:
            # Delete errors are non-fatal for cleanup
            continue


async def _seed_balancing_account(client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
    await client.delete(f"/accounts/{BALANCING_ACCOUNT_ID}", headers=headers)
    try:
        return await _create_account(
            client,
            headers,
            name="balancing-account",
            id=BALANCING_ACCOUNT_ID,
            available_balance="0.00",
        )
    except HTTPStatusError as exc:
        if exc.response.status_code == 500:
            existing_response = await client.get(f"/accounts/{BALANCING_ACCOUNT_ID}", headers=headers)
            existing_response.raise_for_status()
            return cast(dict[str, object], existing_response.json())
        raise


async def _seed_hidden_account(client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
    return await _create_account(
        client,
        headers,
        name="visible-account-hidden",
        hidden=True,
        notes="hidden account seed",
    )


async def _seed_placeholder_account(client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
    return await _create_account(
        client,
        headers,
        name="visible-account-placeholder",
        placeholder=True,
        notes="placeholder account seed",
    )


async def _seed_visible_account(client: AsyncClient, headers: dict[str, str]) -> dict[str, object]:
    return await _create_account(
        client,
        headers,
        name="visible-account",
        notes="visible account seed",
    )


async def _async_sleep() -> None:
    # Yield control so awaiting cleanup occurs even if delete requests hang
    await asyncio.sleep(0)


async def _ensure_cleanup(client: AsyncClient, headers: dict[str, str], ids: list[str]) -> None:
    await _async_sleep()
    await _cleanup_accounts(client, headers, ids)


async def _seed_all_accounts(client: AsyncClient, headers: dict[str, str]) -> dict[str, dict[str, object]]:
    visible = await _seed_visible_account(client, headers)
    hidden = await _seed_hidden_account(client, headers)
    placeholder = await _seed_placeholder_account(client, headers)
    balancing = await _seed_balancing_account(client, headers)
    return {
        "visible": visible,
        "hidden": hidden,
        "placeholder": placeholder,
        "balancing": balancing,
    }


@pytest.fixture
async def seeded_accounts(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str]
) -> AsyncGenerator[dict[str, dict[str, object]], None]:
    """Provide seeded accounts and ensure cleanup after the test."""
    accounts = await _seed_all_accounts(api_client, authenticated_headers)
    try:
        yield accounts
    finally:
        ids_to_remove = [str(acct["id"]) for acct in accounts.values()]
        await _ensure_cleanup(api_client, authenticated_headers, ids_to_remove)
