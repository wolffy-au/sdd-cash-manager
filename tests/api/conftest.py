"""Shared pytest fixtures for the API regression suite."""

import os
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, Timeout

from tests.api.jwt_utils import generate_access_token


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return the base URL for API requests, overridable by env var."""
    return os.environ.get("SDD_CASH_MANAGER_API_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def api_security_enabled() -> bool:
    """Indicate whether JWT security should be enforced during the tests."""
    return os.environ.get("SDD_CASH_MANAGER_SECURITY_ENABLED", "true").lower() in ("1", "true", "yes")


@pytest.fixture
async def api_client(api_base_url: str) -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx AsyncClient configured for the local API."""
    timeout = Timeout(10.0, connect=5.0)
    async with AsyncClient(base_url=api_base_url, timeout=timeout) as client:
        yield client


@pytest.fixture
async def authenticated_headers(api_security_enabled: bool) -> dict[str, str]:
    """Convenience fixture exposing headers for authenticated requests once JWT helpers exist."""
    headers = {"Content-Type": "application/json"}
    if api_security_enabled:
        token = generate_access_token()
        headers["Authorization"] = f"Bearer {token}"
    return headers
