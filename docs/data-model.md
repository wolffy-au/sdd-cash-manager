# Data Models

This document consolidates the data model specifications from various feature documents. It provides an overview of key entities, their attributes, relationships, and validation rules, visualized with embedded PlantUML diagrams.

## Account Management Data Model

Details from `specs/001-account-management/data-model.md`.

### Core Entities

```plantuml
@startuml
skinparam classAttributeIconSize 0

class Account {
  +id: UUID
  +name: String
  +currency: String (ISO 4217)
  +accounting_category: AccountingCategory
  +banking_product_type: BankingProductType
  +account_number: Optional String
  +available_balance: Decimal
  +credit_limit: Optional Decimal
  +notes: Optional String
  +parent_account_id: Optional UUID
  +hidden: Boolean
  +placeholder: Boolean
  +created_at: DateTime
  +updated_at: DateTime
}

class Transaction {
  +id: UUID
  +transaction_date: DateTime
  +description: String
  +created_at: DateTime
  +updated_at: DateTime
}

class Entry {
  +id: UUID
  +transaction_id: UUID
  +account_id: UUID
  +debit_amount: Decimal
  +credit_amount: Decimal
  +running_balance_after: Decimal
  +running_balance_before: Decimal
  +reconciled_balance_after: Decimal
  +reconciled_balance_before: Decimal
}

Account "1" -- "*" Account : parent_account (hierarchical)
Account "1" -- "*" Entry : holds
Transaction "1" -- "*" Entry : generates
@enduml
```
- **Entities**: `Account`, `Transaction`, `Entry`.
- **Account**: Represents a financial account with hierarchical structure, various attributes, and state flags (`hidden`, `placeholder`).
- **Transaction**: A financial event affecting multiple accounts.
- **Entry**: A single debit or credit line item within a `Transaction`, linked to an `Account`.
- **Validation**: String lengths, character restrictions, numeric constraints, enum types, UUID formats, existence checks, ISO 4217 currencies, and double-entry integrity.

## API Testing Artifacts Data Model

Details from `specs/002-add-api-pytests/data-model.md`. These models describe testing-related entities.

### Testing Constructs

```plantuml
@startuml
skinparam classAttributeIconSize 0

class ApiTestCase {
  +method: str
  +path: str
  +payload: JSON
  +headers: Dict
  +assertions: AssertionBundle
}

class TestFixture {
  +seed_accounts: List[Account]
  +balancing_account: Account
  +transactions: List[Transaction]
  +cleanup_strategy: str
}

class AssertionBundle {
  +status_code: int
  +schema_keys: List[str]
  +business_rules: List[str]
}

' Placeholder for core entities, assuming they exist from other specs
class Account {
  ' ...
}
class Transaction {
  ' ...
}

ApiTestCase "N" -- "1" AssertionBundle : expects
TestFixture "1" -- "N" ApiTestCase : sets up
TestFixture "1" -- "*" Account : seeds
TestFixture "1" -- "*" Transaction : includes
@enduml
```
- **Entities**: `API Test Case`, `Test Fixture`, `Assertion Bundle`.
- **API Test Case**: Represents an HTTP interaction with the API.
- **Test Fixture**: Sets up the necessary environment state (accounts, transactions) for tests.
- **Assertion Bundle**: Defines expected outcomes and business rules for API responses.
- **Validation**: Deterministic test data, isolated fixtures, and comprehensive assertion checks.

## Balance Adjustment Data Model

Details from `specs/003-adjust-balance/data-model.md`.

### Adjustment Entities

```plantuml
@startuml
skinparam classAttributeIconSize 0

class ManualBalanceAdjustment {
  +account_id: UUID
  +target_balance: Decimal
  +effective_date: Date
  +submitted_by_user_id: UUID
  +adjustment_attempt_timestamp: DateTime
  +created_transaction_id: Optional UUID
  +status: str (PENDING, COMPLETED, ZERO_DIFFERENCE)
}

class AdjustmentTransaction {
  +transaction_id: UUID
  +account_id: UUID
  +effective_date: Date
  +amount: Decimal
  +transaction_type: str (ADJUSTMENT_DEBIT, ADJUSTMENT_CREDIT)
  +description: String
  +reconciliation_metadata: JSON
  +created_at: DateTime
}

class ReconciliationViewEntry {
  +entry_id: UUID
  +account_id: UUID
  +entry_date: Date
  +amount: Decimal
  +description: String
  +is_adjustment: Boolean
  +reconciled_status: str
  +original_transaction_id: Optional UUID
}

class Account {
  ' ...
}
class User {
  ' ...
}

ManualBalanceAdjustment "1" -- "1" Account : for_account
ManualBalanceAdjustment "1" -- "1" User : submitted_by
ManualBalanceAdjustment "1" -- "0..1" AdjustmentTransaction : creates
AdjustmentTransaction "1" -- "1" Account : applies_to
ReconciliationViewEntry ..> AdjustmentTransaction : represents (optional)
@enduml
```
- **Entities**: `ManualBalanceAdjustment`, `AdjustmentTransaction`, `ReconciliationViewEntry`.
- **ManualBalanceAdjustment**: Represents a user-initiated request to manually adjust an account's balance.
- **AdjustmentTransaction**: An automatically generated ledger entry for the balance adjustment.
- **ReconciliationViewEntry**: A projection for reconciliation display, potentially including adjustment data.
- **Validation**: Target balance non-negative, date considerations, user reference, amount calculation, transaction type consistency.

## Transaction Management Data Model

Details from `specs/004-transaction-management/data-model.md`.

### Feature-Specific Entities

```plantuml
@startuml
skinparam classAttributeIconSize 0

class Transaction {
  ' Assumed to be the core financial transaction entity
  ' Fields from Account Management spec apply
  +id: UUID
  ' ... other core fields
}

class QuickFillTemplate {
  +id: UUID
  +action: str
  +currency: str
  +transfer_from_account_id: UUID
  +transfer_to_account_id: UUID
  +amount: Decimal
  +memo: str
  +confidence_score: float
  +history_count: int
  +last_used_at: datetime
  +source_transaction_id: UUID
}

class DuplicateCandidate {
  +candidate_id: UUID
  +account_id: UUID
  +matching_transaction_ids: List[UUID]
  +amount: Decimal
  +date: date
  +description: str
  +confidence: float
  +scope: str (account or account_group)
}

class AccountMergePlan {
  +plan_id: UUID
  +source_account_id: UUID
  +target_account_id: UUID
  +reparenting_map: Dict[UUID, UUID]
  +affected_entries_count: int
  +audit_notes: str
  +initiated_by: str
  +status: str (pending, validated, executed, rejected)
}

class Account {
  ' ...
}

QuickFillTemplate ..> Transaction : derived from historical
DuplicateCandidate "1" -- "*" Transaction : flags
AccountMergePlan "1" -- "1" Account : source
AccountMergePlan "1" -- "1" Account : target
AccountMergePlan "1" -- "*" Account : reparents child accounts
@enduml
```
- **Entities**: `Transaction` (referencing core entity), `QuickFillTemplate`, `DuplicateCandidate`, `AccountMergePlan`.
- **QuickFillTemplate**: Generated from historical transactions for pre-populating forms.
- **DuplicateCandidate**: Flags potential duplicate transactions for review.
- **AccountMergePlan**: Details account merging, hierarchy reassignment, and audit logging.

## Data Model Assumptions & Relationships Summary

This section consolidates common assumptions and relationship summaries across the models.

- **Core Entities**: `Account`, `Transaction`, `Entry`, `User` are foundational and their detailed models are primarily defined in the 'Account Management Data Model' section.
- **Relationships**:
    - **Account Hierarchy**: `Account` can have a `parent_account_id` linking to another `Account`.
    - **Transaction-Entry**: A `Transaction` generates multiple `Entry` objects.
    - **Entry-Account**: Each `Entry` applies to a specific `Account`.
    - **Adjustment Flow**: `ManualBalanceAdjustment` may create an `AdjustmentTransaction`, which applies to an `Account`. `ReconciliationViewEntry` can represent adjustment data.
    - **Testing Context**: `TestFixture` sets up `Account` and `Transaction` data for `ApiTestCase` executions, which use `AssertionBundle`s.
    - **Transaction Management**: `QuickFillTemplate` is derived from historical `Transaction`s, `DuplicateCandidate` flags `Transaction`s, and `AccountMergePlan` involves `Account`s and child `Account`s.

- **General Validation**: Emphasis on data integrity, correct types, value constraints (e.g., non-negative balances, ISO currency codes), and referential integrity (UUIDs).
- **Double-Entry Principle**: Transactions must maintain a balanced debit and credit sum across all associated entries.
- **Date and Time**: Use of `DateTime` and `Date` types with awareness of timezone implications.
