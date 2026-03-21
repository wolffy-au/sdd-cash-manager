import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
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
    TRANSACTION_CREATED = "TRANSACTION_CREATED"
    QUICKFILL_APPROVED = "QUICKFILL_APPROVED"
    DUPLICATE_MERGED = "DUPLICATE_MERGED"
    ACCOUNT_MERGED = "ACCOUNT_MERGED"


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


def log_transaction_created(
    transaction_id: str,
    debit_account_id: str,
    credit_account_id: str,
    amount: Decimal,
    currency: str,
    action: str,
    user_id: str | None = None,
    account_id: str | None = None,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit an audit event whenever a double-entry transaction is recorded."""
    event_metadata: dict[str, Any] = {
        "transaction_id": transaction_id,
        "debit_account_id": debit_account_id,
        "credit_account_id": credit_account_id,
        "amount": str(amount),
        "currency": currency,
        "action": action,
        "status": status,
    }
    if metadata:
        event_metadata.update(metadata)

    log_security_event(
        SecurityEvent.TRANSACTION_CREATED,
        f"Transaction {transaction_id} created ({action})",
        user_id=user_id,
        account_id=account_id or debit_account_id,
        metadata=event_metadata,
        level=logging.INFO,
    )


def log_quickfill_template_approved(
    template_id: str,
    approved_by: str | None,
    action: str,
    currency: str,
    transfer_from: str,
    transfer_to: str,
    confidence_score: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log QuickFill approvals to capture who confirmed a template before it surfaces."""
    event_metadata: dict[str, Any] = {
        "template_id": template_id,
        "transfer_from": transfer_from,
        "transfer_to": transfer_to,
        "action": action,
        "currency": currency,
        "confidence_score": confidence_score,
    }
    if metadata:
        event_metadata.update(metadata)

    log_security_event(
        SecurityEvent.QUICKFILL_APPROVED,
        f"QuickFill template {template_id} approved",
        user_id=approved_by,
        account_id=transfer_from,
        metadata=event_metadata,
    )


def log_duplicate_merge(
    candidate_id: str,
    merged_transaction_ids: Sequence[str],
    account_scope: str,
    merged_by: str | None = None,
    preserve_audit: bool = False,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Capture duplicate consolidation activity for auditing."""
    event_metadata: dict[str, Any] = {
        "candidate_id": candidate_id,
        "merged_transaction_ids": list(merged_transaction_ids),
        "scope": account_scope,
        "preserve_audit": preserve_audit,
    }
    if metadata:
        event_metadata.update(metadata)

    log_security_event(
        SecurityEvent.DUPLICATE_MERGED,
        f"Duplicate candidate {candidate_id} merged",
        user_id=merged_by,
        metadata=event_metadata,
    )


def log_account_merge(
    plan_id: str,
    source_account_id: str,
    target_account_id: str,
    executed_by: str | None = None,
    reparenting_map: dict[str, str] | None = None,
    affected_entries_count: int | None = None,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log planned and executed account merges with their hierarchy impact."""
    event_metadata: dict[str, Any] = {
        "plan_id": plan_id,
        "source_account_id": source_account_id,
        "target_account_id": target_account_id,
        "reparenting_map": reparenting_map,
        "affected_entries_count": affected_entries_count,
        "plan_status": status,
    }
    if metadata:
        event_metadata.update(metadata)

    log_security_event(
        SecurityEvent.ACCOUNT_MERGED,
        f"Account merge plan {plan_id} executed between {source_account_id} and {target_account_id}",
        user_id=executed_by,
        account_id=target_account_id,
        metadata=event_metadata,
    )

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
