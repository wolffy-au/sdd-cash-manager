import threading
import time
import uuid
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.base import Base
from sdd_cash_manager.models.enums import AccountingCategory, BankingProductType
from sdd_cash_manager.services.account_service import AccountFieldValue, AccountQueryCriteria, AccountService

# Mocking uuid.uuid4 to ensure deterministic IDs for testing
# We'll mock it specifically for the AccountService tests if needed, or rely on the model's mock if it's global
# For now, assuming the Account model's mock is sufficient or we might need a separate one here.
# If the service directly uses uuid.uuid4, we should mock it. Let's assume for now it uses Account's ID.

# Mocking uuid.uuid4 for service tests if they directly generate IDs
@pytest.fixture(autouse=True)
def mock_uuid_for_service_tests(monkeypatch):
    uuids_list = [
        uuid.UUID('00000000-0000-0000-0000-000000000001'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000002'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000003'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000004'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000005'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000006'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000007'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000008'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000009'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000010'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000011'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000012'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000013'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000014'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000015'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000016'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000017'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000018'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000019'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000020'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000021'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000022'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000023'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000024'), # for create_account
        uuid.UUID('00000000-0000-0000-0000-000000000025'), # for create_account
    ]
    monkeypatch.setattr(uuid, 'uuid4', MagicMock(side_effect=uuids_list))


def _ensure_account(account: Account | None) -> Account:
    if account is None:
        raise AssertionError("Expected Account instance, received None")
    return account


def _assert_update_error(
    service: AccountService,
    account_id: str,
    expected_message: str,
    **kwargs: AccountFieldValue,
) -> ValueError:
    with pytest.raises(
        RuntimeError,
        match=f"Failed to update account {account_id} due to unexpected error.",
    ) as exc:
        service.update_account(account_id, **kwargs)
    cause = exc.value.__cause__
    assert isinstance(cause, ValueError)
    assert expected_message in str(cause)
    return cause


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///file:test_db?mode=memory&cache=shared")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_account_service(db_session):
    return AccountService(db_session=db_session)

def test_account_service_create_account():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            name="Test Account",
            currency="USD",
            accounting_category=AccountingCategory.ASSET,
            banking_product_type=BankingProductType.CHECKING,
            notes="A test account"
        )
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
    account1 = _ensure_account(service.create_account("Account 1", "USD", AccountingCategory.ASSET))
    account2 = _ensure_account(service.create_account("Account 2", "EUR", AccountingCategory.LIABILITY))

    all_accounts = service.get_all_accounts()
    assert len(all_accounts) == 2
    # Ensure the correct accounts are returned
    assert any(acc.id == account1.id for acc in all_accounts)
    assert any(acc.id == account2.id for acc in all_accounts)

def test_account_service_update_account():
    service = AccountService()
    # Create an account and get its ID (which will be the mocked UUID)
    account = _ensure_account(service.create_account("Update Me", "USD", AccountingCategory.ASSET))
    initial_id = account.id # This will be the mocked UUID 'aaaaaaaa-...'

    # Update the account
    updated_account = _ensure_account(
        service.update_account(
            initial_id,
            name="Updated Account Name",
            notes="New notes",
            available_balance=Decimal("555.55"),
            hidden=True
        )
    )
    assert updated_account is not None
    assert updated_account.id == initial_id
    assert updated_account.name == "Updated Account Name"
    assert updated_account.notes == "New notes"
    assert updated_account.available_balance == Decimal("555.55")
    assert updated_account.hidden is True

    # Test updating a non-existent account
    non_existent_update = service.update_account("non-existent-id", name="Should Not Change")
    assert non_existent_update is None

def test_account_service_update_account_rejects_unsupported_field():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            "Unsupported Field Account",
            "USD",
            AccountingCategory.ASSET
        )
    )
    account_id = account.id

    with pytest.raises(ValueError, match="Cannot update unsupported field 'foo'\\."):
        service.update_account(account_id, foo="bar")

def test_account_service_delete_account():
    service = AccountService()
    # Create an account and get its ID (mocked UUID)
    account = _ensure_account(service.create_account("Delete Me", "USD", AccountingCategory.ASSET))
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
    account1 = _ensure_account(service.create_account("Checking Account", "USD", AccountingCategory.ASSET))
    account2 = _ensure_account(service.create_account("Savings Account", "USD", AccountingCategory.ASSET))
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
    account = _ensure_account(service.create_account("Balance Test", "USD", AccountingCategory.ASSET))

    # Initially, balance methods should return the stored balance as a placeholder
    # This test assumes that available_balance is the initial value
    assert service.calculate_running_balance(account.id) == account.available_balance
    assert service.calculate_reconciled_balance(account.id) == account.available_balance

    # Test with a non-existent account ID
    assert service.calculate_running_balance("non-existent-id") == 0.0
    assert service.calculate_reconciled_balance("non-existent-id") == 0.0

    # Test updating balance and checking if placeholders reflect it
    service.update_account(account.id, available_balance=Decimal("123.45"))
    updated_account = service.get_account(account.id)
    assert updated_account is not None
    assert service.calculate_running_balance(account.id) == Decimal("123.45")
    assert service.calculate_reconciled_balance(account.id) == Decimal("123.45")
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
    assert isinstance(quantized_value, Decimal)
    assert quantized_value == pytest.approx(Decimal("123.46"))

def test_account_service_update_account_validation_errors():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            "Validation Account",
            "USD",
            AccountingCategory.ASSET,
            banking_product_type=BankingProductType.CHECKING
        )
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
    parent_updated = _ensure_account(service.update_account(account_id, parent_account_id=str(parent_id)))
    assert parent_updated is not None
    assert parent_updated.parent_account_id == str(parent_id)

    cleared_account = _ensure_account(service.update_account(account_id, banking_product_type=None))
    assert cleared_account is not None
    assert cleared_account.banking_product_type is None

def test_account_service_string_field_validation_name():
    service = AccountService()
    account = _ensure_account(service.create_account("Valid Name", "USD", AccountingCategory.ASSET))
    account_id = account.id

    # Test valid name
    updated_account = _ensure_account(service.update_account(account_id, name="New Account Name"))
    assert updated_account.name == "New Account Name"

    # Test name too long
    with pytest.raises(ValueError, match="name cannot exceed 100 characters."):
        service.update_account(account_id, name="a" * 101)

    # Test name with forbidden characters
    with pytest.raises(ValueError, match="contains forbidden characters"):
        service.update_account(account_id, name="Name<Script>")
    with pytest.raises(ValueError, match="name contains invalid characters. Allowed pattern:"):
        service.update_account(account_id, name="Name@Symbol") # @ is not in the allowed regex


def test_account_service_string_field_validation_account_number():
    service = AccountService()
    account = _ensure_account(service.create_account("Valid Account", "USD", AccountingCategory.ASSET))
    account_id = account.id

    # Test valid account number
    updated_account = _ensure_account(service.update_account(account_id, account_number="123-ABC-456"))
    assert updated_account.account_number == "123-ABC-456"

    # Test account number too long
    with pytest.raises(ValueError, match="account_number cannot exceed 50 characters."):
        service.update_account(account_id, account_number="a" * 51)

    # Test account number with forbidden characters (only alphanumeric and hyphen allowed)
    with pytest.raises(ValueError, match="account_number contains invalid characters. Allowed pattern:"):
        service.update_account(account_id, account_number="123_abc")


def test_account_service_string_field_validation_notes():
    service = AccountService()
    account = _ensure_account(service.create_account("Valid Notes", "USD", AccountingCategory.ASSET))
    account_id = account.id

    # Test valid notes
    updated_account = _ensure_account(service.update_account(account_id, notes="Some valid notes here."))
    assert updated_account.notes == "Some valid notes here."

    # Test notes too long
    with pytest.raises(ValueError, match="notes cannot exceed 500 characters."):
        service.update_account(account_id, notes="a" * 501)

    # Test notes with forbidden characters
    with pytest.raises(ValueError, match="contains forbidden characters"):
        service.update_account(account_id, notes="Notes with <script>")

def test_account_service_update_currency_rejects_null():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            "Currency Helper",
            "USD",
            AccountingCategory.ASSET
        )
    )

    with pytest.raises(ValueError, match="currency cannot be null\\."):
        service.update_account(account.id, currency=None)

    updated_account = _ensure_account(service.update_account(account.id, currency="CAD"))
    assert updated_account is not None
    assert updated_account.currency == "CAD"

def test_account_service_update_accounting_category_rejects_null():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            "Category Helper",
            "USD",
            AccountingCategory.ASSET
        )
    )

    with pytest.raises(ValueError, match="accounting_category cannot be null\\."):
        service.update_account(account.id, accounting_category=None)

    updated_account = _ensure_account(service.update_account(account.id, accounting_category="revenue"))
    assert updated_account is not None
    assert updated_account.accounting_category == AccountingCategory.REVENUE

def test_account_service_misc_field_handlers_transform_values():
    service = AccountService()
    account = _ensure_account(
        service.create_account(
            "Conversion Helper",
            "USD",
            AccountingCategory.ASSET,
            banking_product_type=BankingProductType.CHECKING
        )
    )
    parent_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    updated_account = _ensure_account(
        service.update_account(
            account.id,
            account_number="987654321",
            parent_account_id=str(parent_id),
            notes="12345",
            banking_product_type=None,
            credit_limit=Decimal("11.239"),
            placeholder=True
        )
    )

    assert updated_account is not None
    assert updated_account.account_number == "987654321"
    assert updated_account.parent_account_id == str(parent_id)
    assert updated_account.notes == "12345"
    assert updated_account.banking_product_type is None
    assert updated_account.credit_limit == pytest.approx(Decimal("11.24"))
    assert updated_account.placeholder is True

def test_account_service_delete_account_with_placeholder_child():
    service = AccountService()
    parent = _ensure_account(service.create_account("Parent Account", "USD", AccountingCategory.ASSET))
    service.create_account(
        "Placeholder Child",
        "USD",
        AccountingCategory.ASSET,
        parent_account_id=parent.id,
        placeholder=True
    )

    with pytest.raises(ValueError, match="Cannot delete an account that still has placeholder child accounts."):
        service.delete_account(parent.id)

def test_get_account_hierarchy_balance_in_memory():
    service = AccountService()
    parent = _ensure_account(service.create_account("Parent", "USD", AccountingCategory.ASSET, available_balance=Decimal("100.0")))
    child = _ensure_account(
        service.create_account(
            "Child",
            "USD",
            AccountingCategory.ASSET,
            parent_account_id=parent.id,
            available_balance=Decimal("50.0")
        )
    )
    service.create_account(
        "Grandchild",
        "USD",
        AccountingCategory.ASSET,
        parent_account_id=child.id,
        available_balance=Decimal("25.0")
    )

    assert service.get_account_hierarchy_balance(parent.id) == pytest.approx(175.0)
    assert service.get_account_hierarchy_balance(child.id) == pytest.approx(75.0)
    assert service.get_account_hierarchy_balance("non-existent") == 0.0

def test_get_account_hierarchy_balance_db(db_session):
    service = AccountService(db_session=db_session)
    parent = _ensure_account(service.create_account("DB Parent", "USD", AccountingCategory.ASSET, available_balance=Decimal("80.0")))
    child = _ensure_account(
        service.create_account(
            "DB Child",
            "USD",
            AccountingCategory.ASSET,
            parent_account_id=parent.id,
            available_balance=Decimal("40.0")
        )
    )
    grandchild = _ensure_account(
        service.create_account(
            "DB Grandchild",
            "USD",
            AccountingCategory.ASSET,
            parent_account_id=child.id,
            available_balance=Decimal("20.0")
        )
    )

    assert service.get_account_hierarchy_balance(parent.id) == pytest.approx(140.0)
    assert service.get_account_hierarchy_balance(child.id) == pytest.approx(60.0)
    assert service.get_account_hierarchy_balance(grandchild.id) == pytest.approx(20.0)

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

def test_account_query_criteria_build_filters():
    criteria = AccountQueryCriteria(hidden=True, placeholder=False, search_term="cash")
    filters = criteria.build_filters()
    assert len(filters) == 3
    assert filters[0] is not None
    assert filters[1] is not None
    assert filters[2] is not None

def test_account_service_acquire_session_without_db_raises(monkeypatch):
    service = AccountService()
    monkeypatch.setattr(
        "sdd_cash_manager.services.account_service.log_critical_application_error",
        lambda *args, **kwargs: None
    )
    with pytest.raises(RuntimeError, match="Failed to acquire database session due to unexpected error."):
        service._acquire_session()

def test_encrypt_notes_respects_db_flag(monkeypatch):
    service_no_db = AccountService()
    assert service_no_db._encrypt_notes("plain") == "plain"

    dummy_session = object()
    service_with_db = AccountService(db_session=dummy_session)
    encrypted_values: list[str] = []

    def fake_encrypt(value):
        encrypted_values.append(value)
        return "encrypted"

    monkeypatch.setattr(service_with_db._cipher, "encrypt", fake_encrypt)
    assert service_with_db._encrypt_notes("plain") == "encrypted"
    assert encrypted_values == ["plain"]

def test_create_account_logs_runtime_error_on_db_failure(monkeypatch):
    logged_messages: list[str] = []

    def fake_log(message, **kwargs):
        logged_messages.append(message)

    monkeypatch.setattr(
        "sdd_cash_manager.services.account_service.log_critical_application_error",
        fake_log
    )

    class FailingSession:
        def add(self, _):
            raise RuntimeError("boom")

        def flush(self):
            pass

        def refresh(self, _):
            pass

        def close(self):
            pass

    service = AccountService(session_factory=lambda: FailingSession())

    with pytest.raises(RuntimeError, match="Failed to create account test-id due to unexpected error."):
        service.create_account(
            name="Logger Account",
            currency="USD",
            accounting_category=AccountingCategory.ASSET,
            id="test-id"
        )

    assert logged_messages, "Expected critical error to be logged."

def test_record_balance_snapshot_no_account(monkeypatch):
    service = AccountService()
    monkeypatch.setattr(service, "get_account", lambda account_id: None)
    service.record_balance_snapshot("missing")
    assert service.balance_history == {}


def test_account_service_concurrent_update_with_locking(db_session):
    # Setup: Create a single account
    service1 = AccountService(db_session=db_session)
    initial_balance = Decimal("100.00")
    account = _ensure_account(
        service1.create_account(
            name="Concurrent Account",
            currency="USD",
            accounting_category=AccountingCategory.ASSET,
            available_balance=initial_balance
        )
    )
    db_session.commit() # Explicitly commit the initial account creation
    account_id = account.id
    # Create a second service instance with a *new* session to simulate another client
    TestingSession_shared = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)
    session2 = TestingSession_shared()
    service2 = AccountService(db_session=session2)

    # Function to be run in a separate thread, simulating a concurrent update
    def concurrent_update_func():
        try:
            # Attempt to update the same account from the second service
            # This should block until the first transaction (in the main thread) is committed
            # or cause an error depending on SQLite's behavior with FOR UPDATE
            updated_account = _ensure_account(
                service2.update_account(
                    account_id,
                    available_balance=Decimal("200.00") # Attempt to change balance
                )
            )
            session2.commit() # Commit the changes from the second thread
            print(f"Thread updated account: {updated_account.available_balance}")
        except Exception as e:
            session2.rollback()
            print(f"Thread failed to update account: {e}")
        finally:
            session2.close()

    # Main thread (simulating first client)
    # Start a transaction in the main thread (db_session is already part of a transaction)
    # Get the account with a lock, modify it, but delay commit
    account_in_main_thread = db_session.execute(
        select(Account)
        .filter_by(id=account_id)
        .with_for_update() # Acquire pessimistic lock
    ).scalar_one()

    # Modify the account in the main thread's session
    account_in_main_thread.available_balance = Decimal("150.00")
    db_session.add(account_in_main_thread) # Mark as dirty

    # Start the concurrent update thread
    thread = threading.Thread(target=concurrent_update_func)
    thread.start()

    # Give the thread a moment to try and acquire the lock
    time.sleep(0.1)

    # Commit the first transaction (main thread)
    # Changed to rollback to see if concurrent thread's changes persist
    db_session.rollback()
    print(f"Main thread rolled back balance, expected: original. Current account_in_main_thread balance: {account_in_main_thread.available_balance}")

    # Wait for the concurrent thread to finish
    thread.join()

    # Verify the final state of the account from a fresh session
    session3 = TestingSession_shared()
    service3 = AccountService(db_session=session3)
    final_account = service3.get_account(account_id)
    session3.close()

    assert final_account is not None
    # If the concurrent thread successfully updated and committed 200.0,
    # and main thread rolled back, then final should be 200.0
    assert final_account.available_balance == Decimal("200.00") # Expect thread's update to be last
