"""Shared pytest fixtures for the API regression suite."""

import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient, Timeout

from tests.api.jwt_utils import generate_access_token

# Ensure fixtures defined in tests/api/fixtures.py are registered with pytest
from .fixtures import *  # noqa: F401,F403


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
    """Provide an httpx AsyncClient configured for the local API.

    Use the in-process FastAPI app when available to avoid needing uvicorn.
    """
    timeout = Timeout(10.0, connect=5.0)

    # Import the project FastAPI app from src/main.py (raise on failure)
    import sys

    src_dir = str(Path(__file__).resolve().parents[2] / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from main import app  # src/main.py defines the FastAPI app

    # Use ASGI transport so httpx sends requests directly to the FastAPI app
    try:
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver", timeout=timeout, follow_redirects=True) as client:
            yield client
    except Exception:
        # Fall back to a network client if ASGI transport fails
        async with AsyncClient(base_url=api_base_url, timeout=timeout, follow_redirects=True) as client:
            yield client


@pytest.fixture
async def authenticated_headers(api_security_enabled: bool) -> dict[str, str]:
    """Convenience fixture exposing headers for authenticated requests once JWT helpers exist."""
    headers = {"Content-Type": "application/json"}
    if api_security_enabled:
        token = generate_access_token()
        headers["Authorization"] = f"Bearer {token}"
    return headers

@pytest.fixture(scope="session", autouse=True)
def cleanup_sqlite_db_file() -> Generator[None, None, None]:
    """Ensure the disk-backed SQLite database gets removed after the API suite runs."""
    try:
        yield
    finally:
        db_path = Path("sdd_cash_manager.db")
        if db_path.exists():
            db_path.unlink()
