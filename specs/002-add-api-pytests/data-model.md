# Data Model: API Pytest Coverage with httpx

## Entities

- **API Test Case**
  - **Description**: Represents a single HTTP interaction executed through `httpx` against the SDD Cash Manager API.
  - **Fields**:
    - `method`: HTTP verb (e.g., POST, GET).
    - `path`: Endpoint under test (e.g., `/accounts`, `/accounts/{id}/adjustment`).
    - `payload`: JSON body supplied for mutation requests; optional for reads.
    - `headers`: Includes authorization (Bearer JWT) and other metadata for each request.
    - `assertions`: Expected status code, key response properties, and persistence side-effects.
  - **Relationships**:
    - Linked to `Test Fixture` to reuse setup and teardown.

- **Test Fixture**
  - **Description**: Encapsulates the environment state required before a `User Story` runs.
  - **Fields**:
    - `seed_accounts`: Collection of account records (visible, hidden, placeholder) created prior to tests.
    - `balancing_account`: Dedicated entity with `BALANCING_ACCOUNT_ID` to absorb double-entry adjustments.
    - `transactions`: Optional prior transactions used to verify hierarchy behavior.
    - `cleanup_strategy`: Rollback or deletion plan executed after the test to keep the database clean.
  - **Relationships**:
    - Supplies state for multiple `API Test Case` instances.

- **Assertion Bundle**
  - **Description**: Structured expectations verified after an HTTP interaction.
  - **Fields**:
    - `status_code`: Numeric response expectation (200, 201, 422, etc.).
    - `schema_keys`: Keys that must appear in the JSON (e.g., `id`, `available_balance`).
    - `business_rules`: Domain invariants such as balances updating symmetrically, hidden flags filtering, etc.

## Validation Rules

- Each `API Test Case` must execute against a running local API instance using `SDD_CASH_MANAGER_SECURITY_ENABLED=true` and include a valid JWT in the `Authorization` header.
- Fixtures must ensure fixture data is deterministic and isolated (create placeholders/accounts with known IDs, use dedicated balancing account) before tests execute and ensure cleanup after completion.
- Assertions have to verify both HTTP status and critical domain fields (IDs, balances, search flags), so regressions are discernible without manual inspection.

