"""
Utility helpers for the sdd_cash_manager feature.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Union

CurrencyAmount = Union[Decimal, str]


def quantize_currency(amount: CurrencyAmount, precision: int = 2) -> Decimal:
    """Quantize a currency amount to the specified precision using ROUND_HALF_UP."""
    decimal_amount = Decimal(str(amount))
    quantize_pattern = Decimal("1." + "0" * precision)
    return decimal_amount.quantize(quantize_pattern, rounding=ROUND_HALF_UP)


def format_currency(amount: CurrencyAmount) -> str:
    """Format a quantized currency amount as a string for display."""
    quantized_amount = quantize_currency(amount)
    return f"{quantized_amount:.2f}"
