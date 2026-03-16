from enum import Enum


class AccountingCategory(str, Enum):
    """
    Enum for different accounting categories.
    Used for classifying accounts for financial reporting.
    """
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    INCOME = "Income"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class BankingProductType(str, Enum):
    """
    Enum for different types of banking products or financial entities.
    These types influence balance calculations and transaction handling.
    """
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
    ADJUSTMENT_DEBIT = "Adjustment Debit" # Added for T022
    ADJUSTMENT_CREDIT = "Adjustment Credit" # Added for T022

class ProcessingStatus(str, Enum):
    """
    Enum for the processing status of financial operations.
    """
    PENDING = "Pending"
    POSTED = "Posted"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class ReconciliationStatus(str, Enum):
    """
    Enum for the reconciliation status of transactions.
    """
    PENDING_RECONCILIATION = "Pending Reconciliation"
    RECONCILED = "Reconciled"
    UNRECONCILED = "Unreconciled"
