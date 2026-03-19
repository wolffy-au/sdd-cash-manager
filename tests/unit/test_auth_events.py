import pytest
from fastapi import HTTPException

from sdd_cash_manager.lib.auth import Role, TokenPayload, require_role, require_token
from sdd_cash_manager.lib.security_events import SecurityEvent


def test_require_token_logs_missing_credentials(monkeypatch):
    called = {}

    def fake_log(event_type, message, **kwargs):
        called["event_type"] = event_type
        called["message"] = message

    monkeypatch.setattr("sdd_cash_manager.lib.auth.log_security_event", fake_log)

    with pytest.raises(HTTPException) as exc:
        require_token(None)

    assert exc.value.status_code == 401
    assert called.get("event_type") == SecurityEvent.AUTHENTICATION_FAILURE
    assert "credentials" in called.get("message", "")


def test_require_role_logs_authorization_failure(monkeypatch):
    captured = {}

    def fake_log(event_type, message, **kwargs):
        captured["event_type"] = event_type
        captured["user_id"] = kwargs.get("user_id")

    monkeypatch.setattr("sdd_cash_manager.lib.auth.log_security_event", fake_log)

    dependency = require_role(Role.OPERATOR)
    token = TokenPayload(subject="user-123", roles=[Role.VIEWER])

    with pytest.raises(HTTPException) as exc:
        dependency(token=token)

    assert exc.value.status_code == 403
    assert captured.get("event_type") == SecurityEvent.AUTHORIZATION_FAILURE
    assert captured.get("user_id") == "user-123"
