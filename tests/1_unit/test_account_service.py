import uuid
from unittest.mock import MagicMock

import pytest

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.enums import AccountingCategory, BankingAccountType
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
        banking_product_type=BankingAccountType.CHECKING,
        notes="A test account"
    )

    # Check against the mocked UUID from the fixture
    assert account.id == str(uuid.UUID('00000000-0000-0000-0000-000000000001'))
    assert account.name == "Test Account"
    assert account.currency == "USD"
    assert account.accounting_category == AccountingCategory.ASSET
    assert account.banking_product_type == BankingAccountType.CHECKING
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
