# How Quality Standards Work - Complete Guide

## 📍 Local Development on macOS

### Scenario 1: You Create/Edit a Python File

```bash
# You create a new file
vim agents/my_agent.py

# You write some code (doesn't matter if it's messy):
def my_function(x,y,z):
  result=x+y+z  # Bad formatting, no spaces
  return result
```

**Nothing happens yet - quality checks only run on commit!**

---

### Scenario 2: You Stage and Commit Changes

```bash
# Stage your changes
git add agents/my_agent.py

# Try to commit
git commit -m "feat: add my agent"
```

**🚨 PRE-COMMIT HOOKS ACTIVATE AUTOMATICALLY:**

```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
detect private key.......................................................Passed
black....................................................................Failed
- files were modified by this hook

Fixing agents/my_agent.py
```

**What Happened:**
1. ✅ Trailing whitespace removed
2. ✅ End of file fixed
3. ✅ No private keys detected
4. ⚠️ **black FIXED your code automatically:**

```python
# Your code was AUTO-FORMATTED to:
def my_function(x, y, z):
    result = x + y + z  # Now properly formatted
    return result
```

5. **Commit BLOCKED** - You need to stage the fixes and commit again

---

### Scenario 3: Re-stage and Commit After Fixes

```bash
# Stage the auto-fixed code
git add agents/my_agent.py

# Commit again
git commit -m "feat: add my agent"
```

**All Pre-commit Hooks Run Again:**
```
trim trailing whitespace.................................................Passed
fix end of files.........................................................Passed
check yaml...............................................................Passed
detect private key.......................................................Passed
black....................................................................Passed  ✅
isort....................................................................Passed  ✅
flake8...................................................................Passed  ✅
mypy.....................................................................Passed  ✅

[main abc1234] feat: add my agent
 1 file changed, 5 insertions(+)
```

**✅ Commit SUCCESSFUL!** Your code is now:
- Properly formatted (104 char line length)
- Imports sorted
- Linted (no PEP 8 violations)
- Type-checked (no mypy errors)

---

### Scenario 4: You Push to GitHub

```bash
git push origin main
```

**Local:**
- Nothing happens locally (push succeeds immediately)

**On GitHub (GitHub Actions):**
- Workflow triggers automatically
- Runs on Ubuntu Linux with Python 3.10 and 3.11
- **Step 1:** Checkout code ✅
- **Step 2:** Install dependencies ✅
- **Step 3:** Code Formatting Check (black) ✅
- **Step 4:** Import Sorting Check (isort) ✅
- **Step 5:** Linting (flake8) ✅
- **Step 6:** Type Checking (mypy) ✅
- **Step 7:** Run Tests with Coverage ✅
  - **If coverage < 85%:** ❌ **BUILD FAILS**
  - **If any test fails:** ❌ **BUILD FAILS**
- **Step 8:** Upload coverage reports ✅

**Results visible at:**
- https://github.com/igornazarenko434/LLM_Agent_Orchestration_HW7/actions

---

## 🚫 What Happens If Quality Checks Fail?

### Example: You Write Bad Code

```python
# agents/bad_agent.py
def really_long_function_name_that_exceeds_the_104_character_limit_and_will_fail_flake8_check(param1, param2, param3):
    pass
```

**When you commit:**
```
flake8...................................................................Failed
- hook id: flake8
- exit code: 1

agents/bad_agent.py:1:105: E501 line too long (120 > 104 characters)
```

**❌ Commit BLOCKED!** You must fix the issue:

```python
# Fixed version:
def really_long_function_name_that_exceeds_limit(
    param1, param2, param3
):
    pass
```

---

## 📝 What Files Trigger Which Checks?

| File Type | black | isort | flake8 | mypy | tests |
|-----------|-------|-------|--------|------|-------|
| `*.py` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `*.md` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `*.yml` | ❌ | ❌ | ❌ | ❌ | ✅ (check-yaml) |
| `*.json` | ❌ | ❌ | ❌ | ❌ | ✅ (check-json) |
| Any file | ✅ (trailing-whitespace, end-of-file) | ❌ | ❌ | ❌ | ❌ |

---

## 🔧 Manual Quality Checks (Optional)

You can run checks manually WITHOUT committing:

```bash
# Format all Python code
black agents SHARED tests

# Check formatting without changing files
black --check agents SHARED tests

# Sort imports
isort agents SHARED tests

# Lint code
flake8 agents SHARED tests

# Type check
mypy agents SHARED

# Run all pre-commit hooks
pre-commit run --all-files

# Run tests with coverage
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov=SHARED/league_sdk --cov=agents --cov-report=term
```

---

## 🎯 Summary: The Full Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. YOU: Edit code in your IDE/editor                           │
│    → No quality checks yet                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. YOU: git add <files>                                         │
│    → No quality checks yet                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. YOU: git commit -m "message"                                 │
│    → 🚨 PRE-COMMIT HOOKS ACTIVATE (LOCAL)                       │
│    → Auto-fixes: trailing whitespace, end-of-file, formatting  │
│    → Checks: yaml, json, secrets, linting, type-checking       │
│    → ❌ Blocks commit if any check fails                        │
│    → ✅ Allows commit if all checks pass                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. YOU: git push origin main                                    │
│    → Push succeeds immediately (local push)                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. GITHUB: Workflow triggers automatically                      │
│    → Runs on GitHub's servers (Ubuntu Linux)                    │
│    → Re-runs ALL quality checks (black, flake8, mypy)           │
│    → Runs ALL 182 tests                                         │
│    → Checks coverage ≥85%                                        │
│    → ❌ Build fails if any check/test fails                     │
│    → ✅ Build passes if everything succeeds                     │
│    → 📊 Results visible on GitHub Actions page                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Points

1. **Pre-commit hooks run ONLY when you commit** (not when you edit/save files)
2. **Hooks can AUTO-FIX some issues** (formatting, whitespace)
3. **Hooks can BLOCK commits** (if linting/type-checking fails)
4. **GitHub Actions runs AFTER push** (double-checks everything)
5. **Nothing changes in your code logic** (only formatting/whitespace)

---

## 🆘 Bypassing Hooks (Emergency Only)

**NOT RECOMMENDED**, but if you absolutely need to commit without checks:

```bash
git commit --no-verify -m "emergency fix"
```

**⚠️ WARNING:** GitHub Actions will still run and may fail!
