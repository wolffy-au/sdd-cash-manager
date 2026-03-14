"""Helper for issuing JWT tokens inside the API pytest suite."""

from datetime import timedelta

from sdd_cash_manager.lib.auth import Role, create_access_token

DEFAULT_ROLES = [Role.ADMIN]
DEFAULT_EXPIRES_MINUTES = 15


def generate_access_token(
    subject: str = "api-test-suite",
    roles: list[Role] | None = None,
    expires_minutes: int = DEFAULT_EXPIRES_MINUTES,
) -> str:
    """Return a signed JWT ready for the API security dependency."""
    effective_roles = list(roles or DEFAULT_ROLES)
    delta = timedelta(minutes=expires_minutes)
    return create_access_token(subject=subject, roles=effective_roles, expires_delta=delta)
