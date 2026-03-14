"""JWT authentication and RBAC helpers for the sdd-cash-manager API."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from sdd_cash_manager.core.config import settings

_bearer = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer)


class Role(str, Enum):
    """Supported RBAC roles."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


_ROLE_HIERARCHY = {
    Role.VIEWER: {Role.VIEWER, Role.OPERATOR, Role.ADMIN},
    Role.OPERATOR: {Role.OPERATOR, Role.ADMIN},
    Role.ADMIN: {Role.ADMIN},
}


class TokenPayload(BaseModel):
    """Decoded JWT payload for a request context."""

    subject: str
    roles: list[Role] = Field(default_factory=list)
    issued_at: datetime | None = None


_DEFAULT_TOKEN = TokenPayload(subject="system", roles=[Role.ADMIN])


def _decode_token(token: str) -> TokenPayload:
    """Decode the provided JWT string into a structured payload."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials") from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Token missing subject")

    raw_roles = payload.get("roles", [])
    if not isinstance(raw_roles, list):
        raise HTTPException(status_code=401, detail="Token roles are malformed")

    normalized_roles: list[Role] = []
    for raw_role in raw_roles:
        try:
            normalized_roles.append(Role(raw_role))
        except ValueError:
            continue

    issued_at = payload.get("iat")
    issued_at_dt = datetime.fromtimestamp(issued_at, timezone.utc) if isinstance(issued_at, (int, float)) else None

    return TokenPayload(subject=subject, roles=normalized_roles, issued_at=issued_at_dt)


def _security_enabled() -> bool:
    return settings.security_enabled


def require_token(credentials: HTTPAuthorizationCredentials | None = _bearer_dependency) -> TokenPayload:
    """Return the decoded token when security is active or the default token otherwise."""
    if not _security_enabled():
        return _DEFAULT_TOKEN

    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing credentials")

    return _decode_token(credentials.credentials)


_TOKEN_DEPENDENCY = Depends(require_token)


def require_role(required_role: Role) -> Callable[..., TokenPayload]:
    """Return a dependency enforcing the given RBAC role."""

    def _dependency(token: TokenPayload = _TOKEN_DEPENDENCY) -> TokenPayload:
        if not _security_enabled():
            return token

        allowed_roles = _ROLE_HIERARCHY.get(required_role, {required_role})
        if not any(role in allowed_roles for role in token.roles):
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return token

    return _dependency


def create_access_token(
    subject: str,
    roles: list[Role],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT for the requested roles."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "roles": [role.value for role in roles],
        "iat": int(now.timestamp()),
    }
    if expires_delta is not None:
        payload["exp"] = int((now + expires_delta).timestamp())
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
