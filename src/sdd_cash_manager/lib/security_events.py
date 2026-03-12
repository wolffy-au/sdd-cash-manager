import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sdd_cash_manager.core.config import settings

# Initialize a specific logger for security events
security_logger = logging.getLogger("security_events")
security_logger.setLevel(settings.security_log_level)

# Configure handler if not already configured by logging_config
if not security_logger.handlers:
    # Use a separate file handler for security events
    security_file_handler = logging.FileHandler(settings.security_log_file)
    security_file_handler.setFormatter(logging.Formatter(settings.log_format))
    security_logger.addHandler(security_file_handler)

    # Optionally add a console handler for critical security events
    if settings.security_console_log_enabled:
        security_console_handler = logging.StreamHandler()
        security_console_handler.setFormatter(logging.Formatter(settings.log_format))
        security_logger.addHandler(security_console_handler)

class SecurityEvent(str, Enum):
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    DATA_TAMPERING_ATTEMPT = "DATA_TAMPERING_ATTEMPT"
    SENSITIVE_DATA_ACCESS = "SENSITIVE_DATA_ACCESS"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    SYSTEM_ALERT = "SYSTEM_ALERT"
    BREACH_DETECTION = "BREACH_DETECTION"
    CONCURRENCY_VIOLATION = "CONCURRENCY_VIOLATION"


def log_security_event(
    event_type: SecurityEvent,
    message: str,
    user_id: str | None = None,
    account_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    level: int = logging.INFO
) -> None:
    """Logs a security-relevant event with structured data.

    Args:
        event_type: The type of security event.
        message: A human-readable description of the event.
        user_id: Optional ID of the user associated with the event.
        account_id: Optional ID of the account involved in the event.
        metadata: Optional dictionary for additional context.
        level: Logging level (e.g., logging.INFO, logging.WARNING, logging.ERROR).
    """
    event_data: dict[str, Any] = {
        "event_type": event_type.value,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "account_id": account_id,
        "metadata": metadata or {}
    }
    security_logger.log(level, event_data)

    # Placeholder for alerting mechanism
    if level >= logging.WARNING and settings.security_alerts_enabled:
        _send_security_alert(event_type, message, event_data)


def _send_security_alert(event_type: SecurityEvent, message: str, event_data: dict[str, Any]) -> None:
    """Placeholder for sending out security alerts (e.g., email, pager, SIEM)."""
    # In a real system, this would integrate with an alerting platform
    # For now, just log a critical message that an alert *would* be sent.
    security_logger.critical(
        f"!!! SECURITY ALERT !!! Type: {event_type.value}, Message: {message}, Data: {event_data}"
    )
    # Further actions could include:
    # - Sending email to security team
    # - Pushing to a SIEM (Security Information and Event Management) system
    # - Triggering automated response (e.g., temporarily blocking user)
    # - Incrementing a metric for dashboards

def log_critical_application_error(
    message: str,
    user_id: str | None = None,
    account_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    exc_info: bool = True # Capture exception info by default
) -> None:
    """Logs a critical application error as a security event and triggers an alert.

    Args:
        message: A description of the critical error.
        user_id: Optional ID of the user associated with the error.
        account_id: Optional ID of the account involved in the error.
        metadata: Optional dictionary for additional context.
        exc_info: Whether to include exception info (traceback) in the log.
    """
    event_type = SecurityEvent.SYSTEM_ALERT
    event_data: dict[str, Any] = {
        "event_type": event_type.value,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "account_id": account_id,
        "metadata": metadata or {}
    }
    security_logger.error(event_data, exc_info=exc_info)

    if settings.security_alerts_enabled:
        _send_security_alert(event_type, message, event_data)
