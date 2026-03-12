from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

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
