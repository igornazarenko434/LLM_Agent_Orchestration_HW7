# Even/Odd League Multi-Agent System

## Development & Code Quality

We maintain high code quality standards using automated tools and strict workflows.

### Quick Start
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Install Git Hooks:**
    ```bash
    pre-commit install
    ```

### Code Style
Refer to [STYLE_GUIDE.md](STYLE_GUIDE.md) for detailed guidelines on branching, commits, and coding standards.

-   **Formatter:** `black`
-   **Linters:** `flake8`, `pylint`
-   **Type Checker:** `mypy`

### Running Checks Manually

**1. Format Code:**
```bash
black agents SHARED tests
```

**2. Lint Code:**
```bash
flake8 agents SHARED tests
pylint agents SHARED
```

**3. Type Check:**
```bash
mypy agents SHARED
```

**4. Run All Checks:**
```bash
black --check agents SHARED tests && flake8 agents SHARED tests && mypy agents SHARED
```
