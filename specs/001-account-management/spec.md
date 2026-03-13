## Functional Requirement to Task Mapping

| Requirement Key | Has Task? | Task IDs                                                              | Notes                                                                                                |
| :-------------- | :-------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| FR-001          | Yes       | T010, T011, T013, T014, T015, T016, T017, T018, T019                    | Core account creation/management. The primary identifier for each account **MUST be a UUID** (as per Constitution). `account_number` is an optional, secondary identifier for external reference, with a maximum length of 50 characters, allowing alphanumeric and hyphens. Covered by Acceptance Scenarios 1-4 under FR-001; relevant Edge Cases in Account Management apply.                                                                    |
| FR-002          | Yes       | T012, T017 | Account types and enums defined. The standard banking account types include Checking, Savings, Credit Card, and Loan. The comprehensive list of types is defined by the `AccountingCategory` and `BankingProductType` enums, covered by T012 and T017. Covered by Acceptance Scenarios 1-2 under FR-002; relevant Edge Cases in Balance Calculations and Account Management apply. |
| FR-003          | Yes       | T011, T013, T025, T029, T034                                          | Running and reconciled balances. Covered by Acceptance Scenarios 1-4 under FR-003 & FR-004; relevant Edge Cases in Balance Calculations and Data Integrity apply.                                                                     |
| FR-004          | Yes       | T011, T025, T029                                                | Historical running balances. Clarify data fields in Transaction model: e.g., transaction\_running\_balance (after), historical\_running\_balance (prior). Differentiate from Account's available balance. **Calculation: `transaction_running_balance = previous_running_balance + transaction_amount; historical_running_balance = previous_running_balance; available_balance = running_balance - pending_transactions + credit_limit`.** Covered by Acceptance Scenarios 1-4 under FR-003 & FR-004; relevant Edge Cases in Balance Calculations and Data Integrity apply. |
| FR-005          | Yes       | T011                                                                  | Account notes. Covered by Acceptance Scenario 3 under FR-001; relevant Edge Cases in Account Management apply.                                                                                       |
| FR-006          | Yes       | T024, T025, T026, T027, T028, T029                                    | Hierarchical accounts (Task T026 defines recursive aggregation via child running balances). Covered by Acceptance Scenarios 1-2 under FR-006 & FR-007; relevant Edge Cases in Hierarchical Accounts apply. |
| FR-007          | Yes       | T024, T025, T026, T027, T028, T029                                    | Parent account group balances computed on-demand by recursively summing child running balances (see T026). Performance targets: <100ms for up to 5 levels. Covered by Acceptance Scenarios 1-2 under FR-006 & FR-007; relevant Edge Cases in Hierarchical Accounts apply. |
| FR-008          | Yes       | T012, T014                                                            | Account search by name. **Search Logic**: Case-insensitive partial match. Covered by Acceptance Scenario 4 under FR-001; relevant Edge Cases in Account Management apply.                                                                              |
| FR-009          | Yes       | T030                                                                  | Application state management for unsaved changes (see Task T030 for the unsaved-change lifecycle). Covered by Acceptance Scenarios 1-4 under FR-009; relevant Edge Cases in Data Integrity apply. |
| FR-010          | Yes       | T023                                                                  | Manual balance adjustment interface. This involves a user-facing window to set new balances, trigger transactions, and update account states. The interface is accessible within a maximum of 3 clicks from the account details view. Real-time validation feedback (e.g., error messages) is provided instantly for "Adjustment Amount" and "Reason". Confirmation of the adjustment (e.g., transaction creation, balance update) is displayed within 1 second of submission. The interface correctly handles positive, negative, and zero adjustment amounts. Covered by Acceptance Scenarios 1-4 under FR-010; relevant Edge Cases in Manual Balance Adjustments apply. |
| FR-011          | Yes       | T022, T023                                                                  | Upon manual balance adjustment, the system MUST automatically create a corresponding transaction. Covered by Acceptance Scenario 1 under US3; relevant Edge Cases in Data Integrity and Manual Balance Adjustments apply. |
| FR-012          | Yes       | T022, T023                                                                  | The amount of the automatic adjustment transaction MUST match the manually adjusted amount. Covered by Acceptance Scenario 1 under US3; relevant Edge Cases in Data Integrity and Manual Balance Adjustments apply. |
| FR-013          | Yes       | T022, T023                                                                  | Balance adjustment transactions MUST update the account's ledger and reconciliation views. Covered by Acceptance Scenario 1 under US3; relevant Edge Cases in Data Integrity apply. |

## User Story to Task Mapping

| User Story Key | Task IDs                                                              | Notes                                                                                                |
| :------------- | :-------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| US1            | T008, T009, T010, T011, T012, T013, T014, T015, T016, T017 | As a user, I want to create and manage multiple financial accounts, as defined by FR-001. Relevant Edge Cases in Account Management and Data Integrity apply. |
| US2            | T027, T028, T029, T030, T031, T032 | As a user, I want to organize my accounts into a hierarchy. Covered by FR-006, FR-007; relevant Edge Cases in Hierarchical Accounts apply. Covered by FR-006, FR-007; relevant Edge Cases in Hierarchical Accounts apply. Covered by FR-006, FR-007. |
| US3            | T018, T019, T020, T021, T022, T023, T024, T025, T026 | As a user, I want to manually adjust an account's balance. Covered by FR-010, FR-011, FR-012, FR-013; relevant Edge Cases in Manual Balance Adjustments and Data Integrity apply. Covered by FR-010, FR-011, FR-012, FR-013; relevant Edge Cases in Manual Balance Adjustments and Data Integrity apply. Covered by FR-010, FR-011, FR-012, FR-013. |

## Non-Functional Requirements

- **Performance:** API endpoint response times must be under 200ms, aiming for <100ms for typical operations (e.g., account creation, retrieval by ID, simple balance queries). Individual transaction processing (creation, update) must complete within 50ms (p95). The system must support at least 1000 transactions per minute (approx. 16.7 TPS) under normal load. All financial calculations must be performed within a 0.001% tolerance of the true value, with absolute error not exceeding 0.01 units of the smallest currency denomination.
- **Scalability:** Account retrieval for hierarchies up to 5 levels deep must complete within 200ms. The system should be designed to scale horizontally to support increasing transaction volumes and user loads, specifically meeting the throughput and concurrency targets defined in tasks T055 (RPS) and T056 (concurrent transaction capacity).
- **Accuracy & Reliability:** High degree of accuracy and data integrity maintained through atomic transactions. Target uptime is 99.9% (approx. 8.76 hours downtime per year), measured by API endpoint availability and success rate, with a Recovery Time Objective (RTO) of less than 4 hours and a Recovery Point Objective (RPO) of 1 hour.
- **Security:** Implement standard JWT-based authentication using RS256 signing algorithm, adhering to OAuth 2.0 standards. Utilize Role-Based Access Control (RBAC) for authorization. Encrypt sensitive data at rest using AES-256 and ensure data in transit is protected via TLS 1.3.

## Terminology Definitions

- **Running Balance:** The current balance reflecting all entered transactions.
- **Reconciled Balance:** The balance reflecting only transactions that have been cleared or formally reconciled against external statements. The system must provide a mechanism for explicitly setting or updating the reconciled balance for an account, and this action must be logged for auditing.
- **Available Balance:** The readily available balance, which may differ from the running balance due to holds or pending transactions.
- **Account Group:** An Account used to aggregate the balances of its child accounts, creating a hierarchical view.

## Clarifications

### 2026-03-07

- Q: What are the required "Account types" and their associated "enums" to be implemented for FR-001 and FR-002? → A: Standard Banking Types
- Q: What are the precise calculation formulas for transaction_running_balance (after), historical_running_balance (before), and available_balance? → A: transaction_running_balance = previous_running_balance + transaction_amount; historical_running_balance = previous_running_balance; available_balance = running_balance - pending_transactions + credit_limit
- Q: What are the required input fields and their validation rules for the manual balance adjustment interface? → A: Fields: "Adjustment Amount" (numeric, required, +/-), "Reason" (text, optional, <=255 chars). Validation: Amount must be a valid number. Reason length check.
- Q: Do the performance targets (1000 TPS, <100ms API response) apply to all API endpoints, including database operations? → A: Yes
- Q: Are there any external services, APIs, or data sources that this feature will integrate with, and if so, what are their failure modes? → A: Not for MVP, maybe later
- Q: Which JWT signing algorithm and authorization scheme should be used? → A: RS256 JWT with RBAC
- Q: What specific encryption standards should be used for data at rest and in transit? → A: AES-256 (rest), TLS 1.3 (transit)
- Q: How should transaction running balances, historical running balances, and account available balances be differentiated and calculated? → A: Transaction running balance is the account balance *after* the transaction, historical is *before*; available balance is based on cleared transactions + credit limit.
- Q: Regarding double-entry accounting, should the system enforce double-entry for all new transactions from the outset, or should single-entry be permitted as per the current note? → A: Enforce double-entry for all new transactions immediately.
- Q: How do 'Banking Product Types' and 'Accounting Category Types' interact, specifically in balance calculation and system behavior? → A: Banking Product Type is primary; Accounting Category Type defines its role (e.g., CREDIT_CARD is always a Liability.

### 2026-03-11

- Q: How should user roles be differentiated for account management operations (e.g., view, edit, create)? → A: Role-agnostic

## Introduction

This specification details the requirements for the Account Management feature of the sdd-cash-manager system. It outlines the functionalities for creating, managing, and reporting on financial accounts, including hierarchical structures and balance adjustments.

## Scope

This specification covers the core functionalities related to financial account management as detailed in the Functional Requirements (FR) and User Stories (US). It defines the expected behavior, non-functional attributes, and success criteria for these features.

## Assumptions

- The underlying database system (initially SQLite) can support the described operations and data integrity requirements.
- Standard financial conventions for account types, transactions, and balances are followed.
- User roles and permissions for accessing account management features will be defined and managed separately within the authorization system.

## Constraints

- Performance targets for API responses, transaction processing, and hierarchical balance calculations must be met.
- Accuracy tolerance of 0.001% for financial calculations and an absolute error not exceeding 0.01 units of the smallest currency denomination must be adhered to.
- Uptime and recovery objectives (RTO/RPO) must be met for reliability.
- Security standards (JWT, TLS, AES) must be implemented for data protection.

## Out of Scope

- User interface design specifics beyond functional interaction requirements.
- Detailed error handling strategies beyond those specified in Edge Cases and Acceptance Scenarios.
- Integration with external financial institutions or third-party accounting software (as indicated by previous clarifications).
- Detailed implementation of user authentication and authorization mechanisms (though standards are specified in NFRs).

## Acceptance Scenarios

### FR-001: Core Account Creation and Management

- **Scenario 1:** A user can successfully create a new account with a unique name, type (from standard banking types), and initial balance.
- **Scenario 2:** The system correctly displays all created accounts in a list view.
- **Scenario 3:** A user can add or modify a textual note associated with an existing account.
- **Scenario 4:** Account search by name returns case-insensitive partial matches accurately.

### FR-002: Account Types and Enums

- **Scenario 1:** The system correctly supports and uses standard banking account types (Checking, Savings, Credit Card, Loan) and their corresponding enums.
- **Scenario 2:** When creating an account, the user can select from the predefined standard banking account types.

### FR-003 & FR-004: Running, Reconciled, and Historical Balances

- **Scenario 1:** The running balance updates accurately after each new transaction is recorded.
- **Scenario 2:** The historical running balance correctly reflects the balance of the account *before* a specific transaction.
- **Scenario 3:** The available balance calculation (`running_balance - pending_transactions + credit_limit`) is performed accurately.
- **Scenario 4:** A user can explicitly set or update the reconciled balance for an account, and this action is logged for auditing.

### FR-006 & FR-007: Hierarchical Accounts

- **Scenario 1:** Users can successfully create sub-accounts nested under a parent account.
- **Scenario 2:** Parent account groups accurately compute aggregated balances by recursively summing child running balances, meeting the <100ms performance target for hierarchies up to 5 levels deep.

### FR-009: Application state management for unsaved changes

- **Scenario 1:** When a user makes changes to account data (e.g., modifies an account, creates a new one) without saving, the system indicates that there are unsaved changes (e.g., a "Save" button becomes active, a visual cue appears).
- **Scenario 2:** If the user attempts to navigate away from the page or close the application without saving, a prompt warns them about unsaved changes, offering options to save, discard, or cancel navigation.
- **Scenario 3:** If the user saves the changes, the system confirms the save, and the unsaved changes indicator is reset.
- **Scenario 4:** If the user discards changes, the system proceeds with navigation, and the changes are lost.

### FR-010: Manual Balance Adjustment Interface

- **Scenario 1:** The manual balance adjustment interface is accessible within a maximum of 3 clicks from the account details view.
- **Scenario 2:** Real-time validation feedback (e.g., error messages) is provided instantly upon input changes for "Adjustment Amount" and "Reason".
- **Scenario 3:** The interface correctly handles positive, negative, and zero adjustment amounts.
- **Scenario 4:** Confirmation of the balance adjustment (transaction creation, balance update) is displayed within 1 second of submission.
- **Contract:** The double-entry payload expected by POST `/accounts/{account_id}/adjust_balance` is defined in `contracts/public_api.md`; implementations must align with that schema.

### US1: Account Creation and Management

- **Scenario 1:** A user can successfully create and manage multiple financial accounts of standard banking types.

### US2: Hierarchical Account Structure

- **Scenario 1:** A user can organize accounts into a hierarchy, and parent accounts accurately sum the running balances of their children.

### US3: Balance Adjustment

- **Scenario 1:** A user can manually adjust an account's balance via the interface, triggering automatic transaction creation and ledger updates, with all specified performance and validation criteria met.

## Edge Cases

- **Account Management:**
  - Extremely long account names or notes that might exceed display limits or database constraints.
  - Race conditions if multiple users attempt to create or modify the same account data concurrently. **Resolution**: Mitigated through robust concurrency control mechanisms, including pessimistic locking for critical sections, as detailed in the "Concurrency Control" section.
- **Balance Calculations:**
  - Arithmetic overflow/underflow with extremely large or small balance amounts.
  - Precision issues with financial calculations involving many decimal places.
  - Handling of zero-amount adjustments that should not create a transaction.
  - What happens if `credit_limit` is null/negative or `pending_transactions` is malformed in available balance calculation?
  - **Required Response:** Null or negative `credit_limit` defaults to 0 (with a warning log), and malformed `pending_transactions` payloads must be rejected with validation errors before impacting balance calculations.
- **Hierarchical Accounts:**
  - Creation of excessively deep account hierarchies beyond the specified 5 levels. **Resolution**: The system will prevent creation of hierarchies exceeding 5 levels to maintain performance guarantees and data integrity.
  - Circular references between parent and child accounts.
  - Concurrent modification or deletion of accounts within a hierarchy during balance calculation.
- **Manual Balance Adjustments:**
  - Inputting non-numeric values for "Adjustment Amount".
  - Reason string exceeding the 255-character limit.
  - Adjustment causing arithmetic overflow/underflow.
  - Attempting adjustments on accounts in an immutable or deleted state.
- **Data Integrity:**
  - System failures during critical operations (e.g., balance updates, transaction recording).

## Input Validation and Injection Resistance

This section details the comprehensive validation rules applied to all input points to ensure data integrity and prevent injection attacks.

**General Protections**:

- All API inputs are validated using Pydantic schemas, FastAPI's type coercion, and custom validators to enforce data integrity.
- **Validation and sanitization must be consistently applied and enforced across all layers (API, service, and data access) to prevent bypasses and ensure robustness against injection attacks.**
    - **Sanitization for Vulnerabilities**: Implement sanitization mechanisms to mitigate risks from HTML tags (preventing XSS), specific control characters, and command injection patterns. Potentially harmful characters will be removed or replaced to ensure user-supplied data is safe for processing and rendering. This applies to all user-facing input fields and API payloads.
- SQLAlchemy ORM parameter binding is used for all database operations, preventing SQL injection.
- Logging scrubs control characters.

**Specific Input Points and Validation Rules**:

1. **`POST /accounts/` (Account Creation)**
   - **Input Method**: JSON Payload (`AccountCreatePayload`)
   - **Fields and Rules**:
       - **`name`**: String (max_length=100, min_length=1, strip_whitespace=True). Forbids control characters and characters `<>;`. Allows alphanumeric, spaces, `.`, `,`, `-`, `_`, `(`, `)`, `&`, `'`.
       - **`currency`**: String (exactly 3 uppercase letters, ISO 4217). Must be in `ALLOWED_CURRENCIES` set.
       - **`accounting_category`**: Enum value from `AccountingCategory`.
       - **`banking_product_type`**: Enum value from `BankingProductType`.
       - **`account_number`**: Optional string (max_length=50, strip_whitespace=True). **This is a secondary identifier for external reference and is NOT the primary account ID.** Allows alphanumeric and hyphens. Its uniqueness is not enforced by the system, but it may be subject to specific business rules or formats.
       - **`available_balance`**: Decimal (max_digits=18, decimal_places=2, ge=0). Quantized to 0.01.
       - **`credit_limit`**: Optional Decimal (same constraints as `available_balance`). Quantized to 0.01.
       - **`notes`**: Optional string (max_length=500, strip_whitespace=True). Forbids control characters and characters `<>;`.
       - **`parent_account_id`**: Optional UUID. Validated to refer to an existing account.
       - **`hidden`**: Boolean.
       - **`placeholder`**: Boolean.

2. **`GET /accounts/` (Account Listing/Search)**
   - **Input Method**: Query Parameters
   - **Parameters and Rules**:
       - **`search_term`**: Optional string. Trimmed, max_length=100. Rejects control characters.
       - **`hidden`**: Optional boolean.
       - **`placeholder`**: Optional boolean.

3. **`GET /accounts/{account_id}` (Get Specific Account)**
   - **Input Method**: Path Parameter
   - **Parameter and Rules**:
       - **`account_id`**: Must be a valid UUID format.

4. **`PUT /accounts/{account_id}` (Update Account)**
   - **Input Method**: Path Parameter (`account_id`) and JSON Payload (`AccountUpdatePayload`)
   - **Parameters and Rules**:
       - **`account_id`**: Must be a valid UUID format.
       - **Payload fields**: Optional fields are validated if provided, using rules similar to `AccountCreatePayload` (e.g., `name`, `currency`, `notes`, `available_balance`, `credit_limit`, `parent_account_id`). Amounts are quantized. `parent_account_id` validated to exist.

5. **`DELETE /accounts/{account_id}` (Delete Account)**
   - **Input Method**: Path Parameter
   - **Parameter and Rules**:
       - **`account_id`**: Must be a valid UUID format.

6. **`POST /accounts/{account_id}/adjust_balance` (Balance Adjustment)**
   - **Input Method**: Path Parameter (`account_id`) and JSON Payload (`BalanceAdjustmentPayload`)
   - **Parameters and Rules**:
       - **`account_id`**: Must be a valid UUID format.
       - **`target_balance`**: Decimal (max_digits=18, decimal_places=2, ge=0). Quantized to 0.01.
       - **`adjustment_date`**: Valid date format.
       - **`description`**: String (min_length=1, max_length=255). Forbids control characters and characters `<>;`.
       - **`action_type`**: Enum value from `ActionType`.
       - **`notes`**: Optional string (max_length=500). Forbids control characters and characters `<>;`.

## Threat Model

A formal threat model for the Account Management feature has been documented in [specs/001-account-management/threat_model.md](specs/001-account-management/threat_model.md). This model identifies potential threats, vulnerabilities, and attack vectors specific to the system's architecture, data flows, and asset types. All security requirements defined in this specification, and any subsequent derived security controls, **MUST** be explicitly mapped back to specific threats identified in this threat model. This ensures comprehensive coverage and justification for security measures. The threat model **MUST** be regularly reviewed and updated.

## Security Incident Response

Requirements for handling security failures, data breaches, and other security incidents **MUST** be clearly defined, as implemented in task T045. This includes:

- **Detection**: Mechanisms and tools for prompt detection of security incidents.
- **Containment**: Procedures to limit the scope and impact of an incident.
- **Eradication**: Steps to remove the cause of the incident.
- **Recovery**: Processes to restore affected systems and data to normal operation, including post-incident validation.
- **Backup and Recovery (Desktop Application)**:
  - **Frequency**: Data backups will be performed daily.
  - **Recovery Point Objective (RPO)**: An RPO of 5 minutes is targeted, ensuring minimal data loss.
  - **Applicability**: Due to the desktop application nature, specific RTO targets and offsite backup storage requirements are not applicable. Local backups will be managed by the application's data persistence strategy.

- **Breach Notification**: Procedures and timelines for notifying affected parties and regulatory bodies in case of a data breach, adhering to all applicable legal and regulatory requirements.

Measurable outcomes for these procedures will be defined as part of task T045's implementation.

## Concurrency Control

The system **MUST** implement robust concurrency control mechanisms to prevent race conditions and ensure data integrity, especially during simultaneous updates to account balances or hierarchical structures. This includes:

- **Atomicity**: All operations modifying financial data **MUST** be atomic.
- **Isolation**: Concurrent transactions **MUST** execute in isolation, preventing interim states from being visible to other transactions.
- **Durability**: Committed transactions **MUST** persist even in the event of system failures.
- **Locking Strategies**: Explicit locking mechanisms (e.g., pessimistic locking via `SELECT ... FOR UPDATE` at the database level, or optimistic locking with versioning) **MUST** be employed for critical sections involving read-modify-write operations on account balances.
- **Deadlock Prevention/Detection**: Strategies for preventing or detecting and resolving deadlocks **MUST** be implemented.

## Feature Success Criteria

The successful implementation of the Account Management feature will be measured by the following key outcomes:

- **Functional Correctness:** All defined FRs and USs are implemented, and all defined acceptance scenarios pass.
- **Performance:**
  - API response times consistently below 100ms for typical operations.
  - System supports at least 1000 transactions per minute (approx. 16.7 TPS).
  - Hierarchical balance computations complete under 100ms for up to 5 levels.
- **Accuracy:** Financial calculations adhere to a 0.001% tolerance with an absolute error not exceeding 0.01 units of the smallest currency denomination.
- **Reliability:**
  - Target uptime of 99.9% is achieved.
  - Recovery Time Objective (RTO) of less than 4 hours is met.
  - Recovery Point Objective (RPO) of 1 hour is met.

- **Security:**
  - Authentication uses RS256 JWT with OAuth 2.0 adherence.
  - Authorization is managed via Role-Based Access Control (RBAC).
  - Data in transit is protected by TLS 1.3, and data at rest by AES-256.
  - **Security requirements must align with established industry best practices (e.g., OWASP Top 10) and be defined with measurable acceptance criteria (e.g., passing specific security scans, penetration testing results, or compliance audit outcomes).**

## Next Steps

- Continue with other pending tasks from the checklist.
- Proceed to `/speckit.plan` once all checklist items are addressed.
