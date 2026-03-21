import logging
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from sdd_cash_manager.core.config import AppSettings
from sdd_cash_manager.lib.security_events import (
    SecurityEvent,
    log_account_merge,
    log_duplicate_merge,
    log_quickfill_template_approved,
    log_security_event,
    log_transaction_created,
    security_logger,
)


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Fixture to mock settings for security event tests."""
    mock_app_settings = AppSettings(
        security_log_level="INFO",
        security_log_file="/tmp/test_security.log",
        security_console_log_enabled=False,
        security_alerts_enabled=False,
        log_format="%(message)s" # Simplified for testing
    )
    monkeypatch.setattr("sdd_cash_manager.core.config.settings", mock_app_settings)
    # Ensure handlers are cleared for clean test runs
    security_logger.handlers = []


@pytest.fixture
def mock_security_logger(monkeypatch):
    """Fixture to mock the security_logger instance."""
    mock_logger = MagicMock()
    monkeypatch.setattr("sdd_cash_manager.lib.security_events.security_logger", mock_logger)
    return mock_logger


@pytest.fixture
def mock_send_alert(monkeypatch):
    """Fixture to mock _send_security_alert."""
    mock_alert_func = MagicMock()
    monkeypatch.setattr("sdd_cash_manager.lib.security_events._send_security_alert", mock_alert_func)
    return mock_alert_func


def test_log_security_event_info_level(mock_security_logger, mock_send_alert):
    """Test logging an INFO level security event."""
    log_security_event(
        event_type=SecurityEvent.AUTHENTICATION_FAILURE,
        message="Failed login attempt",
        user_id="user123",
        metadata={"ip_address": "192.168.1.1"}
    )
    mock_security_logger.log.assert_called_once()
    args, _ = mock_security_logger.log.call_args
    assert args[0] == logging.INFO
    assert args[1]["event_type"] == SecurityEvent.AUTHENTICATION_FAILURE.value
    assert args[1]["message"] == "Failed login attempt"
    assert args[1]["user_id"] == "user123"
    assert args[1]["metadata"]["ip_address"] == "192.168.1.1"
    mock_send_alert.assert_not_called()


def test_log_security_event_warning_level_alert_disabled(mock_security_logger, mock_send_alert):
    """Test logging a WARNING level event when alerts are disabled."""
    log_security_event(
        event_type=SecurityEvent.DATA_TAMPERING_ATTEMPT,
        message="Potential data tampering",
        level=logging.WARNING
    )
    mock_security_logger.log.assert_called_once()
    args, _ = mock_security_logger.log.call_args
    assert args[0] == logging.WARNING
    mock_send_alert.assert_not_called()


def test_log_security_event_warning_level_alert_enabled(mock_security_logger, mock_send_alert, monkeypatch):
    """Test logging a WARNING level event when alerts are enabled."""
    # Create a new AppSettings instance with alerts enabled for this test
    mock_app_settings_with_alerts = AppSettings(
        security_log_level="INFO",
        security_log_file="/tmp/test_security.log",
        security_console_log_enabled=False,
        security_alerts_enabled=True, # Set to True
        log_format="%(message)s"
    )
    monkeypatch.setattr("sdd_cash_manager.core.config.settings", mock_app_settings_with_alerts)

    # Reload the security_events module to ensure it picks up the new settings
    from importlib import reload

    from sdd_cash_manager.lib import security_events
    reload(security_events)
    # Re-mock the security_logger after reload
    monkeypatch.setattr(security_events, "security_logger", mock_security_logger)
    # Re-mock the _send_security_alert function after reload
    monkeypatch.setattr(security_events, "_send_security_alert", mock_send_alert)

    security_events.log_security_event(
        event_type=security_events.SecurityEvent.BREACH_DETECTION,
        message="Critical breach detected",
        level=logging.CRITICAL
    )
    mock_security_logger.log.assert_called_once()
    mock_send_alert.assert_called_once()
    args, _ = mock_send_alert.call_args
    assert args[0] == SecurityEvent.BREACH_DETECTION
    assert args[1] == "Critical breach detected"


def test_log_critical_application_error(mock_security_logger, mock_send_alert, monkeypatch):
    """Test logging a critical application error, ensuring ERROR level and alert triggering."""
    # Ensure settings are set to trigger alerts for critical errors
    mock_app_settings_with_alerts = AppSettings(
        security_log_level="ERROR", # Log critical as ERROR
        security_log_file="/tmp/test_security.log",
        security_console_log_enabled=False,
        security_alerts_enabled=True, # Alerts enabled
        log_format="%(message)s"
    )
    monkeypatch.setattr("sdd_cash_manager.core.config.settings", mock_app_settings_with_alerts)

    # Reload the security_events module to pick up the new settings
    from importlib import reload

    from sdd_cash_manager.lib import security_events
    reload(security_events)
    monkeypatch.setattr(security_events, "security_logger", mock_security_logger)
    monkeypatch.setattr(security_events, "_send_security_alert", mock_send_alert)

    # Simulate an exception
    try:
        raise ValueError("Simulated critical error")
    except ValueError:
        security_events.log_critical_application_error(
            message="An unexpected error occurred in service",
            user_id="test_user",
            metadata={"component": "test_component"},
            exc_info=True # Capture exception info
        )

    mock_security_logger.error.assert_called_once()
    args, kwargs = mock_security_logger.error.call_args
    assert args[0]["event_type"] == SecurityEvent.SYSTEM_ALERT.value
    assert args[0]["message"] == "An unexpected error occurred in service"
    assert kwargs["exc_info"] is True

    mock_send_alert.assert_called_once()
    args, _ = mock_send_alert.call_args
    assert args[0] == SecurityEvent.SYSTEM_ALERT
    assert args[1] == "An unexpected error occurred in service"


def test_security_logger_configuration(monkeypatch):
    """Test that the security logger is configured correctly with settings."""
    # Ensure handlers are re-initialized for this test
    security_logger.handlers = []

    mock_app_settings = AppSettings(
        security_log_level="DEBUG",
        security_log_file="/tmp/test_security_debug.log",
        security_console_log_enabled=True,
        security_alerts_enabled=False,
        log_format="%(levelname)s: %(message)s"
    )
    monkeypatch.setattr("sdd_cash_manager.core.config.settings", mock_app_settings)

    # Re-import to re-initialize the logger based on new settings
    from importlib import reload

    from sdd_cash_manager.lib import security_events
    reload(security_events)

    assert security_events.security_logger.level == logging.DEBUG
    assert len(security_events.security_logger.handlers) == 2 # File and console

    file_handler = next((h for h in security_events.security_logger.handlers if isinstance(h, logging.FileHandler)), None)
    assert file_handler is not None
    assert file_handler.baseFilename.endswith("/tmp/test_security_debug.log")
    file_formatter = file_handler.formatter
    assert file_formatter is not None
    assert file_formatter._fmt == "%(levelname)s: %(message)s"

    console_handler = next((h for h in security_events.security_logger.handlers if isinstance(h, logging.StreamHandler) and h != file_handler), None)
    assert console_handler is not None
    console_formatter = console_handler.formatter
    assert console_formatter is not None
    assert console_formatter._fmt == "%(levelname)s: %(message)s"


def test_log_transaction_created_calls_log_security_event(monkeypatch, mock_send_alert, mock_security_logger):
    mock_event = MagicMock()
    monkeypatch.setattr(
        "sdd_cash_manager.lib.security_events.log_security_event",
        mock_event,
    )

    log_transaction_created(
        transaction_id="txn-123",
        debit_account_id="acct-1",
        credit_account_id="acct-2",
        amount=Decimal("123.45"),
        currency="USD",
        action="payment",
        user_id="operator",
        metadata={"source": "api"},
    )

    mock_event.assert_called_once()
    args, kwargs = mock_event.call_args
    assert args[0] == SecurityEvent.TRANSACTION_CREATED
    assert args[1].startswith("Transaction txn-123 created")
    assert kwargs["account_id"] == "acct-1"


def test_log_quickfill_template_approved(monkeypatch):
    mock_event = MagicMock()
    monkeypatch.setattr(
        "sdd_cash_manager.lib.security_events.log_security_event",
        mock_event,
    )

    log_quickfill_template_approved(
        template_id="template-1",
        approved_by="admin",
        action="transfer",
        currency="USD",
        transfer_from="acct-10",
        transfer_to="acct-20",
        confidence_score=0.95,
        metadata={"approved_reason": "Test"},
    )

    mock_event.assert_called_once()
    assert mock_event.call_args[0][0] == SecurityEvent.QUICKFILL_APPROVED


def test_log_duplicate_merge_calls_log_security_event(monkeypatch):
    mock_event = MagicMock()
    monkeypatch.setattr(
        "sdd_cash_manager.lib.security_events.log_security_event",
        mock_event,
    )

    log_duplicate_merge(
        candidate_id="dup-1",
        merged_transaction_ids=["t1", "t2"],
        account_scope="account",
        merged_by="auditor",
        preserve_audit=True,
        metadata={"reason": "cleanup"},
    )

    assert mock_event.call_args[0][0] == SecurityEvent.DUPLICATE_MERGED


def test_log_account_merge_invokes_log_security_event(monkeypatch):
    mock_event = MagicMock()
    monkeypatch.setattr(
        "sdd_cash_manager.lib.security_events.log_security_event",
        mock_event,
    )

    log_account_merge(
        plan_id="plan-1",
        source_account_id="src",
        target_account_id="tgt",
        executed_by="admin",
        reparenting_map={"old": "new"},
        affected_entries_count=5,
        status="completed",
    )

    assert mock_event.call_args[0][0] == SecurityEvent.ACCOUNT_MERGED
