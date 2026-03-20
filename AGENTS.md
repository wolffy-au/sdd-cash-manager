# sdd-cash-manager Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-14

## Active Technologies

- Python 3.12 + FastAPI (existing API surface), SQLAlchemy (models), httpx (tests), pytest (runner), python-accounting helpers. (002-add-api-pytests)
- SQLite (development defaults; tests use in-memory or sqlite file nodes when necessary). (002-add-api-pytests)

- (002-add-api-pytests)

## Project Structure

```text
src/
  └── sdd_cash_manager/
      ├── api/
      │   └── accounts.py (RESTful endpoints for accounts and transactions)
      ├── services/
      │   ├── account_service.py (account business logic)
      │   └── transaction_service.py (transaction/balance logic)
      ├── models/
      │   ├── account.py (Account ORM entity)
      │   ├── transaction.py (Transaction ORM entity)
      │   └── enums.py (BankingProductType, TransactionType, etc.)
      ├── schemas/
      │   ├── account_schema.py (Pydantic DTOs for accounts)
      │   └── transaction_schema.py (Pydantic DTOs for transactions)
      ├── lib/
      │   ├── auth.py (JWT token verification)
      │   ├── security_events.py (security audit logging)
      │   ├── encryption.py (encryption utilities)
      │   └── logging_config.py (structured logging setup)
      ├── core/
      │   └── config.py (centralized environment config)
      └── database.py (SQLAlchemy session management)

tests/
  ├── unit/ (legacy unit tests)
  └── api/
      ├── conftest.py (pytest configuration & AsyncClient setup)
      ├── fixtures.py (seeded test accounts & balancing account)
      ├── jwt_utils.py (JWT token generation for tests)
      ├── helpers.py (assertion utilities & DB cleanup)
      ├── test_accounts.py (account creation, listing, filtering)
      ├── test_transactions.py (balance adjustments, hierarchy effects)
      ├── test_validation.py (error handling, auth enforcement)
      └── README.md (quickstart guide for contributors)
```

## Commands

- `pytest tests/api -v` - Run all API integration tests
- `pytest tests/api::test_accounts.py -v` - Run account-specific tests
- `pytest tests/api::test_transactions.py -v` - Run transaction-specific tests
- `pytest tests/api::test_validation.py -v` - Run validation/auth error tests
- `scripts/run_api_tests.sh` - Run API tests with CI-compatible output and logging
- `pytest tests/api --cov` - Run tests with coverage report

## Code Style

Python 3.12 (from .python-version): Follow standard conventions. See TECHNICAL.md for architecture guidance.

## Recent Changes

- 002-add-api-pytests: Added Python 3.12 + FastAPI (existing API surface), SQLAlchemy (models), httpx (tests), pytest (runner), python-accounting helpers.
- 002-add-api-pytests: Added httpx-based integration testing for API contracts, fixtures for seeded test data, JWT token helpers, and validation/auth error testing.

## API Test Suite (002-add-api-pytests)

### Location & Structure
- **Tests**: `tests/api/` - Integration tests exercising the full FastAPI app via httpx
- **Config**: `tests/api/conftest.py` - AsyncClient setup, environment-driven JWT settings
- **Fixtures**: `tests/api/fixtures.py` - Seeded accounts (visible, hidden, placeholder), balancing account with cleanup
- **Utilities**:
  - `jwt_utils.py` - Short-lived token generation matching app auth settings
  - `helpers.py` - HTTP status/payload assertions, database reset
- **Test Modules**:
  - `test_accounts.py` - Account creation, listing, search/filtering (2 tests)
  - `test_transactions.py` - Balance adjustments, hierarchy effects (2 tests)
  - `test_validation.py` - Validation errors (422), auth failures (401), header enforcement (3 tests)

### Running Tests

**Local Development:**

```bash
# All tests
pytest tests/api -v

# Specific test module
pytest tests/api/test_accounts.py -v
pytest tests/api/test_transactions.py -v
pytest tests/api/test_validation.py -v

# With coverage
pytest tests/api --cov=src --cov-report=html
```

**CI/CD Integration:**

```bash
scripts/run_api_tests.sh    # Runs full suite with logging & XML output
```

### Test Results

**Status**: ✅ All tests stable and passing
- 7 tests total covering P1/P2/P3 user stories
- ~2.15s execution time
- 67% overall code coverage
- 100% test pass rate (no flakiness)

**Coverage by Module:**
- Account models: 95%
- Transaction models: 72%
- API endpoints: 72%
- Schemas (DTOs): 100%
- Services: 49-61% (additional tests pending)

### Documentation
- `tests/api/README.md` - Quickstart & execution guide for contributors
- `docs/api-tests.md` - Detailed testing patterns and best practices (if exists)

### Dependencies & Prerequisites
- FastAPI running (typically on `http://127.0.0.1:8000`)
- Environment variables configured (see `tests/api/conftest.py`):
  - `SDD_CASH_MANAGER_SECURITY_ENABLED` (default: true)
  - `SDD_CASH_MANAGER_JWT_SECRET` (default: sdd-test-secret-32-bytes-long-tt)
  - `SDD_CASH_MANAGER_JWT_ALGORITHM` (default: HS256)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
