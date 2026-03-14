from decimal import Decimal

from sdd_cash_manager.lib.utils import format_currency


def test_format_currency_rounds_and_formats_strings() -> None:
    assert format_currency("1.2") == "1.20"
    assert format_currency("2.345") == "2.35"
    assert format_currency("-0.004") == "-0.00"


def test_format_currency_handles_decimals() -> None:
    assert format_currency(Decimal("123.456")) == "123.46"
    assert format_currency(Decimal("0")) == "0.00"
