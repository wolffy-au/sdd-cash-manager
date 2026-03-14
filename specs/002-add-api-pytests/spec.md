# Feature Specification: API Pytest Coverage with httpx

**Feature Branch**: `002-add-api-pytests`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "create a set of pytests to test the api using httpx"

## Clarifications

### Session 2026-03-14

- Q: Should the new pytest suite run with API security enabled or disable auth for easier iteration? → A: Run with JWT tokens (security enabled) so tests mirror production guards and detect auth-related regressions even if faster no-auth runs exist separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify core account flows (Priority: P1)

As a QA engineer maintaining confidence in the API surface, I need automated tests that exercise adding, retrieving, and listing accounts so that regressions in the service are caught before deployment.

**Why this priority**: Core account workflows underpin every customer interaction, so catching regressions early prevents downstream failures in billing, reconciliation, and reporting.

**Independent Test**: Run the new pytest module with httpx fixtures against a running dev server and confirm that the create/get/list endpoints return the documented payloads.

**Acceptance Scenarios**:

1. **Given** the API is running with seed data, **When** the test posts a valid account payload, **Then** the response returns `201 Created`, the body echoes the submitted name/currency, and the account is persisted so that a follow-up GET returns the same ID.
2. **Given** at least two accounts exist and one is filtered, **When** the test calls the GET `/accounts` endpoint with `search_term`, **Then** the response includes only matching accounts and respects `hidden`/`placeholder` flags.

---

### User Story 2 - Verify transactional summaries and hierarchies (Priority: P2)

As a developer updating hierarchy logic, I need regression tests targeting transaction posting and hierarchy balance calculations so I can validate that downstream read-model changes do not break aggregates.

**Why this priority**: Transaction endpoints drive financial integrity; failing to test balance adjustments increases the risk of silent drift in reports.

**Independent Test**: The pytest suite uses httpx to post a transaction adjustment, then fetches the hierarchy balance endpoint and asserts the totals move as expected, all without relying on UI flows.

**Acceptance Scenarios**:

1. **Given** two accounts with known balances, **When** the test posts a balance adjustment via POST `/accounts/{id}/adjustment`, **Then** the transaction status is `COMPLETED`, and the GET `/accounts/{id}/balance` reflects the new total for both accounts involved.

---

### User Story 3 - Detect invalid payload handling (Priority: P3)

As a support engineer, I need tests simulating malformed requests to ensure the API maintains consistent validation errors so that I can confidently explain failure modes to stakeholders.

**Why this priority**: While not business-critical, consistent validation prevents confusion when clients send bad data and ensures monitoring alerts activate on genuine issues.

**Independent Test**: Send intentionally invalid JSON bodies through httpx and verify the API replies with structured error responses and the proper status codes.

**Acceptance Scenarios**:

1. **Given** the API is running, **When** the test submits a payload with missing required fields to creation endpoints, **Then** the status is `422 Unprocessable Entity` and the response lists the missing properties.

---

### Edge Cases

- What happens when the dev server responds slowly or hangs during a pytest run? Tests should fail fast with a reasonable timeout and surface the timeout in the report.
- How does the suite handle intermittent failures when dependent endpoints (like transaction creation) are already occupied by another test? Use isolated fixtures and rollback behavior to keep each test independent.
- How does the suite detect and clean up nested placeholder accounts after creation so that repeated runs start from a known state?

## Requirements *(mandatory)*

- **FR-001**: The test suite MUST provide pytest modules that use httpx AsyncClient/Client to exercise every documented accounts and transaction endpoint described in the API reference.
- **FR-002**: Fixtures MUST initialize and tear down known baseline data (accounts, placeholders, balancing account) so tests can run in isolation and remain deterministic.
- **FR-003**: Tests MUST assert HTTP status codes plus key response attributes (IDs, balances, flags) to give engineers confidence the API honors its contract.
- **FR-004**: The suite MUST include negative tests that submit invalid payloads or unauthorized requests and assert that validation messages and status codes match current documentation.
- **FR-005**: Test metadata MUST document how to run the suite (environment variables, endpoint URL, auth toggles) so other contributors can execute the set without reading implementation code.
- **FR-006**: The suite MUST execute against the API with JWT/security enabled by default so auth enforcement is exercised and any token-related regressions surface immediately.

### Key Entities *(include if feature involves data)*

- **API Test Case**: Represents a single HTTP interaction (method, path, payload) executed via httpx and includes assertions for expected status, schema keys, and persistence side-effects.
- **Test Fixture**: Encapsulates the state setup (seed accounts, transactions, balancing behavior) and cleanup (rollback or deletion) required before running a user story in isolation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The pytest suite can be executed from `./tests/api` in under five minutes and completes without failures against the local dev API on every commit.
- **SC-002**: Each core user scenario (account creation, hierarchy balance, validation errors) has at least one passing pytest that explicitly covers the described acceptance criteria.
- **SC-003**: Running the suite surfaces concrete feedback (pass/fail per test plus captured response payload) so QA and developers can interpret failures without rerunning manually.
- **SC-004**: Documentation for the suite explains required environment variables (base URL, credentials, feature flags) and is reviewed alongside the tests so new contributors can reproduce the results.

## Assumptions

- Tests will run against the local development API (e.g., `http://127.0.0.1:8000`) with the default sqlite configuration unless otherwise overridden by documented environment variables.
- httpx and pytest are already available in the development environment, so the spec focuses on writing tests rather than installing dependencies.
- The API endpoints queried are authenticated using the project’s existing JWT mechanism, but the suite can disable security (setting `SDD_CASH_MANAGER_SECURITY_ENABLED=false`) for faster iteration.
