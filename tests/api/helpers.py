"""Reusable asserts and helpers for API pytest responses."""

from typing import Iterable

from httpx import Response


def assert_status(response: Response, expected: int) -> None:
    """Assert that the response returned the expected status code."""
    assert response.status_code == expected, (
        f"Expected status {expected}, received {response.status_code}: {response.text}"
    )


def assert_payload_keys(payload: dict[str, object], required_keys: Iterable[str]) -> None:
    """Assert that every required key is present in the JSON payload."""
    missing_keys = [key for key in required_keys if key not in payload]
    assert not missing_keys, f"Missing payload keys: {missing_keys}"


def assert_validation_error(response: Response, missing_fields: Iterable[str]) -> None:
    """Assert that a validation error response names every expected missing field."""
    assert_status(response, 422)
    detail = response.json().get("detail", [])
    flattened = {entry.get("loc", [None])[-1] for entry in detail if isinstance(entry, dict)}
    assert set(missing_fields).issubset(flattened), (
        "Validation error missing expected fields:"
        f" expected={set(missing_fields)} actual={flattened}"
    )
