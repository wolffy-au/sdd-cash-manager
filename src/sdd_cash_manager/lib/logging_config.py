"""Logging helpers for sdd-cash-manager observability."""

from __future__ import annotations

import logging
from logging import Formatter, Logger, StreamHandler

from sdd_cash_manager.core.config import settings


def _resolve_log_level() -> int:
    """Return the numeric log level configured for the feature set."""
    level_name = settings.log_level.strip().upper()
    return getattr(logging, level_name, logging.INFO)


def get_logger(name: str = "sdd_cash_manager") -> Logger:
    """Return a logger that honors the shared formatting and policies."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(_resolve_log_level())
    logger.propagate = False
    return logger
