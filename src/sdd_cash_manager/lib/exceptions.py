"""
Common exception types for the sdd_cash_manager domain.
"""


class CashManagerError(Exception):
    """Base error for the cash manager domain."""


class ValidationError(CashManagerError):
    """Raised when input data fails validation rules."""


class NotFoundError(CashManagerError):
    """Raised when a requested resource cannot be located."""
