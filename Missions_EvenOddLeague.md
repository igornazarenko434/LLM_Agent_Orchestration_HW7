# Missions Document
# Even/Odd League Multi-Agent System

**Version:** 1.0.0
**Date:** 2025-01-15
**Project Type:** HYBRID (Backend API + CLI + Multi-Agent Orchestration)
**Protocol:** league.v2 (JSON-RPC 2.0 over HTTP)
**Target Grade:** 90-100

---

## TABLE OF CONTENTS

- [Mission Overview](#mission-overview)
- [Quality Gates](#quality-gates)
- [M0: Kickoff & Planning](#m0-kickoff--planning)
- [M1: PRD & Requirements](#m1-prd--requirements)
- [M2: Setup & Architecture](#m2-setup--architecture)
- [M3: Configuration Layer](#m3-configuration-layer)
- [M4: Testing Infrastructure](#m4-testing-infrastructure)
- [M5: Research & Protocol Design](#m5-research--protocol-design)
- [M6: UX & Developer Experience](#m6-ux--developer-experience)
- [M7: Agent Implementation](#m7-agent-implementation)
- [M8: Documentation](#m8-documentation)
- [M9: Submission & Deployment](#m9-submission--deployment)
- [Dependency Graph](#dependency-graph)

---

## MISSION OVERVIEW

This missions document provides a comprehensive, sequential breakdown of all tasks required to build the Even/Odd League multi-agent system. The project is a **HYBRID** combining:
- **Backend API** components (agents expose MCP servers on HTTP endpoints)
- **CLI** components (command-line tools for agent management)
- **Multi-agent orchestration** (3 agent types communicating via JSON-RPC 2.0)

**Total Missions:** 74 missions across 10 categories (M0-M9)
**Expected Duration:** 60-80 hours for complete implementation
**Target Grade:** 90-100 with all missions completed

---

## QUALITY GATES

Quality Gates are mandatory checkpoints that must pass before proceeding to subsequent phases.

### QG-1: Foundation Quality Gate
**Triggers After:** M2.2 (Protocol Implementation)
**Must Pass Before:** M7.x (Agent Implementation)

**Criteria:**
- [x] All configuration files created and validated
- [x] Shared SDK installed and importable
- [x] Protocol models defined with Pydantic
- [x] Unit tests for SDK modules: 100% pass rate (161/161 tests passing)
- [x] Code quality: Test coverage 91% (exceeds 85% target)

**Verification Command:**
```bash
pytest tests/unit/test_sdk/ -v && \
flake8 SHARED/league_sdk/ && \
python -c "from league_sdk import protocol; print('SDK OK')"
```

**Exit Criteria:** All checks pass
**On Failure:** Fix issues before proceeding to M7.x

---

### QG-2: Player Agent Quality Gate
**Triggers After:** M7.3 (Player Agent Implementation)
**Must Pass Before:** M7.4 (Referee Agent Implementation)

**Criteria:**
- [ ] Player agent implements all 3 mandatory tools
- [ ] Player agent registers successfully with League Manager
- [ ] Player agent responds to invitations within 5 seconds
- [ ] Player agent makes parity choices within 30 seconds
- [ ] Unit tests for player agent: ≥85% coverage
- [ ] Integration tests: Player-Manager registration flow passes

**Verification Command:**
```bash
pytest tests/unit/test_player_agent/ --cov=agents/player_P01 --cov-report=term && \
pytest tests/integration/test_player_registration.py -v && \
python tests/manual/test_player_tools.py --player-id=P01
```

**Exit Criteria:** All checks pass with ≥85% coverage
**On Failure:** Debug and fix player agent before referee implementation

---

### QG-3: Match Execution Quality Gate
**Triggers After:** M7.5, M7.6, M7.7, M7.8 (Match Flow + Timeout + Game Logic + Registration)
**Must Pass Before:** M7.9.1 (Async HTTP Migration) → M7.9 (League Manager Implementation)

**Criteria:**
- [x] Complete match flow executes successfully (invitation → result)
- [x] Timeout enforcement works (5s join, 30s choice) - M7.6 completed
- [x] Even/Odd game logic correct for all scenarios - M7.7 completed (98% coverage)
- [ ] Match results reported to League Manager - Pending M7.9
- [x] Integration tests: Full match flow passes - 256 tests passing
- [x] No unhandled exceptions during match execution
- [ ] **CRITICAL:** M7.9.1 Async HTTP client migration completed before M7.9

**Verification Command:**
```bash
pytest tests/integration/test_match_flow.py -v && \
pytest tests/integration/test_timeout_enforcement.py -v && \
pytest tests/unit/test_even_odd_logic.py --iterations=100
```

**Exit Criteria:** All match flows complete successfully
**On Failure:** Fix match conductor and game logic

---

### QG-4: End-to-End Quality Gate
**Triggers After:** M7.7 (Full System Integration)
**Must Pass Before:** M8.x (Documentation)

**Criteria:**
- [ ] 4-player league completes successfully (6 matches, 3 rounds)
- [ ] Standings calculated correctly (Win=3, Draw=1, Loss=0)
- [ ] All 18 message types exchanged correctly
- [ ] All agents log to JSONL format
- [ ] No crashes or unhandled exceptions
- [ ] E2E tests pass: 4-player league simulation

**Verification Command:**
```bash
pytest tests/e2e/test_4_player_league.py -v && \
python tests/e2e/verify_standings_accuracy.py && \
cat logs/agents/*.log.jsonl | jq . > /dev/null && echo "Logs valid"
```

**Exit Criteria:** Complete league finishes with accurate standings
**On Failure:** Debug system integration issues

---

### QG-5: Production Readiness Quality Gate
**Triggers After:** M9.1 (Final Testing & Validation)
**Must Pass Before:** M9.3 (Final Submission)

**Criteria:**
- [ ] Test coverage ≥85% overall
- [ ] All protocol compliance tests pass (18/18 message types)
- [ ] All error codes tested (18/18 error codes)
- [ ] Code quality: flake8 and mypy pass
- [ ] Documentation complete (README, API docs, PRD, Missions)
- [ ] No TODO or FIXME comments in production code
- [ ] Performance tests pass (50 concurrent matches)

**Verification Command:**
```bash
pytest tests/ --cov=agents --cov=SHARED/league_sdk --cov-report=term | grep "TOTAL.*[8-9][5-9]%" && \
pytest tests/protocol_compliance/ -v && \
flake8 agents/ SHARED/league_sdk/ && \
mypy agents/ SHARED/league_sdk/ --strict && \
pytest tests/load/test_concurrent_matches.py --concurrent=50 -v
```

**Exit Criteria:** All production readiness checks pass
**On Failure:** Address issues before submission

---

## M0: KICKOFF & PLANNING

### M0.1: Environment Setup
**Priority:** P0 (Critical)
**Estimated Time:** 1 hour

**Description:**
Set up development environment with Python 3.9+, virtual environment, and verify system prerequisites.

**Definition of Done:**
- [x] Python 3.9+ installed and verified
- [x] Virtual environment created and activated
- [x] Git repository initialized (if not already)
- [x] Working directory structure created
- [x] Port availability verified (8000, 8001-8002, 8101-8104)

**Self-Verify Command:**
```bash
python3 --version && \
source venv/bin/activate && \
python -c "import sys; assert sys.version_info >= (3, 9)" && \
netstat -an | grep -E "800[0-2]|810[1-4]" && echo "Ports free" || echo "Ports available"
```

**Expected Evidence:**
- Python version output shows 3.9.x or higher
- Virtual environment activated (prompt shows `(venv)`)
- Port check shows no conflicts

**Dependencies:** None
**Blocks:** M0.2

---

### M0.2: Project Structure Creation
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Create complete directory structure for SHARED/, agents/, tests/, doc/, scripts/.

**Definition of Done:**
- [x] SHARED/ directory with config/, data/, logs/, league_sdk/ subdirectories
- [x] agents/ directory with league_manager/, referee_REF01/, referee_REF02/, player_P01-P04/
- [x] tests/ directory with unit/, integration/, e2e/, protocol_compliance/, load/, security/, fixtures/
- [x] doc/ directory created
- [x] scripts/ directory created
- [x] .gitignore file created with appropriate exclusions

**Self-Verify Command:**
```bash
ls -R | grep -E "SHARED|agents|tests|doc|scripts" && \
tree -L 2 -d . | grep -E "config|data|logs|league_sdk" && \
cat .gitignore | grep -E "__pycache__|venv|*.pyc"
```

**Expected Evidence:**
- Directory tree output shows all required directories
- .gitignore exists with Python-specific exclusions

**Dependencies:** M0.1
**Blocks:** M0.3, M2.0

---

### M0.3: Dependency Installation
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Install all required Python packages: FastAPI, Uvicorn, Pydantic, requests, pytest, etc.

**Definition of Done:**
- [x] requirements.txt created with all dependencies
- [x] All packages installed via pip
- [x] No installation errors
- [x] Package versions verified (FastAPI≥0.100, Pydantic≥2.0, etc.)
- [x] Verification script runs successfully

**Self-Verify Command:**
```bash
pip install -r requirements.txt && \
pip list | grep -E "fastapi|uvicorn|pydantic|requests|pytest" && \
python -c "import fastapi, uvicorn, pydantic, requests, pytest; print('All imports OK')"
```

**Expected Evidence:**
- pip list shows all required packages
- Import test succeeds without errors
- requirements.txt contains minimum versions

**Dependencies:** M0.1, M0.2
**Blocks:** M2.1

---

## M1: PRD & REQUIREMENTS

### M1.1: PRD Document Creation
**Priority:** P0 (Critical)
**Estimated Time:** 4 hours

**Description:**
Create comprehensive Product Requirements Document with all 17 required sections for 90-100 score.

**Definition of Done:**
- [x] PRD_EvenOddLeague.md created with 17+ sections
- [x] ≥12 KPIs with verification commands
- [x] ≥16 Functional Requirements (FR-001 to FR-016)
- [x] ≥15 Non-Functional Requirements (NFR-001 to NFR-015) covering ISO/IEC 25010
- [x] ≥12 Architecture Decision Records (ADR-001 to ADR-012)
- [x] ≥35 Evidence Matrix entries
- [x] ≥10 Installation Matrix steps
- [x] All sections use markdown tables where appropriate

**Self-Verify Command:**
```bash
grep -E "^## [0-9]+\." PRD_EvenOddLeague.md | wc -l && \
grep -E "^### FR-" PRD_EvenOddLeague.md | wc -l && \
grep -E "^### NFR-" PRD_EvenOddLeague.md | wc -l && \
grep -E "^### ADR-" PRD_EvenOddLeague.md | wc -l
```

**Expected Evidence:**
- Section count: ≥17
- FR count: ≥16
- NFR count: ≥15
- ADR count: ≥12
- Evidence matrix has ≥35 rows

**Dependencies:** M0.2 (to save file)
**Blocks:** M1.2

---

### M1.2: Missions Document Creation
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Create comprehensive Missions document with 40-50 missions, combining Backend API and CLI templates.

**Definition of Done:**
- [x] Missions_EvenOddLeague.md created with ≥40 missions
- [x] All missions have: Definition of Done, Self-Verify Command, Expected Evidence, Dependencies, Blocks
- [x] 5 Quality Gates defined with clear criteria
- [x] Missions organized into 10 categories (M0-M9)
- [x] Dependency graph included
- [x] Each mission has priority (P0/P1/P2) and estimated time

**Self-Verify Command:**
```bash
grep -E "^### M[0-9]+\.[0-9]+" Missions_EvenOddLeague.md | wc -l && \
grep -E "^### QG-[0-9]" Missions_EvenOddLeague.md | wc -l && \
grep -E "\*\*Definition of Done:\*\*" Missions_EvenOddLeague.md | wc -l
```

**Expected Evidence:**
- Mission count: ≥40
- Quality Gate count: 5
- Each mission has all required sections

**Dependencies:** M1.1
**Blocks:** M2.0

---

### M1.3: Add Personas to PRD
**Priority:** P0 (Critical)
**Estimated Time:** 1.5 hours

**Description:**
Add detailed user personas to PRD Section 2 to provide context for stakeholders and design decisions.

**Definition of Done:**
- [ ] Section 2 in PRD with ≥2 complete personas
- [ ] Each persona includes: Name, Role, Goals, Pain Points, How Project Helps
- [ ] Personas are relevant to multi-agent orchestration context
- [ ] Personas inform design decisions and requirements

**Self-Verify Command:**
```bash
grep -A 10 "Persona" PRD_EvenOddLeague.md | grep -E "Name|Role|Goals|Pain Points|How Project Helps" && echo "Personas complete"
```

**Expected Evidence:**
- PRD Section 2 contains ≥2 complete personas
- Each persona has all required fields
- Personas are well-defined and actionable

**Dependencies:** M1.1
**Blocks:** M1.4

---

### M1.4: Add Research & Analysis Section to PRD ✅ COMPLETED (2025-12-19)
**Priority:** P1 (High)
**Estimated Time:** 2 hours

**Description:**
Document research methodology, experiments to be tested, sensitivity analysis parameters, and planned Jupyter notebook structure.

**Definition of Done:**
- [ ] PRD Section includes Research & Analysis subsection
- [ ] Experiments documented: parity strategies, timeout impacts, retry behaviors
- [ ] ≥3 parameters defined for sensitivity analysis (e.g., timeout values, retry intervals, concurrent match counts)
- [ ] Jupyter notebook plan documented: ≥8 cells, ≥2 LaTeX formulas, ≥4 plots, ≥3 references
- [ ] Analysis approach linked to NFRs (performance, reliability)

**Self-Verify Command:**
```bash
grep -A 50 "Research & Analysis" PRD_EvenOddLeague.md | grep -E "sensitivity|parameters|LaTeX|plots|references" && echo "Research section complete"
```

**Expected Evidence:**
- Research & Analysis section present in PRD
- Experiments and parameters clearly defined
- Notebook structure aligns with M5.5 requirements

**Dependencies:** M1.3
**Blocks:** M5.5

---

### M1.5: Open Questions & Assumptions ✅ COMPLETED (2025-12-19)
**Priority:** P2 (Medium)
**Estimated Time:** 30 minutes

**Description:**
Document open questions, assumptions, and constraints that may impact design or implementation.

**Definition of Done:**
- [ ] PRD section listing ≥5 open questions
- [ ] ≥5 key assumptions documented
- [ ] Constraints and limitations identified
- [ ] Risk implications noted for each

**Self-Verify Command:**
```bash
grep -A 20 "Open Questions\|Assumptions" PRD_EvenOddLeague.md | grep -E "Q:|A:" && echo "Open questions documented"
```

**Expected Evidence:**
- Open questions clearly stated
- Assumptions explicit and traceable
- Constraints inform design decisions

**Dependencies:** M1.4
**Blocks:** M8.8

---

## M2: SETUP & ARCHITECTURE

### M2.0: Shared SDK Package Structure
**Priority:** P0 (Critical)
**Estimated Time:** 1 hour

**Description:**
Create SHARED/league_sdk/ package structure with __init__.py, setup.py, and module stubs.

**Definition of Done:**
- [x] SHARED/league_sdk/__init__.py created
- [x] SHARED/league_sdk/setup.py created for pip install -e
- [x] Module stubs created: config_loader.py, config_models.py, protocol.py, repositories.py, logger.py, utils.py
- [x] Package metadata in setup.py (name, version, dependencies)
- [x] Package installable in editable mode

**Self-Verify Command:**
```bash
cd SHARED/league_sdk && pip install -e . && \
python -c "import league_sdk; print(league_sdk.__version__)" && \
pip show league-sdk
```

**Expected Evidence:**
- pip install succeeds
- league_sdk importable
- setup.py contains correct metadata

**Dependencies:** M0.2, M0.3
**Blocks:** M2.1

---

### M2.1: Protocol Models Definition
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Define Pydantic models for all 18 message types and MessageEnvelope in SHARED/league_sdk/protocol.py.

**Definition of Done:**
- [x] MessageEnvelope base model with 6 mandatory fields (protocol, message_type, sender, timestamp, conversation_id, auth_token)
- [x] 18 message type models (GAME_INVITATION, CHOOSE_PARITY_CALL, etc.)
- [x] Field validation: sender format regex, timestamp format regex, protocol literal
- [x] Comprehensive docstrings for all models
- [x] Unit tests for envelope validation

**Self-Verify Command:**
```bash
python -c "from league_sdk.protocol import MessageEnvelope, GameInvitation; print('Models OK')" && \
pytest tests/unit/test_protocol_models.py -v
```

**Expected Evidence:**
- All 18 message models importable
- Validation tests pass (valid messages accepted, invalid rejected)
- Regex patterns work for sender and timestamp

**Dependencies:** M2.0
**Blocks:** M2.2, M7.x (all agent implementations)

---

### M2.2: Configuration Models & Loader
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement configuration loading and validation in SHARED/league_sdk/config_loader.py and config_models.py.

**Definition of Done:**
- [x] Pydantic models for: SystemConfig, AgentConfig, LeagueConfig, GameConfig
- [x] Config loader functions: load_system_config(), load_league_config(), load_agents_config()
- [x] Schema validation on load
- [x] Helpful error messages for invalid configs
- [x] Unit tests for config loading

**Self-Verify Command:**
```bash
python -c "from league_sdk.config_loader import load_system_config; config = load_system_config('SHARED/config/system.json'); print(config.protocol_version)" && \
pytest tests/unit/test_config_loader.py -v
```

**Expected Evidence:**
- Config files load successfully
- Invalid configs raise ValidationError with helpful messages
- Tests cover all config types

**Dependencies:** M2.1, M3.0 (config files must exist)
**Blocks:** M7.x (agent implementations need config)

---

### M2.3: Data Repository Layer
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement file-based data access layer in SHARED/league_sdk/repositories.py with atomic writes.

**Definition of Done:**
- [x] StandingsRepository: get_standings(), update_standings()
- [x] MatchRepository: save_match(), get_match(), list_matches()
- [x] PlayerHistoryRepository: get_history(), update_history()
- [x] Atomic file writes using temp file + rename pattern
- [x] Create parent directories if missing
- [x] Unit tests for all repositories

**Self-Verify Command:**
```bash
python -c "from league_sdk.repositories import StandingsRepository; repo = StandingsRepository('test_league'); print('Repositories OK')" && \
pytest tests/unit/test_repositories.py -v
```

**Expected Evidence:**
- All repository classes importable
- Atomic write tests pass (no partial writes on crash)
- File operations create necessary directories

**Dependencies:** M2.1
**Blocks:** M7.4, M7.6 (agents need data persistence)

---

### M2.6: Thread Safety Documentation ✅ COMPLETED (2025-12-19)
**Priority:** P2 (Medium)
**Estimated Time:** 1 hour

**Description:**
Document thread safety considerations for concurrent agent operations and shared resource access.

**Definition of Done:**
- [x] doc/thread_safety.md created documenting concurrency model
- [x] Thread-safe data access patterns documented (locks, atomics, immutability)
- [x] Repository layer thread safety guarantees documented
- [x] Shared resource access patterns (config, logs, data files) explained
- [x] Race condition prevention strategies documented

**Self-Verify Command:**
```bash
cat doc/thread_safety.md | grep -E "Thread|Concurrent|Lock|Race|Atomic" && echo "Thread safety documented"
```

**Expected Evidence:**
- Thread safety document exists
- Concurrency patterns clearly explained
- Repository operations documented as thread-safe

**Dependencies:** M2.3 (repositories must exist)
**Blocks:** M8.2

---

### M2.4: Structured Logging Setup
**Priority:** P0 (Critical)
**Estimated Time:** 1.5 hours

**Description:**
Implement JSON Lines logging in SHARED/league_sdk/logger.py with structured log formatting.

**Definition of Done:**
- [x] setup_logger() function returns configured logger
- [x] JSON formatter: timestamp, component, event_type, level, message, extras
- [x] File handler for JSONL output
- [x] Log rotation support (100MB max file size)
- [x] Helper functions: log_message_sent(), log_message_received(), log_error()
- [x] Unit tests for logger setup

**Self-Verify Command:**
```bash
python -c "from league_sdk.logger import setup_logger; logger = setup_logger('test', 'test.log.jsonl'); logger.info('test'); print('Logger OK')" && \
cat test.log.jsonl | jq . && \
pytest tests/unit/test_logger.py -v
```

**Expected Evidence:**
- Logger writes valid JSONL (parseable by jq)
- Log entries have all required fields
- Log rotation works (tested with mock)

**Dependencies:** M2.1
**Blocks:** M7.x (all agents need logging)

---

### M2.5: Retry Policy Implementation
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Implement retry decorator with exponential backoff in SHARED/league_sdk/retry.py.

**Definition of Done:**
- [x] retry_with_backoff() decorator
- [x] Configurable max_retries (default: 3)
- [x] Exponential backoff: 2^attempt seconds (2, 4, 8)
- [x] Retryable vs. non-retryable exception classification
- [x] Logging of retry attempts
- [x] Unit tests with mocked functions

**Self-Verify Command:**
```bash
python -c "from league_sdk.retry import retry_with_backoff; print('Retry OK')" && \
pytest tests/unit/test_retry_policy.py -v
```

**Expected Evidence:**
- Decorator retries transient failures
- Non-retryable errors raise immediately
- Backoff delays measured correctly (2s, 4s, 8s)

**Dependencies:** M2.4 (needs logging)
**Blocks:** M7.4, M7.5 (referee needs retry for player calls)

---

**QG-1 CHECKPOINT:** Run Foundation Quality Gate before proceeding to M7.x

---

## M3: CONFIGURATION LAYER

### M3.0: System Configuration File
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Create SHARED/config/system.json with global system settings.

**Definition of Done:**
- [x] schema_version: "1.0.0"
- [x] protocol_version: "league.v2"
- [x] Timeout settings: move_timeout_sec (30), generic_response_timeout_sec (10), game_join_ack_timeout_sec (5)
- [x] Retry policy: max_retries (3), backoff_strategy ("exponential")
- [x] Network settings: base_host, port ranges
- [x] File validates against config schema

**Self-Verify Command:**
```bash
python -c "from league_sdk.config_loader import load_system_config; config = load_system_config('SHARED/config/system.json'); assert config.protocol_version == 'league.v2'; print('Valid')"
```

**Expected Evidence:**
- JSON file is valid
- Schema validation passes
- All required fields present

**Dependencies:** M2.0
**Blocks:** M2.2, M7.x

---

### M3.1: Agents Registry Configuration
**Priority:** P0 (Critical)
**Estimated Time:** 45 minutes

**Description:**
Create SHARED/config/agents/agents_config.json with league manager, referees, and players registry.

**Definition of Done:**
- [x] League Manager entry with endpoint (http://localhost:8000/mcp)
- [x] 2 Referee entries (REF01, REF02) with endpoints, game_types, max_concurrent_matches
- [x] 4 Player entries (P01-P04) with endpoints, display_names, game_types
- [x] All agents marked as "active": true
- [x] File validates against schema

**Self-Verify Command:**
```bash
python -c "from league_sdk.config_loader import load_agents_config; config = load_agents_config('SHARED/config/agents/agents_config.json'); assert len(config['players']) == 4; print('Valid')"
```

**Expected Evidence:**
- JSON file valid
- All 7 agents defined (1 manager, 2 referees, 4 players)
- Endpoints use correct ports

**Dependencies:** M3.0
**Blocks:** M7.x

---

### M3.2: League Configuration File
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Create SHARED/config/leagues/league_2025_even_odd.json with league-specific settings.

**Definition of Done:**
- [x] league_id: "league_2025_even_odd"
- [x] game_type: "even_odd"
- [x] Scoring: win_points (3), draw_points (1), loss_points (0), technical_loss_points (0)
- [x] Participants: min_players (2), max_players (10000)
- [x] Status: "ACTIVE"

**Self-Verify Command:**
```bash
python -c "from league_sdk.config_loader import load_league_config; config = load_league_config('SHARED/config/leagues/league_2025_even_odd.json'); assert config['scoring']['win_points'] == 3; print('Valid')"
```

**Expected Evidence:**
- JSON file valid
- Scoring rules match requirements (Win=3, Draw=1, Loss=0)

**Dependencies:** M3.0
**Blocks:** M7.6 (League Manager needs league config)

---

### M3.3: Quality Standards Setup ✅ COMPLETED (2025-12-19)
**Priority:** P1 (High)
**Estimated Time:** 3-4 hours
**Status:** ✅ Complete

**Description:**
Establish comprehensive quality standards and automation for code quality, testing, and CI/CD.

**Definition of Done:**
- [x] CONTRIBUTING.md created (300+ lines) with code style, commit conventions, PR checklist, branching strategy
- [x] .pre-commit-config.yaml with hooks: black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer, detect-private-key, check-yaml, check-json, check-large-files
- [x] .flake8 configuration file with project-specific rules (line length: 104)
- [x] .github/workflows/test.yml created (requires manual upload to GitHub)
- [x] pyproject.toml with black, isort, mypy, pylint, pytest configuration
- [x] All quality checks pass: black ✅, flake8 ✅, mypy ✅, pytest 85.23% coverage ✅
- [x] Pre-commit hooks installed and working (10 hooks passing)

**Self-Verify Command:**
```bash
test -f CONTRIBUTING.md && wc -l CONTRIBUTING.md && \
test -f .pre-commit-config.yaml && grep -E "black|mypy|flake8" .pre-commit-config.yaml && \
test -f .github/workflows/test.yml && grep "coverage" .github/workflows/test.yml && \
pre-commit run --all-files && \
echo "Quality standards complete"
```

**Expected Evidence:**
- CONTRIBUTING.md exists with ≥30 lines
- Pre-commit config includes all required hooks
- CI workflow includes lint, type-check, and coverage gate
- All quality checks pass

**Dependencies:** M3.0
**Blocks:** M6.5, M6.6, M6.7

---

### M3.4: Game Registry Configuration
**Priority:** P1 (High)
**Estimated Time:** 20 minutes

**Description:**
Create SHARED/config/games/games_registry.json defining Even/Odd game type.

**Definition of Done:**
- [x] game_type: "even_odd"
- [x] display_name: "Even/Odd Game"
- [x] rules_module: "games.even_odd"
- [x] max_round_time_sec: 60
- [x] supports_draw: true

**Self-Verify Command:**
```bash
cat SHARED/config/games/games_registry.json | jq '.games[] | select(.game_type == "even_odd")' && echo "Valid"
```

**Expected Evidence:**
- JSON file valid
- Even/Odd game defined with correct attributes

**Dependencies:** M3.0
**Blocks:** M7.5 (referee game logic)

---

### M3.5: Default Configuration Templates
**Priority:** P2 (Medium)
**Estimated Time:** 30 minutes

**Description:**
Create default configuration templates for referee and player agents.

**Definition of Done:**
- [x] SHARED/config/defaults/referee.json with default referee settings
- [x] SHARED/config/defaults/player.json with default player settings
- [x] Templates include: log_level, max_concurrent_matches, strategy defaults
- [x] Documented inline comments explaining each setting

**Self-Verify Command:**
```bash
jq . SHARED/config/defaults/referee.json && \
jq . SHARED/config/defaults/player.json && \
echo "Templates valid"
```

**Expected Evidence:**
- Both template files are valid JSON
- Inline comments present (using jq --slurp to handle comments)

**Dependencies:** M3.0
**Blocks:** None (optional templates)

---

### M3.6: Security & Environment Baseline
**Priority:** P1 (High)
**Estimated Time:** 1 hour

**Description:**
Add repo-level security/config hygiene artifacts.

**Definition of Done:**
- [x] `.env.example` with commented variables (auth token length, ports, log level, retry overrides) and guidance on secrets
- [x] `.gitignore` updated with ≥15 patterns covering venv, pycache, logs, data backups, coverage, .env
- [x] Secret handling guidance added to configuration docs (no secrets in code/config)
- [x] Validate config loader supports env overrides where applicable

**Self-Verify Command:**
```bash
cat .env.example | grep "LEAGUE_" && \
grep -c "env" .gitignore && echo "Security baseline present"
```

**Expected Evidence:**
- .env.example present and referenced in README
- gitignore blocks secrets/artifacts
- No secrets committed

**Dependencies:** M3.0, M0.2
**Blocks:** M6.8, CI security checks

---

### M3.7: Data Retention Policy ✅ COMPLETED
**Priority:** P2 (Medium)
**Estimated Time:** 30 minutes
**Actual Time:** 8 hours (extended scope - included full implementation)
**Completed:** 2025-12-20

**Description:**
Document data retention policy for logs, match data, and player history.
**SCOPE EXPANDED:** Implemented complete data retention system with automated cleanup.

**Definition of Done:**
- [x] doc/reference/data_retention_policy.md created (22KB comprehensive spec)
- [x] Retention periods defined for: logs (30 days), match data (1 year), standings (permanent)
- [x] Cleanup procedures documented (manual/automated)
- [x] Archive strategy for historical data (gzip compression, 80% size reduction)
- [x] Privacy considerations documented (PII handling if applicable)

**Additional Deliverables (Beyond Original Scope):**
- [x] SHARED/league_sdk/cleanup.py (258 lines) - 6 async cleanup functions
- [x] SHARED/scripts/cleanup_data.py (273 lines) - Manual CLI cleanup tool
- [x] tests/unit/test_sdk/test_cleanup.py (17 tests, 90% coverage)
- [x] System.json configuration with data_retention section
- [x] Archive directory structure with .gitkeep files
- [x] Integration with BaseAgent lifecycle (cleanup on shutdown)
- [x] PRD updates: FR-017, NFR-016, section 6.2.3
- [x] README documentation with usage examples and troubleshooting
- [x] Thread-safe queue processor (queue_processor.py, 59 lines)
- [x] CleanupStats dataclass for operation metrics
- [x] Python 3.10+ compatibility (asyncio.TimeoutError handling)

**Self-Verify Command:**
```bash
# Verify documentation
cat doc/reference/data_retention_policy.md | grep -E "Retention|Cleanup|Archive|30 days|1 year" && echo "✅ Data retention policy documented"

# Verify implementation
python -c "from league_sdk.cleanup import cleanup_old_logs, archive_old_matches, run_full_cleanup; print('✅ Cleanup functions available')"

# Verify tests
pytest tests/unit/test_sdk/test_cleanup.py -v --tb=short && echo "✅ All cleanup tests passing"

# Verify manual script
python SHARED/scripts/cleanup_data.py --help | grep -q "Data Retention Cleanup" && echo "✅ Manual cleanup script working"
```

**Evidence:**
- ✅ doc/reference/data_retention_policy.md exists (22KB)
- ✅ SHARED/league_sdk/cleanup.py (6 async functions)
- ✅ SHARED/scripts/cleanup_data.py (CLI tool with dry-run mode)
- ✅ 17 unit tests passing (90% coverage)
- ✅ Configuration in system.json (9 settings)
- ✅ Archive directory structure created
- ✅ PRD and README updated
- ✅ 209 total tests passing (up from 199)
- ✅ All CI/CD quality gates passing (Python 3.10 & 3.11)
- ✅ Git repository follows best practices

**Dependencies:** M2.3 (data repositories) ✅
**Blocks:** M8.4

---

## M4: TESTING INFRASTRUCTURE

### M4.0: Pytest Configuration
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Set up pytest with conftest.py, coverage configuration, and test fixtures.

**Definition of Done:**
- [ ] tests/conftest.py created with shared fixtures
- [ ] pytest.ini or pyproject.toml with pytest config
- [ ] Coverage settings: --cov=agents --cov=SHARED/league_sdk, minimum 85%
- [ ] Test markers defined: unit, integration, e2e, slow
- [ ] Fixture for mock MCP server

**Self-Verify Command:**
```bash
pytest --version && \
pytest --collect-only tests/ | grep "test session starts" && \
cat pytest.ini | grep "testpaths"
```

**Expected Evidence:**
- pytest runs without errors
- Configuration file exists
- Fixtures importable from conftest.py

**Dependencies:** M0.3
**Blocks:** M4.1, M4.2, M4.3

---

### M4.1: Unit Test Templates
**Priority:** P0 (Critical)
**Estimated Time:** 1 hour

**Description:**
Create unit test templates for SDK modules and agent components.

**Definition of Done:**
- [ ] tests/unit/test_sdk/test_protocol.py with envelope validation tests
- [ ] tests/unit/test_sdk/test_config_loader.py with config loading tests
- [ ] tests/unit/test_sdk/test_repositories.py with data access tests
- [ ] tests/unit/test_sdk/test_logger.py with logging tests
- [ ] tests/unit/test_sdk/test_retry.py with retry policy tests
- [ ] All tests pass (even if minimal)

**Self-Verify Command:**
```bash
pytest tests/unit/test_sdk/ -v --tb=short
```

**Expected Evidence:**
- All unit test files exist
- Tests pass (≥5 tests per module)
- Coverage ≥90% for SDK modules

**Dependencies:** M4.0, M2.x (SDK modules must exist)
**Blocks:** QG-1

---

### M4.2: Integration Test Templates
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Create integration test templates for agent interactions.

**Definition of Done:**
- [ ] tests/integration/test_player_registration.py (Player → Manager)
- [ ] tests/integration/test_match_flow.py (full match execution)
- [ ] tests/integration/test_timeout_enforcement.py (timeout scenarios)
- [ ] tests/integration/test_standings_update.py (standings broadcast)
- [ ] tests/integration/test_concurrent_matches.py (parallel matches)
- [ ] Mock MCP server fixture for agent testing

**Self-Verify Command:**
```bash
pytest tests/integration/ -v --tb=short -k "not slow"
```

**Expected Evidence:**
- Integration test files exist
- Tests can run in isolation with mocks
- Fixtures enable testing without full system startup

**Dependencies:** M4.0, M2.x
**Blocks:** QG-2, QG-3

---

### M4.3: End-to-End Test Suite
**Priority:** P1 (High)
**Estimated Time:** 2 hours

**Description:**
Create E2E tests that launch full system and run complete league.

**Definition of Done:**
- [ ] tests/e2e/test_4_player_league.py (full 4-player league)
- [ ] tests/e2e/test_standings_accuracy.py (verify final standings)
- [ ] tests/e2e/test_graceful_shutdown.py (agent lifecycle)
- [ ] tests/e2e/test_network_failure_recovery.py (resilience)
- [ ] Subprocess management for agent startup/shutdown
- [ ] Timeout for E2E tests (10 minutes max)

**Self-Verify Command:**
```bash
pytest tests/e2e/test_4_player_league.py -v --timeout=600
```

**Expected Evidence:**
- E2E test can launch all agents
- League completes successfully
- All agents shut down cleanly

**Dependencies:** M4.0, M7.7 (full system must be implemented)
**Blocks:** QG-4

---

### M4.4: Protocol Compliance Test Suite
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Create tests validating all 18 message types conform to league.v2 protocol.

**Definition of Done:**
- [ ] tests/protocol_compliance/test_message_types.py (18 message type tests)
- [ ] tests/protocol_compliance/test_envelope_fields.py (mandatory fields)
- [ ] tests/protocol_compliance/test_timestamp_format.py (ISO 8601 UTC)
- [ ] tests/protocol_compliance/test_sender_format.py ("{agent_type}:{agent_id}")
- [ ] tests/protocol_compliance/test_auth_token_presence.py (all post-registration messages)
- [ ] Automated validation against protocol specification

**Self-Verify Command:**
```bash
pytest tests/protocol_compliance/ -v && echo "Protocol compliance: PASS"
```

**Expected Evidence:**
- All 18 message types validated
- Envelope field tests cover all 6 mandatory fields
- 100% protocol compliance

**Dependencies:** M4.0, M2.1 (protocol models)
**Blocks:** QG-5

---

### M4.5: Load & Performance Tests
**Priority:** P2 (Medium)
**Estimated Time:** 2 hours

**Description:**
Create performance tests for concurrent matches and scalability validation.

**Definition of Done:**
- [ ] tests/load/test_concurrent_matches.py (50 concurrent matches)
- [ ] tests/load/test_response_times.py (latency percentiles)
- [ ] tests/load/test_1000_player_registration.py (stress test)
- [ ] tests/load/analyze_latency.py (log analysis script)
- [ ] Performance benchmarks documented

**Self-Verify Command:**
```bash
pytest tests/load/test_concurrent_matches.py --concurrent=50 -v --timeout=1800
```

**Expected Evidence:**
- System handles 50 concurrent matches
- 99th percentile latency <5s for joins, <30s for choices
- No crashes under load

**Dependencies:** M4.0, M7.7
**Blocks:** QG-5

---

### M4.6: Edge Case Matrix & Coverage Gate
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Add edge-case tests and enforce coverage thresholds.

**Definition of Done:**
- [ ] ≥5 edge-case tests (timeouts, invalid moves, auth failures, protocol mismatch, duplicate conversations)
- [ ] Coverage gate enforced at ≥85% in CI
- [ ] Documentation of edge cases and expected outcomes

**Self-Verify Command:**
```bash
pytest tests/edge_cases -v && \
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=term | grep "TOTAL" && \
cat .github/workflows/test.yml | grep "coverage"
```

**Expected Evidence:**
- Edge-case tests present and passing
- Coverage gate configured and enforced
- Edge-case matrix documented in testing guide

**Dependencies:** M4.0, M4.2
**Blocks:** QG-5

---

## M5: RESEARCH & PROTOCOL DESIGN

### M5.1: MCP Protocol Research
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Research Model Context Protocol (MCP) specification and JSON-RPC 2.0 for implementation guidance.

**Definition of Done:**
- [x] MCP protocol documentation reviewed (https://modelcontextprotocol.io/)
- [x] JSON-RPC 2.0 spec reviewed (https://www.jsonrpc.org/specification)
- [x] Notes on tool calling pattern (method, params, result/error)
- [x] Example MCP server code analyzed
- [x] FastAPI MCP integration pattern documented

**Self-Verify Command:**
```bash
cat doc/research_notes/mcp_protocol.md | grep -E "JSON-RPC 2.0|tool calling|FastAPI" && echo "Research complete"
```

**Expected Evidence:**
- Research notes document created
- Key patterns and examples documented
- Integration approach clarified

**Dependencies:** M0.2 (doc directory)
**Blocks:** M7.1

---

### M5.2: Even/Odd Game Rules Documentation
**Priority:** P0 (Critical)
**Estimated Time:** 1 hour

**Description:**
Document Even/Odd game rules, winner determination logic, and all game scenarios.

**Definition of Done:**
- [x] Game rules documented: players choose "even" or "odd", referee draws 1-10, matching parity wins
- [x] All 4 outcome scenarios documented (both even, both odd, player A match, player B match)
- [x] Draw condition: both players choose same parity
- [x] Scoring documented: Win=3pts, Draw=1pt, Loss=0pts
- [x] Decision matrix for winner determination

**Self-Verify Command:**
```bash
cat doc/game_rules/even_odd.md | grep -E "Draw|Win|Loss|parity" && echo "Rules documented"
```

**Expected Evidence:**
- Game rules document complete
- Decision matrix table for all scenarios
- Examples for each outcome type

**Dependencies:** M0.2
**Blocks:** M7.5 (referee game logic implementation)

---

### M5.3: Round-Robin Scheduling Algorithm
**Priority:** P0 (Critical)
**Estimated Time:** 1.5 hours

**Description:**
Research and document round-robin tournament scheduling algorithm for n*(n-1)/2 matches.

**Definition of Done:**
- [x] Algorithm documented: for n players, generate all unique pairs
- [x] Match distribution across rounds for balance
- [x] Referee assignment strategy (even distribution)
- [x] Example schedules: 4 players (6 matches, 3 rounds), 6 players (15 matches, 5 rounds)
- [x] Python implementation pseudocode

**Self-Verify Command:**
```bash
cat doc/algorithms/round_robin.md | grep -E "n\*\(n-1\)/2|itertools.combinations" && echo "Algorithm documented"
```

**Expected Evidence:**
- Algorithm document with examples
- Pseudocode for implementation
- Test cases for verification

**Dependencies:** M0.2
**Blocks:** M7.6 (League Manager scheduling)

---

### M5.4: Error Handling Strategy Design
**Priority:** P1 (High)
**Estimated Time:** 1 hour

**Description:**
Design comprehensive error handling strategy covering all 18 error codes and retry scenarios.

**Definition of Done:**
- [x] All 18 error codes documented with: code, name, severity, retryable flag, description
- [x] Error response format defined (LEAGUE_ERROR, GAME_ERROR messages)
- [x] Retry policy documented: which errors retry, which fail fast
- [x] Error logging strategy: what to log, log level per error type
- [x] Recovery procedures for each error category

**Self-Verify Command:**
```bash
cat doc/reference/error_handling_strategy.md | grep -E "E001|E018|retryable|LEAGUE_ERROR" && echo "Strategy documented"
```

**Expected Evidence:**
- Error codes table with all 18 codes
- Decision tree for retry vs. fail fast
- Error handling flowchart

**Dependencies:** M0.2
**Blocks:** M7.x (all agents need error handling)

---

### M5.5: Simulation & Research Notebook
**Priority:** P2 (Medium)
**Estimated Time:** 3-4 hours

**Description:**
Create comprehensive research/experimentation Jupyter notebook to analyze strategies, timeouts, and load behaviors with rigorous scientific methodology.

**Definition of Done:**
- [ ] Jupyter notebook in `doc/research_notes/experiments.ipynb` with ≥8 cells
- [ ] ≥2 LaTeX formulas (e.g., win rate calculation, expected value, probability distributions)
- [ ] ≥4 plots/visualizations (e.g., strategy comparison, timeout impact, latency distribution, win rate by strategy)
- [ ] ≥3 academic/technical references cited (papers, RFCs, documentation)
- [ ] Experiments covering: parity choice strategies (random, biased, adaptive), retry/backoff timing sensitivity, timeout impact on match outcomes
- [ ] Statistical analysis with confidence intervals or significance testing
- [ ] Recommendations for optimal configuration parameters
- [ ] Notebook executes without errors and generates all outputs

**Self-Verify Command:**
```bash
jupyter nbconvert --to html --execute doc/research_notes/experiments.ipynb && \
ls doc/research_notes/experiments.html && \
grep -E "LaTeX|\\$\\$|\\\\[a-z]" doc/research_notes/experiments.ipynb && \
echo "Research notebook complete with formulas"
```

**Expected Evidence:**
- Executable notebook with ≥8 cells
- ≥2 LaTeX formulas visible in rendered output
- ≥4 plots generated and displayed
- ≥3 references cited in bibliography/footnotes
- Actionable insights and recommendations

**Dependencies:** M1.4 (research plan), M5.1, M4.x (test harness)
**Blocks:** M8.7

---

## M6: UX & DEVELOPER EXPERIENCE

### M6.1: CLI Argument Parsing
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Implement command-line argument parsing for all agent main.py files using argparse.

**Definition of Done:**
- [ ] argparse configuration in each agent's main.py
- [ ] Common arguments: --config, --log-level, --port
- [ ] Agent-specific arguments: --player-id, --referee-id, --league-id
- [ ] --help displays usage information
- [ ] --version displays agent version
- [ ] Validation of required arguments

**Self-Verify Command:**
```bash
python agents/player_P01/main.py --help | grep -E "usage:|--player-id|--config" && \
python agents/league_manager/main.py --help | grep -E "usage:|--league-id"
```

**Expected Evidence:**
- All agents support --help and --version
- Required arguments validated
- Help text is clear and informative

**Dependencies:** M7.1 (agent main.py must exist)
**Blocks:** M9.0 (deployment scripts)

---

### M6.2: Operational Scripts
**Priority:** P1 (High)
**Estimated Time:** 2 hours

**Description:**
Create shell scripts for common operations: start league, stop league, health check, backup/restore.

**Definition of Done:**
- [ ] scripts/start_league.sh - Launches all agents in correct order
- [ ] scripts/stop_league.sh - Graceful shutdown of all agents
- [ ] scripts/check_health.sh - Health check all agent endpoints
- [ ] scripts/backup_data.sh - Backup data/ and logs/
- [ ] scripts/restore_data.sh - Restore from backup
- [ ] All scripts executable (chmod +x)

**Self-Verify Command:**
```bash
chmod +x scripts/*.sh && \
bash -n scripts/start_league.sh && \
bash -n scripts/stop_league.sh && \
echo "Scripts valid"
```

**Expected Evidence:**
- All scripts exist and are executable
- Bash syntax validation passes
- Scripts include error handling

**Dependencies:** M0.2, M6.1
**Blocks:** M9.2 (deployment)

---

### M6.3: Developer Quick Start Guide
**Priority:** P1 (High)
**Estimated Time:** 1 hour

**Description:**
Create README.md with quick start guide, installation steps, and common commands.

**Definition of Done:**
- [ ] README.md with project overview
- [ ] Installation section: Python version, venv, pip install
- [ ] Quick start section: Launch agents, run league
- [ ] Testing section: Run tests, check coverage
- [ ] Troubleshooting section: Common issues and solutions
- [ ] Links to PRD and Missions documents

**Self-Verify Command:**
```bash
cat README.md | grep -E "# Even/Odd League|## Installation|## Quick Start|## Testing" && echo "README complete"
```

**Expected Evidence:**
- README.md exists with all sections
- Installation steps are clear and tested
- Quick start commands work

**Dependencies:** M0.2
**Blocks:** M9.3 (final submission)

---

### M6.4: API Reference Documentation
**Priority:** P2 (Medium)
**Estimated Time:** 2 hours

**Description:**
Document all MCP tools exposed by each agent with request/response examples.

**Definition of Done:**
- [ ] doc/reference/api_reference.md created
- [ ] League Manager tools documented (register_referee, register_player, report_match_result, get_standings)
- [ ] Referee tools documented (start_match, collect_choices)
- [ ] Player tools documented (handle_game_invitation, choose_parity, notify_match_result)
- [ ] Each tool has: description, parameters, return value, example JSON
- [ ] Error responses documented

**Self-Verify Command:**
```bash
cat doc/reference/api_reference.md | grep -E "handle_game_invitation|choose_parity|notify_match_result|register_player" && echo "API docs complete"
```

**Expected Evidence:**
- API reference complete for all 9 tools
- JSON examples are valid and tested
- Error scenarios documented

**Dependencies:** M0.2, M7.x (tools must be implemented)
**Blocks:** M8.3

---

### M6.5: Screenshots & UX Documentation
**Priority:** P1 (High)
**Estimated Time:** 2 hours

**Description:**
Capture screenshots and document user experience for all agent interactions and system states.

**Definition of Done:**
- [ ] ≥8 screenshots captured (≥20 for 90+ target)
- [ ] Screenshots cover: agent startup, registration flow, match invitation, parity choice, match result, standings update, error scenarios, graceful shutdown
- [ ] doc/screenshots/ directory with organized PNG/JPG files
- [ ] doc/ux_documentation.md with screenshot captions and UX commentary
- [ ] Terminal output screenshots showing CLI interactions
- [ ] Log output screenshots showing structured logging

**Self-Verify Command:**
```bash
ls doc/screenshots/*.png | wc -l && \
cat doc/ux_documentation.md | grep -E "Screenshot|Figure|UX|User Experience" && \
echo "Screenshots and UX docs complete"
```

**Expected Evidence:**
- ≥8 screenshots present (aim for ≥20 for highest grade)
- Screenshots clearly labeled and organized
- UX documentation explains each screenshot

**Dependencies:** M7.14 (system must be running)
**Blocks:** M8.4

---

### M6.6: Usability Analysis
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Analyze system usability based on CLI design principles and accessibility standards.

**Definition of Done:**
- [ ] doc/usability_analysis.md created
- [ ] CLI design principles analysis (discoverability, consistency, feedback, error prevention)
- [ ] Accessibility considerations (screen readers, color contrast, text output)
- [ ] Usability heuristics evaluation (Nielsen's 10 heuristics)
- [ ] Error message clarity assessment
- [ ] Documentation clarity evaluation

**Self-Verify Command:**
```bash
cat doc/usability_analysis.md | grep -E "CLI|Usability|Accessibility|Heuristics|Nielsen" && echo "Usability analysis complete"
```

**Expected Evidence:**
- Usability analysis document complete
- CLI principles evaluated
- Accessibility considerations documented
- Recommendations for improvements

**Dependencies:** M6.5 (screenshots), M6.1 (CLI must exist)
**Blocks:** M8.7

---

### M6.7: Code Quality Tooling ✅ COMPLETED (2025-12-19)
**Priority:** P1 (High)
**Estimated Time:** 2 hours
**Status:** ✅ Complete

**Description:**
Configure linting, formatting, and type-checking for the codebase.

**Definition of Done:**
- [x] `.flake8` and `pyproject.toml` with pylint/flake8 settings (line length: 104)
- [x] `black` formatter configured (line length: 104, consistent with flake8)
- [x] `mypy` configured with per-module ignores in mypy.ini
- [x] Commands documented in README Quality Standards section and CONTRIBUTING.md

**Self-Verify Command:**
```bash
black --check agents SHARED && \
flake8 agents SHARED && \
pylint agents SHARED && \
mypy agents SHARED --strict
```

**Expected Evidence:**
- Config files present and enforced
- Lint/format/type-check pass on clean tree
- Deviations justified with inline comments or config ignores

**Dependencies:** M0.3
**Blocks:** M6.7, CI setup

---

### M6.8: Pre-Commit Hooks & Style Guide ✅ COMPLETED (2025-12-19)
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours
**Status:** ✅ Complete

**Description:**
Establish automated quality gates locally and codify team standards.

**Definition of Done:**
- [x] `.pre-commit-config.yaml` with 10 hooks: black, isort, flake8, mypy, trailing-whitespace, end-of-file-fixer, check-yaml, check-json, detect-private-key, check-added-large-files
- [x] `CONTRIBUTING.md` (300+ lines) covering code style, commit messages (Conventional Commits), branching strategy, PR checklist, testing requirements, quality gates
- [x] Hooks installed (.git/hooks/pre-commit) and documented in README Quality Standards section

**Self-Verify Command:**
```bash
pre-commit run --all-files && \
cat CONTRIBUTING.md | grep -E "Code Style|Commit|Branch"
```

**Expected Evidence:**
- Hooks run cleanly on repo
- Style guide exists with actionable rules
- Developers can onboard with one command

**Dependencies:** M6.7
**Blocks:** M6.9

---

### M6.9: CI/CD Pipeline ⚠️ PARTIALLY COMPLETE (2025-12-19)
**Priority:** P1 (High)
**Estimated Time:** 2 hours
**Status:** ⚠️ Workflow created, awaiting GitHub upload

**Description:**
Create GitHub Actions (or GitLab CI) workflow to enforce quality gates.

**Definition of Done:**
- [x] `.github/workflows/test.yml` created with: black, isort, flake8, mypy, pytest with coverage
- [x] Caches pip dependencies for speed (cache: 'pip')
- [x] Coverage gate configured (fail if <85%)
- [x] Tests on Python 3.10 and 3.11 matrix
- [x] Uploads coverage reports (Codecov, HTML artifacts)
- [ ] Workflow uploaded to GitHub (requires manual upload due to OAuth scope)
- [ ] Badges added to README (pending workflow upload)

**Self-Verify Command:**
```bash
cat .github/workflows/test.yml | grep -E "pytest|mypy|flake8|black" && echo "CI wired"
```

**Expected Evidence:**
- Workflow passes on main branch
- Quality gates enforced automatically
- Artifacts (coverage HTML) uploaded

**Dependencies:** M6.7, M6.8
**Blocks:** M9.0

---

### M6.10: README Quality Gate
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Enhance README with all required sections per kickoff agent guidance.

**Definition of Done:**
- [ ] Sections: Overview, Architecture summary, Setup, Quick Start, Testing, Lint/Type-check commands, CI status/badges placeholder, Troubleshooting, Support matrix, Links to PRD/Missions
- [ ] Commands verified on clean env
- [ ] Table of contents for navigation

**Self-Verify Command:**
```bash
cat README.md | grep -E "Architecture|Testing|Lint|Type|Troubleshooting" && echo "README sections present"
```

**Expected Evidence:**
- README comprehensive and actionable
- Matches actual commands/config
- No stale instructions

**Dependencies:** M6.7, M6.8, M6.9
**Blocks:** M9.3

---

### M6.11: Packaging & Release Standards
**Priority:** P2 (Medium)
**Estimated Time:** 1.5 hours

**Description:**
Ensure project is installable and production-aligned.

**Definition of Done:**
- [ ] `pyproject.toml`/setup.cfg for agents package (pip-installable) with entry points as needed
- [ ] Logging config file (YAML/JSON) documented and used by agents
- [ ] Repository structure validated against package organization guidelines (__init__.py in packages)
- [ ] Release/build script to generate wheel/sdist

**Self-Verify Command:**
```bash
pip install . && \
python -c \"import agents\" && \
python -c \"import league_sdk\" && \
ls dist | grep whl
```

**Expected Evidence:**
- Install succeeds in clean venv
- Packages import without issues
- Build artifacts generated

**Dependencies:** M6.7
**Blocks:** M9.2

---

## M7: AGENT IMPLEMENTATION

### M7.1: Agent Base Class & Common Utilities
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Create base agent class with common functionality: HTTP server setup, lifecycle management, logging.

**Definition of Done:**
- [x] agents/base/agent_base.py with BaseAgent class
- [x] Common methods: start(), stop(), register(), setup_logger(), load_config()
- [x] FastAPI app initialization
- [x] Uvicorn server configuration
- [x] Graceful shutdown handler (SIGTERM/SIGINT)
- [x] Unit tests for base class

**Self-Verify Command:**
```bash
python -c "from agents.base.agent_base import BaseAgent; print('BaseAgent OK')" && \
pytest tests/unit/test_agent_base.py -v
```

**Expected Evidence:**
- BaseAgent class importable
- Lifecycle methods work (start/stop)
- Graceful shutdown tested

**Dependencies:** M2.x (SDK), M0.3 (dependencies)
**Blocks:** M7.2, M7.3, M7.4, M7.6

---

### M7.2: Player Agent - MCP Server Setup
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Set up FastAPI MCP server for player agent with /mcp endpoint and tool routing.

**Definition of Done:**
- [x] agents/player_P01/server.py with FastAPI app
- [x] POST /mcp endpoint accepting JSON-RPC 2.0 requests
- [x] Request routing to tool handlers based on method name
- [x] Error handling for unknown methods
- [x] JSON-RPC 2.0 response format (result/error, id)
- [x] Server starts on configured port (8101)

**Thread Safety (Already Implemented ✅):**
- [x] MCP endpoint is async: `async def mcp(request: Request)` (server.py:113)
- [x] Uses `await asyncio.wait_for()` for timeout handling (server.py:137)
- [x] Uses async `call_with_retry()` for registration (server.py:310)
- [x] Pattern established for Mission 7.5+ agents to follow

**Self-Verify Command:**
```bash
python agents/player_P01/main.py --player-id=P01 --port=8101 &
sleep 2 && \
curl -X POST http://localhost:8101/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"GAME_INVITATION","params":{"protocol":"league.v2","message_type":"GAME_INVITATION","sender":"referee:REF01","timestamp":"2025-01-01T00:00:00Z","conversation_id":"conv-smoke-1","league_id":"league_2025_even_odd","round_id":1,"match_id":"R1M1","game_type":"even_odd","role_in_match":"PLAYER_A","opponent_id":"P02"},"id":1}' && \
pkill -f "player_P01"
```

**Expected Evidence:**
- Server starts without errors
- /mcp endpoint responds to POST
- JSON-RPC 2.0 format validated

**Dependencies:** M7.1, M2.1
**Blocks:** M7.3

---

### M7.3: Player Agent - Three Mandatory Tools
**Priority:** P0 (Critical)
**Estimated Time:** 4 hours

**Description:**
Implement handle_game_invitation, choose_parity, notify_match_result tools for player agent.

**Definition of Done:**
- [x] handle_game_invitation() - Accepts GAME_INVITATION, returns GAME_JOIN_ACK within 5s
- [x] choose_parity() - Accepts CHOOSE_PARITY_CALL, returns choice ("even"/"odd") within 30s
- [x] notify_match_result() - Accepts GAME_OVER, updates history, returns acknowledgment
- [x] All tools validate message envelope
- [x] All tools include auth_token in responses
- [x] Enforce protocol == league.v2 and map validation errors to E002 (JSON-RPC -32602)
- [x] Reject unsupported game_type via games_registry config (E002) and ensure sender format is valid
- [x] Cross-check incoming sender against agents_config entries; reject mismatches with E004/E018
- [x] Auth token required on all non-registration calls (E012 on missing/invalid)
- [x] Load player metadata/port from agents_config/defaults to avoid drift
- [x] Map errors consistently: invalid params → -32602/E002, unknown method → -32601/E018, protocol mismatch → E011, timeout → E001
- [x] Log each tool call with conversation_id/match_id correlation
- [x] Strategy for choose_parity: random choice initially
- [x] Unit tests for each tool

**Self-Verify Command:**
```bash
pytest tests/unit/test_player_agent/test_tools.py -v && \
python tests/manual/test_player_tools.py --player-id=P01 --test-all
```

**Expected Evidence:**
- All 3 tools respond correctly
- Response times within limits (5s, 30s)
- Unit tests pass with ≥85% coverage

**Dependencies:** M7.2
**Blocks:** QG-2, M7.5

---

### M7.4: Player Agent - Registration & Lifecycle
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement player registration with League Manager and lifecycle state management.

**Definition of Done:**
- [x] send_registration_request() - Sends LEAGUE_REGISTER_REQUEST to League Manager
- [x] handle_registration_response() - Stores player_id and auth_token
- [x] State machine: INIT → REGISTERED → ACTIVE → SHUTDOWN
- [x] Retry registration on failure (3 retries with backoff)
- [x] Update state to REGISTERED on success
- [x] Use agents_config.json for player metadata/endpoint and system.json for LM endpoint/ports
- [x] Include protocol version league.v2 and validate LM response; store auth_token for later tool calls
- [x] Log state transitions and registration outcomes with correlation ids
- [x] Map errors consistently: invalid params → -32602/E002, protocol mismatch → E011, timeout → E001
- [ ] Integration test: Player registers successfully

**Self-Verify Command:**
```bash
pytest tests/integration/test_player_registration.py -v && \
grep "REGISTERED" logs/agents/P01.log.jsonl
```

**Expected Evidence:**
- Player sends registration request
- Player stores auth_token
- State transitions logged
- Integration test passes

**Dependencies:** M7.3, M2.5 (retry policy)
**Blocks:** QG-2

---

#### M7.4.5: Player Data Cleanup on Unregister
**Priority:** P2 (Medium)
**Estimated Time:** 30 minutes

**Description:**
Implement cleanup of player-specific data when a player unregisters from the league.

**Definition of Done:**
- [x] Add cleanup_player_data() method to PlayerAgent
- [x] On unregister/shutdown: Archive player history
- [x] Delete temporary player files (if any)
- [x] Log cleanup completion
- [ ] Unit test for player cleanup

**Self-Verify Command:**
```bash
# Create test player history and verify cleanup
python -c "from pathlib import Path; import asyncio; from agents.player_P01.server import PlayerAgent; \
  agent = PlayerAgent('P01'); asyncio.run(agent.cleanup_player_data())" && \
ls SHARED/archive/players/P01/history_shutdown.json.gz
```

**Expected Evidence:**
- Player history archived to SHARED/archive/players/{player_id}/history_shutdown.json.gz
- Cleanup logged in player logs
- Archive directory created automatically

**Dependencies:** M7.4, M3.7 (Data Retention Policy)
**Blocks:** None (optional enhancement)

---

### M7.5: Referee Agent - Match Conductor ✅ COMPLETED (2025-12-23)
**Priority:** P0 (Critical)
**Estimated Time:** 5 hours

**Description:**
Implement complete match conductor flow: invitation → acknowledgment → choices → result → report.

**6-Step Match Protocol (as per PRD Section 8.2.1):**
- [x] conduct_match() - Orchestrates full match flow following 6 core steps
- [x] Step 1: Send GAME_INVITATION to both players
- [x] Step 2: Wait for GAME_JOIN_ACK (5s timeout each, retry policy)
- [x] Step 3: Send CHOOSE_PARITY_CALL to both players
- [x] Step 4: Receive PARITY_CHOICE responses (30s timeout each)
- [x] Step 5: Draw random number (1-10), determine outcome using Even/Odd logic
- [x] Step 6: Send GAME_OVER to both players with results
- [x] Post-Match: Send MATCH_RESULT_REPORT to League Manager
- [x] Match state machine: WAITING_FOR_PLAYERS → COLLECTING_CHOICES → DRAWING_NUMBER → FINISHED
- [x] Complete match transcript logged (MatchRepository with atomic writes)

**Thread Safety Requirements (CRITICAL):**
- [ ] ✅ Use async/await for all HTTP calls (`await call_with_retry()`)
- [ ] ✅ conduct_match() must be async function
- [ ] ✅ Use `asyncio.gather()` for concurrent invitations to both players
- [ ] ✅ Use `await asyncio.sleep()` for delays (never `time.sleep()`)
- [ ] ✅ Each match isolated by unique conversation_id
- [ ] ✅ Can handle 50+ concurrent matches without blocking
- [ ] ✅ Reference: `doc/architecture/thread_safety.md` Section 2.4

**Self-Verify Command:**
```bash
pytest tests/integration/test_match_flow.py -v && \
cat data/matches/league_2025_even_odd/R1M1.json | jq '.lifecycle.state'
```

**Expected Evidence:**
- Match completes successfully
- All 6 core steps + post-match reporting execute in order
- Match transcript includes all messages
- Integration test passes

**Dependencies:** M7.1, M7.3 (player must respond)
**Blocks:** QG-3

---

### M7.6: Referee Agent - Timeout Enforcement ✅ COMPLETED (2025-12-23)
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement timeout enforcement for GAME_JOIN_ACK (5s) and CHOOSE_PARITY_RESPONSE (30s).

**Definition of Done:**
- [x] wait_for_join_ack() - 5s timeout, retry 3 times with backoff
- [x] wait_for_parity_choice() - 30s timeout, retry 3 times
- [x] award_technical_loss() - Award WIN to opponent on timeout (in game_logic.py)
- [x] send_game_error() - Send GAME_ERROR (E001) to offending player
- [x] Log timeout events with error codes (E001 TIMEOUT_ERROR)
- [x] Unit tests for timeout scenarios (12/12 passing, 98% coverage)

**Self-Verify Command:**
```bash
pytest tests/integration/test_timeout_enforcement.py -v && \
grep "E001" logs/agents/REF01.log.jsonl
```

**Expected Evidence:**
- Timeouts enforced correctly
- Technical losses awarded
- GAME_ERROR messages sent
- Tests pass for both timeout types

**Dependencies:** M7.5, M2.5 (retry policy)
**Blocks:** QG-3

---

### M7.7: Referee Agent - Even/Odd Game Logic ✅ COMPLETED (2025-12-23)
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement Even/Odd game winner determination logic.

**Definition of Done:**
- [x] determine_winner() - Returns WIN/DRAW/LOSS based on choices and drawn number
- [x] draw_random_number() - Returns 1-10 with cryptographic randomness (secrets.randbelow)
- [x] check_parity() - Returns "even" or "odd" for given number
- [x] Handle all 4 scenarios: both even, both odd, player A match, player B match
- [x] Handle DRAW: both players choose same parity
- [x] Unit tests with 100 iterations (22 tests passing, 98% coverage)

**Self-Verify Command:**
```bash
pytest tests/unit/test_even_odd_logic.py --iterations=100 -v && \
python tests/manual/test_game_logic.py --verify-all-scenarios
```

**Expected Evidence:**
- All 4 outcome scenarios tested
- Draw scenario tested
- 100 iterations pass
- Randomness verified (roughly 50% even/odd distribution)

**Dependencies:** M7.5, M5.2 (game rules)
**Blocks:** QG-3

---

### M7.8: Referee Agent - Registration & Setup ✅ COMPLETED (2025-12-23)
**Priority:** P0 (Critical)
**Estimated Time:** 1.5 hours

**Description:**
Implement referee registration with League Manager.

**Definition of Done:**
- [x] send_referee_registration() - Sends REFEREE_REGISTER_REQUEST (register_with_league_manager method)
- [x] Include referee metadata: display_name, version, game_types, endpoint, max_concurrent_matches
- [x] Store referee_id and auth_token from response
- [x] Retry on failure (3 retries with backoff via call_with_retry)
- [x] Integration test: Referee registers successfully (13 tests passing)

**Self-Verify Command:**
```bash
pytest tests/integration/test_referee_registration.py -v && \
grep "REFEREE_REGISTER_RESPONSE" logs/agents/REF01.log.jsonl
```

**Expected Evidence:**
- Referee sends registration
- Referee stores auth_token
- Integration test passes

**Dependencies:** M7.1, M7.5
**Blocks:** M7.9

---

### M7.9: League Manager - Registration Handler
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Implement registration endpoint accepting REFEREE_REGISTER_REQUEST and LEAGUE_REGISTER_REQUEST.

**Definition of Done:**
- [ ] register_referee tool - Generates referee_id (REF01, REF02...), auth_token, stores metadata
- [ ] register_player tool - Generates player_id (P01, P02...), auth_token, stores metadata
- [ ] validate_registration() - Check for duplicate registrations (E017)
- [ ] generate_auth_token() - Cryptographically random 32+ character token
- [ ] Store registrations in memory (dict)
- [ ] Return REFEREE_REGISTER_RESPONSE / LEAGUE_REGISTER_RESPONSE
- [ ] Unit tests for registration logic

**Thread Safety Requirements (CRITICAL):**
- [ ] ✅ MCP endpoint must be async: `async def mcp(request: Request)`
- [ ] ✅ All registration handlers must be async
- [ ] ✅ Store registrations in memory (dict) - no file I/O during registration
- [ ] ✅ Use BaseAgent.register() pattern (already async in base class)
- [ ] ✅ Can handle concurrent registrations from multiple agents

**Self-Verify Command:**
```bash
pytest tests/unit/test_league_manager/test_registration.py -v && \
python tests/manual/test_registration_endpoint.py --agent-type=player
```

**Expected Evidence:**
- Both registration tools work
- Unique IDs generated (P01, P02, REF01, REF02)
- Auth tokens are unique and random
- Duplicate registration rejected

**Dependencies:** M7.1, M2.1
**Blocks:** M7.10

---

#### M7.9.1: Async HTTP Client Migration (PREREQUISITE)
**Priority:** P0 (CRITICAL - BLOCKING)
**Estimated Time:** 2-3 hours

**Description:**
Migrate from synchronous `requests` library to async `httpx` client to enable non-blocking HTTP calls. This is CRITICAL for handling 50+ concurrent matches without blocking the event loop.

**Current Problem:**
```python
# SHARED/league_sdk/retry.py:350-400 (current implementation)
def call_with_retry(url, payload, ...):
    """BLOCKS ENTIRE EVENT LOOP!"""
    response = requests.post(url, json=payload, timeout=timeout)  # ← BLOCKING!
    return response.json()
```

**Impact:**
- ✅ Works for single matches (current Mission 7.6 testing)
- ❌ Will BLOCK event loop with 50+ concurrent matches
- ❌ Referee handling multiple matches will freeze on HTTP calls
- ❌ Deadlock scenario: All matches waiting for each other

**Required Fix:**
```python
# SHARED/league_sdk/retry.py (async version)
import httpx

async def call_with_retry(url, payload, logger, max_retries=3, timeout=10):
    """Non-blocking async HTTP calls."""
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=timeout)
        return response.json()
```

**Definition of Done:**
- [ ] Install `httpx` package: `pip install httpx`
- [ ] Update `call_with_retry()` in `league_sdk/retry.py` to async
- [ ] Update `BaseAgent.register()` to async (if needed)
- [ ] Update all callers to use `await call_with_retry(...)`
- [ ] Update timeout enforcement to use async HTTP
- [ ] Update match conductor to use async HTTP
- [ ] All existing tests still pass (256 tests)
- [ ] Verify non-blocking: 50 concurrent matches complete in <60s (not 1500s)

**Files to Update:**
| File | Function | Change Required | Severity |
|------|----------|----------------|----------|
| `league_sdk/retry.py` | `call_with_retry()` | Add `async`, use `httpx` | **CRITICAL** |
| `agents/base/agent_base.py` | `register()` | Add `async` (if needed) | **HIGH** |
| `agents/referee_*/match_conductor.py` | `conduct_match()` | Already `async` ✓ | ✓ NO CHANGE |
| `agents/league_manager/*` | All tools | Add `async` | **HIGH** |

**Thread Safety Verification:**
```python
# Test concurrent match handling
import asyncio
import time

async def test_concurrent_matches():
    """Verify 50 concurrent matches complete in ~30s (not 1500s)"""
    start = time.time()

    # Simulate 50 concurrent matches, each taking 30s for parity choice
    tasks = [conduct_match(f"M{i}") for i in range(50)]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start

    # Should complete concurrently in ~30s, not sequentially in 1500s
    assert elapsed < 60, f"BLOCKING DETECTED! Took {elapsed}s (expected <60s)"
    print(f"✅ Non-blocking verified: 50 matches in {elapsed}s")
```

**Self-Verify Command:**
```bash
# 1. Install httpx
pip install httpx

# 2. Run all tests
pytest tests/ -v

# 3. Test concurrent execution
python tests/performance/test_concurrent_capacity.py --matches=50

# 4. Verify non-blocking behavior
pytest tests/unit/test_async_http.py -v
```

**Expected Evidence:**
- All 256 existing tests pass
- New async HTTP tests pass
- 50 concurrent matches complete in <60 seconds
- No event loop blocking detected
- `httpx` imported successfully

**Why This Is Critical:**
From `thread_safety.md` Section 11.1:
> **Referee handling 50 concurrent matches makes 50 synchronous HTTP calls**
> **Each call blocks for up to 30 seconds (parity choice timeout)**
> **Event loop completely frozen → other matches can't progress**
> **Deadlock scenario: All matches waiting for each other**

**Dependencies:** M7.6 (Timeout Enforcement - completed)
**Blocks:** M7.9 (League Manager), M7.14 (Full System Integration)
**MUST BE COMPLETED BEFORE:** Any League Manager implementation or concurrent match testing

---

#### M7.9.5: Data Retention Initialization
**Priority:** P1 (High)
**Estimated Time:** 30 minutes

**Description:**
Initialize data retention subsystem when League Manager starts.

**Definition of Done:**
- [ ] Load retention config on startup
- [ ] Verify archive directories exist
- [ ] Log retention policy status
- [ ] Create archive directories if missing
- [ ] Unit test for retention initialization

**Implementation Notes:**
```python
# In agents/league_manager/server.py (to be created)
from league_sdk.cleanup import get_retention_config
from pathlib import Path

class LeagueManager(BaseAgent):
    def __init__(self, league_id: str):
        super().__init__(agent_id="LM01", agent_type="league_manager")
        self.league_id = league_id

        # Initialize data retention
        self.retention_config = get_retention_config()
        self._init_data_retention()

    def _init_data_retention(self):
        """Initialize data retention subsystem."""
        if not self.retention_config.get("enabled", True):
            self.logger.warning("Data retention is DISABLED in config")
            return

        # Create archive directories
        archive_path = Path(self.retention_config.get("archive_path", "SHARED/archive"))
        for subdir in ["logs", "matches", "players", "leagues"]:
            (archive_path / subdir).mkdir(parents=True, exist_ok=True)

        self.logger.info("Data retention initialized", extra={
            "logs_retention_days": self.retention_config.get("logs_retention_days"),
            "match_retention_days": self.retention_config.get("match_data_retention_days"),
            "archive_enabled": self.retention_config.get("archive_enabled"),
            "archive_path": str(archive_path)
        })
```

**Self-Verify Command:**
```bash
# Verify archive directories created
ls -la SHARED/archive/ && \
grep "Data retention initialized" logs/league/LM01.log.jsonl
```

**Expected Evidence:**
- Archive directories created (logs/, matches/, players/, leagues/)
- Retention configuration logged
- No errors on startup

**Dependencies:** M7.9, M3.7 (Data Retention Policy)
**Blocks:** M7.13.5 (requires retention to be initialized)

---

### M7.10: League Manager - Round-Robin Scheduler
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Implement round-robin tournament scheduling algorithm.

**Definition of Done:**
- [ ] create_schedule() - Generates n*(n-1)/2 matches for n players
- [ ] Use itertools.combinations for unique pairs
- [ ] Distribute matches across balanced rounds
- [ ] Assign referees evenly using round-robin assignment
- [ ] Generate match IDs: R{round}M{match} (e.g., R1M1, R1M2)
- [ ] Persist schedule to data/leagues/<league_id>/rounds.json
- [ ] Unit tests: 4 players → 6 matches, 6 players → 15 matches

**Self-Verify Command:**
```bash
pytest tests/unit/test_league_manager/test_scheduler.py -v && \
python tests/manual/test_scheduler.py --players=4 --verify-count
```

**Expected Evidence:**
- Schedule generated with correct match count
- Matches distributed across rounds
- Referees assigned evenly
- Unit tests pass for 4, 6, 8 players

**Dependencies:** M7.9, M5.3 (scheduling algorithm)
**Blocks:** M7.11

---

### M7.11: League Manager - Standings Calculator
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Implement standings calculation and update logic.

**Definition of Done:**
- [ ] update_standings() - Updates standings after match result
- [ ] Award points: Win=3, Draw=1, Loss=0
- [ ] Update counters: played, wins, losses, draws
- [ ] sort_standings() - Sort by points (primary), wins (tiebreaker)
- [ ] Persist to data/leagues/<league_id>/standings.json
- [ ] Broadcast LEAGUE_STANDINGS_UPDATE to all players
- [ ] Unit tests for standings calculation

**Thread Safety Requirements (CRITICAL - Queue Processor):**
- [ ] ✅ Use `SequentialQueueProcessor` for standings updates (eliminates race conditions)
- [ ] ✅ Import: `from league_sdk import SequentialQueueProcessor`
- [ ] ✅ Create processor in `__init__()` with `_update_standings_file` callback
- [ ] ✅ Start processor in `start()` method: `await self.standings_processor.start()`
- [ ] ✅ Stop processor in `stop()` method: `await self.standings_processor.stop(timeout=10.0)`
- [ ] ✅ Enqueue results instead of direct updates (prevents race conditions)
- [ ] ✅ Reference: `SHARED/league_sdk/QUEUE_PROCESSOR_GUIDE.md` for complete examples

**Self-Verify Command:**
```bash
pytest tests/unit/test_league_manager/test_standings.py -v && \
python tests/test_standings_accuracy.py --matches=6 --verify && \
grep "SequentialQueueProcessor" agents/league_manager/*.py
```

**Expected Evidence:**
- Standings calculated correctly
- Point totals match match results
- Sorting works (points primary, wins secondary)
- Unit tests pass

**Dependencies:** M7.9, M2.3 (StandingsRepository)
**Blocks:** M7.12

---

### M7.12: League Manager - Match Result Handler
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement report_match_result tool to receive MATCH_RESULT_REPORT from referees.

**Definition of Done:**
- [ ] report_match_result tool - Accepts match result from referee
- [ ] Validate auth_token (must be from registered referee)
- [ ] Call update_standings() with result
- [ ] Update round completion status
- [ ] Broadcast LEAGUE_STANDINGS_UPDATE to all players
- [ ] Send ROUND_COMPLETED if all matches in round finished
- [ ] Integration test: Referee reports result, standings update

**Thread Safety Requirements (CRITICAL):**
- [ ] ✅ Enqueue match results to standings processor (don't update directly)
- [ ] ✅ Handler returns immediately after enqueuing (non-blocking)
- [ ] ✅ Multiple concurrent referees can safely report results: `await self.standings_processor.enqueue(result)`
- [ ] ✅ Why Queue? Without: race condition → lost updates. With: sequential → zero lost updates

**Self-Verify Command:**
```bash
pytest tests/integration/test_match_result_reporting.py -v && \
grep "LEAGUE_STANDINGS_UPDATE" logs/agents/P01.log.jsonl && \
grep "standings_processor.enqueue" agents/league_manager/*.py
```

**Expected Evidence:**
- Match results received and processed
- Standings updated immediately
- Broadcasts sent to all players
- Integration test passes

**Dependencies:** M7.11, M7.5 (referee must send results)
**Blocks:** M7.13

---

### M7.13: League Manager - League Orchestration
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Implement league orchestration: round announcements, round management, league completion.

**Definition of Done:**
- [ ] start_league() - Trigger league start after sufficient registrations
- [ ] broadcast_round_announcement() - Send ROUND_ANNOUNCEMENT to all players
- [ ] manage_round() - Track match completion, trigger next round
- [ ] detect_league_completion() - Check if all rounds finished
- [ ] identify_champion() - Find player with highest points
- [ ] broadcast_league_completed() - Send LEAGUE_COMPLETED with champion
- [ ] Integration test: Full league flow

**Thread Safety Requirements:**
- [ ] ✅ Use `asyncio.gather()` for concurrent broadcasts to all players
- [ ] ✅ Broadcasting doesn't block main orchestration loop
- [ ] ✅ Each broadcast uses `await call_with_retry()` (async)
- [ ] ✅ Handle broadcast failures gracefully with `return_exceptions=True`

**Self-Verify Command:**
```bash
pytest tests/integration/test_league_orchestration.py -v && \
grep "LEAGUE_COMPLETED" logs/league/league_2025_even_odd/league.log.jsonl && \
grep "asyncio.gather" agents/league_manager/*.py
```

**Expected Evidence:**
- League starts automatically or via trigger
- Round announcements sent before each round
- League completion detected
- Champion identified and announced

**Dependencies:** M7.10, M7.11, M7.12
**Blocks:** M7.14

---

#### M7.13.5: Automated Cleanup Scheduler
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Implement automated data retention cleanup scheduler that runs periodically.

**Definition of Done:**
- [ ] Add cleanup scheduler using asyncio task
- [ ] Run cleanup on League Manager startup
- [ ] Schedule periodic cleanup (daily at 2 AM UTC)
- [ ] Run cleanup on league completion
- [ ] Log all cleanup operations
- [ ] Handle cleanup failures gracefully
- [ ] Integration test for cleanup execution

**Implementation Notes:**
```python
# In agents/league_manager/server.py
from league_sdk.cleanup import run_full_cleanup
import asyncio
from datetime import datetime, time, timezone, timedelta

class LeagueManager(BaseAgent):
    def __init__(self, league_id: str):
        super().__init__(agent_id="LM01", agent_type="league_manager")
        self.league_id = league_id
        self.retention_config = get_retention_config()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._init_data_retention()

    async def start(self):
        """Start League Manager with cleanup scheduler."""
        super().start(run_in_thread=True)

        # Run initial cleanup on startup
        if self.retention_config.get("enabled", True):
            self.logger.info("Running initial data retention cleanup...")
            try:
                await run_full_cleanup(logger=self.std_logger)
            except Exception as e:
                self.logger.error(f"Initial cleanup failed: {e}", exc_info=True)

            # Start periodic cleanup scheduler
            self._cleanup_task = asyncio.create_task(self._run_cleanup_scheduler())

        self.logger.info("League Manager started with cleanup scheduler")

    async def _run_cleanup_scheduler(self):
        """Run periodic cleanup at scheduled time (2 AM UTC daily)."""
        while True:
            try:
                # Calculate next cleanup time (2 AM UTC)
                now = datetime.now(timezone.utc)
                next_run = datetime.combine(now.date(), time(2, 0), tzinfo=timezone.utc)

                if next_run <= now:
                    # If 2 AM already passed today, schedule for tomorrow
                    next_run += timedelta(days=1)

                sleep_seconds = (next_run - now).total_seconds()

                self.logger.info(f"Next cleanup scheduled for {next_run.isoformat()}")
                await asyncio.sleep(sleep_seconds)

                # Run cleanup
                self.logger.info("Starting scheduled data retention cleanup...")
                results = await run_full_cleanup(logger=self.std_logger)

                total_mb = sum(r.bytes_freed / (1024**2) for r in results.values())
                self.logger.info(f"Scheduled cleanup completed, freed {total_mb:.2f} MB")

            except asyncio.CancelledError:
                self.logger.info("Cleanup scheduler cancelled")
                break
            except Exception as e:
                self.logger.error(f"Cleanup scheduler error: {e}", exc_info=True)
                # Wait 1 hour before retry
                await asyncio.sleep(3600)

    async def stop(self):
        """Stop League Manager and cancel cleanup scheduler."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        super().stop()
        self.logger.info("League Manager stopped")

    async def on_league_completed(self, league_id: str):
        """Callback when league completes - run final cleanup."""
        self.logger.info(f"League {league_id} completed, running final cleanup...")

        try:
            # Archive all matches from this league immediately
            from league_sdk.cleanup import archive_old_matches

            await archive_old_matches(
                retention_days=0,  # Archive all, regardless of age
                logger=self.std_logger
            )

            self.logger.info(f"League {league_id} data archived successfully")

        except Exception as e:
            self.logger.error(f"Failed to archive league {league_id}: {e}", exc_info=True)
```

**Thread Safety:**
- ✅ Cleanup runs in background asyncio task (non-blocking)
- ✅ Uses `run_full_cleanup()` which is fully async
- ✅ Scheduler cancellation handled gracefully
- ✅ No shared mutable state (each cleanup is independent)

**Self-Verify Command:**
```bash
# Test cleanup scheduler integration
python -c "import asyncio; from agents.league_manager.server import LeagueManager; \
  lm = LeagueManager('test_league'); asyncio.run(lm.start()); asyncio.sleep(2)" && \
grep "Data retention cleanup" logs/league/LM01.log.jsonl
```

**Expected Evidence:**
- Cleanup runs on League Manager startup
- Cleanup scheduler task created and running
- Periodic cleanup scheduled for 2 AM UTC
- Final cleanup runs on league completion
- All cleanup operations logged

**Dependencies:** M7.9, M7.13, M7.9.5 (League Manager must be implemented, retention initialized)
**Blocks:** None (final enhancement)

---

### M7.14: Full System Integration
**Priority:** P0 (Critical)
**Estimated Time:** 4 hours

**Description:**
Integrate all agents and run complete 4-player league end-to-end.

**Definition of Done:**
- [ ] League Manager, 2 Referees, 4 Players all start successfully
- [ ] All agents register automatically
- [ ] League starts and creates schedule (6 matches)
- [ ] All matches execute in 3 rounds
- [ ] Standings updated after each match
- [ ] League completes with champion announcement
- [ ] All agents shut down gracefully
- [ ] E2E test passes

**Self-Verify Command:**
```bash
pytest tests/e2e/test_4_player_league.py -v --timeout=600 && \
cat data/leagues/league_2025_even_odd/standings.json | jq '.standings[0]'
```

**Expected Evidence:**
- Complete league finishes without errors
- 6 matches completed
- Final standings accurate
- Champion correctly identified
- All logs valid JSONL

**Dependencies:** M7.3, M7.5, M7.6, M7.7, M7.8, M7.9, M7.10, M7.11, M7.12, M7.13
**Blocks:** QG-4

---

**QG-2 CHECKPOINT:** Run Player Agent Quality Gate
**QG-3 CHECKPOINT:** Run Match Execution Quality Gate
**QG-4 CHECKPOINT:** Run End-to-End Quality Gate

---

## M8: DOCUMENTATION

### M8.1: Code Documentation - Docstrings
**Priority:** P1 (High)
**Estimated Time:** 3 hours

**Description:**
Add comprehensive docstrings to all public functions, classes, and modules.

**Definition of Done:**
- [ ] All public functions have docstrings (Google/NumPy style)
- [ ] All classes have docstrings with class-level description
- [ ] All modules have module-level docstrings
- [ ] Docstrings include: description, args, returns, raises, examples
- [ ] pydocstyle passes with 0 errors

**Self-Verify Command:**
```bash
pydocstyle agents/ SHARED/league_sdk/ --count && \
python -m pydoc agents.player_P01.server | grep "handle_game_invitation"
```

**Expected Evidence:**
- pydocstyle reports 0 errors
- All public APIs documented
- Examples in docstrings are valid

**Dependencies:** M7.14 (code must be complete)
**Blocks:** QG-5

---

### M8.2: Architecture Documentation
**Priority:** P1 (High)
**Estimated Time:** 2 hours

**Description:**
Create doc/architecture.md documenting system architecture, data flow, and design decisions.

**Definition of Done:**
- [ ] C4-1 (Context) and C4-2 (Container) diagrams showing agents, MCP endpoints, configs, data/log layers
- [ ] C4-3 (Component) views for League Manager, Referee, Player, shared SDK
- [ ] Sequence diagram for match flow and registration
- [ ] State machine diagrams for agent lifecycle
- [ ] Data flow diagram (config → agents → data → logs)
- [ ] API/data contracts for JSON-RPC methods and persisted JSON schemas
- [ ] ADR index linking to architecture decisions
- [ ] Concurrency approach documented (threading vs multiprocessing) and building-block responsibilities (SRP)

**Self-Verify Command:**
```bash
cat doc/architecture.md | grep -E "Architecture|Component Diagram|Data Flow|Sequence" && echo "Architecture documented"
```

**Expected Evidence:**
- Architecture document complete
- Diagrams are clear and accurate
- Covers all major architectural aspects

**Dependencies:** M0.2, M7.14
**Blocks:** M8.4

---

### M8.3: Configuration Guide
**Priority:** P1 (High)
**Estimated Time:** 1.5 hours

**Description:**
Create doc/configuration.md explaining all configuration files and settings.

**Definition of Done:**
- [ ] All config files documented: system.json, agents_config.json, league config, game registry
- [ ] Each setting explained: name, type, default, description
- [ ] Examples for common configurations
- [ ] Validation rules documented
- [ ] How to add new agents/leagues/games

**Self-Verify Command:**
```bash
cat doc/configuration.md | grep -E "system.json|agents_config.json|timeouts|retry_policy" && echo "Config documented"
```

**Expected Evidence:**
- Configuration guide complete
- All settings explained
- Examples are valid and tested

**Dependencies:** M3.x (config files), M0.2
**Blocks:** M8.4

---

### M8.4: Developer Guide
**Priority:** P2 (Medium)
**Estimated Time:** 2 hours

**Description:**
Create doc/developer_guide.md with setup instructions, common tasks, and troubleshooting.

**Definition of Done:**
- [ ] Setup section: Installation, prerequisites, verification
- [ ] Development workflow: Running tests, code quality checks, debugging
- [ ] Adding new agents: Step-by-step guide
- [ ] Adding new game types: Extension point documentation
- [ ] Troubleshooting: Common issues and solutions
- [ ] Contributing guidelines: Code style, PR process

**Self-Verify Command:**
```bash
cat doc/developer_guide.md | grep -E "Setup|Development Workflow|Troubleshooting|Contributing" && echo "Developer guide complete"
```

**Expected Evidence:**
- Developer guide complete
- Clear step-by-step instructions
- Troubleshooting covers common issues

**Dependencies:** M8.1, M8.2, M8.3
**Blocks:** M9.3

---

### M8.5: Testing Guide
**Priority:** P2 (Medium)
**Estimated Time:** 1 hour

**Description:**
Create doc/testing_guide.md explaining how to run tests and interpret results.

**Definition of Done:**
- [ ] Running tests: Unit, integration, E2E, protocol compliance, load
- [ ] Coverage measurement: How to generate and interpret coverage reports
- [ ] Writing new tests: Templates and patterns
- [ ] Debugging test failures: Tools and techniques
- [ ] CI/CD integration: GitHub Actions setup

**Self-Verify Command:**
```bash
cat doc/testing_guide.md | grep -E "pytest|coverage|integration tests|E2E" && echo "Testing guide complete"
```

**Expected Evidence:**
- Testing guide complete
- All test types covered
- Examples for writing new tests

**Dependencies:** M4.x (test infrastructure)
**Blocks:** M9.3

---

### M8.6: Architecture Decision Records (ADRs)
**Priority:** P1 (High)
**Estimated Time:** 1 hour

**Description:**
Document key architectural decisions with ADRs.

**Definition of Done:**
- [ ] `doc/architecture/adr/` directory created with numbered ADRs (e.g., 0001-use-fastapi-jsonrpc, 0002-async-httpx-client)
- [ ] Each ADR includes context, decision, alternatives, consequences, and status
- [ ] ADR index linked from architecture.md
- [ ] Minimum ADR count: ≥5 (target ≥7 for 90+)

**Self-Verify Command:**
```bash
ls doc/architecture/adr | grep 0001 && cat doc/architecture/adr/0001-use-fastapi-jsonrpc.md | grep "Decision"
```

**Expected Evidence:**
- ADRs exist and are referenced
- Decisions align with PRD and protocol requirements

**Dependencies:** M8.2
**Blocks:** M9.0

---

### M8.7: Prompt Engineering Log
**Priority:** P2 (Medium)
**Estimated Time:** Ongoing (30 min setup + ongoing entries)

**Description:**
Maintain a prompt engineering log documenting all Claude/LLM interactions used during development.

**Definition of Done:**
- [ ] doc/prompt_engineering_log.md created
- [ ] ≥10 prompt entries documented (target ≥15 for 90+)
- [ ] Each entry includes: date, prompt text, model used, purpose/context, output quality assessment, iterations/refinements
- [ ] Prompts categorized by: code generation, debugging, architecture design, documentation, testing
- [ ] Lessons learned and best practices documented
- [ ] Examples of successful and unsuccessful prompts

**Self-Verify Command:**
```bash
cat doc/prompt_engineering_log.md | grep -c "^### Entry" && \
cat doc/prompt_engineering_log.md | grep -E "Prompt|Purpose|Output|Iterations" && \
echo "Prompt log complete"
```

**Expected Evidence:**
- Prompt engineering log with ≥10 entries
- Each entry well-documented
- Insights on effective prompting strategies

**Dependencies:** M0.2
**Blocks:** M8.9

---

### M8.8: Extensibility & ISO/IEC 25010 Usability Analysis
**Priority:** P2 (Medium)
**Estimated Time:** 1.5 hours

**Description:**
Analyze extensibility and usability quality characteristics and document extension points.

**Definition of Done:**
- [ ] doc/usability_extensibility.md mapping all ISO/IEC 25010 characteristics (functional suitability, performance, compatibility, usability, reliability, security, maintainability, portability) to current design with KPIs and verification commands where applicable
- [ ] Extension points documented: adding games, agents, configs, retry/logging policies
- [ ] UX/operability considerations for MCP endpoints (timeouts, helpful errors, health checks)
- [ ] Risks and mitigations listed

**Self-Verify Command:**
```bash
cat doc/usability_extensibility.md | grep -E "ISO/IEC 25010|Extensibility|Usability" && echo "Analysis complete"
```

**Expected Evidence:**
- Clear mapping of quality attributes to current design
- Actionable guidance for future extensions

**Dependencies:** M8.2, M5.x
**Blocks:** M9.0

---

### M8.9: Evidence Matrix & Risk Register Refresh
**Priority:** P1 (High)
**Estimated Time:** 1 hour

**Description:**
Consolidate verification artifacts and risks per kickoff/PRD requirements.

**Definition of Done:**
- [ ] Evidence matrix (≥30 entries for 90+) with item, verification command, status, artifact link
- [ ] Risk register with ≥3 risks (likelihood/impact/mitigation/owner)
- [ ] Linked from PRD and README

**Self-Verify Command:**
```bash
cat doc/evidence_matrix.md | grep -c \"Evidence\" && \
cat doc/risk_register.md | grep -E \"High|Medium|Low\"
```

**Expected Evidence:**
- Evidence matrix and risk register exist and are current
- Verification commands align with tests/scripts

**Dependencies:** M1.x, M4.x, M8.8
**Blocks:** M9.0

---

## M9: SUBMISSION & DEPLOYMENT

### M9.0: Pre-Submission Checklist
**Priority:** P0 (Critical)
**Estimated Time:** 2 hours

**Description:**
Run comprehensive pre-submission checklist covering all requirements.

**Definition of Done:**
- [ ] All 74 missions completed (check Dependencies: None for last missions)
- [ ] All 5 Quality Gates passed
- [ ] Test coverage ≥85% overall
- [ ] All protocol compliance tests pass (18/18)
- [ ] All error codes tested (18/18)
- [ ] Code quality: flake8 and mypy pass
- [ ] Documentation complete: README, PRD, Missions, API docs
- [ ] No TODO/FIXME in production code
- [ ] Evidence matrix: All 35+ items verified

**Self-Verify Command:**
```bash
python scripts/verify_all_evidence.py --output=evidence_report.html && \
pytest tests/ --cov=agents --cov=SHARED/league_sdk --cov-report=html && \
flake8 agents/ SHARED/league_sdk/ && \
mypy agents/ SHARED/league_sdk/ --strict && \
grep -r "TODO\|FIXME" agents/ SHARED/league_sdk/ | wc -l
```

**Expected Evidence:**
- Evidence report shows all items passing
- Coverage report shows ≥85%
- Code quality checks pass
- No TODO/FIXME found (or all documented as future work)

**Dependencies:** M7.14, M8.x, QG-5
**Blocks:** M9.1

---

### M9.1: Final Testing & Validation
**Priority:** P0 (Critical)
**Estimated Time:** 3 hours

**Description:**
Run comprehensive final testing: full test suite, manual validation, performance tests.

**Definition of Done:**
- [ ] All unit tests pass (100+ tests)
- [ ] All integration tests pass (30+ tests)
- [ ] All E2E tests pass (5+ tests)
- [ ] All protocol compliance tests pass (18 tests)
- [ ] Load tests pass (50 concurrent matches)
- [ ] Manual testing: Start fresh league, verify completion
- [ ] Log analysis: No errors or warnings in successful run
- [ ] Performance benchmarks met (response times, throughput)

**Self-Verify Command:**
```bash
pytest tests/ -v --tb=short --duration=10 && \
pytest tests/load/test_concurrent_matches.py --concurrent=50 -v && \
python scripts/run_manual_validation.py --full-league
```

**Expected Evidence:**
- All automated tests pass
- Manual league completes successfully
- Performance within acceptable limits
- Logs show clean run (INFO level, no errors)

**Dependencies:** M9.0, QG-5
**Blocks:** M9.2

---

### M9.2: Deployment Package Creation
**Priority:** P0 (Critical)
**Estimated Time:** 1.5 hours

**Description:**
Create deployment package with all necessary files for submission.

**Definition of Done:**
- [ ] Clean build: Remove __pycache__, *.pyc, test artifacts
- [ ] Verify directory structure matches requirements
- [ ] Create archive: tar.gz or zip with project files
- [ ] Include: SHARED/, agents/, tests/, doc/, scripts/, PRD, Missions, README
- [ ] Exclude: venv/, .git/, __pycache__, *.pyc, test outputs
- [ ] Verify archive integrity (extract and test)

**Self-Verify Command:**
```bash
python scripts/create_deployment_package.py --output=LLM_Agent_Orchestration_HW7.tar.gz && \
tar -tzf LLM_Agent_Orchestration_HW7.tar.gz | head -20 && \
mkdir test_extract && tar -xzf LLM_Agent_Orchestration_HW7.tar.gz -C test_extract && \
cd test_extract && pytest tests/smoke/ -v
```

**Expected Evidence:**
- Archive created successfully
- Archive contains all required files
- Extracted archive passes smoke tests
- Archive size reasonable (<50MB)

**Dependencies:** M9.1
**Blocks:** M9.3

---

### M9.3: Final Submission
**Priority:** P0 (Critical)
**Estimated Time:** 30 minutes

**Description:**
Submit project via course platform with all required deliverables.

**Definition of Done:**
- [ ] PRD_EvenOddLeague.md uploaded
- [ ] Missions_EvenOddLeague.md uploaded
- [ ] Deployment package uploaded (tar.gz or zip)
- [ ] README.md with quick start uploaded
- [ ] Evidence report uploaded (evidence_report.html)
- [ ] Submission confirmation received
- [ ] All deadlines met

**Self-Verify Command:**
```bash
ls -lh PRD_EvenOddLeague.md Missions_EvenOddLeague.md LLM_Agent_Orchestration_HW7.tar.gz evidence_report.html README.md && \
echo "All files ready for submission"
```

**Expected Evidence:**
- All deliverable files exist and have recent timestamps
- File sizes are reasonable
- Submission confirmation email/receipt

**Dependencies:** M9.2, QG-5
**Blocks:** None (final mission)

---

### M9.4: .claude Handoff Update
**Priority:** P1 (High)
**Estimated Time:** 30 minutes

**Description:**
Finalize `.claude` living documentation with mission outcomes and handoff notes.

**Definition of Done:**
- [ ] .claude file created/updated with summary of all missions, key decisions, verification commands, file locations, and common pitfalls
- [ ] Linked from README and included in submission package
- [ ] Reflects final test/coverage results and quality gates status

**Self-Verify Command:**
```bash
cat .claude | grep -E "missions|decisions|commands" && echo ".claude updated"
```

**Expected Evidence:**
- .claude present and current
- Handoff-ready summary for evaluators

**Dependencies:** M9.0, M8.x
**Blocks:** Final submission

---

## DEPENDENCY GRAPH

```
M0.1 (Environment Setup)
  └─> M0.2 (Project Structure)
       ├─> M0.3 (Dependency Installation)
       │    └─> M2.0 (Shared SDK Package)
       │         ├─> M2.1 (Protocol Models)
       │         │    ├─> M2.2 (Config Models & Loader) ──> M3.0, M3.1, M3.2, M3.3
       │         │    ├─> M2.3 (Data Repository Layer)
       │         │    ├─> M2.4 (Structured Logging)
       │         │    │    └─> M2.5 (Retry Policy)
       │         │    └─> [QG-1: Foundation Quality Gate]
       │         │         └─> M7.1 (Agent Base Class)
       │         │              ├─> M7.2 (Player MCP Server)
       │         │              │    └─> M7.3 (Player Tools)
       │         │              │         └─> M7.4 (Player Registration)
       │         │              │              └─> [QG-2: Player Agent QG]
       │         │              ├─> M7.5 (Referee Match Conductor)
       │         │              │    ├─> M7.6 (Referee Timeout)
       │         │              │    ├─> M7.7 (Even/Odd Logic)
       │         │              │    └─> M7.8 (Referee Registration)
       │         │              │         └─> [QG-3: Match Execution QG]
       │         │              └─> M7.9.1 (Async HTTP Client Migration) ⚠️ CRITICAL
       │         │                   └─> M7.9 (League Manager Registration)
       │         │                        ├─> M7.10 (Round-Robin Scheduler)
       │         │                   ├─> M7.11 (Standings Calculator)
       │         │                   ├─> M7.12 (Match Result Handler)
       │         │                   └─> M7.13 (League Orchestration)
       │         │                        └─> M7.14 (Full System Integration)
       │         │                             └─> [QG-4: E2E Quality Gate]
       │         │                                  ├─> M8.1 (Code Documentation)
       │         │                                  ├─> M8.2 (Architecture Docs)
       │         │                                  ├─> M8.3 (Configuration Guide)
       │         │                                  ├─> M8.4 (Developer Guide)
       │         │                                  └─> M8.5 (Testing Guide)
       │         │                                       └─> M9.0 (Pre-Submission Checklist)
       │         │                                            └─> [QG-5: Production Readiness QG]
       │         │                                                 └─> M9.1 (Final Testing)
       │         │                                                      └─> M9.2 (Deployment Package)
       │         │                                                           └─> M9.3 (Final Submission)
       │         └─> M4.0 (Pytest Configuration)
       │              ├─> M4.1 (Unit Test Templates)
       │              ├─> M4.2 (Integration Test Templates)
       │              ├─> M4.3 (E2E Test Suite)
       │              ├─> M4.4 (Protocol Compliance Tests)
       │              └─> M4.5 (Load & Performance Tests)
       ├─> M1.1 (PRD Document)
       │    └─> M1.2 (Missions Document)
       ├─> M5.1 (MCP Protocol Research)
       ├─> M5.2 (Even/Odd Game Rules)
       ├─> M5.3 (Round-Robin Algorithm)
       └─> M5.4 (Error Handling Strategy)

M6.1 (CLI Argument Parsing) depends on M7.1
M6.2 (Operational Scripts) depends on M6.1
M6.3 (Developer Quick Start) depends on M0.2
M6.4 (API Reference Docs) depends on M7.x
```

**Critical Path (longest dependency chain):**
M0.1 → M0.2 → M0.3 → M2.0 → M2.1 → QG-1 → M7.1 → M7.3 → QG-2 → M7.5 → QG-3 → **M7.9.1 (Async HTTP)** → M7.9 → M7.10 → M7.11 → M7.12 → M7.13 → M7.14 → QG-4 → M8.x → M9.0 → QG-5 → M9.1 → M9.2 → M9.3

**Estimated Total Time on Critical Path:**
M0 (2h) + M2 (9.5h) + M7 (34h including M7.9.1) + M8 (9.5h) + M9 (7h) = **62 hours**

---

## MISSION SUMMARY TABLE

| Category | Missions | Total Time | Completion % | Status |
|----------|----------|------------|--------------|--------|
| **M0: Kickoff** | 3 | 2h | 100% | ☑ Complete |
| **M1: PRD** | 5 | 11h | 40% | ⏳ In Progress |
| **M2: Setup** | 7 | 12.5h | 86% | ⏳ In Progress |
| **M3: Config** | 8 | 8.5h | 62% | ⏳ In Progress |
| **M4: Testing** | 7 | 9.5h | 29% | ⏳ In Progress |
| **M5: Research** | 5 | 8h | 80% | ⏳ In Progress |
| **M6: UX** | 11 | 15.5h | 0% | ☐ Not Started |
| **M7: Agents** | 14 | 38h | 7% | ⏳ In Progress |
| **M8: Docs** | 9 | 12h | 0% | ☐ Not Started |
| **M9: Submission** | 5 | 8h | 0% | ☐ Not Started |
| **Quality Gates** | 5 | - | 20% | ⏳ In Progress |
| **TOTAL** | **74 + 5 QGs** | **125h** | **41%** | **⏳ In Progress** |

---

## TRACKING & PROGRESS

### How to Use This Missions Document

1. **Sequential Execution:** Follow missions in order, respecting dependencies
2. **Quality Gates:** Must pass QG checkpoints before proceeding
3. **Self-Verification:** Run self-verify command after each mission
4. **Evidence Collection:** Document expected evidence for grading
5. **Status Updates:** Mark missions as ☑ Complete when all DoD items checked

### Progress Tracking Commands

**Check overall progress:**
```bash
python scripts/check_mission_progress.py --status
```

**Verify specific mission:**
```bash
python scripts/verify_mission.py --mission=M7.3
```

**Generate progress report:**
```bash
python scripts/generate_progress_report.py --output=progress.html
```

---

## APPENDIX: MISSION TEMPLATES

### Unit Test Mission Template
```markdown
### M#.#: <Component> Unit Tests
**Priority:** P0/P1/P2
**Estimated Time:** X hours

**Description:**
Create comprehensive unit tests for <component> with ≥85% coverage.

**Definition of Done:**
- [ ] Test file created: tests/unit/test_<component>.py
- [ ] ≥10 test cases covering happy path, edge cases, errors
- [ ] Code coverage ≥85% for module under test
- [ ] All tests pass
- [ ] Test docstrings explain what is being tested

**Self-Verify Command:**
```bash
pytest tests/unit/test_<component>.py --cov=<module> --cov-report=term -v
```

**Expected Evidence:**
- Test file exists with ≥10 tests
- Coverage report shows ≥85%
- All tests pass (green)

**Dependencies:** <module implementation>
**Blocks:** <dependent missions>
```

### Integration Test Mission Template
```markdown
### M#.#: <Interaction> Integration Test
**Priority:** P0/P1/P2
**Estimated Time:** X hours

**Description:**
Test interaction between <Agent A> and <Agent B> for <scenario>.

**Definition of Done:**
- [ ] Test file created: tests/integration/test_<scenario>.py
- [ ] Mock/fixture for agent startup/shutdown
- [ ] Test covers complete interaction flow
- [ ] Assertions verify expected behavior
- [ ] Test cleans up resources (no orphaned processes)

**Self-Verify Command:**
```bash
pytest tests/integration/test_<scenario>.py -v --timeout=60
```

**Expected Evidence:**
- Integration test passes
- Both agents communicate successfully
- Expected messages exchanged

**Dependencies:** <both agent implementations>
**Blocks:** <dependent missions>
```

---

**END OF MISSIONS DOCUMENT**

**Total Missions:** 74 missions + 5 Quality Gates
**Estimated Total Effort:** 125 hours
**Target Grade:** 90-100 with all missions completed
**Project Type:** HYBRID (Backend API + CLI + Multi-Agent Orchestration)
