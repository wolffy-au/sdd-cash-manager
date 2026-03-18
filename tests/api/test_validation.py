"""HTTP tests covering validation and auth error scenarios (User Story 3)."""

import logging
import pytest
from httpx import AsyncClient

from tests.api.helpers import assert_status, assert_validation_error

logger = logging.getLogger(__name__) # Initialize logger

@pytest.mark.asyncio
async def test_missing_fields_returns_422(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
) -> None:
    """Ensure missing required fields return an informative 422 response."""
    incomplete_payload = {
        "name": "Incomplete Account",
        # Deliberately omitting currency and accounting_category
    }

    response = await api_client.post("/accounts", json=incomplete_payload, headers=authenticated_headers)
    assert_validation_error(response, missing_fields=["currency", "accounting_category"])


@pytest.mark.asyncio
async def test_unauthorized_request_returns_401(api_client: AsyncClient) -> None:
    """Verify the API rejects requests without Authorization headers."""
    payload = {
        "name": "Unauthorized Account",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "CHECKING",
    }

    response = await api_client.post("/accounts", json=payload)
    assert_status(response, 401)


@pytest.mark.asyncio
async def test_list_accounts_requires_authenticated_headers(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
) -> None:
    """Ensure listing accounts succeeds when a valid JWT is supplied."""
    response = await api_client.get("/accounts", headers=authenticated_headers)
    assert_status(response, 200)


@pytest.mark.asyncio
async def test_missing_fields_returns_422(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
) -> None:
    """Ensure missing required fields return an informative 422 response."""
    incomplete_payload = {
        "name": "Incomplete Account",
        # Deliberately omitting currency and accounting_category
    }

    response = await api_client.post("/accounts", json=incomplete_payload, headers=authenticated_headers)
    assert_validation_error(response, missing_fields=["currency", "accounting_category"])


@pytest.mark.asyncio
async def test_unauthorized_request_returns_401(api_client: AsyncClient) -> None:
    """Verify the API rejects requests without Authorization headers."""
    payload = {
        "name": "Unauthorized Account",
        "currency": "USD",
        "accounting_category": "ASSET",
        "banking_product_type": "CHECKING",
    }

    response = await api_client.post("/accounts", json=payload)
    assert_status(response, 401)


@pytest.mark.asyncio
async def test_list_accounts_requires_authenticated_headers(
    api_client: AsyncClient,
    authenticated_headers: dict[str, str],
) -> None:
    """Ensure listing accounts succeeds when a valid JWT is supplied."""
    response = await api_client.get("/accounts", headers=authenticated_headers)
    assert_status(response, 200)
