# Research Notes: API Pytest Coverage with httpx

## Decision: run tests with httpx AsyncClient and pytest
- **Rationale**: The feature explicitly targets pytest modules that interact with the API, and httpx supports both sync and async clients which align with the FastAPI stack and existing async endpoints. Using pytest ensures we can leverage fixtures, paramization, and coverage thresholds already expected by the project.
- **Alternatives considered**: (A) Use `requests` + `pytest` – simpler but lacks native async support for FastAPI endpoints; (B) Use `playwright` – overkill for backend-only API tests.

## Decision: execute suite with JWT/security enabled
- **Rationale**: Running the suite under production-like guards catches authentication regressions early and satisfies the security emphasis outlined in TECHNICAL.md and the spec. It also ensures we cover token issuance and validation paths that could otherwise drift silently.
- **Alternatives considered**: (A) Disable security via `SDD_CASH_MANAGER_SECURITY_ENABLED=false` – faster for iteration but risks drifting from deployed behavior; (B) Provide two modes – still mirrors prod but doubles maintenance without clear demand right now.

## Decision: base fixtures on local dev API and deterministic DB seeding
- **Rationale**: Seeded accounts, balancing accounts, and cleanup ensure each test can be rerun without persistence side-effects while keeping runtime predictable and isolated, which satisfies the spec requirement for deterministic fixtures.
- **Alternatives considered**: (A) Rely on mocks rather than hitting the API – would miss integration regressions; (B) Reset a production-like database via migrations – heavier than needed for this suite.
