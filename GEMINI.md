# sdd-cash-manager Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-22

## Active Technologies

- Python 3.11 + FastAPI, SQLAlchemy, Pydantic, python-accounting (for core financial logic) (001-account-management)
- SQLite (for MVP, extensible to PostgreSQL) (001-account-management)
- SQLite (for MVP) (001-account-management)

## Project Structure

```text
src/
    └── sdd_cash_manager/
        ├── core/
        ├── api/
        ├── database/
        ├── lib/
        ├── models/
        ├── schemas/
        └── services/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]
pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]
ruff check .

## Code Style

Python 3.11 (Inferred from .python-version): Follow standard conventions

## Recent Changes

- 001-account-management: Added Python 3.11 + FastAPI, SQLAlchemy, Pydantic, python-accounting
- 001-account-management: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

<!-- MANUAL ADDITIONS START -->
## Reference Documents

- `.specify/memory/constitution.md` – canonical constitution covering governance, code quality, testing, performance, and security principles.
- `TECHNICAL.md` – authoritative architecture and coding standard guidance.
- `NONFUNCTIONALS.md` – definitive non-functional requirements for performance, reliability, security, and compliance.
- `PROJECT_CONSTITUTION.md` – project-specific principles and expectations.
- `PROJECT_SPECIFICATION.md` – business and functional requirements that drive implementation work.

These files contain the authoritative guidance for architecture, coding standards, non-functional requirements, and project principles, so consult them instead of relying solely on GEMINI.
<!-- MANUAL ADDITIONS END -->
