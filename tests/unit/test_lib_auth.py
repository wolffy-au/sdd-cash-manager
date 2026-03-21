from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt import InvalidTokenError

from sdd_cash_manager.core.config import settings
from sdd_cash_manager.lib.auth import (
    Role,
    TokenPayload,
    _decode_token,
    create_access_token,
    require_role,
    require_token,
)


def _reset_security_enabled(value: bool) -> None:
    object.__setattr__(settings, "security_enabled", value)


def test_create_access_token_roundtrip():
    token = create_access_token("tester", [Role.OPERATOR], expires_delta=timedelta(minutes=5))
    payload = _decode_token(token)
    assert payload.subject == "tester"
    assert Role.OPERATOR in payload.roles


def test_require_token_uses_security_flag():
    original_flag = settings.security_enabled
    _reset_security_enabled(True)
    try:
        token = create_access_token("operator", [Role.OPERATOR])
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        payload = require_token(credentials)
        assert payload.subject == "operator"
        assert Role.OPERATOR in payload.roles
    finally:
        _reset_security_enabled(original_flag)


def test_require_token_returns_default_when_disabled():
    original_flag = settings.security_enabled
    _reset_security_enabled(False)
    try:
        payload = require_token(None)
        assert payload.roles == [Role.ADMIN]
    finally:
        _reset_security_enabled(original_flag)


def test_require_role_enforces_operator():
    original_flag = settings.security_enabled
    _reset_security_enabled(True)
    try:
        dependency = require_role(Role.OPERATOR)
        token = TokenPayload(subject="tester", roles=[Role.OPERATOR])
        assert dependency(token) is token
        with pytest.raises(HTTPException):
            dependency(TokenPayload(subject="tester", roles=[Role.VIEWER]))
    finally:
        _reset_security_enabled(original_flag)


def test_decode_token_invalid_token(monkeypatch):
    def fake_decode(token: str, secret: str, algorithms: list[str]) -> dict[str, Any]:
        raise InvalidTokenError("boom")

    monkeypatch.setattr("sdd_cash_manager.lib.auth.jwt.decode", fake_decode)
    with pytest.raises(HTTPException) as exc:
        _decode_token("garbage")
    assert exc.value.status_code == 401


def test_decode_token_missing_subject(monkeypatch):
    monkeypatch.setattr("sdd_cash_manager.lib.auth.jwt.decode", lambda *args, **kwargs: {"roles": []})
    with pytest.raises(HTTPException) as exc:
        _decode_token("token")
    assert exc.value.detail == "Token missing subject"


def test_decode_token_roles_malformed(monkeypatch):
    monkeypatch.setattr(
        "sdd_cash_manager.lib.auth.jwt.decode",
        lambda *args, **kwargs: {"sub": "tester", "roles": "admin"},
    )
    with pytest.raises(HTTPException) as exc:
        _decode_token("token")
    assert exc.value.detail == "Token roles are malformed"


def test_decode_token_ignores_unknown_roles(monkeypatch):
    monkeypatch.setattr(
        "sdd_cash_manager.lib.auth.jwt.decode",
        lambda *args, **kwargs: {"sub": "tester", "roles": [Role.OPERATOR.value, "unknown"]},
    )
    payload = _decode_token("token")
    assert payload.roles == [Role.OPERATOR]


def test_require_role_noop_when_security_disabled():
    original_flag = settings.security_enabled
    _reset_security_enabled(False)
    try:
        dependency = require_role(Role.ADMIN)
        token = TokenPayload(subject="tester", roles=[Role.ADMIN])
        assert dependency(token) is token
    finally:
        _reset_security_enabled(original_flag)
