import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.enums import AccountingCategory, BankingProductType
from sdd_cash_manager.services.account_service import AccountService

# Mocking uuid.uuid4 to ensure deterministic IDs for testing
# We'll mock it specifically for the AccountService tests if needed, or rely on the model's mock if it's global
# For now, assuming the Account model's mock is sufficient or we might need a separate one here.
# If the service directly uses uuid.uuid4, we should mock it. Let's assume for now it uses Account's ID.

# Mocking uuid.uuid4 for service tests if they directly generate IDs
@pytest.fixture(autouse=True)
def mock_uuid_for_service_tests(monkeypatch):
    uuids = [
        uuid.UUID('00000000-0000-0000-0000-000000000001'),
        uuid.UUID('00000000-0000-0000-0000-000000000002'),
        uuid.UUID('00000000-0000-0000-0000-000000000003'),
        uuid.UUID('00000000-0000-0000-0000-000000000004'),
        uuid.UUID('00000000-0000-0000-0000-000000000005'),
        uuid.UUID('00000000-0000-0000-0000-000000000006'),
        uuid.UUID('00000000-0000-0000-0000-000000000007'),
        uuid.UUID('00000000-0000-0000-0000-000000000008'),
    ]
    monkeypatch.setattr('sdd_cash_manager.services.account_service.uuid.uuid4',
                        MagicMock(side_effect=uuids))

def test_account_service_create_account():
    service = AccountService()
    account = service.create_account(
        name="Test Account",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        banking_product_type=BankingProductType.CHECKING,
        notes="A test account"
    )

    # Check against the mocked UUID from the fixture
    assert account.id == str(uuid.UUID('00000000-0000-0000-0000-000000000001'))
    assert account.name == "Test Account"
    assert account.currency == "USD"
    assert account.accounting_category == AccountingCategory.ASSET
    assert account.banking_product_type == BankingProductType.CHECKING
    assert account.notes == "A test account"
    assert account.available_balance == 0.0
    assert account.hidden is False
    assert account.placeholder is False
    assert len(service.accounts) == 1
    assert service.accounts[account.id] == account

def test_account_service_create_account_required_fields():
    service = AccountService()
    # Test missing name
    with pytest.raises(ValueError, match="Name, currency, and accounting category are required."):
        service.create_account(name="", currency="USD", accounting_category=AccountingCategory.ASSET)
    # Test missing currency
    with pytest.raises(ValueError, match="Name, currency, and accounting category are required."):
        service.create_account(name="Test", currency="", accounting_category=AccountingCategory.ASSET)
    # Test missing accounting_category (using "" as an example of invalid/empty string)
    with pytest.raises(ValueError, match="Name, currency, and accounting category are required."):
        service.create_account(name="Test", currency="USD", accounting_category="")

def test_account_service_get_account():
    service = AccountService()
    # Use the mocked UUID from the fixture for consistency
    account_id = str(uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'))
    account = Account(id=account_id, name="Get Account", currency="EUR", accounting_category=AccountingCategory.LIABILITY)
    service.accounts[account_id] = account

    retrieved_account = service.get_account(account_id)
    assert retrieved_account is not None
    assert retrieved_account.id == account_id
    assert retrieved_account.name == "Get Account"

    # Test getting a non-existent account
    non_existent_account = service.get_account("non-existent-id")
    assert non_existent_account is None

def test_account_service_get_all_accounts():
    service = AccountService()
    # Use mocked UUIDs for accounts created by the service
    account1 = service.create_account("Account 1", "USD", AccountingCategory.ASSET)
    account2 = service.create_account("Account 2", "EUR", AccountingCategory.LIABILITY)

    all_accounts = service.get_all_accounts()
    assert len(all_accounts) == 2
    # Ensure the correct accounts are returned
    assert any(acc.id == account1.id for acc in all_accounts)
    assert any(acc.id == account2.id for acc in all_accounts)

def test_account_service_update_account():
    service = AccountService()
    # Create an account and get its ID (which will be the mocked UUID)
    account = service.create_account("Update Me", "USD", AccountingCategory.ASSET)
    initial_id = account.id # This will be the mocked UUID 'aaaaaaaa-...'

    # Update the account
    updated_account = service.update_account(
        initial_id,
        name="Updated Account Name",
        notes="New notes",
        available_balance=555.55,
        hidden=True
    )

    assert updated_account is not None
    assert updated_account.id == initial_id
    assert updated_account.name == "Updated Account Name"
    assert updated_account.notes == "New notes"
    assert updated_account.available_balance == 555.55
    assert updated_account.hidden is True

    # Test updating a non-existent account
    non_existent_update = service.update_account("non-existent-id", name="Should Not Change")
    assert non_existent_update is None

def test_account_service_update_account_rejects_unsupported_field():
    service = AccountService()
    account = service.create_account(
        "Unsupported Field Account",
        "USD",
        AccountingCategory.ASSET
    )
    account_id = account.id

    with pytest.raises(ValueError, match="Cannot update unsupported field 'foo'\\."):
        service.update_account(account_id, foo="bar")

def test_account_service_delete_account():
    service = AccountService()
    # Create an account and get its ID (mocked UUID)
    account = service.create_account("Delete Me", "USD", AccountingCategory.ASSET)
    account_id = account.id # This will be the mocked UUID 'aaaaaaaa-...'

    # Delete the account
    delete_success = service.delete_account(account_id)
    assert delete_success is True
    assert service.get_account(account_id) is None
    assert len(service.accounts) == 0

    # Test deleting a non-existent account
    delete_fail = service.delete_account("non-existent-id")
    assert delete_fail is False

def test_account_service_search_accounts_by_name():
    service = AccountService()
    # Create accounts using the service's creation method to ensure IDs are set
    account1 = service.create_account("Checking Account", "USD", AccountingCategory.ASSET)
    account2 = service.create_account("Savings Account", "USD", AccountingCategory.ASSET)
    service.create_account("Credit Card", "USD", AccountingCategory.LIABILITY) # This is not used, so remove the assignment.
    service.create_account("Investment Portfolio", "USD", AccountingCategory.ASSET) # This is not used, so remove the assignment.

    # Case-insensitive partial match
    results_checking = service.search_accounts_by_name("checking")
    assert len(results_checking) == 1
    assert results_checking[0].name == "Checking Account"

    results_account = service.search_accounts_by_name("Account")
    assert len(results_account) == 2
    assert any(acc.id == account1.id for acc in results_account)
    assert any(acc.name == "Checking Account" for acc in results_account)
    assert any(acc.id == account2.id for acc in results_account)
    assert any(acc.name == "Savings Account" for acc in results_account)

    results_empty = service.search_accounts_by_name("NonExistent")
    assert len(results_empty) == 0

def test_account_service_balance_placeholders():
    service = AccountService()
    account = service.create_account("Balance Test", "USD", AccountingCategory.ASSET)

    # Initially, balance methods should return the stored balance as a placeholder
    # This test assumes that available_balance is the initial value
    assert service.calculate_running_balance(account.id) == account.available_balance
    assert service.calculate_reconciled_balance(account.id) == account.available_balance

    # Test with a non-existent account ID
    assert service.calculate_running_balance("non-existent-id") == 0.0
    assert service.calculate_reconciled_balance("non-existent-id") == 0.0

    # Test updating balance and checking if placeholders reflect it
    service.update_account(account.id, available_balance=123.45)
    updated_account = service.get_account(account.id)
    assert updated_account is not None
    assert service.calculate_running_balance(account.id) == 123.45
    assert service.calculate_reconciled_balance(account.id) == 123.45

def test_account_service_validation_helpers():
    with pytest.raises(ValueError, match="Currency must be"):
        AccountService._validate_currency("US")
    with pytest.raises(ValueError, match="Currency must be"):
        AccountService._validate_currency("usd")

    assert AccountService._validate_enum(AccountingCategory.ASSET, AccountingCategory, "accounting_category") == AccountingCategory.ASSET.value
    assert AccountService._validate_enum("asset", AccountingCategory, "accounting_category") == AccountingCategory.ASSET.value
    assert AccountService._validate_enum("ASSET", AccountingCategory, "accounting_category") == AccountingCategory.ASSET.value
    with pytest.raises(ValueError, match="Invalid accounting_category"):
        AccountService._validate_enum("UNKNOWN", AccountingCategory, "accounting_category")

    assert AccountService._quantize_value(None) is None
    quantized_value = AccountService._quantize_value(Decimal("123.456"))
    assert isinstance(quantized_value, float)
    assert quantized_value == pytest.approx(123.46)

def test_account_service_update_account_validation_errors():
    service = AccountService()
    account = service.create_account(
        "Validation Account",
        "USD",
        AccountingCategory.ASSET,
        banking_product_type=BankingProductType.CHECKING
    )
    account_id = account.id

    with pytest.raises(ValueError, match="Currency must be a 3-letter uppercase ISO 4217 code\\."):
        service.update_account(account_id, currency="US")
    with pytest.raises(ValueError, match="Invalid accounting_category 'Unknown'\\."):
        service.update_account(account_id, accounting_category="Unknown")
    with pytest.raises(ValueError, match="Invalid banking_product_type 'BadType'\\."):
        service.update_account(account_id, banking_product_type="BadType")
    with pytest.raises(ValueError, match="available_balance cannot be null\\."):
        service.update_account(account_id, available_balance=None)
    with pytest.raises(ValueError, match="name cannot be null\\."):
        service.update_account(account_id, name=None)
    with pytest.raises(ValueError, match="hidden must be a boolean value\\."):
        service.update_account(account_id, hidden="yes")
    with pytest.raises(ValueError, match="placeholder must be a boolean value\\."):
        service.update_account(account_id, placeholder="no")

    parent_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    parent_updated = service.update_account(account_id, parent_account_id=str(parent_id))
    assert parent_updated is not None
    assert parent_updated.parent_account_id == str(parent_id)

    cleared_account = service.update_account(account_id, banking_product_type=None)
    assert cleared_account is not None
    assert cleared_account.banking_product_type is None

def test_account_service_update_currency_rejects_null():
    service = AccountService()
    account = service.create_account(
        "Currency Helper",
        "USD",
        AccountingCategory.ASSET
    )

    with pytest.raises(ValueError, match="currency cannot be null\\."):
        service.update_account(account.id, currency=None)

    updated_account = service.update_account(account.id, currency="CAD")
    assert updated_account is not None
    assert updated_account.currency == "CAD"

def test_account_service_update_accounting_category_rejects_null():
    service = AccountService()
    account = service.create_account(
        "Category Helper",
        "USD",
        AccountingCategory.ASSET
    )

    with pytest.raises(ValueError, match="accounting_category cannot be null\\."):
        service.update_account(account.id, accounting_category=None)

    updated_account = service.update_account(account.id, accounting_category="revenue")
    assert updated_account is not None
    assert updated_account.accounting_category == AccountingCategory.REVENUE

def test_account_service_misc_field_handlers_transform_values():
    service = AccountService()
    account = service.create_account(
        "Conversion Helper",
        "USD",
        AccountingCategory.ASSET,
        banking_product_type=BankingProductType.CHECKING
    )
    parent_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    updated_account = service.update_account(
        account.id,
        account_number=987654321,
        parent_account_id=str(parent_id),
        notes=12345,
        banking_product_type=None,
        credit_limit=Decimal("11.239"),
        placeholder=True
    )

    assert updated_account is not None
    assert updated_account.account_number == "987654321"
    assert updated_account.parent_account_id == str(parent_id)
    assert updated_account.notes == "12345"
    assert updated_account.banking_product_type is None
    assert updated_account.credit_limit == pytest.approx(11.24)
    assert updated_account.placeholder is True

def test_account_service_delete_account_with_placeholder_child():
    service = AccountService()
    parent = service.create_account("Parent Account", "USD", AccountingCategory.ASSET)
    service.create_account(
        "Placeholder Child",
        "USD",
        AccountingCategory.ASSET,
        parent_account_id=parent.id,
        placeholder=True
    )

    with pytest.raises(ValueError, match="Cannot delete an account that still has placeholder child accounts."):
        service.delete_account(parent.id)

def test_account_service_search_accounts_visibility_filters():
    service = AccountService()
    service.create_account("Visible Account", "USD", AccountingCategory.ASSET)
    service.create_account("Hidden Account", "USD", AccountingCategory.ASSET, hidden=True)
    service.create_account("Placeholder Account", "USD", AccountingCategory.ASSET, placeholder=True)

    default_results = service.search_accounts_by_name("account")
    assert len(default_results) == 1
    assert default_results[0].name == "Visible Account"

    hidden_results = service.search_accounts_by_name("account", include_hidden=True)
    assert any(acc.name == "Hidden Account" for acc in hidden_results)
    assert all(acc.hidden is False or acc.name == "Hidden Account" for acc in hidden_results)

    placeholder_results = service.search_accounts_by_name("account", include_placeholder=True)
    assert any(acc.name == "Placeholder Account" for acc in placeholder_results)
    assert all(acc.placeholder is False or acc.name == "Placeholder Account" for acc in placeholder_results)

    all_results = service.search_accounts_by_name("account", include_hidden=True, include_placeholder=True)
    assert any(acc.name == "Visible Account" for acc in all_results)
    assert any(acc.name == "Hidden Account" for acc in all_results)
    assert any(acc.name == "Placeholder Account" for acc in all_results)
