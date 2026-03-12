from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import HTTPException

from sdd_cash_manager.api import accounts
from sdd_cash_manager.api.accounts import (
    AccountCreatePayload,
    AccountingCategory,
    AccountUpdatePayload,
    ActionType,
    BalanceAdjustmentPayload,
    BankingProductType,
    _assert_no_control_chars,
    _ensure_parent_account_exists,
    _sanitize_search_term,
    _validate_currency_value,
    _validate_name_value,
    _validate_text_field_no_special_chars,
    adjust_account_balance,
    create_account,
    get_accounts,
    update_account,
)
from sdd_cash_manager.services.account_service import AccountService
from sdd_cash_manager.services.transaction_service import TransactionService


def test_validate_name_value_rejects_unsupported_pattern():
    with pytest.raises(ValueError, match="unsupported characters"):
        _validate_name_value("bad@name")

def test_validate_name_value_rejects_disallowed_literal():
    with pytest.raises(ValueError, match="unsupported characters"):
        _validate_name_value("bad<name")

def test_validate_currency_value_rejects_unknown():
    with pytest.raises(ValueError, match="unsupported currency"):
        _validate_currency_value("ZZZ")

def test_validate_text_field_no_special_chars_rejects_invalid_sequence():
    with pytest.raises(ValueError, match="notes contain invalid characters"):
        _validate_text_field_no_special_chars("invalid<>", "notes", "notes contain invalid characters")

def test_assert_no_control_chars():
    with pytest.raises(ValueError, match="contains invalid characters"):
        _assert_no_control_chars("bad\x00name", "account name")
    assert _assert_no_control_chars("clean name", "account name") == "clean name"

def test_sanitize_search_term_various_paths():
    assert _sanitize_search_term(None) is None
    assert _sanitize_search_term("  valid term  ") == "valid term"
    long_term = "a" * (accounts.MAX_SEARCH_TERM_LENGTH + 1)
    with pytest.raises(HTTPException) as excinfo:
        _sanitize_search_term(long_term)
    assert excinfo.value.status_code == 400
    with pytest.raises(HTTPException) as excinfo:
        _sanitize_search_term("bad\x00term")
    assert excinfo.value.status_code == 400

class _StubAccountService:
    def __init__(self, result):
        self._result = result

    def get_account(self, account_id):
        return self._result

    def get_account_hierarchy_balance(self, account_id):
        return 0.0

def test_ensure_parent_account_exists_branch(monkeypatch):
    assert _ensure_parent_account_exists(
        cast(AccountService, _StubAccountService(None)), None
    ) is None
    with pytest.raises(HTTPException) as excinfo:
        _ensure_parent_account_exists(
            cast(AccountService, _StubAccountService(None)), uuid4()
        )
    assert excinfo.value.status_code == 400

def _build_account_payload():
    return AccountCreatePayload(
        name="Test Account",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        banking_product_type=BankingProductType.BANK,
        available_balance=Decimal("100.00"),
    )

class _ErrorAccountService:
    def __init__(self, exc):
        self.exc = exc

    def create_account(self, *args, **kwargs):
        raise self.exc

    def update_account(self, *args, **kwargs):
        raise self.exc

    def get_account_hierarchy_balance(self, account_id):
        return 0.0

def test_create_account_value_error():
    payload = _build_account_payload()
    with pytest.raises(HTTPException) as excinfo:
        create_account(
            payload,
            account_service=cast(
                AccountService, _ErrorAccountService(ValueError("bad input"))
            ),
        )
    assert excinfo.value.status_code == 400
    assert "bad input" in excinfo.value.detail

def test_create_account_runtime_error():
    payload = _build_account_payload()
    with pytest.raises(HTTPException) as excinfo:
        create_account(
            payload,
            account_service=cast(
                AccountService, _ErrorAccountService(RuntimeError("boom"))
            ),
        )
    assert excinfo.value.status_code == 500

def test_get_accounts_filters_by_search_term(monkeypatch):
    monkeypatch.setattr(accounts, "AccountResponse", lambda **kwargs: kwargs)

    class StubAccountService:
        def get_all_accounts(self):
            return [
                SimpleNamespace(id=str(uuid4()), name="Matching Account", hidden=False, placeholder=False),
                SimpleNamespace(id=str(uuid4()), name="Other", hidden=False, placeholder=False),
            ]

        def get_account_hierarchy_balance(self, account_id):
            return 0.0

    results = cast(
        list[dict[str, Any]],
        get_accounts(
            search_term="matching",
            account_service=cast(AccountService, StubAccountService()),
        ),
    )
    assert len(results) == 1
    assert results[0]["name"] == "Matching Account"

def test_get_accounts_filters_hidden_placeholder(monkeypatch):
    monkeypatch.setattr(accounts, "AccountResponse", lambda **kwargs: kwargs)

    class StubAccountService:
        def get_all_accounts(self):
            return [
                SimpleNamespace(id=str(uuid4()), name="Match 1", hidden=True, placeholder=False),
                SimpleNamespace(id=str(uuid4()), name="Match 2", hidden=True, placeholder=True),
            ]

        def get_account_hierarchy_balance(self, account_id):
            return 0.0

    results = cast(
        list[dict[str, Any]],
        get_accounts(
            search_term=None,
            hidden=True,
            placeholder=False,
            account_service=cast(AccountService, StubAccountService()),
        ),
    )
    assert all(acc["hidden"] for acc in results)
    assert all(acc["placeholder"] is False for acc in results)

def test_update_account_quantization(monkeypatch):
    monkeypatch.setattr(accounts, "AccountResponse", lambda **kwargs: kwargs)
    captured = {}

    class StubAccountService:
        def get_account(self, account_id):
            return SimpleNamespace(id=account_id)

        def update_account(self, account_id, **kwargs):
            captured["account_id"] = account_id
            captured["kwargs"] = kwargs
            return SimpleNamespace(id=account_id, **kwargs)

        def get_account_hierarchy_balance(self, account_id):
            return 0.0

    payload = AccountUpdatePayload(
        parent_account_id=uuid4(),
        available_balance=Decimal("123.456"),
        credit_limit=Decimal("456.789"),
    )
    response = cast(
        dict[str, Any],
        update_account(
            uuid4(),
            payload,
            account_service=cast(AccountService, StubAccountService()),
        ),
    )
    assert response["id"] == captured["account_id"]
    assert captured["kwargs"]["parent_account_id"] == str(payload.parent_account_id)
    assert captured["kwargs"]["available_balance"] == float(Decimal("123.46"))
    assert captured["kwargs"]["credit_limit"] == float(Decimal("456.79"))
    assert response["available_balance"] == float(Decimal("123.46"))
    assert response["credit_limit"] == float(Decimal("456.79"))

def test_update_account_returns_error_for_unsupported_field():
    payload = _UnsupportedFieldPayload(
        parent_account_id=uuid4(),
        available_balance=Decimal("10.00"),
    )

    class UnsupportedFieldService:
        def get_account(self, account_id):
            return SimpleNamespace(id=account_id)

        def update_account(self, account_id, **kwargs):
            assert "foo" in kwargs
            raise ValueError("Cannot update unsupported field 'foo'.")

    with pytest.raises(HTTPException) as excinfo:
        update_account(
            uuid4(),
            payload,
            account_service=cast(
                AccountService, UnsupportedFieldService()
            ),
        )
    assert excinfo.value.status_code == 400
    assert "Cannot update unsupported field 'foo'." in str(excinfo.value.detail)

@pytest.mark.parametrize(
    "error_message",
    [
        "currency cannot be null.",
        "accounting_category cannot be null.",
        "Currency must be a 3-letter uppercase ISO 4217 code.",
        "Invalid accounting_category 'Unknown'.",
        "Invalid banking_product_type 'BadType'.",
        "available_balance cannot be null.",
        "name cannot be null.",
        "hidden must be a boolean value.",
        "placeholder must be a boolean value.",
    ],
)
def test_update_account_validation_errors_surface(error_message):
    payload = _build_update_payload()
    with pytest.raises(HTTPException) as excinfo:
        update_account(
            uuid4(),
            payload,
            account_service=cast(
                AccountService, _ErrorAccountService(ValueError(error_message))
            ),
        )
    assert excinfo.value.status_code == 400
    assert error_message in str(excinfo.value.detail)

class _TransactionStub:
    def __init__(self, result=None, exc=None):
        self._result = result
        self._exc = exc

    def perform_balance_adjustment(self, **kwargs):
        if self._exc:
            raise self._exc
        return self._result

def _build_balance_payload():
    return BalanceAdjustmentPayload(
        target_balance=Decimal("200.00"),
        adjustment_date=date.today(),
        description="Valid desc",
        action_type=ActionType.ADJUSTMENT,
    )

def _build_update_payload():
    return AccountUpdatePayload(
        available_balance=Decimal("10.00"),
    )


class _UnsupportedFieldPayload(AccountUpdatePayload):
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        data["foo"] = "bar"
        return data


def test_adjust_account_balance_no_change():
    payload = _build_balance_payload()
    with pytest.raises(HTTPException) as excinfo:
        adjust_account_balance(
            uuid4(),
            payload,
            transaction_service=cast(
                TransactionService, _TransactionStub(result=None)
            ),
        )
    assert excinfo.value.status_code == 400
    assert "No adjustment needed" in excinfo.value.detail

def test_adjust_account_balance_value_error():
    payload = _build_balance_payload()
    with pytest.raises(HTTPException) as excinfo:
        adjust_account_balance(
            uuid4(),
            payload,
            transaction_service=cast(
                TransactionService,
                _TransactionStub(exc=ValueError("bad")),
            ),
        )
    assert excinfo.value.status_code == 400

def test_adjust_account_balance_runtime_error():
    payload = _build_balance_payload()
    with pytest.raises(HTTPException) as excinfo:
        adjust_account_balance(
            uuid4(),
            payload,
            transaction_service=cast(
                TransactionService,
                _TransactionStub(exc=RuntimeError("boom")),
            ),
        )
    assert excinfo.value.status_code == 500

def test_adjust_account_balance_generic_error():
    payload = _build_balance_payload()
    with pytest.raises(HTTPException) as excinfo:
        adjust_account_balance(
            uuid4(),
            payload,
            transaction_service=cast(
                TransactionService,
                _TransactionStub(exc=TypeError("oops")),
            ),
        )
    assert excinfo.value.status_code == 500
