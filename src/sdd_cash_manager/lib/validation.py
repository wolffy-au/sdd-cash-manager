"""Shared validation helpers for sdd-cash-manager inputs."""

from __future__ import annotations

import re
from typing import Pattern

CONTROL_CHAR_PATTERN: Pattern[str] = re.compile(r"[\x00-\x1F\x7F]")
NAME_ALLOWED_PATTERN: Pattern[str] = re.compile(r"^[A-Za-z0-9\s\.,\-\_\(\)\&']+$")


def assert_no_control_chars(value: str, field_name: str) -> str:
    """Ensure a string contains no ISO control characters."""
    if CONTROL_CHAR_PATTERN.search(value):
        raise ValueError(f"{field_name} contains invalid characters")
    return value


def validate_name_value(value: str) -> str:
    """Validate that an account name contains only the allowed characters."""
    assert_no_control_chars(value, "account name")
    if not NAME_ALLOWED_PATTERN.match(value):
        raise ValueError("account name contains unsupported characters")
    if any(ch in value for ch in "<>;"):
        raise ValueError("account name contains invalid characters")
    return value


def validate_currency_value(value: str) -> str:
    """Ensure the currency code matches a 3-letter ISO format."""
    if len(value) != 3 or not value.isalpha() or not value.isupper():
        raise ValueError("Currency must be a 3-letter uppercase ISO 4217 code.")
    return value


def validate_text_field_no_special_chars(value: str, field_name: str, invalid_message: str) -> str:
    """Ensure the text field does not include forbidden characters."""
    assert_no_control_chars(value, field_name)
    if any(ch in value for ch in "<>;"):
        raise ValueError(invalid_message)
    return value


def sanitize_search_term(search_term: str | None, max_length: int = 100) -> str | None:
    """Trim and validate a search term, raising when limits are exceeded."""
    if search_term is None:
        return None
    trimmed = search_term.strip()
    if len(trimmed) > max_length:
        raise ValueError("Search term exceeds maximum allowed length.")
    assert_no_control_chars(trimmed, "search term")
    return trimmed
