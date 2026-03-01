# Technical Specifications and Guidelines

This document consolidates technical specifications, patterns, utilities, and preferred libraries. It provides specific guidance that complements the high-level principles outlined in the *SpecKit Constitution* (`.specify\memory\constitution.md`).

## Code Style

* **Indentation**: 4 spaces; no tabs.
* **Line Length**: Maximum 120 characters; break after operators; use backslash for line continuation.
* **Naming Conventions**:
  * Variables and functions: `snake_case`
  * Classes: `PascalCase`
  * Constants: `UPPER_CASE`
  * Avoid single-character variable names (except loop counters).
* **Comments**:
  * Single-line: `#`
  * Docstrings: `"""`
  * Comment complex logic.
  * Update comments when code changes.

## File Structure

* **File Naming**: Descriptive names in `snake_case`.
* **Modularity**: Keep related functionality in the same module.
* **Separation of Concerns**: Separate concerns into different files.
* **Reusability**: Separate reusable components into different packages.
* **Package Initialization**: Use `__init__.py` for package initialization.

## Patterns and Practices

* **Testing**:
  * Write tests for all new functionality.
  * Stub functions to facilitate testing before production code is fully implemented.
  * Aim for greater than 90% test coverage.
  * Test positive and negative cases.
  * Use descriptive test function names.
    * *See SpecKit Constitution II. Testing Standards for core principles.*
* **Documentation**:
  * Document all public functions with docstrings.
  * Include type hints where appropriate.
  * Keep documentation up-to-date with code changes.
  * Use Google-style docstrings.
* **Version Control**:
  * Commit frequently with meaningful messages.
  * Use present tense in commit messages.
  * Follow semantic versioning.
  * Keep commits small and focused.
  * Use `commitizen` for managing version changes.
  * Adopt the Conventional Commits specification for commit message structure (e.g., feat, fix, refactor, chore) to ensure consistency and facilitate automated changelog generation.
* **Security**:
  * *For overarching security principles, refer to SpecKit Constitution V. Security Practices.*
* **Performance**:
  * Avoid unnecessary computations.
  * Use efficient data structures.
  * Profile code when performance is critical.
  * Consider memory usage for large datasets.
    * *Refer to SpecKit Constitution IV. Performance Requirements for fundamental guidelines.*
* **Code Quality**:
  * Keep functions small and focused.
  * Avoid code duplication.
  * Use meaningful variable names.
  * Write readable and maintainable code.
  * Use strict type casting.
  * Use native types (e.g., `list`, `dict`) over `typing` library equivalents (e.g., `List`, `Dict`).
    * *For broader quality principles, see SpecKit Constitution I. Code Quality.*
* **Diagramming**:
  * When documenting in UML and C4, use PlantUML and C4-PlantUML.
  * Primarily focus on structural representation.
  * When documenting instance information, use appropriate diagram types such as UML Object diagrams, and include examples in parentheses.
* **Shell Scripting Best Practices**:
  * Use `set -euo pipefail` for robust script execution.
  * Implement explicit error checking and informative logging for commands.
  * Prefer using helper functions for common operations (e.g., `run_command`).

* **Configuration Management**: Always use fit-for-purpose utilities for managing project configuration and dependencies (e.g., use `uv add` or `uv remove` for dependency management instead of manual `pyproject.toml` edits).

## Automated Code Uplift and Quality Improvement

The concept of using autonomous agents to uplift code quality and incrementally increase test coverage involves leveraging AI-driven tools and automated processes for iterative improvement. It is designed for an iterative development process where an AI coding assistant works alongside static analysis and test coverage tools.

### Core Concepts

* **Isolated Development Environment**: Employs `git worktree` to establish an isolated branch for modifications, preventing interference with the main codebase. A dedicated Python virtual environment (`venv`) is also established to manage dependencies specifically for this uplift process, ensuring consistency and reproducibility.

* **AI-Assisted Fixing**: Integrates with an AI coding assistant (e.g., Aider) configured for autonomous operations, including auto-accepting suggestions, auto-committing fixes, and performing automated linting and testing. Specific parameters for the AI model must be clearly defined to tailor its interventions effectively.

* **Iterative Static Analysis and Correction**: The core workflow involves:
    1. Running static type checking using a chosen static analysis tool on individual files.
    2. If the static analysis tool reports errors, these are relayed to the AI assistant along with the file path for contextual awareness.
    3. The AI assistant attempts to resolve the reported errors autonomously, applying context-aware recommendations.
    4. Following corrections, the file is re-evaluated using the static analysis tool. This loop continues until the tool reports no errors, ensuring compliance with type safety and quality standards.

* **Incremental Test Coverage Enhancement**: The process consists of:
    1. Evaluating the current state of test coverage within the codebase.
    2. Identifying specific code segments (such as functions, branches, or files) that lack sufficient test coverage.
    3. Generating targeted test cases for these segments, potentially utilizing AI assistance to comprehend code behavior and formulate precise assertions.
    4. Integrating the newly generated tests into the existing test suite and verifying their successful execution to ensure an overall increase in test coverage.

* **Configuration Management**: Specific configuration files are dynamically generated to tailor the AI assistant's behavior, encompassing parameters like the selected AI model and enabling autonomous capabilities. This flexibility allows adaptation to varying project needs and workflows.

* **Outcome Metrics and Considerations**: To gauge the success of this automated process, metrics such as reduced bug counts, improvement in test pass rates, and time savings in code reviews should be established and monitored. Additionally, potential challenges such as dependency conflicts and AI reasoning errors should be anticipated and addressed proactively.

## Error Management

* **Consistent Error Responses**: Define a standard format for API error responses (e.g., JSON structure including error code, message, and details) for predictable client-side handling.
* **Exception Handling**: Implement robust try-except blocks to catch and handle exceptions gracefully, preventing application crashes.
* **Meaningful Error Codes**: Utilize standardized HTTP status codes for API errors and define custom error codes for specific application-level issues.

## Observability and Logging

* **Structured Logging**: Implement structured logging (e.g., JSON format) to facilitate easier parsing and analysis of log data.
* **Log Levels**: Utilize standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) appropriately to categorize messages.
* **Centralized Logging**: Consider strategies for aggregating logs from different services/components into a central system for monitoring and analysis.
* **Metrics Collection**: Instrument the application to collect key performance indicators (KPIs) and system metrics (e.g., request latency, error rates, resource usage) for monitoring and alerting.
* **Distributed Tracing**: For microservices or complex workflows, implement distributed tracing to track requests across multiple services.

## Continuous Integration and Continuous Deployment (CI/CD)

* **Automated Pipelines**: Establish CI/CD pipelines for automated building, testing, linting, and deployment.
* **Build Automation**: Ensure consistent and reproducible builds.
* **Automated Testing**: Integrate all automated tests (unit, integration, BDD) into the CI pipeline to run on every commit.
* **Linting and Formatting**: Integrate `Ruff` or similar tools into the pipeline to enforce code style and quality.
* **Deployment Strategy**: Define clear deployment strategies (e.g., blue-green, canary releases) and automate deployment processes where feasible.

## API Design Principles

* **RESTful Conventions**: Adhere to RESTful principles for API design, including resource-based URLs, appropriate HTTP methods (GET, POST, PUT, DELETE), and status codes.
* **API Versioning**: Implement a clear versioning strategy (e.g., URL path versioning) for managing API evolution.
* **Authentication and Authorization**: Define secure mechanisms for authenticating API consumers and authorizing access to resources.
* **Data Validation**: Utilize `Pydantic V2` for request and response data validation to ensure data integrity.
* **State Transition Enforcement**: When designing APIs for entities modeled as FSMs, use Pydantic models to define valid states and enforce transition rules. Prefer action-based endpoints (e.g., `/resource/{id}/action`) that trigger state changes as side-effects, rather than direct state updates, to maintain workflow integrity.

## Project Configuration

*   **pyproject.toml**: Adhere to [PEP 621](https://peps.python.org/pep-0621/) for defining project metadata and configuration.

## Software Architectural Patterns

* **Model-View-Controller (MVC)**: A common pattern for structuring applications, separating concerns into model (data and business logic), view (UI), and controller (handles input and updates).
* **Two-Tier and Three-Tier Architectures**: Understand and apply standard architectural patterns for client-server applications, separating presentation, application logic, and data management layers as appropriate for the solution.
* **Finite State Machines (FSM)**: Employ FSMs to model entities with distinct states and transitions, ensuring predictable lifecycles, data integrity, and controlled workflows. This pattern is especially useful for entities with complex operational states or governance processes.

## Domain-Driven Design (DDD)

* **Ubiquitous Language**: Establish and use a common language shared by developers and domain experts throughout the project.
* **Bounded Contexts**: Define clear boundaries for different parts of the domain model, managing complexity and allowing for independent evolution.
* **Aggregates and Entities**: Design domain models around aggregates to enforce invariants and manage consistency. FSMs often complement DDD by managing the state of aggregates or entities.

## Utilities and Frameworks

* **Testing Frameworks**: `pytest`, `pytest-mock`, `behave` (for BDD)
* **Linters/Formatters**: `Ruff`
* **Type Checkers**: `MyPy`, `PyRight`
* **Build/Dependency Management**: Prefer `uv` for dependency installation and resolution from `pyproject.toml`. Avoid use of `requirements.txt`. Only use `poetry` when `uv` has no equivalent option.
* **Package Installation/Running**: `UV`
* **API Framework**: `FastAPI`
* **UI Frameworks**: `Streamlit`, `Chainlit` (for building interactive UIs and LLM-based applications)
* **Messaging/Orchestration**: `CrewAI` (implied by usage context)
* **Utilities for LLM**: `LiteLLM`
* **Data Validation**: `Pydantic V2`

### Python Specifics

*   **Dataclass Argument Order**: When defining dataclasses, ensure all non-default arguments (fields without default values) are listed before any arguments with default values. Failing to do so will result in a `TypeError`.
*   **Avoiding Circular Imports**: Be mindful of import dependencies between modules. A common pitfall occurs when module A imports from module B, and module B simultaneously imports from module A, leading to `ImportError`. Refactor code to break these cycles, often by moving shared logic or type hints to a separate, lower-level module.
*   **Import Style for `src` Layouts**: For projects using a `src` layout (where application code resides in a `src` directory), ensure `src` is correctly added to `PYTHONPATH` (e.g., via `pyproject.toml` or build tools). Subsequently, remove redundant `src.` prefixes from import statements (e.g., use `from sdd_cash_manager.models.module import ...` instead of `from src.models.module import ...`) for cleaner, more idiomatic Python.
*   **Mypy Configuration for `src` Layouts**: For projects utilizing a `src` directory structure, correctly configuring `mypy` in `pyproject.toml` is crucial to avoid "Duplicate module named" or `[import-untyped]` errors.
    *   **Module Name Collisions**: Ensure that Python files within different subdirectories of `src` (e.g., `src/models/account.py` and `src/schemas/account.py`) do not share the same base filename (e.g., `account.py`). If they do, rename one (e.g., `account_schema.py`) and update all corresponding import statements to prevent `mypy` from flagging duplicate module names.
    *   **Package Discovery**: Use `mypy_path = "src"` to instruct `mypy` to find top-level modules (like `models`, `schemas`, `services`, `api`) directly within `src`.
    *   **Explicit Package Listing**: Combine `mypy_path = "src"` with `packages = ["models", "schemas", "services", "api", "tests"]` within the `[tool.mypy]` section to explicitly tell `mypy` which packages (relative to `mypy_path`) to type-check, including the `tests` directory. Avoid `files = ["src", "tests"]` when using `mypy_path` and `packages` as it can lead to duplicate processing.

### Testing

*   **Static Analysis vs. Runtime Exception Tests**: When writing tests that specifically aim to assert a `TypeError` or other runtime exceptions for syntactically incorrect code (e.g., missing required arguments in a constructor call), static analysis tools like `pyright` may flag these test calls as errors. To satisfy static analyzers, consider providing valid but semantically "empty" or "invalid" values (e.g., empty strings for required string fields) and then validate these values with runtime logic (e.g., using `__post_init__` in dataclasses to raise `ValueError`).
*   Write tests for all new functionality.
*   Stub functions to facilitate testing before production code is fully implemented.
*   Aim for greater than 90% test coverage.
*   Test positive and negative cases.
*   Use descriptive test function names.
    *   *See SpecKit Constitution II. Testing Standards for core principles.*

# Dependency Installation

To set up `uv`, run:

```bash
sudo apt-get update
pip install --upgrade uv
```

- Add dependency
  - uv: `uv add <package> [--group <group>] [--dev] [--version <constraint>]`
  - examples: `uv add requests`, `uv add pytest --group dev`

- Remove dependency
  - uv: `uv remove <package>`

- Install / sync including all groups / extras
  - uv: `uv sync --upgrade --all`
  - or to include specific groups: `uv sync --upgrade --groups dev,tests,lint,docs`

- Update dependencies
  - uv: `uv update [<packages>...] [--group <group>]`

- Lock dependencies / generate lockfile
  - uv: `uv lock [--no-update]`

- Show dependencies / tree
  - uv: `uv show [--tree] [<package>]`

- Run a command in the venv, run scripts / entry points defined in pyproject
  - uv: `uv run -- <command>` or `uv run <command> [args...]`
  - example: `uv run python`, `uv run pytest`
  - uv: `uv run <script-name>` (scripts exposed via project config)

- Spawn a shell in the venv
  - uv: `uv shell`

- Env / venv management (uv venv namespace)
  - List venvs: `uv venv list`
  - Create venv: `uv venv create [--python <python>] [--path <path>]`
  - Use/select venv: `uv venv use <name-or-path>`
  - Remove venv: `uv venv remove <name>`
  - Show venv info: `uv venv show <name>`
  - Activate shell for specific venv: `uv venv shell <name>`

- Build package
  - uv: `uv build [--format wheel,sdist]`

- Publish package
  - uv: `uv publish [--repository <repo>]`

- Show project info / metadata
  - uv: `uv info`

- Security audit
  - uv: `uv audit`

Notes:
- Flags/option names above follow the uv CLI documented patterns (e.g., `--all`, `--groups`, `--python`). Use `uv <command> --help` for full option lists and exact formatting for your uv version.

# SonarQube

To force a SonarQube check, run:
```bash
sudo apt-get update && sudo apt-get install -y default-jre
pysonar \
  --sonar-host-url=http://host.containers.internal:9000 \
  --sonar-token=squ_0ef6cbaa955c58d8b5e8073b4c64a71fe3ccd7bf \
  --sonar-project-key=sdd-cash-manager
```
