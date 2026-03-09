from enum import Enum


class AccountingCategory(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class BankingProductType(str, Enum):
    CHECKING = "Checking"
    BANK = "Bank"
    SAVINGS = "Savings"
    CREDIT_CARD = "Credit Card"
    LOAN = "Loan"
    PORTFOLIO = "Portfolio"
    MUTUAL_FUND = "Mutual Fund"
    GENERAL_ASSET = "General Asset"
    GENERAL_LIABILITY = "General Liability"
    OWNERS_EQUITY = "Owner's Equity"
    SALARY = "Salary"
    WAGES = "Wages"
    INVESTMENT_INCOME = "Investment Income"
    SALES_REVENUE = "Sales Revenue"
    RENT = "Rent"
    UTILITIES = "Utilities"
    GROCERIES = "Groceries"
    SALARIES_PAID = "Salaries Paid"
    # Add other types as needed

class ProcessingStatus(str, Enum):
    PENDING = "Pending"
    POSTED = "Posted"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class ReconciliationStatus(str, Enum):
    PENDING_RECONCILIATION = "Pending Reconciliation"
    RECONCILED = "Reconciled"
    UNRECONCILED = "Unreconciled"
