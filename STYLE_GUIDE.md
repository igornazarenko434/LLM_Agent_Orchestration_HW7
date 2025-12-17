# Style Guide & Contributing

This document outlines the coding standards and contribution workflow for the Even/Odd League Multi-Agent System.

## Code Style

We enforce a strict code style using automated tools. Please ensure your code passes all checks before submitting.

### Python
-   **Formatter:** `black` (line length 104)
-   **Import Sorting:** `isort` (profile "black")
-   **Linter:** `flake8` and `pylint`
-   **Type Checking:** `mypy` (strict mode where possible)
-   **Docstrings:** Google style or NumPy style. All public modules, classes, and functions must have docstrings.

### Configuration
All tool configurations are centralized in `pyproject.toml`, `.flake8`, and `mypy.ini`. Do not modify these unless necessary for the entire project.

## Workflow

### Branching Strategy
-   `main`: Stable, production-ready code.
-   `feature/<name>`: New features (e.g., `feature/player-agent`).
-   `fix/<issue>`: Bug fixes (e.g., `fix/timeout-handler`).
-   `chore/<task>`: Maintenance (e.g., `chore/dependency-update`).

### Commit Messages
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
-   `feat: add player registration tool`
-   `fix: resolve timeout in match conductor`
-   `docs: update API reference`
-   `style: format code with black`
-   `refactor: simplify game logic`
-   `test: add unit tests for retry policy`
-   `chore: update dependencies`

### Pull Request (PR) Checklist
1.  **Tests:** Ensure all unit and integration tests pass.
2.  **Coverage:** Maintain or increase code coverage (target ≥85%).
3.  **Linting:** Run `pre-commit run --all-files` to ensure style compliance.
4.  **Documentation:** Update docstrings and relevant markdown files.
5.  **Description:** Clearly describe the changes and link to related issues/missions.

## Development Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Pre-Commit Hooks:**
    ```bash
    pre-commit install
    ```

3.  **Run Checks Manually:**
    ```bash
    black agents SHARED tests
    flake8 agents SHARED tests
    mypy agents SHARED
    ```
