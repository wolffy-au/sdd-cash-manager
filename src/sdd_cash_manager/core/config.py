"""Environment-driven configuration for the sdd-cash-manager feature."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

ENV_FILE = Path(".env")


def _load_dotenv() -> None:
    """Load `.env` values into the process environment when the file exists."""
    if not ENV_FILE.is_file():
        return
    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not key:
            continue
        normalized_key = key.strip()
        if not normalized_key:
            continue
        normalized_value = value.strip().strip('"').strip("'")
        if normalized_key not in os.environ:
            os.environ[normalized_key] = normalized_value


def _coerce_bool(env_key: str, default: bool) -> bool:
    raw = os.environ.get(env_key)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


_load_dotenv()


@dataclass(frozen=True)
class AppSettings:
    """Simple configuration backed by environment variables."""

    database_url: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_DATABASE_URL", "sqlite:///./sdd_cash_manager.db")
    )
    database_echo: bool = field(
        default_factory=lambda: _coerce_bool("SDD_CASH_MANAGER_DATABASE_ECHO", False)
    )
    log_level: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_LOG_LEVEL", "INFO")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_JWT_SECRET", "change-me-secret")
    )
    jwt_algorithm: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_JWT_ALGORITHM", "HS256")
    )
    encryption_key: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_ENCRYPTION_KEY", "change-me-key")
    )
    # Security guard is enabled by default; opt-out explicitly via the env var if needed.
    security_enabled: bool = field(
        default_factory=lambda: _coerce_bool("SDD_CASH_MANAGER_SECURITY_ENABLED", True)
    )
    log_format: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    security_log_level: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_SECURITY_LOG_LEVEL", "INFO")
    )
    security_log_file: str = field(
        default_factory=lambda: os.environ.get("SDD_CASH_MANAGER_SECURITY_LOG_FILE", "security.log")
    )
    security_console_log_enabled: bool = field(
        default_factory=lambda: _coerce_bool("SDD_CASH_MANAGER_SECURITY_CONSOLE_LOG_ENABLED", False)
    )
    security_alerts_enabled: bool = field(
        default_factory=lambda: _coerce_bool("SDD_CASH_MANAGER_SECURITY_ALERTS_ENABLED", False)
    )


settings: Final[AppSettings] = AppSettings()
