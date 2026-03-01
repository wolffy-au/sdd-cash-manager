from sdd_cash_manager.models.account import Account
from sdd_cash_manager.models.enums import AccountingCategory, BankingAccountType

# Test stubs for Account model and enums

def test_account_model_creation():
    account = Account(
        name="Checking Account",
        currency="USD",
        accounting_category=AccountingCategory.ASSET,
        banking_product_type=BankingAccountType.CHECKING,
        available_balance=1000.50,
        credit_limit=None,
        notes="Primary checking account"
    )
    assert account.name == "Checking Account"
    assert account.currency == "USD"
    assert account.accounting_category == AccountingCategory.ASSET
    assert account.banking_product_type == BankingAccountType.CHECKING
    assert account.available_balance == 1000.50
    assert account.notes == "Primary checking account"
    assert account.id is not None
    assert isinstance(account.id, str)

def test_account_model_defaults():
    account = Account(name="Default Account", currency="XYZ", accounting_category=AccountingCategory.ASSET)
    assert account.available_balance == 0.0
    assert account.hidden is False
    assert account.placeholder is False
    assert account.parent_account_id is None
    assert account.banking_product_type is None

def test_account_model_hidden_and_placeholder():
    account_hidden = Account(name="Hidden Account", currency="USD", accounting_category=AccountingCategory.ASSET, hidden=True)
    assert account_hidden.hidden is True
    assert account_hidden.placeholder is False

    account_placeholder = Account(name="Placeholder Account", currency="USD", accounting_category=AccountingCategory.ASSET, placeholder=True)
    assert account_placeholder.hidden is False
    assert account_placeholder.placeholder is True

    account_both = Account(name="Hidden Placeholder Account", currency="USD", accounting_category=AccountingCategory.ASSET, hidden=True, placeholder=True)
    assert account_both.hidden is True
    assert account_both.placeholder is True

def test_account_model_hierarchical():
    parent_account = Account(name="Assets", currency="USD", accounting_category=AccountingCategory.ASSET)
    child_account = Account(name="Cash On Hand", currency="USD", accounting_category=AccountingCategory.ASSET, parent_account_id=parent_account.id)
    assert child_account.parent_account_id == parent_account.id

def test_enums_are_strings():
    assert isinstance(AccountingCategory.ASSET, str)
    assert isinstance(BankingAccountType.CHECKING, str)
    assert AccountingCategory.ASSET.value == "Asset"
    assert BankingAccountType.CHECKING.value == "Checking"
