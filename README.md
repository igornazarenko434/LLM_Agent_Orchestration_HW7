# 🎮 Even/Odd League: Multi-Agent Orchestration System

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Protocol](https://img.shields.io/badge/protocol-league.v2-green.svg)](docs/protocol_spec.md)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](htmlcov/index.html)
[![Tests Passing](https://img.shields.io/badge/tests-209%20passing-success.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A Production-Ready Multi-Agent System Demonstrating Advanced Distributed Computing Patterns**

[Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#-technical-architecture) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Executive Summary](#-executive-summary)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Results & Achievements](#-results--achievements)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Technical Architecture](#-technical-architecture)
- [Testing](#-testing)
- [Quality Standards](#-quality-standards)
- [Troubleshooting](#-troubleshooting)
- [Research & Analysis](#-research--analysis)
- [Quality Standards Summary](#-quality-standards-summary)
- [Project Status](#-project-status)
- [Extensibility & Maintenance](#-extensibility--maintenance)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License & Attribution](#-license--attribution)
- [Screenshots](#-screenshots)
- [Support & Contact](#-support--contact)
- [Acknowledgments](#-acknowledgments)

---

## 📋 Executive Summary

The **Even/Odd League** is a sophisticated multi-agent orchestration platform where autonomous AI agents compete in strategic games using the **Model Context Protocol (MCP)**. This system showcases production-grade distributed computing patterns including:

- ✅ **Protocol-Driven Communication:** JSON-RPC 2.0 over HTTP with league.v2 specification
- ✅ **Resilience Engineering:** Exponential backoff retry, circuit breaker pattern, timeout enforcement
- ✅ **Scalable Architecture:** Designed to support 10,000+ concurrent agents
- ✅ **Comprehensive Testing:** 209 tests with 85% code coverage
- ✅ **Structured Observability:** JSON Lines logging with correlation IDs

**Current Status:** Core System Complete (70% of missions) • All Primary Agents Operational • Production-Grade SDK • Research Notebook Complete

---

## 🎯 Problem Statement

Building distributed multi-agent systems presents several critical challenges:

1. **Protocol Compliance:** Ensuring all agents communicate using consistent message formats
2. **Resilience:** Handling network failures, timeouts, and transient errors gracefully
3. **Scalability:** Supporting thousands of concurrent agents without performance degradation
4. **Observability:** Tracking request flows across multiple agents with structured logging
5. **Data Integrity:** Maintaining consistent state across distributed components

The Even/Odd League addresses these challenges through:
- **Shared SDK Design:** Centralized protocol models, configuration, and utilities
- **Retry Policies:** Exponential backoff with circuit breaker for fault tolerance
- **Repository Pattern:** Atomic file operations ensuring data consistency
- **Structured Logging:** JSONL format with conversation IDs for distributed tracing
- **Configuration Management:** Environment-aware settings with validation

---

## ✨ Key Features

### Protocol & Communication
- 🔌 **18 Message Types:** Complete league.v2 protocol implementation
- 🔐 **Authentication:** Token-based auth with 32-character cryptographic tokens
- 📡 **JSON-RPC 2.0:** Standard request/response format over HTTP
- ⏱️ **Timeout Enforcement:** 5s, 10s, 30s timeouts per operation type
- 🔄 **Conversation Tracking:** Unique IDs for multi-message request flows

### Resilience & Reliability
- 🔁 **Exponential Backoff:** 2s → 4s → 8s retry delays (max 3 retries)
- 🛡️ **Circuit Breaker:** Prevents cascading failures (5 failure threshold, 60s reset)
- ⚠️ **Error Classification:** 18 error codes with retryable vs. terminal categorization
- 📊 **Retry Metrics:** Track success/failure rates for monitoring

### Data & Configuration
- 💾 **Atomic Writes:** Temp file + rename pattern for data integrity
- 🗄️ **Repository Pattern:** Standings, rounds, matches, player history
- ⚙️ **Environment Overrides:** 15+ config settings via env vars
- ✅ **Schema Validation:** Pydantic models for all configs and messages
- 🗑️ **Data Retention:** Automated cleanup with configurable retention periods
- 📦 **Archive Strategy:** Gzip compression (80% reduction) before deletion
- ⏰ **Scheduled Cleanup:** Daily automated cleanup at 2 AM UTC
- 🛡️ **Data Protection:** In-progress matches and active logs never deleted

### Observability
- 📝 **Structured Logging:** JSON Lines format for log analysis tools
- 🔍 **Correlation IDs:** Track requests across agent boundaries
- 📂 **Automatic Organization:** Separate logs for agents, leagues, system
- 🔄 **Log Rotation:** 100MB files, 5 backup generations

### Testing & Quality
- ✅ **209 Tests Passing:** Unit, integration, protocol compliance
- 📊 **85% Coverage:** Comprehensive test suite for SDK and agents
- 🔬 **Test Fixtures:** Reusable test utilities and mock data
- 🎯 **Pytest Markers:** unit, integration, e2e, slow, protocol

---

## 🏆 Results & Achievements

### Completed Milestones

| Milestone | Status | Evidence |
|-----------|--------|----------|
| **Foundation Quality Gate (QG-1)** | ✅ Complete | 209 tests, 85% coverage, SDK operational |
| **Protocol Implementation** | ✅ Complete | 18/18 message types, 18/18 error codes |
| **SDK Infrastructure** | ✅ Complete | Protocol, config, logging, retry, repositories, cleanup, queue processor, method aliases |
| **Player Agents (P01-P04)** | ✅ Complete | MCP server, 3 tools, registration flow |
| **Referee Agents (REF01-REF02)** | ✅ Complete | Match conductor, timeout enforcement, Even/Odd logic, registration (M7.5-M7.8) |
| **League Manager (LM01)** | ✅ Complete | Registration, scheduler, standings, orchestration (M7.9-M7.13) |
| **Research Notebook (M5.5)** | ✅ Complete | 14 cells, 3 LaTeX formulas, 7 plots, statistical analysis |
| **Configuration System** | ✅ Complete | System, agents, league, game configs |

### Metrics Dashboard

```
📊 PROJECT HEALTH METRICS
┌─────────────────────────────┬──────────┬────────┐
│ Metric                      │ Current  │ Target │
├─────────────────────────────┼──────────┼────────┤
│ Test Coverage               │ 85%      │ ≥85%   │
│ Tests Passing               │ 209/209  │ 100%   │
│ Protocol Compliance         │ 100%     │ 100%   │
│ Config Validation           │ 100%     │ 100%   │
│ Missions Complete           │ 33/47    │ 47     │
│ Code Quality (Flake8)       │ Pass     │ Pass   │
└─────────────────────────────┴──────────┴────────┘
```

### Performance Characteristics
- **Response Time:** <500ms mean across all message types
- **Retry Success Rate:** ~90% for transient failures
- **Data Integrity:** 100% (atomic writes)
- **Log Format Compliance:** 100% valid JSONL
- **Timeout Compliance:** 100% within SLA

---

## 📁 Project Structure

```
LLM_Agent_Orchestration_HW7/
├── 📦 SHARED/                          # Shared resources for all agents
│   ├── league_sdk/                     # Core SDK package (installed via pip)
│   │   ├── __init__.py                 # Public API exports
│   │   ├── protocol.py                 # 18 message type models (891 lines)
│   │   ├── config_models.py            # Pydantic config schemas (458 lines)
│   │   ├── config_loader.py            # Load configs with env overrides (156 lines)
│   │   ├── repositories.py             # Data persistence layer (485 lines)
│   │   ├── logger.py                   # JSONL structured logging (403 lines)
│   │   ├── retry.py                    # Retry + Circuit Breaker (514 lines)
│   │   ├── queue_processor.py          # Thread-safe sequential queue (59 lines)
│   │   ├── method_aliases.py           # PDF compatibility layer (106 lines)
│   │   ├── cleanup.py                  # Data retention & cleanup (258 lines)
│   │   ├── utils.py                    # Utility functions (33 lines)
│   │   ├── setup.py                    # Package installation config
│   │   └── pyproject.toml              # Package metadata for league_sdk
│   ├── config/                         # Configuration files (JSON)
│   │   ├── system.json                 # Global system settings
│   │   ├── agents/                     # Agent registry
│   │   │   └── agents_config.json      # 7 agents (LM, 2 Refs, 4 Players)
│   │   ├── leagues/                    # League-specific configs
│   │   │   └── league_2025_even_odd.json
│   │   ├── games/                      # Game type definitions
│   │   │   └── games_registry.json     # Even/Odd game rules
│   │   └── defaults/                   # Default config templates
│   │       ├── player.json
│   │       └── referee.json
│   ├── data/                           # Runtime data (git-ignored)
│   │   ├── leagues/                    # League standings, rounds
│   │   ├── matches/                    # Match records
│   │   └── players/                    # Player history
│   ├── logs/                           # Structured logs (git-ignored)
│   │   ├── agents/                     # Per-agent logs (P01.log.jsonl, etc.)
│   │   ├── league/                     # League-level logs
│   │   └── system/                     # System-level logs
│   ├── archive/                        # Archived data (compressed, git-ignored)
│   │   ├── logs/                       # Old logs (gzipped)
│   │   ├── matches/                    # Old match records (gzipped)
│   │   ├── players/                    # Player history archives
│   │   └── leagues/                    # League rounds archives
│   └── scripts/                        # Utility scripts
│       └── cleanup_data.py             # Manual cleanup script (273 lines)
├── 🤖 agents/                          # Agent implementations
│   ├── base/                           # Shared base agent
│   │   ├── __init__.py
│   │   └── agent_base.py               # BaseAgent class (212 lines)
│   ├── league_manager/                 # League Manager agent (LM01) ✅ COMPLETE
│   │   ├── __init__.py                 # Package exports
│   │   ├── server.py                   # MCP server + orchestration (2075 lines) M7.9-M7.13
│   │   └── main.py                     # Entry point
│   ├── referee_REF01/                  # Referee agent #1 ✅ COMPLETE
│   │   ├── __init__.py                 # Package exports
│   │   ├── server.py                   # MCP server + registration (1008 lines) M7.5-M7.8
│   │   ├── match_conductor.py          # Match orchestration logic
│   │   └── main.py                     # Entry point
│   ├── referee_REF02/                  # Referee agent #2 ✅ COMPLETE
│   │   ├── __init__.py                 # Package exports
│   │   ├── server.py                   # Same implementation as REF01
│   │   └── main.py                     # Entry point with different ID
│   ├── player_P01/                     # Player agent #1 (Reference impl) ✅ COMPLETE
│   │   ├── __init__.py
│   │   ├── server.py                   # MCP server + JSON-RPC dispatch (367 lines)
│   │   ├── handlers.py                 # Tool handlers (132 lines)
│   │   └── main.py                     # Entry point
│   ├── player_P02/                     # Player agent #2 ✅ COMPLETE
│   │   ├── __init__.py
│   │   └── main.py                     # Reuses PlayerAgent class
│   ├── player_P03/                     # Player agent #3 ✅ COMPLETE
│   │   ├── __init__.py
│   │   └── main.py                     # Reuses PlayerAgent class
│   └── player_P04/                     # Player agent #4 ✅ COMPLETE
│       ├── __init__.py
│       └── main.py                     # Reuses PlayerAgent class
├── 🧪 tests/                           # Test suite (209 tests, 85% coverage)
│   ├── conftest.py                     # Pytest fixtures and configuration
│   ├── unit/                           # Unit tests for SDK and agents
│   │   ├── test_sdk/
│   │   │   ├── test_protocol_models.py     # 60 tests - Protocol validation
│   │   │   ├── test_logger.py              # 35 tests - Logging infrastructure
│   │   │   ├── test_retry.py               # 34 tests - Retry & circuit breaker
│   │   │   ├── test_repositories.py        # 33 tests - Data persistence
│   │   │   ├── test_cleanup.py             # 17 tests - Data retention & cleanup
│   │   │   ├── test_config_models.py       # 16 tests - Config schemas
│   │   │   ├── test_config_loader.py       # Config loading + env overrides
│   │   │   └── test_games_registry.py      # 8 tests - Game definitions
│   │   ├── test_agents/
│   │   │   ├── test_agent_base.py          # BaseAgent functionality
│   │   │   └── test_player_server.py       # PlayerAgent MCP server
│   │   ├── test_league_manager/            # League Manager tests ✅ NEW
│   │   │   ├── test_registration.py        # Registration handlers
│   │   │   ├── test_scheduler.py           # Round-robin scheduler
│   │   │   └── test_standings.py           # Standings calculator
│   │   └── test_referee_agent/             # Referee tests ✅ NEW
│   │       ├── test_match_conductor.py     # Match orchestration
│   │       ├── test_timeout_enforcement.py # Timeout handling
│   │       └── test_registration.py        # Referee registration
│   ├── integration/                    # Integration tests
│   │   ├── test_player_registration.py # Player registration flow
│   │   └── test_referee_integration.py # Referee integration tests ✅ NEW
│   ├── e2e/                            # End-to-end tests ✅ NEW
│   └── protocol_compliance/            # Protocol compliance tests ✅ NEW
├── 📚 doc/                             # Documentation
│   ├── README.md                       # Documentation index ✅ NEW
│   ├── research_notes/
│   │   ├── mcp_protocol.md             # MCP research and analysis
│   │   ├── experiments.ipynb           # Research notebook (M5.5) ✅ NEW
│   │   ├── experiments.html            # Pre-rendered HTML (601 KB) ✅ NEW
│   │   ├── README.md                   # Notebook documentation ✅ NEW
│   │   ├── plot1_strategy_comparison.png ✅ NEW
│   │   ├── plot2_timeout_impact.png    ✅ NEW
│   │   └── plot3_4_retry_outcomes.png  ✅ NEW
│   ├── game_rules/
│   │   └── even_odd.md                 # Even/Odd game specification
│   ├── algorithms/
│   │   └── round_robin.md              # Round-robin scheduling algorithm
│   ├── reference/                      # Specs, APIs, error codes ✅ NEW
│   │   ├── api_reference.md            # MCP tools and message formats
│   │   ├── error_codes_reference.md    # E001–E018 reference
│   │   ├── error_handling_strategy.md  # Retry, circuit breaker guidance
│   │   └── data_retention_policy.md    # Data lifecycle & cleanup (22KB)
│   ├── architecture/                   # Architecture docs ✅ NEW
│   │   ├── thread_safety.md            # Concurrency model
│   │   └── adr/                        # Architecture Decision Records
│   ├── plans/                          # Execution & verification plans ✅ NEW
│   │   ├── system_integration_verification_plan.md # Integration testing guide
│   │   └── M6.1_M6.2_IMPLEMENTATION_PLAN_v2.md     # CLI + ops plan
│   ├── guides/
│   │   └── HOW_QUALITY_WORKS.md        # Quality workflow
│   ├── usability_analysis.md           # M6.6 usability review ✅ NEW
│   └── prompt_log/                     # Implementation prompt logs
│       ├── mission_2_implementation_prompt.md
│       ├── config_layer_mission_3.0-3.3_prompt.md
│       ├── mission_4_0_4_1_implementation_prompt.md
│       └── league_manager_implementation_prompt.md ✅ NEW
├── 📄 Configuration Files
│   ├── .env.example                    # Environment template (61 lines)
│   ├── .gitignore                      # Git exclusions (90 lines)
│   ├── pytest.ini                      # Pytest configuration
│   ├── mypy.ini                        # Type checking config
│   ├── .flake8                         # Linting config
│   ├── requirements.txt                # Python dependencies (with research packages)
│   ├── pyproject.toml                  # Project metadata
│   ├── PRD_EvenOddLeague.md            # Product Requirements Document (102KB)
│   ├── PROGRESS_TRACKER.md             # Mission tracking and status
│   └── guides/
│       └── HOW_QUALITY_WORKS.md       # Quality standards workflow guide
└── 📜 Project Documentation
    ├── README.md                       # This file
    ├── INSTALL.md                      # Comprehensive installation guide ✅ NEW
    ├── QUICK_START_NOTEBOOK.md         # Notebook quick start guide ✅ NEW
    ├── verify_installation.py          # Installation verification script ✅ NEW
    └── LICENSE                         # MIT License
```

### Key Directories

- **[SHARED/league_sdk/](SHARED/league_sdk/)**: Installable Python package with protocol, config, logging, retry utilities
- **[SHARED/config/](SHARED/config/)**: JSON configuration files validated by Pydantic models
- **[agents/](agents/)**: Agent implementations (League Manager, Referees, Players)
- **[tests/](tests/)**: Comprehensive test suite with pytest fixtures
- **[doc/](doc/)**: Research notes, game rules, algorithms, implementation logs

---

## 🚀 Installation

### Prerequisites

Ensure you have the following installed on your system:

1. **Python 3.10+** (tested on 3.10, 3.11, 3.12, 3.13, 3.14)
   ```bash
   python3 --version  # Should show 3.10.0 or higher
   ```

2. **Virtual Environment** (recommended)
   ```bash
   python3 -m venv venv
   ```

3. **Git** (for version control)
   ```bash
   git --version
   ```

### Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-org/even-odd-league.git
cd even-odd-league
```

#### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Upgrade pip
```bash
pip install --upgrade pip
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- **Core Framework:** FastAPI, Uvicorn, Pydantic
- **HTTP Client:** Requests, HTTPX
- **Testing:** Pytest, pytest-cov, pytest-asyncio, pytest-timeout
- **Code Quality:** Black, Flake8, Mypy, Pylint, Radon, Pydocstyle

#### 5. Install League SDK (Editable Mode)
```bash
pip install -e SHARED/league_sdk
```

This installs the `league-sdk` package in editable mode, allowing live code changes.

#### 6. Verify Installation
```bash
python3 -c "from league_sdk import JsonLogger, retry_with_backoff, CircuitBreaker; print('✅ SDK Imported Successfully')"
```

Expected output: `✅ SDK Imported Successfully`

#### 7. Create Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` with your settings (optional, defaults work for local development).

#### 8. Verify Configuration Files
```bash
ls -la SHARED/config/
```

Expected files:
- `system.json` - Global system settings
- [agents/agents_config.json](agents/agents_config.json) - Agent registry
- `leagues/league_2025_even_odd.json` - League config
- `games/games_registry.json` - Game definitions

#### 9. Create Data Directories
```bash
mkdir -p SHARED/data/{leagues,matches,players}
mkdir -p SHARED/logs/{agents,league,system}
mkdir -p SHARED/archive/{logs,matches,players,leagues}
```

#### 10. Run Tests to Validate Setup
```bash
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v --cov=SHARED/league_sdk --cov=agents --cov-report=term
```

Expected: `209 passed` with `85% coverage`

#### 11. Install Pre-commit Hooks (Optional, Recommended)
```bash
pre-commit install
```

This enables automatic code formatting and linting before each commit.

#### 12. Verify Port Availability
```bash
# Check if required ports are available
lsof -i :8000  # League Manager
lsof -i :8001  # Referee 1
lsof -i :8002  # Referee 2
lsof -i :8101  # Player 1
lsof -i :8102  # Player 2
lsof -i :8103  # Player 3
lsof -i :8104  # Player 4
```

If any ports are in use, either stop the conflicting service or update [SHARED/config/system.json](SHARED/config/system.json).

### Docker Installation (Alternative)

```bash
# Build Docker image
docker build -t even-odd-league:latest .

# Run container
docker run -p 8000-8104:8000-8104 even-odd-league:latest
```

**Note:** Docker support is planned for future releases.

---

## 🎮 Quick Start

### Starting a Player Agent

```bash
# Terminal 1: Start Player P01
cd agents/player_P01
PYTHONPATH=../../SHARED:$PYTHONPATH python3 main.py
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8101 (Press CTRL+C to quit)
```

### Testing Player Agent Health

```bash
# Terminal 2: Check health endpoint
curl -X GET http://localhost:8101/health
```

Expected response:
```json
{"status": "ok"}
```

### Sending a Test Message (MCP Tool Call)

```bash
# Example: GAME_INVITATION
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "GAME_INVITATION",
    "params": {
      "protocol": "league.v2",
      "message_type": "GAME_INVITATION",
      "sender": "referee:REF01",
      "timestamp": "2025-01-15T10:30:00Z",
      "conversation_id": "conv-abc123",
      "auth_token": "test-token-32-characters-long",
      "league_id": "league_2025_even_odd",
      "match_id": "R1M1",
      "game_type": "even_odd",
      "player_id": "P01",
      "opponent_id": "P02",
      "opponent_endpoint": "http://localhost:8102/mcp"
    }
  }'
```

Expected response (GAME_JOIN_ACK):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P01",
    "timestamp": "2025-01-15T10:30:01Z",
    "conversation_id": "conv-abc123",
    "auth_token": "test-token-32-characters-long",
    "match_id": "R1M1",
    "player_id": "P01",
    "arrival_timestamp": "2025-01-15T10:30:01Z",
    "accept": true
  }
}
```

### Running Multiple Agents

```bash
# Start all player agents in separate terminals
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P01/main.py &
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P02/main.py &
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P03/main.py &
PYTHONPATH=SHARED:$PYTHONPATH python3 agents/player_P04/main.py &
```

### Stopping Agents

```bash
# Graceful shutdown (CTRL+C in each terminal)
# Or kill all:
pkill -f "python3.*player.*main.py"
```

---

## 🎛️ Usage

### CLI Usage

All agents expose a consistent CLI with accessibility and automation options.

#### Common Arguments (All Agents)

| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--help` | Show usage information | - | `--help` |
| `--version` | Show agent version | - | `--version` |
| `--log-level` | Set logging level | INFO | `--log-level DEBUG` |
| `--verbose` | Verbose output | false | `--verbose` |
| `--quiet` | Minimal output (errors only) | false | `--quiet` |
| `--plain` | Plain text output (screen reader friendly) | false | `--plain` |
| `--json` | JSON output (automation) | false | `--json` |
| `--config` | Custom config path (see notes below) | SHARED/config | `--config /path/to/config` |

Notes:
- Player agents use `--config` as a config base directory override.
- League Manager/Referee expose `--config` for compatibility; current behavior
  uses default config paths.

#### Agent-Specific Examples

```bash
# League Manager
python -m agents.league_manager.main \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8000 \
  --log-level INFO

# Referee
python -m agents.referee_REF01.main \
  --referee-id REF01 \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8001 \
  --log-level INFO

# Player
python -m agents.player_P01.main \
  --player-id P01 \
  --league-id league_2025_even_odd \
  --host localhost \
  --port 8101 \
  --log-level INFO
```

### Accessibility

All agents and scripts support `--plain` for screen readers and `--json` for
automation.

```bash
python -m agents.player_P01.main --plain
./scripts/check_health.sh --plain
./scripts/query_standings.sh --json
```

### Exit Codes (Agents)

| Code | Meaning | Examples |
|------|---------|----------|
| 0 | Success | Agent running normally |
| 1 | Configuration error | E002, E008, E011 |
| 2 | Network error | E016, E018 |
| 3 | Authentication error | E003, E004, E012 |
| 4 | Runtime error | E015 |

See [doc/reference/error_codes_reference.md](doc/reference/error_codes_reference.md) for detailed error definitions.

---

### Operational Scripts

#### Core Operations

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/start_league.sh` | Start all agents (LM + 2 refs + 4 players) | `./scripts/start_league.sh` |
| `scripts/stop_league.sh` | Graceful shutdown of all agents | `./scripts/stop_league.sh` |
| `scripts/check_health.sh` | Health check all endpoints | `./scripts/check_health.sh` |
| `scripts/backup_data.sh` | Backup SHARED/data and SHARED/logs | `./scripts/backup_data.sh` |
| `scripts/restore_data.sh` | Restore from backup | `./scripts/restore_data.sh data_20251227_143022` |

#### Verification & Debug Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/verify_configs.sh` | Validate config files | `./scripts/verify_configs.sh` |
| `scripts/check_registration_status.sh` | Show LM registration state | `./scripts/check_registration_status.sh` |
| `scripts/trigger_league_start.sh` | Start league orchestration | `./scripts/trigger_league_start.sh` |
| `scripts/query_standings.sh` | Query standings | `./scripts/query_standings.sh --plain` |
| `scripts/view_match_state.sh` | Inspect match state | `./scripts/view_match_state.sh R1M1 --referee-id REF01 --sender player:P01 --auth-token <token>` |
| `scripts/analyze_logs.sh` | Filter log output | `./scripts/analyze_logs.sh MESSAGE_SENT` |
| `scripts/cleanup_old_data.sh` | Cleanup old backups/logs | `./scripts/cleanup_old_data.sh --dry-run` |

#### Script Options

All scripts support:
- `--plain` (screen reader friendly)
- `--json` (automation)
- `--help`

Some scripts additionally support:
- `--verbose` (e.g., `verify_configs.sh`)
- `--quiet` (e.g., `check_health.sh`, `start_league.sh`)
- `--dry-run`, `--force` (backup/restore/cleanup scripts)

#### Example Workflow

```bash
./scripts/verify_configs.sh
./scripts/start_league.sh
./scripts/check_health.sh
./scripts/check_registration_status.sh
./scripts/trigger_league_start.sh
./scripts/query_standings.sh
./scripts/view_match_state.sh R1M1 --referee-id REF01 --sender player:P01 --auth-token <token>
./scripts/analyze_logs.sh MESSAGE_SENT
./scripts/backup_data.sh post_league_$(date +%Y%m%d)
./scripts/stop_league.sh
```

#### Log and Data Paths

- Structured logs: [SHARED/logs/league/<league_id>/*.log.jsonl](SHARED/logs/league/)
- Agent stdout logs: [SHARED/logs/agents/*.log](SHARED/logs/agents/)
- Data outputs: [SHARED/data/](SHARED/data/)

### Player Agent Registration Flow

```python
from agents.player_P01.server import PlayerAgent

# 1. Create player agent instance
agent = PlayerAgent(
    agent_id="P01",
    league_id="league_2025_even_odd",
    host="localhost",
    port=8101
)

# 2. Start the MCP server
agent.start(run_in_thread=False)  # Blocks until shutdown

# 3. Register with League Manager (async)
import asyncio
response = asyncio.run(agent.send_registration_request())
print(response)
# {
#   "protocol": "league.v2",
#   "message_type": "LEAGUE_REGISTER_RESPONSE",
#   "status": "ACCEPTED",
#   "player_id": "P01",
#   "auth_token": "generated-32-char-token-here"
# }
```

### Using SDK Components Directly

#### Protocol Models
```python
from league_sdk.protocol import (
    GameInvitation,
    GameJoinAck,
    ChooseParityCall,
    ChooseParityResponse,
    ErrorCode
)

# Create a game invitation
invitation = GameInvitation(
    sender="referee:REF01",
    timestamp="2025-01-15T10:00:00Z",
    conversation_id="conv-123",
    auth_token="token",
    league_id="league_2025_even_odd",
    match_id="R1M1",
    game_type="even_odd",
    player_id="P01",
    opponent_id="P02",
    opponent_endpoint="http://localhost:8102/mcp"
)

# Validate automatically via Pydantic
print(invitation.model_dump_json(indent=2))
```

#### Configuration Loading
```python
from league_sdk.config_loader import load_system_config, load_league_config

# Load system config with environment overrides
system_config = load_system_config("SHARED/config/system.json")
print(f"Timeout for parity choice: {system_config.timeouts.parity_choice_sec}s")

# Load league config
league_config = load_league_config("SHARED/config/leagues/league_2025_even_odd.json")
print(f"Win points: {league_config.scoring.points_for_win}")
```

#### Structured Logging
```python
from league_sdk.logger import JsonLogger

# Create logger for an agent
logger = JsonLogger(
    component="player:P01",
    agent_id="P01",
    league_id="league_2025_even_odd",
    min_level="INFO"
)

# Log events
logger.info("Agent started", event_type="AGENT_STARTUP", version="1.0.0")
logger.log_message_sent("GAME_JOIN_ACK", recipient="referee:REF01", match_id="R1M1")
logger.error("Timeout occurred", event_type="TIMEOUT_ERROR", match_id="R1M1")
```

#### Retry with Exponential Backoff
```python
from league_sdk.retry import retry_with_backoff, call_with_retry, CircuitBreaker
import requests

# Decorator approach
@retry_with_backoff(max_retries=3)
def fetch_data():
    response = requests.get("http://localhost:8000/api/data")
    response.raise_for_status()
    return response.json()

# Direct call approach
result = call_with_retry(
    endpoint="http://localhost:8000/mcp",
    method="LEAGUE_REGISTER_REQUEST",
    params={...},
    timeout=10,
    circuit_breaker=CircuitBreaker()
)
```

#### Data Repositories
```python
from league_sdk.repositories import StandingsRepository, PlayerHistoryRepository

# Standings management
standings_repo = StandingsRepository("league_2025_even_odd")
standings_repo.update_player("P01", result="WIN", points=3)
current_standings = standings_repo.load()

# Player history
history_repo = PlayerHistoryRepository("P01")
history_repo.add_match(
    match_id="R1M1",
    league_id="league_2025_even_odd",
    round_id=1,
    opponent_id="P02",
    result="WIN",
    points=3,
    details={"parity_choice": "even", "drawn_number": 4}
)
```

#### Data Retention & Cleanup

**Automated Cleanup (League Manager):**
```python
from league_sdk.cleanup import run_full_cleanup

# Run full cleanup (all data types)
results = await run_full_cleanup(logger=logger)

# Print statistics
for data_type, stats in results.items():
    print(f"{data_type}: {stats.files_deleted} files deleted, {stats.mb_freed:.2f} MB freed")
```

**Manual Cleanup Script:**
```bash
# Preview what would be deleted (dry-run)
python SHARED/scripts/cleanup_data.py --dry-run

# Execute full cleanup
python SHARED/scripts/cleanup_data.py --execute

# Cleanup specific data type
python SHARED/scripts/cleanup_data.py --execute --type logs

# Custom retention period (override config)
python SHARED/scripts/cleanup_data.py --execute --type matches --retention-days 180

# Verbose output with statistics
python SHARED/scripts/cleanup_data.py --execute --verbose
```

**Using Cleanup Functions Directly:**
```python
from league_sdk.cleanup import (
    cleanup_old_logs,
    archive_old_matches,
    prune_player_histories,
    prune_league_rounds,
    get_retention_config
)

# Get current retention configuration
config = get_retention_config()
print(f"Logs retention: {config['logs_retention_days']} days")

# Cleanup old logs (rotated logs only, active logs preserved)
stats = await cleanup_old_logs(retention_days=30)
print(f"Deleted {stats.files_deleted} old log files")

# Archive old completed matches (in-progress matches preserved)
stats = await archive_old_matches(retention_days=365)
print(f"Archived {stats.files_archived} matches, freed {stats.mb_freed:.2f} MB")

# Prune player history (removes old match records, preserves aggregate stats)
stats = await prune_player_histories(retention_days=365)
print(f"Pruned {stats.files_deleted} old match records from player histories")

# Prune league rounds (removes old round records)
stats = await prune_league_rounds(retention_days=365)
print(f"Pruned {stats.files_deleted} old rounds")
```

**Player Agent Cleanup (on Shutdown):**
```python
# Automatically called when player shuts down
async def cleanup_player_data(self):
    """Archive player history before shutdown."""
    config = get_retention_config()
    if config.get("archive_enabled", True):
        # Archive to SHARED/archive/players/{player_id}/history_shutdown.json.gz
        # Logged automatically
```

**Configuration-Driven:**
All retention periods are configurable in [SHARED/config/system.json](SHARED/config/system.json) under `data_retention` section. Change retention periods without code changes!

**Safety Guarantees:**
- ✅ IN_PROGRESS matches never deleted
- ✅ Active logs never deleted (only rotated logs)
- ✅ Aggregate player stats always preserved
- ✅ Standings data retained permanently
- ✅ Atomic operations prevent data corruption

---

## ⚙️ Configuration

### System Configuration ([SHARED/config/system.json](SHARED/config/system.json))

```json
{
  "schema_version": "1.0.0",
  "protocol_version": "league.v2",
  "timeouts": {
    "registration_sec": 10,
    "game_join_ack_sec": 5,
    "parity_choice_sec": 30,
    "game_over_sec": 5,
    "match_result_sec": 10,
    "league_query_sec": 10,
    "generic_sec": 10
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "initial_delay_sec": 2.0,
    "max_delay_sec": 10.0,
    "retryable_errors": ["E001", "E005", "E006", "E009", "E014", "E015", "E016"]
  },
  "circuit_breaker": {
    "failure_threshold": 5,
    "reset_timeout_sec": 60
  },
  "security": {
    "auth_token_length": 32,
    "token_ttl_minutes": 1440,
    "require_auth": true
  },
  "network": {
    "host": "localhost",
    "league_manager_port": 8000,
    "referee_port_start": 8001,
    "referee_port_end": 8002,
    "player_port_start": 8101,
    "player_port_end": 9100
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "max_file_size_mb": 100,
    "backup_count": 5
  },
  "data_retention": {
    "enabled": true,
    "logs_retention_days": 30,
    "match_data_retention_days": 365,
    "player_history_retention_days": 365,
    "rounds_retention_days": 365,
    "standings_retention": "permanent",
    "cleanup_schedule_cron": "0 2 * * *",
    "archive_enabled": true,
    "archive_path": "SHARED/archive/",
    "archive_compression": "gzip"
  }
}
```

**Data Retention Configuration:**
- **enabled**: Master switch for automated cleanup
- **logs_retention_days**: Keep rotated logs for 30 days
- **match_data_retention_days**: Keep completed matches for 1 year
- **player_history_retention_days**: Keep individual match records for 1 year (stats preserved)
- **rounds_retention_days**: Keep league round records for 1 year
- **standings_retention**: "permanent" - never deleted
- **cleanup_schedule_cron**: Daily at 2 AM UTC
- **archive_enabled**: Compress and archive before deletion
- **archive_path**: Location for archived data
- **archive_compression**: "gzip" for 80% size reduction

### Environment Variables (`.env`)

Override any config value:

```bash
# Logging
LOG_LEVEL=DEBUG

# Network
BASE_HOST=localhost
LEAGUE_MANAGER_PORT=8000
PLAYER_PORT_START=8101

# Timeouts
TIMEOUT_PARITY_CHOICE=30
TIMEOUT_GAME_JOIN_ACK=5

# Retry Policy
RETRY_MAX_RETRIES=3
RETRY_INITIAL_DELAY_SEC=2.0

# League
LEAGUE_ID=league_2025_even_odd
```

### Agent Configuration ([SHARED/config/agents/agents_config.json](SHARED/config/agents/agents_config.json))

Register all agents:

```json
{
  "league_manager": {
    "agent_id": "LM01",
    "display_name": "League Manager",
    "endpoint": "http://localhost:8000/mcp",
    "port": 8000,
    "active": true
  },
  "referees": [
    {
      "agent_id": "REF01",
      "display_name": "Referee 01",
      "endpoint": "http://localhost:8001/mcp",
      "port": 8001,
      "game_types": ["even_odd"]
    }
  ],
  "players": [
    {
      "agent_id": "P01",
      "display_name": "Player 01",
      "endpoint": "http://localhost:8101/mcp",
      "port": 8101,
      "metadata": {"strategy": "random"}
    }
  ]
}
```

---

## 🏗️ Technical Architecture

Detailed diagrams and flows live in [doc/architecture.md](doc/architecture.md).

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         LEAGUE SYSTEM                           │
│  ┌───────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ League        │    │ Referee Agents  │    │ Player       │ │
│  │ Manager       │◄──►│ (REF01, REF02)  │◄──►│ Agents       │ │
│  │ (LM01)        │    │                 │    │ (P01-P04)    │ │
│  └───────────────┘    └─────────────────┘    └──────────────┘ │
│         ▲                      ▲                      ▲         │
│         │                      │                      │         │
│         └──────────────────────┴──────────────────────┘         │
│                    league.v2 Protocol                           │
│                   (JSON-RPC 2.0 over HTTP)                      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
         ┌─────────────────────────────────────────┐
         │         SHARED SDK (league_sdk)         │
         ├─────────────────────────────────────────┤
         │ • Protocol Models (18 message types)    │
         │ • Configuration Management              │
         │ • Data Repositories (atomic writes)     │
         │ • Structured Logging (JSONL)            │
         │ • Retry & Circuit Breaker               │
         │ • Data Retention & Cleanup (async)      │
         │ • Queue Processing (thread-safe)        │
         └─────────────────────────────────────────┘
                               │
                               ▼
         ┌─────────────────────────────────────────┐
         │        4-LAYER DATA ARCHITECTURE        │
         ├─────────────────────────────────────────┤
         │ SHARED/config/  │ Static configuration  │
         │ SHARED/data/    │ Runtime data          │
         │ SHARED/logs/    │ JSONL logs            │
         │ SHARED/archive/ │ Compressed archive    │
         └─────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Automated Cleanup    │
                    │ (Daily 2 AM UTC)     │
                    │ • Logs: 30 days      │
                    │ • Matches: 365 days  │
                    │ • Standings: ∞       │
                    └──────────────────────┘
```

### Agent Communication Flow

```
Player Registration Flow:
┌─────────┐                ┌──────────────┐
│ Player  │                │ League       │
│ (P01)   │                │ Manager      │
└────┬────┘                └──────┬───────┘
     │ LEAGUE_REGISTER_REQUEST   │
     │─────────────────────────► │
     │                            │ (Validate, assign ID)
     │ LEAGUE_REGISTER_RESPONSE  │
     │◄───────────────────────── │
     │ {player_id, auth_token}   │
     │                            │

Match Invitation Flow:
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Referee │    │ Player  │    │ Player  │
│ (REF01) │    │  (P01)  │    │  (P02)  │
└────┬────┘    └────┬────┘    └────┬────┘
     │ GAME_INVITATION  │           │
     │─────────────────►│           │
     │                  │           │
     │ GAME_JOIN_ACK    │           │
     │◄─────────────────│           │
     │                  │           │
     │ GAME_INVITATION  │           │
     │──────────────────────────────►│
     │                  │           │
     │ GAME_JOIN_ACK    │           │
     │◄──────────────────────────────│
```

### Protocol Layers

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Application** | Agent Logic | Business logic, game strategy |
| **Protocol** | league.v2 | Message validation, envelope structure |
| **Transport** | JSON-RPC 2.0 | Request/response format |
| **Network** | HTTP/REST | Agent communication over localhost |
| **Data** | File System | JSON files for config, data, logs |

### Design Patterns

1. **Repository Pattern:** Abstraction over data storage (standings, matches, history)
2. **Circuit Breaker:** Fault tolerance for network failures
3. **Retry Pattern:** Exponential backoff for transient errors
4. **Factory Pattern:** Agent creation via `build_player_agent()`
5. **Singleton Pattern:** Config loader reuses parsed configs
6. **Observer Pattern:** Event logging with structured data
7. **Strategy Pattern:** Different parity choice strategies (random, history-based, LLM)

---

## 🧪 Testing

### Running Tests

#### All Tests
```bash
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v
```

#### Unit Tests Only
```bash
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/unit/ -v
```

#### Integration Tests Only
```bash
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/integration/ -v
```

#### With Coverage Report
```bash
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ \
  --cov=SHARED/league_sdk \
  --cov=agents \
  --cov-report=term \
  --cov-report=html
```

Open coverage report: `open htmlcov/index.html`

#### Specific Test Markers
```bash
# Run only protocol tests
pytest -m protocol

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Structure

| Test Suite | Tests | Coverage | Focus |
|------------|-------|----------|-------|
| `test_protocol_models.py` | 60 | 94% | Message validation, JSON-RPC |
| `test_logger.py` | 35 | 99% | JSONL logging, rotation |
| `test_retry.py` | 34 | 86% | Retry, circuit breaker |
| `test_repositories.py` | 33 | 96% | Data persistence |
| `test_cleanup.py` | 17 | 90% | Data retention & cleanup ✅ |
| `test_config_models.py` | 16 | 99% | Config schemas |
| `test_agent_base.py` | 6 | 83% | BaseAgent functionality |
| `test_player_server.py` | 3 | 88% | PlayerAgent MCP server |
| **TOTAL** | **209** | **85%** | **Comprehensive coverage** |

### Test Examples

```python
# tests/unit/test_sdk/test_protocol_models.py
def test_game_invitation_validation():
    """Verify GAME_INVITATION message structure."""
    invitation = GameInvitation(
        sender="referee:REF01",
        timestamp="2025-01-15T10:00:00Z",
        conversation_id="conv-123",
        auth_token="token",
        league_id="league_2025_even_odd",
        match_id="R1M1",
        game_type="even_odd",
        player_id="P01",
        opponent_id="P02",
        opponent_endpoint="http://localhost:8102/mcp"
    )
    assert invitation.message_type == "GAME_INVITATION"
    assert invitation.protocol == "league.v2"

# tests/unit/test_sdk/test_cleanup.py
@pytest.mark.asyncio
async def test_cleanup_old_logs_deletes_old_files(temp_data_dir):
    """Verify cleanup deletes rotated logs older than retention period."""
    logs_dir = temp_data_dir / "logs" / "agents"

    # Create old rotated log (60 days old)
    old_log = logs_dir / "P01.log.jsonl.1"
    old_log.write_text("old log data")
    old_time = datetime.now(timezone.utc) - timedelta(days=60)
    os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))

    # Create active log (should not be deleted)
    active_log = logs_dir / "P01.log.jsonl"
    active_log.write_text("active log data")

    # Run cleanup
    stats = await cleanup_old_logs(retention_days=30, log_dir=logs_dir)

    # Old rotated log should be deleted
    assert not old_log.exists()
    # Active log should be preserved
    assert active_log.exists()
    assert stats.files_deleted == 1
```

---

## ⭐ Quality Standards

This project maintains production-ready code quality through automated tooling and comprehensive CI/CD enforcement.

### Code Quality Tools

| Tool | Purpose | Configuration | Status |
|------|---------|---------------|--------|
| **black** | Code formatting (line length: 104) | `pyproject.toml` | ✅ Enforced |
| **isort** | Import sorting (black profile) | `pyproject.toml` | ✅ Enforced |
| **flake8** | Linting (PEP 8 compliance) | `.flake8` | ✅ Enforced |
| **mypy** | Static type checking | `mypy.ini` | ✅ Enforced |
| **pylint** | Advanced linting | `pyproject.toml` | ✅ Configured |
| **pytest** | Testing with coverage (≥85%) | `pyproject.toml` | ✅ Enforced |

### Pre-Commit Hooks

Automated quality checks run before every commit:

#### Installation

```bash
# Install pre-commit (already in requirements.txt)
pip install pre-commit

# Install git hooks
pre-commit install

# Verify installation
pre-commit --version
```

#### Running Hooks

```bash
# Run all hooks on staged files (automatic on commit)
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
```

#### Configured Hooks

1. **trailing-whitespace** - Remove trailing whitespace
2. **end-of-file-fixer** - Ensure files end with newline
3. **check-yaml** - Validate YAML syntax
4. **check-json** - Validate JSON syntax
5. **detect-private-key** - Prevent committing secrets
6. **check-added-large-files** - Prevent large file commits
7. **black** - Auto-format code
8. **isort** - Sort imports
9. **flake8** - Lint code
10. **mypy** - Type checking

### Manual Quality Checks

Run quality checks manually before pushing:

```bash
# Format code (auto-fixes)
black agents SHARED tests
isort agents SHARED tests

# Linting (report only)
flake8 agents SHARED tests
pylint agents SHARED

# Type checking
mypy agents SHARED --config-file=mypy.ini

# All pre-commit hooks
pre-commit run --all-files

# Tests with coverage
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ \
  --cov=SHARED/league_sdk \
  --cov=agents \
  --cov-report=term-missing \
  --cov-fail-under=85
```

### CI/CD Pipeline

Every push and pull request triggers automated quality gates via GitHub Actions:

#### Quality Gates

1. ✅ **Code Formatting** - `black --check` (line length: 104)
2. ✅ **Import Sorting** - `isort --check-only`
3. ✅ **Linting** - `flake8` (zero violations)
4. ✅ **Type Checking** - `mypy` (no errors)
5. ✅ **Tests** - `pytest` with coverage gate (≥85%)

#### Workflow Configuration

See `.github/workflows/test.yml` for full pipeline configuration.

#### Build Status

- **Python Versions:** 3.10, 3.11
- **Test Coverage:** 85% (209 tests passing)
- **Quality Gates:** All passing ✅

### Contributing Guidelines

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Code style standards
- Testing requirements
- Commit message format (Conventional Commits)
- Branching strategy
- Pull request process
- Development setup

### Quality Verification

Verify all quality standards are met:

```bash
# 1. Format check
black --check agents SHARED tests

# 2. Lint check
flake8 agents SHARED tests

# 3. Type check
mypy agents SHARED

# 4. Run tests
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ --cov-fail-under=85

# Expected: All checks pass ✅
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Tests Fail with `ModuleNotFoundError: No module named 'league_sdk'`

**Cause:** SDK not installed or PYTHONPATH not set.

**Solution:**
```bash
# Option 1: Install SDK
pip install -e SHARED/league_sdk

# Option 2: Set PYTHONPATH
export PYTHONPATH=SHARED:$PYTHONPATH
pytest tests/ -v
```

#### 2. Port Already in Use (Address already in use)

**Cause:** Another process is using the required port.

**Solution:**
```bash
# Find the process
lsof -i :8101  # Replace with your port

# Kill the process
kill -9 <PID>

# Or change port in system.json
```

#### 3. Config File Not Found

**Cause:** Config files missing or wrong path.

**Solution:**
```bash
# Verify configs exist
ls -la SHARED/config/system.json
ls -la SHARED/config/agents/agents_config.json

# Check current working directory
pwd  # Should be project root
```

#### 4. Import Error: `cannot import name 'JsonLogger'`

**Cause:** SDK installation incomplete.

**Solution:**
```bash
# Reinstall SDK
pip uninstall league-sdk -y
pip install -e SHARED/league_sdk

# Verify
python3 -c "from league_sdk import JsonLogger; print('OK')"
```

#### 5. Pydantic Validation Errors

**Cause:** Config file doesn't match schema.

**Solution:**
```bash
# Validate config manually
python3 -c "
from league_sdk.config_loader import load_system_config
config = load_system_config('SHARED/config/system.json')
print('✅ Config valid')
"
```

#### 6. Logs Not Being Created

**Cause:** Log directories don't exist.

**Solution:**
```bash
# Create log directories
mkdir -p SHARED/logs/{agents,league,system}
```

#### 7. Timeout Errors in Tests

**Cause:** Tests running too slowly.

**Solution:**
```bash
# Increase pytest timeout
pytest tests/ --timeout=300

# Or skip slow tests
pytest -m "not slow"
```

#### 8. Data Retention / Cleanup Issues

**Issue 8.1:** Cleanup script fails with "Permission denied"

**Cause:** Insufficient permissions on archive directory.

**Solution:**
```bash
# Create archive directory with proper permissions
mkdir -p SHARED/archive/{logs,matches,players,leagues}
chmod -R 755 SHARED/archive
```

**Issue 8.2:** Old logs not being deleted

**Cause:** Data retention is disabled in config.

**Solution:**
```bash
# Check if retention is enabled
python3 -c "
from league_sdk.config_loader import load_system_config
config = load_system_config('SHARED/config/system.json')
print(f\"Retention enabled: {config.data_retention.enabled}\")
"

# Enable in system.json if needed
# Set "data_retention.enabled": true
```

**Issue 8.3:** Cleanup deletes in-progress matches

**Cause:** This should NEVER happen - safety checks prevent this.

**Solution:**
```bash
# Verify safety checks are working
pytest tests/unit/test_sdk/test_cleanup.py::test_archive_old_matches_skips_in_progress -v

# If test fails, report bug immediately
```

**Issue 8.4:** Archive files too large

**Cause:** Gzip compression not enabled.

**Solution:**
```bash
# Verify compression is enabled in system.json
# "data_retention.archive_compression": "gzip"

# Manually compress existing archives
find SHARED/archive -type f ! -name "*.gz" -exec gzip {} \;
```

### Debug Mode

Enable debug logging:

```bash
# Via environment variable
export LOG_LEVEL=DEBUG
python3 agents/player_P01/main.py

# Or edit .env
echo "LOG_LEVEL=DEBUG" >> .env
```

View logs:
```bash
# Real-time log monitoring
tail -f SHARED/logs/agents/P01.log.jsonl | jq .

# Search for errors
grep "ERROR" SHARED/logs/agents/*.log.jsonl | jq .
```

---

## 📊 Research & Analysis

### MCP Protocol Research

**Document:** [`doc/research_notes/mcp_protocol.md`](doc/research_notes/mcp_protocol.md)

Key findings:
- JSON-RPC 2.0 over HTTP/SSE/WebSocket
- Tool calling pattern: method, params, result/error
- Server-initiated requests via notifications
- Protocol negotiation via capabilities

### Round-Robin Algorithm

**Document:** [`doc/algorithms/round_robin.md`](doc/algorithms/round_robin.md)

Formula: `n * (n - 1) / 2` matches for `n` players

Example: 4 players = 6 matches across 3 rounds

### Even/Odd Game Rules

**Document:** [`doc/game_rules/even_odd.md`](doc/game_rules/even_odd.md)

- Players choose "even" or "odd"
- Random number drawn (1-10)
- Winner: Player whose choice matches parity
- Draw: Both players choose same parity

### Error Handling Strategy

**Document:** [`doc/reference/error_handling_strategy.md`](doc/reference/error_handling_strategy.md)

- 18 error codes (E001-E018)
- Retryable: E001, E005, E006, E009, E014, E015, E016
- Non-retryable: E002, E003, E004, E007-E013, E017-E018
- Circuit breaker: 5 failures → OPEN → 60s → HALF_OPEN

---

## 🎨 Quality Standards Summary

### Code Quality Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Test Coverage | ≥85% | 85% | ✅ Met |
| Flake8 Compliance | 100% | 100% | ✅ Pass |
| Mypy Type Checking | No errors | Minor warnings | 🟡 Good |
| Cyclomatic Complexity | <10 | <8 average | ✅ Excellent |
| Code Duplication | <5% | <3% | ✅ Excellent |
| Docstring Coverage | 100% | ~95% | 🟡 Very Good |

### Protocol Compliance

- ✅ **18/18 Message Types:** All defined and validated
- ✅ **18/18 Error Codes:** Comprehensive error handling
- ✅ **Envelope Validation:** Sender, timestamp, protocol, conversation_id
- ✅ **JSON-RPC 2.0:** Full compliance with spec
- ✅ **Timeout Enforcement:** 5s, 10s, 30s per operation type

### Best Practices

- ✅ **Atomic Writes:** Temp file + rename for data integrity
- ✅ **Structured Logging:** JSONL format for log analysis
- ✅ **Environment Overrides:** 15+ settings configurable via env vars
- ✅ **Type Hints:** Pydantic models + function annotations
- ✅ **Dependency Injection:** Config passed to components
- ✅ **Error Recovery:** Retry with exponential backoff + circuit breaker

---

## 📈 Project Status

### Completed (57%)

- ✅ **Foundation (M0-M1):** Environment, structure, PRD, missions
- ✅ **SDK Infrastructure (M2):** Protocol, config, logging, retry, repositories
- ✅ **Configuration Layer (M3):** System, agents, league, game configs
- ✅ **Testing Setup (M4.0-M4.1):** Pytest config, unit test templates
- ✅ **Research (M5.1-M5.4):** MCP, game rules, algorithms, error handling
- ✅ **Player Agent (M7.1-M7.4):** BaseAgent, MCP server, tools, registration

### In Progress (29%)

- 🔄 **Referee Agent (M7.5-M7.8):** Match conductor, timeout enforcement, game logic
- 🔄 **League Manager (M7.9-M7.14):** Registration, scheduling, standings
- 🔄 **Integration Tests (M4.2):** Agent interaction tests

### Not Started (14%)

- ☐ **E2E Tests (M4.3):** Full league simulation
- ☐ **Protocol Compliance Tests (M4.4):** 18 message type validation
- ☐ **Load Tests (M4.5):** 50+ concurrent matches
- ☐ **Documentation (M8.1-M8.5):** Architecture, config, developer guides
- ☐ **UX/DevEx (M6.1-M6.4):** CLI, scripts, quick start
- ☐ **Submission (M9.0-M9.3):** Pre-submission, final testing, deployment

### Quality Gates

| Gate | Status | Criteria |
|------|--------|----------|
| **QG-1: Foundation** | ✅ Passed | SDK operational, 85% coverage, 209 tests passing |
| **QG-2: Player Agent** | ⏸ Ready | Player implements 3 tools, registration working |
| **QG-3: Match Execution** | ☐ Pending | Referee conducts matches, timeouts enforced |
| **QG-4: End-to-End** | ☐ Pending | Full 4-player league completes successfully |
| **QG-5: Production Ready** | ☐ Pending | All tests pass, docs complete, deployment ready |

---

## 🔧 Extensibility & Maintenance

The Even/Odd League system is designed with **extensibility as a first-class architectural concern**, enabling rapid adaptation to new requirements without core code changes. For comprehensive details, see **[Extensibility & ISO/IEC 25010 Analysis](doc/usability_extensibility.md)**.

### Quick Reference: Extension Points

| Extension Type | Configuration | Code Changes | Example Use Case |
|----------------|---------------|--------------|------------------|
| **New Game Types** | ✅ Add GameConfig to `games_registry.json` | ✅ Implement game logic module | Add "Rock/Paper/Scissors" game |
| **New Agent Types** | ✅ Register in `agents_config.json` | ✅ Extend BaseAgent class | Add "Observer" agent for analytics |
| **Player Strategies** | ⚠️ Optional metadata in agent config | ✅ Implement strategy module | Replace random with LLM-based decisions |
| **Retry Policies** | ✅ Update `retry_policy` in `system.json` | ❌ No code changes needed | Aggressive retry for critical ops |
| **Logging Levels** | ✅ Component-specific levels in `system.json` | ❌ No code changes needed | Debug mode for specific agents |
| **Timeout Values** | ✅ Update `timeouts` in `system.json` | ❌ No code changes needed | Increase parity choice timeout |

### Adding New Game Types

**Step 1**: Define game in `SHARED/config/games/games_registry.json`:

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

**Step 2**: Implement game logic in `agents/referee_REF01/games/rock_paper_scissors.py`:

```python
class RockPaperScissorsLogic:
    def determine_winner(self, player_a_choice, player_b_choice):
        # Game-specific winner determination logic
        pass
```

**Step 3**: Referees auto-discover via `games_registry.json` (no code changes needed).

**Detailed Guide:** [doc/usability_extensibility.md § 3.1](doc/usability_extensibility.md#31-adding-new-game-types)

### Adding New Agent Types

**Example**: Add an "Observer" agent that spectates matches.

1. **Extend BaseAgent** (`agents/observer_OBS01/server.py`):
   ```python
   from agents.base import BaseAgent

   class ObserverAgent(BaseAgent):
       def __init__(self, agent_id: str):
           super().__init__(agent_id, agent_type="observer")
   ```

2. **Register in Config** (`SHARED/config/agents/agents_config.json`):
   ```json
   {
     "observers": [
       {
         "agent_id": "OBS01",
         "agent_type": "observer",
         "endpoint": "http://localhost:8201/mcp",
         "port": 8201
       }
     ]
   }
   ```

**Detailed Guide:** [doc/usability_extensibility.md § 3.2](doc/usability_extensibility.md#32-adding-new-agent-types)

### Custom Player Strategies (LLM-Powered)

Replace random parity selection with LLM-based decision-making:

```python
# agents/player_P01/strategies/llm_strategy.py
class LLMParityStrategy:
    def choose_parity(self, match_history: list, opponent_id: str) -> str:
        # Use OpenAI API to analyze patterns and choose parity
        prompt = f"Based on match history, should I choose even or odd?"
        response = openai.ChatCompletion.create(model="gpt-4", messages=[...])
        return response['choices'][0]['message']['content']

# agents/player_P01/handlers.py
from strategies.llm_strategy import LLMParityStrategy

strategy = LLMParityStrategy()
parity_choice = strategy.choose_parity(history_repo.get_recent_matches(10), opponent_id)
```

**Configuration**:
```json
{
  "players": [
    {"agent_id": "P01", "strategy": "llm", "metadata": {"llm_model": "gpt-4"}}
  ]
}
```

**Environment**: `export OPENAI_API_KEY="sk-..."`

**Detailed Guide:** [doc/usability_extensibility.md § 3.3](doc/usability_extensibility.md#33-custom-parity-strategies-llm-powered-players)

### ISO/IEC 25010 Quality Characteristics

The system maps all **8 ISO/IEC 25010 quality characteristics** to implementation with measurable KPIs:

| Characteristic | KPI | Verification Command |
|----------------|-----|----------------------|
| **Functional Suitability** | 18/18 message types (100%) | `grep -c "class.*Message.*MessageEnvelope" SHARED/league_sdk/protocol.py` |
| **Reliability** | Retry success rate ~90% | `pytest tests/unit/test_sdk/test_retry.py -v` |
| **Performance Efficiency** | Response time P95 < 500ms | Manual performance testing |
| **Usability** | 3 accessibility modes (plain, quiet, json) | `./scripts/check_health.sh --plain` |
| **Security** | 32-byte auth tokens | `grep "auth_token_length" SHARED/config/system.json` |
| **Compatibility** | 100% JSON-RPC 2.0 compliant | Protocol compliance tests |
| **Maintainability** | 85% test coverage | `pytest --cov=SHARED/league_sdk --cov=agents` |
| **Portability** | Python 3.10+ compatible | `python3 --version` |

**Full Analysis:** [doc/usability_extensibility.md § 2](doc/usability_extensibility.md#2-isoiec-25010-quality-characteristics-mapping)

### Configuration Extensibility

**Philosophy**: 90% of users should never need to change defaults. Power users can override everything.

**Configuration Hierarchy** (highest to lowest priority):
1. **CLI Arguments**: `--port 8101`
2. **Environment Variables**: `LEAGUE_MANAGER_PORT=9000`
3. **JSON Config Files**: `SHARED/config/system.json`
4. **Hardcoded Defaults**: Fallback values in code

**Example Override**:
```bash
# Override via environment
LEAGUE_MANAGER_PORT=9000 python -m agents.league_manager.main

# Override via CLI
python -m agents.league_manager.main --port 9000
```

**50+ Configurable Parameters** in `system.json` covering timeouts, retry policies, network settings, data retention, logging, security, and more.

### Monitoring & Observability

- **Structured Logs**: JSONL format for ELK stack, Splunk, or Grafana Loki
- **Health Checks**: `/health` endpoint on all agents (200 OK = healthy)
- **Distributed Tracing**: `conversation_id` tracks requests across agent boundaries
- **Future Enhancements**: Prometheus `/metrics` endpoint, OpenTelemetry tracing

**Log Analysis**:
```bash
# Query logs for errors
grep "ERROR" SHARED/logs/agents/*.log.jsonl | jq '.message'

# Aggregate by event type
cat SHARED/logs/league/*/LM01.log.jsonl | jq -r '.event_type' | sort | uniq -c
```

### Best Practices for Extensions

1. **Strategy Pattern**: Swap algorithms without changing core logic (see § 5.1.1)
2. **Repository Pattern**: Abstract data storage (currently file-based, can be SQL/NoSQL)
3. **Configuration-Driven**: Avoid hardcoded values; use `system.json` for all settings
4. **Version Fields**: All configs and messages include `schema_version` for evolution
5. **Graceful Degradation**: Missing config keys log warnings but use sensible defaults

### Future Extensibility Roadmap

**Short-Term (1-3 months)**:
- Plugin auto-discovery (load game modules dynamically)
- Database backend support (PostgreSQL, MongoDB)
- Prometheus metrics exporter

**Medium-Term (3-6 months)**:
- Multi-league support (run multiple tournaments concurrently)
- Real-time match spectating (WebSocket streaming)
- Advanced player strategies (reinforcement learning, genetic algorithms)

**Long-Term (6-12 months)**:
- Multi-game tournaments (aggregate scores across game types)
- Federated leagues (inter-league player transfers)
- Cloud deployment (Kubernetes, auto-scaling)

**Full Roadmap:** [doc/usability_extensibility.md § 7](doc/usability_extensibility.md#7-future-extensibility-roadmap)

---

## 📚 Documentation

### Available Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **Documentation Index** | [doc/README.md](doc/README.md) | Map of all docs by category |
| **Product Requirements** | [PRD_EvenOddLeague.md](PRD_EvenOddLeague.md) | Complete PRD (102KB, 17 sections) |
| **Missions Document** | [PROGRESS_TRACKER.md](PROGRESS_TRACKER.md) | 47 missions with DoD and verify commands |
| **MCP Protocol Research** | [doc/research_notes/mcp_protocol.md](doc/research_notes/mcp_protocol.md) | MCP analysis and recommendations |
| **Even/Odd Game Rules** | [doc/game_rules/even_odd.md](doc/game_rules/even_odd.md) | Game specification and examples |
| **Round-Robin Algorithm** | [doc/algorithms/round_robin.md](doc/algorithms/round_robin.md) | Scheduling algorithm with examples |
| **Error Handling Strategy** | [doc/reference/error_handling_strategy.md](doc/reference/error_handling_strategy.md) | Error classification and retry logic |
| **Data Retention Policy** | [doc/reference/data_retention_policy.md](doc/reference/data_retention_policy.md) | Data lifecycle & cleanup specification (22KB) ✅ |
| **Extensibility & ISO/IEC 25010** | [doc/usability_extensibility.md](doc/usability_extensibility.md) | Extensibility guide + quality characteristics mapping (M8.8) ✅ NEW |
| **Implementation Logs** | [doc/prompt_log/](doc/prompt_log/) | Mission implementation prompts |
| **Contributing Guide** | [CONTRIBUTING.md](CONTRIBUTING.md) | Code style, workflow, and quality standards |
| **Quality Workflow** | [doc/guides/HOW_QUALITY_WORKS.md](doc/guides/HOW_QUALITY_WORKS.md) | How quality checks work locally and on CI/CD |
| **API Reference** | [doc/reference/api_reference.md](doc/reference/api_reference.md) | MCP tools, message formats, and examples |
| **Architecture Docs** | [doc/architecture.md](doc/architecture.md) | C4 views, sequences, states, data flow |
| **Configuration Guide** | ⚠️ Pending | Mission M8.3 - Config file documentation |
| **Developer Guide** | ⚠️ Pending | Mission M8.4 - Contributor onboarding |
| **Testing Guide** | ⚠️ Pending | Mission M8.5 - Test writing guide |

### External Resources

- **Pydantic Documentation:** https://docs.pydantic.dev/
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **JSON-RPC 2.0 Spec:** https://www.jsonrpc.org/specification
- **Model Context Protocol:** https://modelcontextprotocol.io/
- **Python Testing (pytest):** https://docs.pytest.org/
- **Structured Logging:** https://www.structlog.org/

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/even-odd-league.git
   cd even-odd-league
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e SHARED/league_sdk
   pre-commit install
   ```

4. **Make Changes**
   - Follow [CONTRIBUTING.md](CONTRIBUTING.md)
   - Write tests for new features
   - Update documentation

5. **Run Quality Checks**
   ```bash
   # Format code
   black agents SHARED tests

   # Lint
   flake8 agents SHARED tests
   pylint agents SHARED

   # Type check
   mypy agents SHARED

   # Run tests
   PYTHONPATH=SHARED:$PYTHONPATH pytest tests/ -v --cov=SHARED/league_sdk --cov=agents
   ```

6. **Commit with Conventional Commits**
   ```bash
   git add .
   git commit -m "feat: add new parity strategy for players"
   # Or: fix, docs, style, refactor, test, chore
   ```

7. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Open PR on GitHub
   ```

### Code Review Checklist

- [ ] Code follows style guide (black, flake8, mypy pass)
- [ ] All tests pass (`pytest tests/`)
- [ ] Test coverage ≥85%
- [ ] Docstrings added for public functions/classes
- [ ] Config changes documented
- [ ] PROGRESS_TRACKER.md updated if applicable
- [ ] No secrets or hardcoded credentials

### Reporting Issues

Use GitHub Issues with templates:
- **Bug Report:** Include steps to reproduce, expected vs. actual behavior, logs
- **Feature Request:** Describe use case, proposed solution, alternatives
- **Documentation:** Identify unclear/missing docs, suggest improvements

---

## 📜 License & Attribution

### License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Even/Odd League Development Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Attribution

This project builds upon:

- **FastAPI:** Modern web framework for building APIs (https://fastapi.tiangolo.com/)
- **Pydantic:** Data validation using Python type hints (https://pydantic-docs.helpmanual.io/)
- **Pytest:** Testing framework (https://pytest.org/)
- **Model Context Protocol (MCP):** Anthropic's protocol for AI agent communication (https://modelcontextprotocol.io/)

### Third-Party Licenses

All dependencies are listed in `requirements.txt` with their respective licenses:
- FastAPI: MIT License
- Pydantic: MIT License
- Uvicorn: BSD License
- Pytest: MIT License
- Requests: Apache 2.0
- Black: MIT License

---

## 📸 Screenshots

### Agent Startup
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8101 (Press CTRL+C to quit)
```

### Health Check Response
```json
{
  "status": "ok"
}
```

### Test Coverage Report
```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
SHARED/league_sdk/__init__.py            6      0   100%
SHARED/league_sdk/cleanup.py            95     10    90%
SHARED/league_sdk/config_loader.py      73      7    90%
SHARED/league_sdk/config_models.py     101      1    99%
SHARED/league_sdk/logger.py             84      1    99%
SHARED/league_sdk/protocol.py          202     12    94%
SHARED/league_sdk/repositories.py      198      8    96%
SHARED/league_sdk/retry.py             141     20    86%
agents/base/agent_base.py               93     16    83%
agents/player_P01/handlers.py           46      4    91%
agents/player_P01/server.py            160     20    88%
--------------------------------------------------------
TOTAL                                 1288    186    85%
```

### Structured Log Entry (JSONL)
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "INFO",
  "agent_id": "P01",
  "component": "player:P01",
  "message": "Sent GAME_JOIN_ACK to referee:REF01",
  "event_type": "MESSAGE_SENT",
  "message_type": "GAME_JOIN_ACK",
  "recipient": "referee:REF01",
  "conversation_id": "conv-abc123",
  "match_id": "R1M1"
}
```

---

## 💬 Support & Contact

### Getting Help

- **GitHub Issues:** Report bugs, request features (https://github.com/your-org/even-odd-league/issues)
- **Discussions:** Ask questions, share ideas (https://github.com/your-org/even-odd-league/discussions)
- **Documentation:** Check existing docs in [doc/](doc/) folder
- **Email:** dev@evenoddleague.local (for sensitive issues)

### Community

- **Slack/Discord:** (Coming soon)
- **Twitter:** @EvenOddLeague (Coming soon)
- **Blog:** https://evenoddleague.dev/blog (Coming soon)

### Maintainers

- **Project Lead:** Igor Nazarenko
- **Architecture:** Even/Odd League Development Team
- **Contributors:** See [CONTRIBUTORS.md](CONTRIBUTORS.md) (Coming soon)

---

## 🎓 Acknowledgments

This project was developed as part of an advanced software engineering course focusing on:
- Multi-agent systems design
- Protocol-driven architecture
- Distributed computing patterns
- Production-grade software engineering practices

Special thanks to:
- **Anthropic** for the Model Context Protocol (MCP) specification
- **FastAPI community** for the excellent web framework
- **Pydantic team** for data validation infrastructure
- **Open source contributors** for the tools and libraries used

---

<div align="center">

**Built with ❤️ using Python, FastAPI, and MCP**

[⬆ Back to Top](#-evenodd-league-multi-agent-orchestration-system)

</div>
