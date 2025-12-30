# Developer Guide

**Document Version:** 1.0.0
**Date:** 2025-01-15
**Status:** Complete
**Mission:** M8.4

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation Methods](#2-installation-methods)
   - [Method 1: Development Setup (Clone + venv)](#method-1-development-setup-clone--venv)
   - [Method 2: Distribution Package (Wheel/Tarball)](#method-2-distribution-package-wheeltarball)
3. [Project Structure](#3-project-structure)
4. [Development Workflow](#4-development-workflow)
5. [Running the System](#5-running-the-system)
6. [Testing](#6-testing)
7. [Code Quality](#7-code-quality)
8. [Adding New Agents](#8-adding-new-agents)
9. [Adding New Game Types](#9-adding-new-game-types)
10. [Debugging](#10-debugging)
11. [Contributing](#11-contributing)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

Before starting, ensure you have the following installed:

### Required Software

| Software | Version | Purpose | Verification |
|----------|---------|---------|--------------|
| **Python** | ≥3.10 | Runtime environment | `python3 --version` |
| **pip** | ≥21.0 | Package manager | `pip --version` |
| **git** | ≥2.0 | Version control | `git --version` |
| **virtualenv** | Latest | Virtual environments | `python3 -m venv --help` |

### Optional Tools (Recommended)

| Tool | Purpose | Installation |
|------|---------|--------------|
| **jq** | JSON processing for log analysis | `brew install jq` (macOS) or `apt-get install jq` (Linux) |
| **curl** | Testing HTTP endpoints | Usually pre-installed |
| **make** | Build automation | Usually pre-installed |

### System Requirements

- **OS**: macOS, Linux, or Windows (WSL recommended for Windows)
- **RAM**: Minimum 4GB (8GB+ recommended for 100+ players)
- **Disk**: 1GB free space for code + data + logs
- **Network**: Ports 8000-9100 available (or configure custom ranges)

### Verification Script

Run this to verify all prerequisites:

```bash
#!/bin/bash
echo "=== Prerequisites Check ==="

# Python version
python3 --version && echo "✅ Python installed" || echo "❌ Python missing"

# pip version
pip --version && echo "✅ pip installed" || echo "❌ pip missing"

# git version
git --version && echo "✅ git installed" || echo "❌ git missing"

# venv support
python3 -m venv --help > /dev/null 2>&1 && echo "✅ venv supported" || echo "❌ venv missing"

# jq (optional)
jq --version > /dev/null 2>&1 && echo "✅ jq installed" || echo "⚠️ jq recommended but optional"

echo "=== Check Complete ==="
```

---

## 2. Installation Methods

### 🎯 Installation Decision Guide

**Choose Method 1 (Development Setup) if:**
- ✅ You're a professor evaluating the project
- ✅ You want to run the complete Even/Odd League system
- ✅ You want to run all 588 tests
- ✅ You want to modify code or contribute
- ✅ You want full source access with git history

**Choose Method 2A (SDK Wheel Only) if:**
- ✅ You only want the SDK library to build your own custom agents
- ❌ You DON'T need the Even/Odd League system, agents, tests, or scripts

**Choose Method 2B (Full System Archive) if:**
- ✅ You want to deploy the complete system quickly without git
- ✅ Same capabilities as Method 1, just pre-packaged
- ✅ Production deployment

---

### Summary Table

| Method | Use Case | Time | Git Needed | Tests Included | Scripts Included |
|--------|----------|------|------------|----------------|------------------|
| **Method 1: Development** | Active development, testing, evaluation | 5 min | Yes | Yes (588 tests) | Yes (12 scripts) |
| **Method 2A: SDK Wheel** | Building custom agents with SDK | 1 min | No | No | No |
| **Method 2B: Full Archive** | Quick deployment, production | 3 min | No | Yes (588 tests) | Yes (12 scripts) |

---

## Method 1: Development Setup (Clone + venv)

**Recommended for:** Contributors, developers, researchers

### Step 1: Clone Repository

```bash
# Clone from GitHub (or your preferred method)
git clone https://github.com/your-org/LLM_Agent_Orchestration_HW7.git
cd LLM_Agent_Orchestration_HW7

# Verify structure
ls -la
# Expected: SHARED/, agents/, tests/, doc/, scripts/, README.md, requirements.txt
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation (should show venv path)
which python3
```

**Important**: Always activate the virtual environment before running any commands. You'll see `(venv)` in your terminal prompt when active.

### Step 3: Upgrade pip

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Verify
pip --version
# Expected: pip 24.0 or higher
```

### Step 4: Install Dependencies

```bash
# Install all dependencies from requirements.txt
pip install -r requirements.txt

# This installs:
# - Core Framework: FastAPI, Uvicorn, Pydantic
# - HTTP Client: Requests, HTTPX
# - Testing: Pytest, pytest-cov, pytest-asyncio
# - Code Quality: Black, Flake8, Mypy, Pylint
# - Research: Jupyter, NumPy, Pandas, Matplotlib, Seaborn, SciPy
# - Utilities: python-dateutil

# Verify installation (should complete without errors)
pip list | grep fastapi
pip list | grep pytest
```

**Expected Installation Time**: 2-5 minutes depending on internet speed.

### Step 5: Install League SDK (Editable Mode)

```bash
# Install league_sdk in editable/development mode
# This allows you to modify SDK code and see changes immediately
pip install -e SHARED/league_sdk

# Verify installation
pip show league-sdk
# Expected output:
# Name: league-sdk
# Version: 1.0.0
# Location: /path/to/LLM_Agent_Orchestration_HW7/SHARED/league_sdk

# Test import
python3 -c "from league_sdk import JsonLogger, retry_with_backoff, CircuitBreaker; print('✅ SDK installed successfully')"
```

**What is editable mode?**
- Changes to `SHARED/league_sdk/*.py` files are immediately available (no reinstall needed)
- Useful for SDK development and debugging
- Uses `pip install -e` flag

### Step 6: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional)
nano .env
# or
vim .env

# Example customizations:
# LOG_LEVEL=DEBUG
# LEAGUE_MANAGER_PORT=8000
# PLAYER_PORT_END=10000
```

### Step 7: Create Data Directories

```bash
# Create required directories for runtime data and logs
mkdir -p SHARED/data/{leagues,matches,players}
mkdir -p SHARED/logs/{agents,league,system}
mkdir -p SHARED/archive/{logs,matches,players,leagues}

# Verify structure
ls -la SHARED/data
ls -la SHARED/logs
```

### Step 8: Verify Installation

```bash
# Run verification script
PYTHONPATH=SHARED:$PYTHONPATH python3 -c "
from league_sdk import JsonLogger, retry_with_backoff, CircuitBreaker
from league_sdk.config_loader import load_system_config
from league_sdk.protocol import GameInvitation

print('✅ All imports successful')

# Load config
config = load_system_config('SHARED/config/system.json')
print(f'✅ System config loaded: protocol {config.protocol_version}')

# Test message creation
msg = GameInvitation(
    sender='referee:REF01',
    timestamp='2025-01-15T10:00:00Z',
    conversation_id='test',
    auth_token='test-token-32-characters-long',
    league_id='test_league',
    match_id='TEST_MATCH',
    game_type='even_odd',
    player_id='P01',
    opponent_id='P02',
    opponent_endpoint='http://localhost:8102/mcp'
)
print(f'✅ Protocol models working: {msg.message_type}')

print('\\n🎉 Installation verified successfully!')
"
```

**Expected Output:**
```
✅ All imports successful
✅ System config loaded: protocol league.v2
✅ Protocol models working: GAME_INVITATION

🎉 Installation verified successfully!
```

### Step 9: Run Tests (Optional but Recommended)

```bash
# Run full test suite to verify everything works
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v --cov=SHARED/league_sdk --cov=agents

# Expected: 588 tests passed, 85%+ coverage
```

### Step 10: Start Your First Agent

```bash
# Start a player agent
cd agents/player_P01
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py

# Expected output:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://localhost:8101 (Press CTRL+C to quit)

# Test health endpoint (in another terminal)
curl http://localhost:8101/health
# Expected: {"status":"ok"}
```

**Congratulations!** You now have a working development environment. 🎉

---

## Method 2: Distribution Package (Wheel/Tarball)

**Recommended for:** Production deployment, quick evaluation, demos

### Overview

There are **two distribution formats**:

1. **Python Wheel (.whl)** - For pip installation (includes SDK + agents)
2. **Deployment Archive (.tar.gz)** - For complete system deployment (includes everything)

### Option 2A: Install from Python Wheel

**Use Case**: Install as a Python package without cloning the repository.

#### Building the Wheel (for maintainers)

```bash
# From project root
cd SHARED/league_sdk

# Build wheel and source distribution
python3 -m build

# Output in dist/ directory:
# - league_sdk-1.0.0-py3-none-any.whl
# - league_sdk-1.0.0.tar.gz

ls dist/
```

#### Installing the Wheel (for users)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install from wheel file
pip install league_sdk-1.0.0-py3-none-any.whl

# Or install from PyPI (if published)
pip install league-sdk==1.0.0

# Verify installation
python3 -c "from league_sdk import JsonLogger; print('✅ SDK installed')"
```

**Limitations of Wheel-Only Installation:**
- SDK only, does not include agents, configs, or scripts
- Suitable for using SDK as a library in other projects
- Not suitable for running the full league system

### Option 2B: Install from Deployment Archive

**Use Case**: Deploy the complete Even/Odd League system in one step.

#### Creating the Deployment Archive (for maintainers)

```bash
# From project root
./scripts/create_deployment_package.sh --output=even-odd-league-v1.0.0.tar.gz

# Or manually:
tar -czf even-odd-league-v1.0.0.tar.gz \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='htmlcov' \
  --exclude='.coverage' \
  SHARED/ agents/ tests/ doc/ scripts/ \
  README.md requirements.txt pyproject.toml \
  PRD_EvenOddLeague.md Missions_EvenOddLeague.md \
  .env.example

# Verify archive
tar -tzf even-odd-league-v1.0.0.tar.gz | head -20
```

**Archive Contents:**
```
even-odd-league-v1.0.0/
├── SHARED/           # SDK, config, data directories
├── agents/           # League Manager, Referees, Players
├── tests/            # Test suite (588 tests)
├── doc/              # Documentation
├── scripts/          # Operational scripts (12 scripts)
├── README.md         # Main documentation
├── requirements.txt  # Python dependencies
├── pyproject.toml    # Project metadata
├── PRD_EvenOddLeague.md       # Product Requirements
├── Missions_EvenOddLeague.md  # Mission specifications
└── .env.example      # Environment template
```

**Archive Size**: ~10-20 MB (without venv, git, cache)

#### Installing from Deployment Archive (for users)

**Step 1: Extract Archive**

```bash
# Extract to current directory
tar -xzf even-odd-league-v1.0.0.tar.gz

# Navigate to extracted directory
cd even-odd-league-v1.0.0

# Verify contents
ls -la
# Expected: SHARED/, agents/, tests/, doc/, scripts/, README.md
```

**Step 2: Set Up Environment**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install SDK in editable mode
pip install -e SHARED/league_sdk
```

**Step 3: Configure**

```bash
# Copy environment template
cp .env.example .env

# Create data directories
mkdir -p SHARED/data/{leagues,matches,players}
mkdir -p SHARED/logs/{agents,league,system}
mkdir -p SHARED/archive/{logs,matches,players,leagues}
```

**Step 4: Verify Installation**

```bash
# Verify configs
./scripts/verify_configs.sh

# Run tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v
# Expected: 588 tests passed
```

**Step 5: Start the System**

```bash
# Start all agents (League Manager + 2 Referees + 4 Players)
./scripts/start_league.sh

# Check health
./scripts/check_health.sh

# Trigger league start
./scripts/trigger_league_start.sh
```

**Congratulations!** The full system is now running. 🎉

---

## 3. Project Structure

Understanding the project structure is crucial for development.

### High-Level Overview

```
LLM_Agent_Orchestration_HW7/
├── SHARED/                  # Shared resources (SDK, config, data, logs)
├── agents/                  # Agent implementations
├── tests/                   # Test suite
├── doc/                     # Documentation
├── scripts/                 # Operational scripts
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata
├── README.md                # Main documentation
└── PRD_EvenOddLeague.md     # Product requirements
```

### Detailed Structure

```
LLM_Agent_Orchestration_HW7/
│
├── SHARED/                          # Shared Resources (SDK + Config + Data)
│   ├── league_sdk/                  # Core SDK Package (installed via pip)
│   │   ├── __init__.py              # Public API exports
│   │   ├── setup.py                 # pip install -e configuration
│   │   ├── pyproject.toml           # Package metadata (PEP 621)
│   │   ├── protocol.py              # 18 message type models (891 lines)
│   │   ├── config_models.py         # Pydantic config schemas (458 lines)
│   │   ├── config_loader.py         # Config loading with env overrides (156 lines)
│   │   ├── repositories.py          # Data persistence layer (485 lines)
│   │   ├── logger.py                # JSONL structured logging (403 lines)
│   │   ├── retry.py                 # Retry + Circuit Breaker (514 lines)
│   │   ├── queue_processor.py       # Sequential async queue (59 lines)
│   │   ├── method_aliases.py        # PDF compatibility (106 lines)
│   │   ├── cleanup.py               # Data retention (258 lines)
│   │   └── utils.py                 # Utility functions (33 lines)
│   │
│   ├── config/                      # Configuration Files (JSON)
│   │   ├── system.json              # Global system settings
│   │   ├── agents/
│   │   │   └── agents_config.json   # 7 agents (LM, 2 refs, 4 players)
│   │   ├── leagues/
│   │   │   └── league_2025_even_odd.json
│   │   ├── games/
│   │   │   └── games_registry.json  # Even/Odd game rules
│   │   └── defaults/                # Default templates
│   │       ├── player.json
│   │       └── referee.json
│   │
│   ├── data/                        # Runtime Data (git-ignored)
│   │   ├── leagues/                 # Standings, rounds
│   │   ├── matches/                 # Match records
│   │   └── players/                 # Player history
│   │
│   ├── logs/                        # Structured Logs (git-ignored)
│   │   ├── agents/                  # P01.log.jsonl, REF01.log.jsonl
│   │   ├── league/                  # League Manager logs
│   │   └── system/                  # System logs
│   │
│   └── archive/                     # Archived Data (git-ignored)
│       ├── logs/                    # Gzipped old logs
│       ├── matches/                 # Gzipped old matches
│       ├── players/                 # Player history archives
│       └── leagues/                 # League round archives
│
├── agents/                          # Agent Implementations
│   ├── base/                        # Shared Base Agent
│   │   ├── __init__.py
│   │   └── agent_base.py            # BaseAgent class (212 lines)
│   │
│   ├── league_manager/              # League Manager (LM01)
│   │   ├── __init__.py
│   │   ├── server.py                # MCP server + orchestration (2075 lines)
│   │   └── main.py                  # Entry point
│   │
│   ├── referee_REF01/               # Referee Agent #1
│   │   ├── __init__.py
│   │   ├── server.py                # MCP server + registration (1008 lines)
│   │   ├── match_conductor.py       # Match orchestration
│   │   └── main.py                  # Entry point
│   │
│   ├── referee_REF02/               # Referee Agent #2
│   │   ├── __init__.py
│   │   ├── server.py                # Same as REF01
│   │   └── main.py                  # Entry point with different ID
│   │
│   └── player_P01/ ... player_P04/  # Player Agents (4 total)
│       ├── __init__.py
│       ├── server.py                # MCP server + tools (367 lines)
│       ├── handlers.py              # Tool handlers (132 lines)
│       └── main.py                  # Entry point
│
├── tests/                           # Test Suite (588 tests, 85% coverage)
│   ├── conftest.py                  # Pytest fixtures
│   ├── unit/                        # Unit tests
│   │   ├── test_sdk/                # SDK tests
│   │   ├── test_agents/             # Agent tests
│   │   ├── test_league_manager/     # League Manager tests
│   │   └── test_referee_agent/      # Referee tests
│   ├── integration/                 # Integration tests
│   │   ├── test_player_registration.py
│   │   └── test_referee_integration.py
│   ├── e2e/                         # End-to-end tests
│   └── protocol_compliance/         # Protocol tests
│
├── doc/                             # Documentation
│   ├── architecture.md              # System architecture (M8.2)
│   ├── configuration.md             # Configuration guide (M8.3)
│   ├── developer_guide.md           # This file (M8.4)
│   ├── testing_guide.md             # Testing guide (M8.5)
│   ├── usability_extensibility.md   # ISO/IEC 25010 analysis (M8.8)
│   ├── research_notes/
│   │   ├── mcp_protocol.md          # MCP research
│   │   └── experiments.ipynb        # Research notebook
│   ├── game_rules/
│   │   └── even_odd.md              # Even/Odd game spec
│   └── algorithms/
│       └── round_robin.md           # Scheduling algorithm
│
└── scripts/                         # Operational Scripts (12 total)
    ├── start_league.sh              # Start all agents
    ├── stop_league.sh               # Stop all agents
    ├── check_health.sh              # Health check all endpoints
    ├── verify_configs.sh            # Validate configs
    ├── check_registration_status.sh # Show LM registration state
    ├── trigger_league_start.sh      # Start league orchestration
    ├── query_standings.sh           # Query standings
    ├── view_match_state.sh          # Inspect match state
    ├── analyze_logs.sh              # Filter logs
    ├── backup_data.sh               # Backup data/logs
    ├── restore_data.sh              # Restore from backup
    └── cleanup_old_data.sh          # Cleanup old data
```

### Key Directories Explained

| Directory | Purpose | Git Tracked | Notes |
|-----------|---------|-------------|-------|
| `SHARED/league_sdk/` | Core SDK package | ✅ Yes | Installable via `pip install -e` |
| `SHARED/config/` | Configuration files | ✅ Yes | JSON configs validated by Pydantic |
| `SHARED/data/` | Runtime data | ❌ No (.gitignore) | Created at runtime |
| `SHARED/logs/` | Structured logs | ❌ No (.gitignore) | JSONL format |
| `SHARED/archive/` | Archived data | ❌ No (.gitignore) | Gzipped old data |
| `agents/` | Agent implementations | ✅ Yes | League Manager, Referees, Players |
| `tests/` | Test suite | ✅ Yes | 588 tests, 85% coverage |
| `doc/` | Documentation | ✅ Yes | Architecture, guides, research |
| `scripts/` | Operational scripts | ✅ Yes | Bash scripts for league management |

---

## 4. Development Workflow

### Daily Development Cycle

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Pull latest changes (if using git)
git pull origin main

# 3. Install/update dependencies if requirements.txt changed
pip install -r requirements.txt

# 4. Make code changes
# Edit files in SHARED/league_sdk/, agents/, or tests/

# 5. Run tests for affected modules
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/test_sdk/test_protocol_models.py -v

# 6. Run code quality checks
black SHARED/league_sdk/protocol.py
flake8 SHARED/league_sdk/protocol.py

# 7. Commit changes (if satisfied)
git add SHARED/league_sdk/protocol.py
git commit -m "feat: add new message type for tournament brackets"
git push origin feature/tournament-brackets

# 8. Create pull request
# Open PR on GitHub for code review
```

### Code-Test-Commit Cycle

```
┌──────────────┐
│ Write Code   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Run Tests    │ ──❌──> Fix Failures ──┐
└──────┬───────┘                        │
       │✅                               │
       ▼                                │
┌──────────────┐                        │
│ Code Quality │ ──❌──> Fix Issues ────┘
└──────┬───────┘
       │✅
       ▼
┌──────────────┐
│ Commit       │
└──────────────┘
```

### Hot Reload During Development

Since the SDK is installed in **editable mode** (`pip install -e`), changes are immediately available:

```bash
# Terminal 1: Start agent
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P01/main.py

# Terminal 2: Edit SDK code
nano SHARED/league_sdk/protocol.py
# Make changes, save

# Restart agent in Terminal 1 (Ctrl+C, then re-run)
# Changes are immediately active (no reinstall needed)
```

---

## 5. Running the System

### Starting Individual Agents

#### League Manager

```bash
cd agents/league_manager
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8000

# Expected output:
# INFO:     Uvicorn running on http://localhost:8000
```

#### Referee

```bash
cd agents/referee_REF01
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py \
  --referee-id REF01 \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8001

# Expected output:
# INFO:     Uvicorn running on http://localhost:8001
```

#### Player

```bash
cd agents/player_P01
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py \
  --player-id P01 \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8101

# Expected output:
# INFO:     Uvicorn running on http://localhost:8101
```

### Starting All Agents (Automated)

```bash
# From project root
./scripts/start_league.sh

# This script:
# 1. Starts League Manager (LM01) on port 8000
# 2. Starts Referee 1 (REF01) on port 8001
# 3. Starts Referee 2 (REF02) on port 8002
# 4. Starts Player 1-4 (P01-P04) on ports 8101-8104
# 5. Waits for all agents to be healthy

# Check status
./scripts/check_health.sh
# Expected: All agents report {"status":"ok"}
```

### Running a Full League

```bash
# 1. Start all agents
./scripts/start_league.sh

# 2. Verify health
./scripts/check_health.sh

# 3. Check registration status
./scripts/check_registration_status.sh

# 4. Trigger league start (round-robin tournament)
./scripts/trigger_league_start.sh

# 5. Monitor standings
./scripts/query_standings.sh

# 6. View specific match
./scripts/view_match_state.sh R1M1 --referee-id REF01 --sender player:P01 --auth-token <token>

# 7. Analyze logs
./scripts/analyze_logs.sh ERROR

# 8. Stop league
./scripts/stop_league.sh
```

### Workflow with Scripts

All operational scripts support `--help`, `--plain`, `--json`, `--quiet`, and `--verbose` flags for accessibility and automation.

**Example Workflow:**

```bash
# Plain mode (screen reader friendly)
./scripts/check_health.sh --plain

# JSON mode (automation/parsing)
./scripts/query_standings.sh --json | jq '.standings[0].player_id'

# Quiet mode (errors only)
./scripts/start_league.sh --quiet

# Verbose mode (debug info)
./scripts/verify_configs.sh --verbose
```

---

## 6. Testing

See [Testing Guide](testing_guide.md) for comprehensive testing documentation.

### Quick Testing Reference

```bash
# Run all tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v

# Run with coverage
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov=SHARED/league_sdk --cov=agents --cov-report=term

# Run specific test file
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/test_sdk/test_protocol_models.py -v

# Run specific test
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/test_sdk/test_protocol_models.py::test_game_invitation_validation -v

# Run tests matching pattern
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -k "protocol" -v

# Run tests with markers
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -m "unit" -v
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -m "integration" -v
```

---

## 7. Code Quality

### Automated Quality Checks

The project uses multiple tools to ensure code quality:

| Tool | Purpose | Configuration | Command |
|------|---------|---------------|---------|
| **black** | Code formatting | `pyproject.toml` | `black agents SHARED tests` |
| **isort** | Import sorting | `pyproject.toml` | `isort agents SHARED tests` |
| **flake8** | Linting (PEP 8) | `.flake8` | `flake8 agents SHARED tests` |
| **mypy** | Type checking | `myproject.toml` | `mypy agents SHARED` |
| **pylint** | Advanced linting | `pyproject.toml` | `pylint agents SHARED` |
| **pytest** | Testing | `pyproject.toml` | `pytest tests/` |

### Running Quality Checks

```bash
# Format code (auto-fix)
black agents SHARED tests
isort agents SHARED tests

# Lint code (report only)
flake8 agents SHARED tests
pylint agents SHARED

# Type check
mypy agents SHARED --config-file=pyproject.toml

# Run all checks
black agents SHARED tests && \
isort agents SHARED tests && \
flake8 agents SHARED tests && \
mypy agents SHARED && \
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov=SHARED/league_sdk --cov=agents
```

### Pre-Commit Hooks (Recommended)

```bash
# Install pre-commit (if not in requirements.txt)
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Now quality checks run automatically on git commit
git commit -m "feat: add new feature"
# Output: black, isort, flake8, mypy all run automatically
```

### Code Style Standards

- **Line Length**: 104 characters (black configuration)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Sorted with isort (black profile)
- **Docstrings**: Google style (enforced via pydocstyle)
- **Type Hints**: Encouraged but not mandatory
- **Naming Conventions**:
  - Classes: `PascalCase`
  - Functions/Variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Agent IDs: `UPPERCASE` (P01, REF01, LM01)

---

## 8. Adding New Agents

### Adding a New Player Agent

**Step 1: Create Agent Directory**

```bash
mkdir -p agents/player_P05
cd agents/player_P05
```

**Step 2: Create `__init__.py`**

```python
"""Player P05 agent package."""
from agents.player_P01.server import PlayerAgent

__all__ = ["PlayerAgent"]
```

**Step 3: Create `main.py`**

```python
"""Entry point for Player P05."""
import sys
from pathlib import Path

# Add SHARED to Python path
SHARED_DIR = Path(__file__).resolve().parents[2] / "SHARED"
sys.path.insert(0, str(SHARED_DIR))

from agents.player_P01.server import PlayerAgent


def main():
    """Start Player P05 agent."""
    agent = PlayerAgent(
        agent_id="P05",
        league_id="league_2025_even_odd",
        host="localhost",
        port=8105
    )
    agent.start()


if __name__ == "__main__":
    main()
```

**Step 4: Register in Agent Config**

Edit `SHARED/config/agents/agents_config.json`:

```json
{
  "players": [
    ...existing players...,
    {
      "agent_id": "P05",
      "agent_type": "player",
      "display_name": "Player 05",
      "endpoint": "http://localhost:8105/mcp",
      "port": 8105,
      "active": true,
      "version": "1.0.0",
      "capabilities": [
        "handle_game_invitation",
        "choose_parity",
        "notify_match_result",
        "get_player_state"
      ],
      "game_types": ["even_odd"],
      "metadata": {
        "strategy": "random",
        "team": "epsilon",
        "skill_level": "beginner",
        "auto_register": true
      }
    }
  ]
}
```

**Step 5: Test New Agent**

```bash
# Start agent
cd agents/player_P05
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py

# Test health (in another terminal)
curl http://localhost:8105/health
# Expected: {"status":"ok"}
```

### Adding a Custom Player Strategy

**Step 1: Create Strategy Module**

```bash
mkdir -p agents/player_P05/strategies
```

Create `agents/player_P05/strategies/llm_strategy.py`:

```python
"""LLM-based parity selection strategy."""
import os
import openai


class LLMParityStrategy:
    """Use OpenAI API for parity decisions."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key

    def choose_parity(self, match_history: list, opponent_id: str) -> str:
        """Choose parity using LLM reasoning."""
        # Build prompt from match history
        prompt = self._build_prompt(match_history, opponent_id)

        # Query LLM
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )

        choice = response['choices'][0]['message']['content'].strip().lower()
        return choice if choice in ["even", "odd"] else "even"

    def _build_prompt(self, history: list, opponent_id: str) -> str:
        """Build prompt from match history."""
        recent = [m for m in history if m.get("opponent_id") == opponent_id][-5:]
        summary = "\n".join([
            f"Match {m['match_id']}: You chose {m['parity_choice']}, Result: {m['outcome']}"
            for m in recent
        ])

        return f"""
        You are playing the Even/Odd game against {opponent_id}.

        Match history:
        {summary if summary else "No previous matches"}

        Should you choose "even" or "odd"? Respond with only one word.
        """
```

**Step 2: Update Player Handler**

Modify `agents/player_P05/handlers.py`:

```python
from strategies.llm_strategy import LLMParityStrategy

# In handle_choose_parity:
if use_llm:  # Configure via metadata
    strategy = LLMParityStrategy()
    parity_choice = strategy.choose_parity(match_history, opponent_id)
else:
    parity_choice = random.choice(valid_choices)
```

**Step 3: Configure in agents_config.json**

```json
{
  "metadata": {
    "strategy": "llm",
    "llm_model": "gpt-4"
  }
}
```

**Step 4: Set Environment Variable**

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

---

## 9. Adding New Game Types

See [Extensibility Guide](usability_extensibility.md#31-adding-new-game-types) for comprehensive documentation.

### Quick Reference

**Step 1: Define Game in games_registry.json**

```json
{
  "game_type": "rock_paper_scissors",
  "display_name": "Rock/Paper/Scissors",
  "supports_draw": true,
  "min_players": 2,
  "max_players": 2,
  "game_specific_config": {
    "valid_choices": ["rock", "paper", "scissors"]
  }
}
```

**Step 2: Implement Game Logic**

Create `agents/referee_REF01/games/rock_paper_scissors.py`:

```python
class RockPaperScissorsLogic:
    def determine_winner(self, choice_a, choice_b):
        # Implementation
        pass
```

**Step 3: Update Referee to Load Game**

Referees auto-discover games from `games_registry.json`.

**Step 4: Create League Config**

```bash
cp SHARED/config/leagues/league_2025_even_odd.json \
   SHARED/config/leagues/league_2025_rps.json

# Edit to set game_type: "rock_paper_scissors"
```

---

## 10. Debugging

### Debug Logging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Or edit .env
echo "LOG_LEVEL=DEBUG" >> .env

# Start agent with debug logging
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P01/main.py
```

### Analyzing Logs

```bash
# View real-time logs
tail -f SHARED/logs/agents/P01.log.jsonl | jq .

# Search for errors
grep "ERROR" SHARED/logs/agents/*.log.jsonl | jq '.message'

# Filter by event type
cat SHARED/logs/league/*/LM01.log.jsonl | jq 'select(.event_type == "MESSAGE_SENT")'

# Count messages by type
cat SHARED/logs/agents/P01.log.jsonl | jq -r '.message_type' | sort | uniq -c
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()

# Run agent (debugger will pause at breakpoint)
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P01/main.py
```

### Network Debugging

```bash
# Test agent health
curl -X GET http://localhost:8101/health

# Send test message
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "GAME_INVITATION",
    "params": {...}
  }'

# Monitor network traffic (macOS)
sudo tcpdump -i lo0 -A 'port 8101'
```

---

## 11. Contributing

### Contribution Workflow

1. **Fork Repository**
2. **Create Feature Branch**: `git checkout -b feature/your-feature`
3. **Make Changes**: Follow code style standards
4. **Write Tests**: Maintain 85%+ coverage
5. **Run Quality Checks**: black, flake8, mypy, pytest
6. **Commit**: Use [Conventional Commits](https://www.conventionalcommits.org/)
7. **Push**: `git push origin feature/your-feature`
8. **Create Pull Request**: On GitHub with description

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:
```
feat(protocol): add tournament bracket message types
fix(referee): handle timeout during parity choice correctly
docs(readme): update installation instructions
test(sdk): add tests for retry with circuit breaker
```

### Code Review Checklist

- [ ] Code follows style guide (black, flake8)
- [ ] All tests pass (`pytest tests/`)
- [ ] Test coverage ≥85%
- [ ] Docstrings added for public functions
- [ ] Config changes documented
- [ ] No secrets or hardcoded credentials
- [ ] PROGRESS_TRACKER.md updated if applicable

---

## 12. Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'league_sdk'`

**Cause**: SDK not installed or PYTHONPATH not set.

**Solution**:
```bash
# Option 1: Install SDK
pip install -e SHARED/league_sdk

# Option 2: Set PYTHONPATH
export PYTHONPATH=SHARED:$PYTHONPATH
```

#### Issue: `Address already in use (port 8101)`

**Cause**: Another process using the port.

**Solution**:
```bash
# Find process
lsof -i :8101

# Kill process
kill -9 <PID>

# Or change port
python3 main.py --port 8105
```

#### Issue: `Config file not found`

**Cause**: Wrong working directory.

**Solution**:
```bash
# Verify current directory
pwd
# Should be: /path/to/LLM_Agent_Orchestration_HW7

# Navigate to project root
cd /path/to/LLM_Agent_Orchestration_HW7
```

#### Issue: `Pydantic ValidationError`

**Cause**: Config file doesn't match schema.

**Solution**:
```bash
# Validate config
PYTHONPATH=SHARED:$PYTHONPATH python3 -c "
from league_sdk.config_loader import load_system_config
config = load_system_config('SHARED/config/system.json')
print('✅ Config valid')
"
```

#### Issue: Tests fail with import errors

**Cause**: PYTHONPATH not set for tests.

**Solution**:
```bash
# Always use PYTHONPATH for tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v
```

---

## Summary

This developer guide covers:

- ✅ **Two Installation Methods**: Clone + venv (development) and wheel/tarball (production)
- ✅ **Project Structure**: Complete directory tree with explanations
- ✅ **Development Workflow**: Code-test-commit cycle
- ✅ **Running the System**: Individual agents and full league
- ✅ **Testing**: Quick reference (see testing_guide.md for details)
- ✅ **Code Quality**: Automated checks with black, flake8, mypy
- ✅ **Adding New Agents**: Step-by-step guides with examples
- ✅ **Adding New Game Types**: Extension point documentation
- ✅ **Debugging**: Logging, network, Python debugger
- ✅ **Contributing**: Workflow, commit format, code review
- ✅ **Troubleshooting**: Common issues and solutions

For more information:
- [Configuration Guide](configuration.md) - All config files explained
- [Testing Guide](testing_guide.md) - Comprehensive testing documentation
- [Extensibility Guide](usability_extensibility.md) - ISO/IEC 25010 analysis
- [Architecture Documentation](architecture.md) - System design

**Happy Coding!** 🚀
