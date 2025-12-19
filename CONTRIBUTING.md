# Contributing to Even/Odd League

Thank you for your interest in contributing to the Even/Odd League Multi-Agent Orchestration System! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Commit Message Format](#commit-message-format)
- [Branching Strategy](#branching-strategy)
- [Pull Request Process](#pull-request-process)
- [Pre-Commit Hooks](#pre-commit-hooks)
- [Running Quality Checks](#running-quality-checks)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Getting Started

### Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/igornazarenko434/LLM_Agent_Orchestration_HW7.git
   cd LLM_Agent_Orchestration_HW7
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install League SDK in editable mode:**
   ```bash
   pip install -e SHARED/league_sdk
   ```

5. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

6. **Verify installation:**
   ```bash
   python3 -c "from league_sdk import JsonLogger, retry_with_backoff, CircuitBreaker; print('✅ SDK Imported Successfully')"
   ```

---

## Code Style

We enforce strict code quality standards using automated tools. All code must pass these checks before merging.

### Python Style Guidelines

- **Formatter:** `black` (line length: 104 characters)
- **Import Sorting:** `isort` (profile: "black")
- **Linter:** `flake8` and `pylint`
- **Type Checking:** `mypy` (configured per module)
- **Docstrings:** Google style or NumPy style required for all public modules, classes, and functions

### Configuration Files

All tool configurations are centralized in:
- `pyproject.toml` - black, isort, mypy, pylint, pytest
- `.flake8` - flake8 rules
- `mypy.ini` - mypy type checking rules
- `.pre-commit-config.yaml` - pre-commit hook configuration

**DO NOT modify these configurations** unless the change is needed project-wide and has been discussed with the team.

### Naming Conventions

- **Variables/Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** `_leading_underscore`
- **Agent IDs:** Uppercase (e.g., `P01`, `R01`, `LM01`)
- **Message types:** `UPPER_SNAKE_CASE` (e.g., `GAME_INVITATION`, `CHOOSE_PARITY_CALL`)
- **Error codes:** Format `E###` (e.g., `E001`, `E012`)

### File Organization

```
agents/
  {agent_type}_{agent_id}/     # e.g., player_P01, referee_R01
    __init__.py
    server.py                  # FastAPI server + MCP endpoint
    handlers.py                # Tool handlers
    {game_type}_strategy.py    # Game-specific logic (if applicable)
```

---

## Testing Requirements

### Coverage Standards

- **Minimum coverage:** 85% (enforced by CI/CD)
- **Target coverage:** 90%+
- All new features MUST include tests
- All bug fixes MUST include regression tests

### Test Organization

```python
tests/
  unit/              # Fast, isolated tests
  integration/       # Multi-component tests
  e2e/              # End-to-end system tests
  fixtures/         # Shared test data
```

### Test Markers

Use pytest markers to categorize tests:
```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Slow-running test
```

### Running Tests

```bash
# All tests with coverage
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov=SHARED/league_sdk --cov=agents --cov-report=term-missing

# Specific test categories
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests
pytest -m "not slow"     # Skip slow tests

# Single test file
pytest tests/unit/test_protocol.py -v

# With debugging
pytest tests/unit/test_protocol.py -v -s --pdb
```

---

## Documentation Standards

### Docstring Requirements

All public modules, classes, and functions MUST have docstrings.

**Example - Function Docstring:**
```python
def retry_with_backoff(max_retries: int = 3, initial_delay: float = 2.0) -> Callable:
    """
    Decorator for retrying failed operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 2.0)

    Returns:
        Decorated function with retry logic applied

    Raises:
        Exception: Re-raises the last exception if all retries exhausted

    Example:
        @retry_with_backoff(max_retries=3, initial_delay=2.0)
        def unreliable_function():
            # May fail transiently
            pass
    """
```

**Example - Class Docstring:**
```python
class PlayerAgent(BaseAgent):
    """
    Player agent implementing MCP server for Even/Odd League.

    Handles game invitations, parity choices, and match result notifications.
    Maintains player history and statistics in data/players/{player_id}/.

    Attributes:
        agent_id: Player identifier (e.g., "P01")
        history_repo: Repository for match history persistence
        state: Current agent state (INIT, REGISTERING, REGISTERED, ACTIVE)

    Example:
        agent = PlayerAgent(agent_id="P01")
        agent.start()  # Start FastAPI server on configured port
    """
```

### README Updates

When adding new features or changing behavior:
1. Update relevant sections in README.md
2. Update code examples if applicable
3. Add new features to "Key Features" section
4. Update installation steps if dependencies change

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, no logic change)
- `refactor:` Code refactoring (no feature/fix)
- `test:` Add or update tests
- `chore:` Maintenance tasks (dependencies, configs)
- `perf:` Performance improvements

### Examples

```
feat(player): add LLM-guided parity selection strategy

Implement GPT-4 based strategy for choosing even/odd based on
opponent history analysis and game theory principles.

Closes #42
```

```
fix(retry): resolve exponential backoff calculation error

Fixed issue where delay was calculated as delay^2 instead of
delay*2, causing excessively long waits.

Fixes #18
```

```
docs(readme): update installation instructions for M1 Macs

Added section for Apple Silicon specific setup steps including
Rosetta requirements for some dependencies.
```

---

## Branching Strategy

### Branch Naming

- `main` - Stable, production-ready code (protected)
- `develop` - Integration branch (if used)
- `feature/<name>` - New features (e.g., `feature/llm-parity-strategy`)
- `fix/<issue>` - Bug fixes (e.g., `fix/timeout-handler`)
- `chore/<task>` - Maintenance (e.g., `chore/dependency-update`)
- `docs/<topic>` - Documentation (e.g., `docs/api-reference`)

### Workflow

1. Create branch from `main`
2. Make changes and commit
3. Push branch and open Pull Request
4. Address review comments
5. Merge after approval and CI passes

---

## Pull Request Process

### Before Opening PR

1. **Run all quality checks locally:**
   ```bash
   pre-commit run --all-files
   ```

2. **Ensure tests pass:**
   ```bash
   PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov-fail-under=85
   ```

3. **Verify no new issues:**
   ```bash
   flake8 agents SHARED tests
   mypy agents SHARED
   ```

### PR Checklist

- [ ] **Tests:** All tests pass locally
- [ ] **Coverage:** Coverage maintained or increased (≥85%)
- [ ] **Linting:** No flake8/pylint warnings
- [ ] **Type Checking:** mypy passes without errors
- [ ] **Documentation:** Docstrings added/updated for new code
- [ ] **README:** Updated if user-facing changes
- [ ] **Commit Messages:** Follow Conventional Commits format
- [ ] **Pre-commit:** Hooks pass (`pre-commit run --all-files`)
- [ ] **No Secrets:** No API keys, tokens, or credentials committed
- [ ] **Backwards Compatible:** Existing functionality not broken

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List key changes
- Highlight breaking changes (if any)

## Testing
How was this tested?

## Related Issues
Closes #123
```

### Review Process

1. At least 1 approval required before merge
2. All CI checks must pass
3. Address all review comments
4. Keep PR focused (one feature/fix per PR)
5. Rebase on main if needed before merge

---

## Pre-Commit Hooks

Pre-commit hooks run automatically before each commit to catch issues early.

### Installation

```bash
# Install pre-commit (already in requirements.txt)
pip install pre-commit

# Install git hooks
pre-commit install

# Test hooks on all files
pre-commit run --all-files
```

### Configured Hooks

1. **trailing-whitespace** - Remove trailing whitespace
2. **end-of-file-fixer** - Ensure files end with newline
3. **check-yaml** - Validate YAML syntax
4. **check-json** - Validate JSON syntax
5. **detect-private-key** - Prevent committing secrets
6. **check-added-large-files** - Prevent large file commits
7. **black** - Auto-format Python code (line length: 104)
8. **isort** - Sort imports
9. **flake8** - Lint Python code
10. **mypy** - Type checking

### Bypassing Hooks (Use Sparingly)

```bash
# Skip hooks for specific commit (not recommended)
git commit --no-verify -m "emergency fix"

# Skip specific hook
SKIP=flake8 git commit -m "WIP: feature in progress"
```

---

## Running Quality Checks

### Manual Commands

```bash
# Format code (auto-fixes)
black agents SHARED tests
isort agents SHARED tests

# Linting (report only)
flake8 agents SHARED tests
pylint agents SHARED

# Type checking
mypy agents SHARED --config-file=mypy.ini

# Run all pre-commit hooks
pre-commit run --all-files

# Tests with coverage
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ \
  --cov=SHARED/league_sdk \
  --cov=agents \
  --cov-report=term-missing \
  --cov-fail-under=85
```

### Expected Output

All commands should exit with code 0 (success):
- `black --check` - "All done! ✨ 🍰 ✨"
- `flake8` - No output (means no issues)
- `mypy` - "Success: no issues found"
- `pytest` - All tests pass, coverage ≥85%

---

## CI/CD Pipeline

### Automated Checks

Every push and pull request triggers:

1. **Code Formatting** - `black --check`
2. **Import Sorting** - `isort --check-only`
3. **Linting** - `flake8`
4. **Type Checking** - `mypy`
5. **Tests** - `pytest` with coverage gate (≥85%)

### Workflow File

See `.github/workflows/test.yml` for full configuration.

### Failure Handling

If CI fails:
1. Check the GitHub Actions log for details
2. Run the failing command locally
3. Fix the issue
4. Push the fix
5. CI will re-run automatically

### Coverage Reports

Coverage reports are generated on every CI run. If coverage drops below 85%, the build fails.

---

## Common Issues & Solutions

### Import Errors in Tests

**Problem:** `ModuleNotFoundError: No module named 'league_sdk'`

**Solution:**
```bash
# Set PYTHONPATH before running tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/

# Or install SDK in editable mode
pip install -e SHARED/league_sdk
```

### Line Too Long Errors

**Problem:** `E501 line too long (120 > 104 characters)`

**Solution:**
```bash
# Auto-format with black
black <file.py>

# Or break line manually
long_function_call(
    arg1="value1",
    arg2="value2",
    arg3="value3"
)
```

### mypy Type Errors

**Problem:** `error: Missing return statement`

**Solution:**
```python
# Add return type annotation
def my_function() -> None:  # Explicitly return None
    print("Hello")

# Or return a value
def my_function() -> str:
    return "Hello"
```

### Pre-commit Hook Failures

**Problem:** Pre-commit modifies files but commit fails

**Solution:**
```bash
# Hooks auto-fixed files (e.g., black formatting)
# Simply add the changes and commit again
git add .
git commit -m "your message"  # Will succeed now
```

---

## Questions or Need Help?

- **Documentation:** Check README.md and doc/ folder
- **Issues:** Open a GitHub issue with detailed description
- **Style Questions:** Refer to this CONTRIBUTING.md
- **Testing Help:** See test examples in tests/ directory
- **Protocol Questions:** See PRD_EvenOddLeague.md Section 8 (Protocol Specification)

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

See [LICENSE](LICENSE) file for details.
