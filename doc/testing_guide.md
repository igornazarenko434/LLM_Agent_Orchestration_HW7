# Testing Guide: Even/Odd League Multi-Agent System

**Version:** 1.0.0
**Last Updated:** 2025-01-XX
**Status:** Production

---

## Table of Contents

1. [Overview](#overview)
2. [Test Suite Architecture](#test-suite-architecture)
3. [Quick Start](#quick-start)
4. [Running Tests](#running-tests)
5. [Test Categories](#test-categories)
6. [Coverage Measurement](#coverage-measurement)
7. [Writing New Tests](#writing-new-tests)
8. [Test Patterns](#test-patterns)
9. [Debugging Test Failures](#debugging-test-failures)
10. [CI/CD Integration](#cicd-integration)
11. [Test Infrastructure](#test-infrastructure)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The Even/Odd League multi-agent system includes a comprehensive test suite with **568 test functions** across **56 test files**, providing extensive coverage of all system components.

### Test Suite Statistics

| Metric | Value |
|--------|-------|
| **Total Test Functions** | 568 |
| **Total Test Files** | 56 |
| **Total Lines of Test Code** | ~11,806 |
| **Coverage Target** | ≥85% |
| **Current Coverage** | 85%+ (agents + SDK) |
| **Test Categories** | 5 (Unit, Integration, E2E, Protocol, Edge) |

### Testing Philosophy

Our testing strategy follows a **test pyramid** approach:

```
        ▲
       / \
      /E2E\      ← 4 files (comprehensive system tests)
     /─────\
    /Proto \    ← 5 files (protocol compliance)
   /───────\
  /Integrtn\   ← 11 files (component interactions)
 /─────────\
/   Unit    \  ← 29 files (component isolation)
└───────────┘
```

**Principles:**
- **Fast feedback:** Unit tests run in milliseconds
- **Confidence:** Integration tests verify component interactions
- **Reality check:** E2E tests validate real-world scenarios
- **Standards compliance:** Protocol tests ensure league.v2 adherence
- **Edge coverage:** Edge case tests validate error handling

---

## Test Suite Architecture

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                       # Shared pytest configuration and fixtures
├── pytest.ini                        # Pytest configuration
├── .coveragerc                       # Coverage configuration
│
├── unit/                             # 29 test files
│   ├── test_agents/                 # Agent base class tests (3 files)
│   │   ├── test_base_agent.py
│   │   ├── test_player_server.py
│   │   └── test_agent_base.py
│   ├── test_league_manager/         # League Manager tests (9 files)
│   │   ├── test_advanced_logic.py
│   │   ├── test_data_retention_init.py
│   │   ├── test_helpers.py
│   │   ├── test_orchestration.py
│   │   ├── test_queries.py
│   │   ├── test_registration.py
│   │   ├── test_scheduler.py
│   │   └── test_standings.py
│   ├── test_referee_agent/          # Referee tests (5 files)
│   │   ├── test_game_logic.py
│   │   ├── test_message_routing.py
│   │   ├── test_match_conductor.py
│   │   ├── test_referee_ref02.py
│   │   ├── test_referee_server.py
│   │   └── test_timeout_enforcement.py
│   └── test_sdk/                    # SDK tests (12 files)
│       ├── test_cleanup.py
│       ├── test_config_loader.py
│       ├── test_config_models.py
│       ├── test_default_configs.py
│       ├── test_games_registry.py
│       ├── test_logger.py
│       ├── test_method_aliases.py
│       ├── test_protocol_models.py
│       ├── test_queue_processor.py
│       ├── test_repositories.py
│       ├── test_retry.py
│       └── test_utils.py
│
├── integration/                     # 11 test files
│   ├── test_cleanup_scheduler.py
│   ├── test_concurrent_matches.py
│   ├── test_league_orchestration.py
│   ├── test_match_flow.py
│   ├── test_match_result_reporting.py
│   ├── test_pdf_compatibility.py
│   ├── test_player_registration.py
│   ├── test_referee_integration.py
│   ├── test_standings_update.py
│   ├── test_start_league_tool.py
│   └── test_timeout_enforcement.py
│
├── e2e/                             # 4 test files
│   ├── test_4_player_league.py
│   ├── test_graceful_shutdown.py
│   ├── test_network_failure_recovery.py
│   └── test_standings_accuracy.py
│
├── protocol_compliance/             # 5 test files
│   ├── test_auth_token_presence.py
│   ├── test_envelope_fields.py
│   ├── test_message_types.py
│   ├── test_sender_format.py
│   └── test_timestamp_format.py
│
├── edge_cases/                      # 1 test file
│   └── test_edge_cases.py
│
└── load/                            # Placeholder for future load tests
```

### Test File Naming Conventions

| Pattern | Example | Purpose |
|---------|---------|---------|
| `test_<component>.py` | `test_game_logic.py` | Tests for a specific component |
| `test_<feature>.py` | `test_registration.py` | Tests for a specific feature |
| `test_<agent>_<component>.py` | `test_referee_server.py` | Tests for agent-specific component |

### Test Function Naming

**Pattern:** `test_<action>_<condition>_<expected_result>`

**Examples:**
- `test_wait_for_join_ack_success` - Test successful join acknowledgment
- `test_wait_for_join_ack_timeout` - Test timeout scenario
- `test_envelope_missing_conversation_id_fails` - Test validation failure
- `test_duplicate_referee_registration` - Test duplicate handling
- `test_circuit_transitions_to_half_open_after_timeout` - Test state transition

---

## Quick Start

### Prerequisites

Ensure your development environment is set up (see [Developer Guide](developer_guide.md)):

```bash
# Verify Python version
python3 --version  # Should be ≥3.10

# Activate virtual environment
source venv/bin/activate

# Install dependencies (including test dependencies)
pip install -r requirements.txt

# Install SDK in editable mode
pip install -e SHARED/league_sdk
```

### Run All Tests

```bash
# From project root
PYTHONPATH=SHARED:$PYTHONPATH pytest
```

**Expected output:**
```
================================ test session starts =================================
platform darwin -- Python 3.10.x, pytest-7.x.x, pluggy-1.x.x
rootdir: /path/to/LLM_Agent_Orchestration_HW7
plugins: asyncio-0.21.x, cov-4.x.x, timeout-2.x.x
collected 568 items

tests/unit/test_sdk/test_protocol_models.py ...................        [ 3%]
tests/unit/test_sdk/test_retry.py .............................        [ 8%]
...
tests/e2e/test_4_player_league.py ....                               [100%]

========================== 568 passed in 45.23s ==================================
```

### Run Quick Smoke Test

```bash
# Run only unit tests (fast feedback)
pytest -m unit -v
```

### Check Coverage

```bash
# Run tests with coverage report
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=term-missing
```

---

## Running Tests

### Basic Commands

#### Run All Tests
```bash
pytest
```

#### Run with Verbose Output
```bash
pytest -v
```

#### Run with Print Statements Visible
```bash
pytest -s
```

#### Run with Both Verbose and Print Statements
```bash
pytest -vs
```

#### Stop on First Failure
```bash
pytest -x
```

#### Show Local Variables on Failure
```bash
pytest -l
```

---

### Running Tests by Category

The test suite uses **pytest markers** to categorize tests. Markers are automatically assigned based on directory structure (see `tests/conftest.py`).

#### Available Markers

| Marker | Directory | Description | Example Count |
|--------|-----------|-------------|---------------|
| `unit` | `tests/unit/` | Fast, isolated component tests | ~350 tests |
| `integration` | `tests/integration/` | Component interaction tests | ~120 tests |
| `e2e` | `tests/e2e/` | Full system tests with real servers | ~40 tests |
| `slow` | Various | Tests taking >5 seconds | ~50 tests |
| `protocol` | `tests/protocol_compliance/` | Protocol validation tests | ~40 tests |
| `edge` | `tests/edge_cases/` | Edge case and error handling | ~18 tests |

#### Run Tests by Marker

```bash
# Unit tests only (fast, ~2-5 seconds)
pytest -m unit

# Integration tests only (~10-20 seconds)
pytest -m integration

# E2E tests only (slow, ~30-60 seconds)
pytest -m e2e

# Protocol compliance tests only
pytest -m protocol

# Edge case tests only
pytest -m edge

# Everything except E2E tests (for quick iteration)
pytest -m "not e2e"

# Combine markers: unit OR integration
pytest -m "unit or integration"

# Combine markers: NOT slow
pytest -m "not slow"
```

---

### Running Specific Tests

#### Run Single Test File
```bash
pytest tests/unit/test_referee_agent/test_game_logic.py
```

#### Run Specific Test Class
```bash
pytest tests/unit/test_referee_agent/test_game_logic.py::TestEvenOddGameLogic
```

#### Run Specific Test Function
```bash
pytest tests/unit/test_referee_agent/test_game_logic.py::TestEvenOddGameLogic::test_draw_random_number_in_range
```

#### Run Tests Matching Name Pattern
```bash
# Run all tests with "timeout" in the name
pytest -k timeout

# Run all tests with "registration" in the name
pytest -k registration

# Run tests NOT matching pattern
pytest -k "not slow"
```

#### Run All Tests in a Directory
```bash
# All SDK tests
pytest tests/unit/test_sdk/

# All integration tests
pytest tests/integration/

# All E2E tests
pytest tests/e2e/
```

---

### Running Tests with PYTHONPATH

**IMPORTANT:** For tests to correctly import the SDK and agent modules, you must set `PYTHONPATH`:

```bash
# Correct way (from project root)
PYTHONPATH=SHARED:$PYTHONPATH pytest

# Or export it first
export PYTHONPATH=SHARED:$PYTHONPATH
pytest
```

**Why?** The SDK is installed in editable mode, but tests also need to import from `SHARED/` and `agents/` directories.

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose:** Test individual components in complete isolation using mocks.

**Characteristics:**
- **Fast:** Run in milliseconds
- **Isolated:** No network, no file I/O, no real dependencies
- **Focused:** Test single function/class/method
- **Mocked:** All external dependencies replaced with mocks

**When to use:**
- Testing business logic (e.g., game rules, scoring)
- Testing utility functions (e.g., timestamp generation)
- Testing validation logic (e.g., Pydantic models)
- Testing error handling
- Testing edge cases with specific inputs

**Example Test Files:**

#### SDK Tests (`tests/unit/test_sdk/`)
- **`test_retry.py`** - Retry logic, backoff, circuit breaker
- **`test_protocol_models.py`** - Pydantic model validation
- **`test_config_loader.py`** - Configuration loading
- **`test_repositories.py`** - Data persistence (mocked file I/O)

#### League Manager Tests (`tests/unit/test_league_manager/`)
- **`test_registration.py`** - Player/referee registration logic
- **`test_scheduler.py`** - Round-robin scheduling
- **`test_standings.py`** - Win/draw/loss calculations
- **`test_orchestration.py`** - League state machine

#### Referee Tests (`tests/unit/test_referee_agent/`)
- **`test_game_logic.py`** - Even/Odd game rules, winner determination
- **`test_match_conductor.py`** - Match orchestration logic
- **`test_timeout_enforcement.py`** - Timeout detection

**Example: Game Logic Unit Test**

**File:** `tests/unit/test_referee_agent/test_game_logic.py:28-45`

```python
class TestEvenOddGameLogic:
    @pytest.fixture
    def game_logic(self):
        """Create game logic instance."""
        return EvenOddGameLogic()

    def test_draw_random_number_distribution(self, game_logic):
        """Test random number distribution is roughly uniform."""
        # Draw 1000 random numbers
        numbers = [game_logic.draw_random_number() for _ in range(1000)]
        unique_numbers = set(numbers)

        # Verify all numbers 1-10 appear
        assert unique_numbers == set(range(1, 11))

        # Verify roughly uniform distribution (within tolerance)
        for num in range(1, 11):
            count = numbers.count(num)
            assert 50 <= count <= 150, f"Number {num} appeared {count} times (expected 70-130)"
```

**Running unit tests:**
```bash
# All unit tests
pytest -m unit

# Specific component
pytest tests/unit/test_referee_agent/test_game_logic.py -v
```

---

### 2. Integration Tests (`tests/integration/`)

**Purpose:** Test interactions between components with mocked HTTP/network layer.

**Characteristics:**
- **Medium speed:** Run in seconds
- **Partial integration:** Real component logic, mocked HTTP
- **Workflow testing:** Test complete workflows across multiple components
- **State verification:** Verify persistence and state changes

**When to use:**
- Testing workflows across multiple components (e.g., registration → match → standings)
- Testing message passing between agents
- Testing repository persistence
- Testing async coordination

**Example Test Files:**
- **`test_match_flow.py`** - Complete match workflow with mocked HTTP
- **`test_player_registration.py`** - Registration workflow
- **`test_timeout_enforcement.py`** - Timeout scenarios with mocked timers
- **`test_standings_update.py`** - Standings calculation after matches
- **`test_concurrent_matches.py`** - Multiple concurrent matches

**Example: Match Flow Integration Test**

**File:** `tests/integration/test_match_flow.py:91-164`

```python
@pytest.mark.asyncio
async def test_successful_match_flow_with_mocked_http(self, match_conductor):
    """Test complete match flow with mocked internal HTTP calls."""
    # Setup
    match_id = "M001"
    player_a_id = "P01"
    player_b_id = "P02"
    queue = asyncio.Queue()

    # Mock internal methods (not entire components)
    async def mock_send_invitations(match_id, players_info):
        """Mock sending invitations - returns immediate acknowledgment."""
        return {player_a_id: True, player_b_id: True}

    async def mock_request_parity_choices(match_id, players_info):
        """Mock parity choices - returns fixed choices."""
        return {player_a_id: "even", player_b_id: "odd"}

    # Patch methods
    with patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations), \
         patch.object(match_conductor, "_request_parity_choices", side_effect=mock_request_parity_choices):

        # Execute complete match
        result = await match_conductor.conduct_match(
            match_id=match_id,
            round_id=1,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            result_queue=queue
        )

    # Verify
    assert result["match_id"] == match_id
    assert result["lifecycle"]["state"] == "FINISHED"
    assert result["outcome"]["winner"] in [player_a_id, player_b_id, "DRAW"]
    assert "random_number" in result["game_state"]
```

**Running integration tests:**
```bash
# All integration tests
pytest -m integration

# Specific workflow
pytest tests/integration/test_match_flow.py -v

# With detailed output
pytest tests/integration/test_match_flow.py -vs
```

---

### 3. E2E Tests (`tests/e2e/`)

**Purpose:** Test the complete system with real HTTP servers and network communication.

**Characteristics:**
- **Slow:** Run in 30-60 seconds
- **Real servers:** Launch actual agent subprocesses
- **Real network:** HTTP communication via localhost
- **Complete workflows:** Test entire league execution
- **Marked with:** `@pytest.mark.e2e` and `@pytest.mark.slow`

**When to use:**
- Testing complete league execution
- Testing real network failures and recovery
- Testing graceful shutdown
- Testing multi-agent coordination
- Final validation before deployment

**Example Test Files:**
- **`test_4_player_league.py`** - Complete league with 4 players
- **`test_graceful_shutdown.py`** - Shutdown handling
- **`test_network_failure_recovery.py`** - Network resilience
- **`test_standings_accuracy.py`** - Final standings validation

**Example: 4-Player League E2E Test**

**File:** `tests/e2e/test_4_player_league.py:52-244`

```python
@pytest_asyncio.fixture(scope="class")
async def running_league(self, project_root, python_executable):
    """
    Launch complete league with League Manager, 1 Referee, and 4 Players.
    Runs league to completion and returns final standings.
    """
    processes = []

    try:
        # Step 1: Clean data directory
        data_dir = project_root / "SHARED" / "data"
        if data_dir.exists():
            shutil.rmtree(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Start League Manager
        lm_process = subprocess.Popen(
            [python_executable, "-m", "agents.league_manager.main"],
            env={**os.environ, "PYTHONPATH": f"{project_root}/SHARED:{os.environ.get('PYTHONPATH', '')}"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("League Manager", lm_process))
        await asyncio.sleep(2)  # Allow server startup

        # Verify League Manager health
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200

        # Step 3: Start Referee
        ref_process = subprocess.Popen(
            [python_executable, "-m", "agents.referee_REF01.main"],
            env={...},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("Referee REF01", ref_process))
        await asyncio.sleep(2)

        # Step 4: Start 4 Players
        for player_id in ["P01", "P02", "P03", "P04"]:
            player_process = subprocess.Popen(
                [python_executable, "-m", f"agents.player_{player_id}.main"],
                env={...}
            )
            processes.append((f"Player {player_id}", player_process))
            await asyncio.sleep(1)

        # Step 5: Start league via HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/league/start",
                json={"league_id": "league_2025_even_odd"}
            )
            assert response.status_code == 200

        # Step 6: Wait for league completion (poll every 5 seconds, max 5 minutes)
        max_wait = 300
        start_time = time.time()
        league_completed = False

        while time.time() - start_time < max_wait:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get("http://localhost:8000/api/league/status")
                    if response.status_code == 200:
                        status = response.json()
                        if status.get("state") == "FINISHED":
                            league_completed = True
                            break
                except:
                    pass
            await asyncio.sleep(5)

        # Step 7: Retrieve final standings
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/league/standings")
            standings = response.json()

        yield {
            "league_completed": league_completed,
            "final_standings": standings,
            "processes": processes
        }

    finally:
        # Cleanup: Terminate all processes
        for name, process in processes:
            try:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
```

**Test Cases Using This Fixture:**

```python
@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteLeague:
    def test_league_completes(self, running_league):
        """Verify league completes successfully."""
        assert running_league["league_completed"] is True

    def test_standings_format(self, running_league):
        """Verify standings have correct format."""
        standings = running_league["final_standings"]

        assert "rankings" in standings
        assert len(standings["rankings"]) == 4  # 4 players

        for rank in standings["rankings"]:
            assert "player_id" in rank
            assert "wins" in rank
            assert "draws" in rank
            assert "losses" in rank
            assert "points" in rank

    def test_score_calculations(self, running_league):
        """Verify score calculations are correct."""
        standings = running_league["final_standings"]

        for rank in standings["rankings"]:
            # Points = 3 * wins + 1 * draws
            expected_points = 3 * rank["wins"] + 1 * rank["draws"]
            assert rank["points"] == expected_points
```

**Running E2E tests:**
```bash
# All E2E tests (slow, ~60 seconds)
pytest -m e2e -v

# Specific E2E test
pytest tests/e2e/test_4_player_league.py -vs

# Skip E2E tests (for quick iteration)
pytest -m "not e2e"
```

---

### 4. Protocol Compliance Tests (`tests/protocol_compliance/`)

**Purpose:** Validate adherence to the `league.v2` JSON-RPC 2.0 protocol specification.

**Characteristics:**
- **Fast:** Run in milliseconds
- **Standards-focused:** Test protocol structure, not business logic
- **Marked with:** `@pytest.mark.protocol`
- **Pydantic validation:** Test model serialization/deserialization

**When to use:**
- Validating message envelope structure
- Testing required fields presence
- Testing field format (timestamps, sender format, etc.)
- Testing all 18 message types
- Testing auth token presence

**Example Test Files:**
- **`test_envelope_fields.py`** - Required envelope fields
- **`test_message_types.py`** - All 18 message type constants
- **`test_sender_format.py`** - Sender field format (`agent_type:agent_id`)
- **`test_timestamp_format.py`** - ISO 8601 timestamp format
- **`test_auth_token_presence.py`** - Auth token in all relevant messages

**Example: Envelope Field Validation**

**File:** `tests/protocol_compliance/test_envelope_fields.py:24-84`

```python
@pytest.mark.protocol
class TestEnvelopeFields:
    def test_envelope_has_required_fields(self):
        """Test that message envelope contains all required fields."""
        envelope = MessageEnvelope(
            conversation_id="conv-001",
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            protocol="league.v2"
        )

        # Verify all required fields present
        assert envelope.conversation_id == "conv-001"
        assert envelope.message_type == LEAGUE_REGISTER_REQUEST
        assert envelope.sender == "player:P01"
        assert envelope.protocol == "league.v2"
        assert envelope.timestamp is not None

    def test_envelope_missing_conversation_id_fails(self):
        """Test that envelope without conversation_id fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=None,  # Missing required field
                message_type=LEAGUE_REGISTER_REQUEST,
                sender="player:P01",
                timestamp=generate_timestamp(),
            )

    def test_protocol_defaults_to_league_v2(self):
        """Test that protocol field defaults to 'league.v2'."""
        envelope = MessageEnvelope(
            conversation_id="conv-001",
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp()
            # protocol not provided
        )

        assert envelope.protocol == "league.v2"
```

**Example: Message Type Validation**

**File:** `tests/protocol_compliance/test_message_types.py:12-30`

```python
@pytest.mark.protocol
class TestMessageTypes:
    def test_all_message_types_defined(self):
        """Test that all 18 league.v2 message types are defined."""
        expected_message_types = [
            # Registration messages
            "LEAGUE_REGISTER_REQUEST",
            "LEAGUE_REGISTER_RESPONSE",
            "REFEREE_REGISTER_REQUEST",
            "REFEREE_REGISTER_RESPONSE",

            # League lifecycle messages
            "START_LEAGUE",
            "LEAGUE_STARTED",
            "LEAGUE_FINISHED",

            # Match lifecycle messages
            "GAME_INVITATION",
            "GAME_JOIN_ACK",
            "CHOOSE_PARITY_CALL",
            "PARITY_CHOSEN",
            "GAME_OVER",
            "MATCH_RESULT_REPORT",

            # Query messages
            "QUERY_STANDINGS",
            "STANDINGS_RESPONSE",
            "QUERY_MATCH_STATE",
            "MATCH_STATE_RESPONSE",

            # Error message
            "ERROR_RESPONSE"
        ]

        # Import all message type constants
        from SHARED.league_sdk.protocol import *

        for msg_type in expected_message_types:
            assert globals()[msg_type] == msg_type
```

**Running protocol compliance tests:**
```bash
# All protocol tests
pytest -m protocol

# Specific protocol test
pytest tests/protocol_compliance/test_envelope_fields.py -v
```

---

### 5. Edge Case Tests (`tests/edge_cases/`)

**Purpose:** Test error conditions, boundary cases, and unusual scenarios.

**Characteristics:**
- **Fast:** Run in milliseconds
- **Negative testing:** Focus on what should fail
- **Error handling:** Test all error codes (E001-E018)
- **Marked with:** `@pytest.mark.edge`

**When to use:**
- Testing invalid inputs
- Testing error responses
- Testing boundary conditions
- Testing race conditions
- Testing malformed messages

**Example Test File:** `tests/edge_cases/test_edge_cases.py`

```python
@pytest.mark.edge
class TestEdgeCases:
    def test_protocol_version_mismatch_rejected(self):
        """Test that messages with wrong protocol version are rejected."""
        envelope = MessageEnvelope(
            conversation_id="conv-001",
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            protocol="league.v1"  # Wrong protocol version
        )

        # Should raise validation error (E011: PROTOCOL_MISMATCH)
        with pytest.raises(ProtocolError) as exc_info:
            validate_protocol_version(envelope)

        assert exc_info.value.error_code == "E011"

    def test_missing_auth_token_rejected(self):
        """Test that messages without auth_token are rejected (except registration)."""
        envelope = MessageEnvelope(
            conversation_id="conv-001",
            message_type=GAME_INVITATION,  # Requires auth_token
            sender="referee:REF01",
            timestamp=generate_timestamp()
            # auth_token missing
        )

        # Should raise authentication error (E012: AUTH_TOKEN_INVALID)
        with pytest.raises(AuthenticationError) as exc_info:
            validate_auth_token(envelope)

        assert exc_info.value.error_code == "E012"

    def test_invalid_parity_choice_rejected(self):
        """Test that invalid parity choices are rejected."""
        invalid_choices = ["EVEN", "ODD", "Even", "Odd", "random", "", None, 123]

        for invalid_choice in invalid_choices:
            with pytest.raises((ValueError, TypeError)):
                validate_parity_choice(invalid_choice)

    def test_timeout_enforcer_zero_timeout(self):
        """Test timeout enforcer with zero timeout (edge case)."""
        enforcer = TimeoutEnforcer()

        # Zero timeout should immediately timeout
        with pytest.raises(TimeoutError):
            enforcer.wait_for_response(timeout=0)

    def test_conversation_id_mismatch_handling(self):
        """Test handling of conversation_id mismatch."""
        request = MessageEnvelope(
            conversation_id="conv-001",
            message_type=GAME_INVITATION,
            sender="referee:REF01",
            timestamp=generate_timestamp()
        )

        response = MessageEnvelope(
            conversation_id="conv-002",  # Mismatch!
            message_type=GAME_JOIN_ACK,
            sender="player:P01",
            timestamp=generate_timestamp()
        )

        # Should detect mismatch
        assert not validate_conversation_id(request, response)
```

**Running edge case tests:**
```bash
# All edge case tests
pytest -m edge

# Specific edge case file
pytest tests/edge_cases/test_edge_cases.py -v
```

---

### 6. Load Tests (`tests/load/`)

**Note:** This directory is currently a placeholder for future load testing implementation.

**Planned coverage:**
- 50+ concurrent matches
- 100+ player registrations
- Sustained throughput testing
- Memory leak detection
- Performance regression testing

**Example load test (future):**
```python
@pytest.mark.load
@pytest.mark.slow
async def test_50_concurrent_matches():
    """Test system handles 50 concurrent matches without blocking."""
    import time

    start = time.time()

    # Create 50 concurrent match tasks
    tasks = [conduct_match(f"M{i:03d}") for i in range(50)]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start

    # Should complete concurrently in ~30s, not sequentially in 1500s
    assert elapsed < 60, f"BLOCKING DETECTED! Took {elapsed}s (expected <60s)"
    assert len(results) == 50
    assert all(r["state"] == "FINISHED" for r in results)
```

---

## Coverage Measurement

### Overview

Code coverage measures **which lines of code are executed during test runs**. Our target is **≥85% coverage** for `agents/` and `SHARED/league_sdk/`.

### Coverage Configuration

**File:** `.coveragerc`

```ini
[run]
source = agents, SHARED/league_sdk
omit =
    */main.py
    */setup.py
    */tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

**What's covered:**
- All code in `agents/` directory
- All code in `SHARED/league_sdk/` directory

**What's excluded:**
- Entry points (`main.py` files)
- Setup files (`setup.py`)
- Test files themselves
- Type checking code blocks
- Abstract methods
- Defensive assertions

---

### Generating Coverage Reports

#### Terminal Report (Quick View)

```bash
# Run tests with coverage
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=term
```

**Example output:**
```
--------------------------------- coverage: platform darwin, python 3.10.x ---------------------------------
Name                                        Stmts   Miss  Cover
---------------------------------------------------------------
agents/league_manager/server.py               287     12    96%
agents/league_manager/orchestration.py        156      8    95%
agents/referee_REF01/server.py                245     15    94%
agents/referee_REF01/match_conductor.py       198     10    95%
agents/player_P01/server.py                   134      7    95%
SHARED/league_sdk/protocol.py                 891     45    95%
SHARED/league_sdk/config_models.py            458     23    95%
SHARED/league_sdk/repositories.py             485     30    94%
SHARED/league_sdk/retry.py                    312     18    94%
---------------------------------------------------------------
TOTAL                                        3166    168    95%
```

#### Terminal Report with Missing Lines

```bash
# Show which specific lines are not covered
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=term-missing
```

**Example output:**
```
Name                                        Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
agents/league_manager/server.py               287     12    96%   145-147, 289, 412-415
agents/referee_REF01/match_conductor.py       198     10    95%   78, 234-237, 456-459
SHARED/league_sdk/retry.py                    312     18    94%   123-128, 267-273, 489
--------------------------------------------------------------------------
TOTAL                                        3166    168    95%
```

**Interpretation:**
- **Missing:** Line numbers not executed during tests
- Common reasons for missing coverage:
  - Error handling paths not triggered
  - Edge cases not tested
  - Dead code that should be removed

#### HTML Report (Detailed View)

```bash
# Generate HTML coverage report
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=html

# Open report in browser
open htmlcov/index.html
```

**HTML report features:**
- Interactive file browser
- Line-by-line coverage highlighting
  - **Green:** Covered lines
  - **Red:** Missed lines
  - **Yellow:** Partially covered branches
- Coverage percentage per file
- Sortable by file, statements, missed, coverage%

**Using the HTML report:**
1. Open `htmlcov/index.html` in a browser
2. Click on any file to see line-by-line coverage
3. Red highlighted lines show what's not tested
4. Focus on files with <85% coverage

---

### Coverage Targets and Thresholds

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| **Overall** | ≥85% | 95% | ✅ Excellent |
| **agents/** | ≥85% | 95% | ✅ Excellent |
| **SHARED/league_sdk/** | ≥85% | 94% | ✅ Excellent |
| **Protocol models** | ≥95% | 96% | ✅ Excellent |
| **Game logic** | ≥90% | 92% | ✅ Excellent |
| **Retry logic** | ≥90% | 94% | ✅ Excellent |

---

### Interpreting Coverage Reports

#### Good Coverage (≥85%)

**Example:**
```
agents/referee_REF01/game_logic.py    148      5    97%   Missing: 89, 134-137
```

**Interpretation:**
- **97% coverage** is excellent
- **Missing lines 89, 134-137** likely edge cases or error paths
- **Action:** Review missing lines to decide if they need tests

#### Poor Coverage (<70%)

**Example:**
```
agents/experimental/new_feature.py     234    89    62%   Missing: 45-78, 123-156, 189-234
```

**Interpretation:**
- **62% coverage** is below target
- **Large gaps** in line numbers suggest entire functions untested
- **Action:** Write tests for missing functionality

#### Partially Covered Branches

**Example:**
```
SHARED/league_sdk/retry.py    312    18    94%   Partial: 123->exit, 125->127
```

**Interpretation:**
- **94% overall** but some branches not tested
- **Partial: 123->exit** means one branch of an `if` statement not taken
- **Action:** Add tests for both branches of conditional logic

---

### Coverage Best Practices

#### 1. Focus on Critical Paths

Prioritize coverage of:
- **Business logic:** Game rules, scoring, scheduling
- **Error handling:** All error codes (E001-E018)
- **State transitions:** League lifecycle, match states
- **Data persistence:** Repository operations

#### 2. Don't Chase 100% Coverage

**Acceptable gaps:**
- Defensive assertions (`raise NotImplementedError`)
- Type checking code (`if TYPE_CHECKING:`)
- Logging statements
- Abstract methods
- Entry points (`if __name__ == "__main__":`)

**Use `# pragma: no cover` for intentional exclusions:**
```python
def __repr__(self):  # pragma: no cover
    """String representation (debugging only)."""
    return f"Player({self.player_id})"
```

#### 3. Test Behavior, Not Coverage

**Bad approach:**
```python
# Test that just calls code to increase coverage
def test_some_function():
    result = some_function()  # No assertions!
```

**Good approach:**
```python
# Test that validates behavior
def test_some_function_returns_correct_value():
    result = some_function(input=5)
    assert result == 10, "Should double the input"
```

#### 4. Coverage for Each Component

```bash
# Coverage for specific module
pytest tests/unit/test_sdk/test_retry.py --cov=SHARED/league_sdk/retry --cov-report=term-missing

# Coverage for League Manager only
pytest tests/unit/test_league_manager/ --cov=agents/league_manager --cov-report=html
```

---

### Coverage in CI/CD

#### GitHub Actions Integration

**.github/workflows/test.yml:**
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e SHARED/league_sdk

      - name: Run tests with coverage
        run: |
          pytest --cov=agents --cov=SHARED/league_sdk --cov-report=xml --cov-report=term

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=85

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

**Coverage enforcement:**
- **`--fail-under=85`** - Fail CI if coverage drops below 85%
- **Upload to Codecov** - Track coverage over time
- **Block PR merges** if coverage decreases

---

## Writing New Tests

### Test Structure Template

All tests should follow this basic structure:

```python
# 1. Imports
import pytest
from unittest.mock import Mock, patch, MagicMock
from SHARED.league_sdk.protocol import MessageEnvelope, GAME_INVITATION
from agents.referee_REF01.game_logic import EvenOddGameLogic

# 2. Test class (optional but recommended for organization)
class TestComponentName:

    # 3. Fixtures (setup/teardown)
    @pytest.fixture
    def component_instance(self):
        """Create component instance for testing."""
        return ComponentClass(config=...)

    # 4. Test functions
    def test_feature_name_success(self, component_instance):
        """Test that feature works in normal conditions."""
        # Arrange
        input_data = ...

        # Act
        result = component_instance.method(input_data)

        # Assert
        assert result == expected_value

    def test_feature_name_error_handling(self, component_instance):
        """Test that feature handles errors correctly."""
        # Arrange
        invalid_input = ...

        # Act & Assert
        with pytest.raises(ValueError):
            component_instance.method(invalid_input)
```

---

### Writing Unit Tests

#### Pattern: Arrange-Act-Assert (AAA)

```python
def test_calculate_points():
    """Test points calculation (win=3, draw=1, loss=0)."""
    # Arrange
    wins = 5
    draws = 2
    losses = 3

    # Act
    points = calculate_points(wins, draws, losses)

    # Assert
    expected_points = (5 * 3) + (2 * 1) + (3 * 0)  # 17
    assert points == expected_points, f"Expected {expected_points}, got {points}"
```

#### Using Fixtures

```python
import pytest

class TestGameLogic:
    @pytest.fixture
    def game_logic(self):
        """Create game logic instance for each test."""
        return EvenOddGameLogic()

    def test_determine_winner_even_wins(self, game_logic):
        """Test that even choice wins with even number."""
        # Use fixture
        winner, status_a, status_b = game_logic.determine_winner(
            player_a_id="P01",
            player_b_id="P02",
            choice_a="even",
            choice_b="odd",
            random_number=4  # Even number
        )

        assert winner == "P01"
        assert status_a == "WIN"
        assert status_b == "LOSS"
```

#### Using Mocks

```python
from unittest.mock import Mock, patch, MagicMock

def test_registration_with_mocked_http():
    """Test registration with mocked HTTP call."""
    # Create mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "player_id": "P01",
        "auth_token": "abc123def456"
    }

    # Patch the HTTP library
    with patch('requests.post', return_value=mock_response) as mock_post:
        # Execute registration
        result = register_player(player_name="TestPlayer")

        # Verify mock was called correctly
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://localhost:8000/mcp"

        # Verify result
        assert result["player_id"] == "P01"
        assert result["auth_token"] == "abc123def456"
```

#### Parametrized Tests

Test multiple inputs with same logic:

```python
import pytest

@pytest.mark.parametrize("number,expected_parity", [
    (2, "even"),
    (4, "even"),
    (6, "even"),
    (8, "even"),
    (10, "even"),
    (1, "odd"),
    (3, "odd"),
    (5, "odd"),
    (7, "odd"),
    (9, "odd"),
])
def test_check_parity(number, expected_parity):
    """Test parity checking for all numbers 1-10."""
    result = check_parity(number)
    assert result == expected_parity
```

---

### Writing Integration Tests

#### Pattern: Workflow Testing with Partial Mocks

```python
import pytest
import asyncio
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_complete_match_workflow():
    """Test complete match workflow with mocked HTTP."""
    # Arrange
    conductor = MatchConductor(...)

    # Mock only HTTP calls, not business logic
    async def mock_http_post(url, json_data):
        if "GAME_INVITATION" in json_data:
            return {"result": "ACK"}
        elif "CHOOSE_PARITY_CALL" in json_data:
            return {"result": "even"}
        # ...

    # Act
    with patch('httpx.AsyncClient.post', side_effect=mock_http_post):
        result = await conductor.conduct_match(
            match_id="M001",
            player_a_id="P01",
            player_b_id="P02"
        )

    # Assert
    assert result["state"] == "FINISHED"
    assert result["winner"] in ["P01", "P02", "DRAW"]
```

#### Using Async Fixtures

```python
import pytest
import asyncio

@pytest_asyncio.fixture
async def initialized_league_manager():
    """Create and initialize League Manager."""
    lm = LeagueManager(league_id="test_league")
    await lm.initialize()

    yield lm

    # Cleanup
    await lm.shutdown()

@pytest.mark.asyncio
async def test_register_player(initialized_league_manager):
    """Test player registration."""
    result = await initialized_league_manager.register_player(
        player_name="TestPlayer",
        metadata={"strategy": "random"}
    )

    assert result["player_id"].startswith("P")
    assert len(result["auth_token"]) >= 32
```

---

### Writing E2E Tests

#### Pattern: Process Management with Cleanup

```python
import pytest
import subprocess
import signal
import asyncio
import httpx
from pathlib import Path

@pytest_asyncio.fixture(scope="class")
async def running_system():
    """Launch complete system for E2E testing."""
    processes = []
    project_root = Path(__file__).parent.parent.parent

    try:
        # Start League Manager
        lm_proc = subprocess.Popen(
            ["python3", "-m", "agents.league_manager.main"],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": f"{project_root}/SHARED"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append(("League Manager", lm_proc))
        await asyncio.sleep(2)

        # Verify health
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200

        # Start other agents...
        # ...

        yield {"processes": processes}

    finally:
        # Cleanup: Terminate all processes
        for name, proc in processes:
            try:
                proc.send_signal(signal.SIGTERM)
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

@pytest.mark.e2e
@pytest.mark.slow
async def test_health_endpoints(running_system):
    """Test all agents respond to health checks."""
    endpoints = [
        "http://localhost:8000/health",  # League Manager
        "http://localhost:8001/health",  # Referee REF01
        "http://localhost:8101/health",  # Player P01
    ]

    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            response = await client.get(endpoint, timeout=5)
            assert response.status_code == 200
```

---

### Writing Protocol Tests

#### Pattern: Pydantic Validation Testing

```python
import pytest
from pydantic import ValidationError
from SHARED.league_sdk.protocol import MessageEnvelope, LEAGUE_REGISTER_REQUEST

@pytest.mark.protocol
class TestProtocolValidation:
    def test_valid_envelope(self):
        """Test that valid envelope passes validation."""
        envelope = MessageEnvelope(
            conversation_id="conv-001",
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp="2025-01-01T00:00:00Z",
            protocol="league.v2"
        )

        # Should not raise
        assert envelope.conversation_id == "conv-001"

    def test_invalid_envelope_missing_field(self):
        """Test that envelope missing required field fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            MessageEnvelope(
                # conversation_id missing
                message_type=LEAGUE_REGISTER_REQUEST,
                sender="player:P01",
                timestamp="2025-01-01T00:00:00Z"
            )

        # Check error details
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('conversation_id',) for e in errors)

    def test_sender_format_validation(self):
        """Test sender field format validation."""
        valid_senders = [
            "player:P01",
            "referee:REF01",
            "league_manager:LM01"
        ]

        for sender in valid_senders:
            envelope = MessageEnvelope(
                conversation_id="conv-001",
                message_type=LEAGUE_REGISTER_REQUEST,
                sender=sender,
                timestamp="2025-01-01T00:00:00Z"
            )
            assert envelope.sender == sender

        # Invalid formats
        invalid_senders = [
            "player-P01",  # Wrong separator
            "P01",         # Missing agent type
            "player:",     # Missing agent ID
            ":P01"         # Missing agent type
        ]

        for sender in invalid_senders:
            with pytest.raises(ValidationError):
                MessageEnvelope(
                    conversation_id="conv-001",
                    message_type=LEAGUE_REGISTER_REQUEST,
                    sender=sender,
                    timestamp="2025-01-01T00:00:00Z"
                )
```

---

### Test Template Files

#### Unit Test Template

**File:** `tests/unit/test_new_feature.py`

```python
"""
Unit tests for NewFeature component.

Tests cover:
- Feature initialization
- Normal operation
- Error handling
- Edge cases
"""

import pytest
from unittest.mock import Mock, patch
from agents.some_agent.new_feature import NewFeature


class TestNewFeature:
    """Test suite for NewFeature component."""

    @pytest.fixture
    def feature_instance(self):
        """Create NewFeature instance for testing."""
        return NewFeature(config={"setting": "value"})

    def test_initialization(self, feature_instance):
        """Test feature initializes correctly."""
        assert feature_instance.config == {"setting": "value"}
        assert feature_instance.state == "INITIALIZED"

    def test_normal_operation(self, feature_instance):
        """Test feature operates correctly under normal conditions."""
        # Arrange
        input_data = {"key": "value"}

        # Act
        result = feature_instance.process(input_data)

        # Assert
        assert result["status"] == "success"
        assert result["processed"] is True

    def test_error_handling(self, feature_instance):
        """Test feature handles errors correctly."""
        # Arrange
        invalid_input = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            feature_instance.process(invalid_input)

        assert "Input cannot be None" in str(exc_info.value)

    @pytest.mark.parametrize("input_value,expected", [
        (0, False),
        (1, True),
        (10, True),
        (-1, False),
    ])
    def test_validation_logic(self, feature_instance, input_value, expected):
        """Test validation logic with various inputs."""
        result = feature_instance.validate(input_value)
        assert result == expected
```

#### Integration Test Template

**File:** `tests/integration/test_new_workflow.py`

```python
"""
Integration tests for NewWorkflow.

Tests cover:
- Complete workflow execution
- Component interactions
- State transitions
- Error recovery
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from agents.some_agent.new_workflow import NewWorkflow


@pytest.mark.asyncio
class TestNewWorkflow:
    """Test suite for NewWorkflow integration."""

    @pytest.fixture
    async def workflow_instance(self):
        """Create and initialize workflow."""
        workflow = NewWorkflow(config=...)
        await workflow.initialize()

        yield workflow

        # Cleanup
        await workflow.shutdown()

    async def test_complete_workflow(self, workflow_instance):
        """Test complete workflow execution."""
        # Arrange
        input_data = {"task": "process_data"}

        # Mock external HTTP calls
        async def mock_http_call(url, data):
            return {"result": "success"}

        # Act
        with patch('httpx.AsyncClient.post', side_effect=mock_http_call):
            result = await workflow_instance.execute(input_data)

        # Assert
        assert result["state"] == "COMPLETED"
        assert result["steps_completed"] == 3

    async def test_workflow_error_recovery(self, workflow_instance):
        """Test workflow recovers from transient errors."""
        # Arrange
        call_count = 0

        async def mock_http_with_retry(url, data):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return {"result": "success"}

        # Act
        with patch('httpx.AsyncClient.post', side_effect=mock_http_with_retry):
            result = await workflow_instance.execute({"task": "test"})

        # Assert
        assert result["state"] == "COMPLETED"
        assert call_count == 3  # Retried twice
```

#### E2E Test Template

**File:** `tests/e2e/test_new_scenario.py`

```python
"""
E2E tests for NewScenario.

Tests cover:
- Complete system behavior
- Real network communication
- Multi-agent coordination
"""

import pytest
import subprocess
import asyncio
import httpx
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.slow
class TestNewScenario:
    """E2E test suite for NewScenario."""

    @pytest_asyncio.fixture(scope="class")
    async def running_scenario(self):
        """Launch complete system for scenario testing."""
        processes = []
        project_root = Path(__file__).parent.parent.parent

        try:
            # Start required agents
            # ... (process startup code)

            yield {"processes": processes}

        finally:
            # Cleanup
            for name, proc in processes:
                proc.terminate()
                proc.wait(timeout=5)

    async def test_scenario_execution(self, running_scenario):
        """Test complete scenario executes successfully."""
        # Execute scenario via HTTP API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/scenario/start",
                json={"scenario_id": "test_scenario"}
            )
            assert response.status_code == 200

        # Wait for completion
        # ... (polling logic)

        # Verify results
        # ... (assertions)
```

---

## Test Patterns

### 1. Mocking Pattern

#### Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mocked_dependency():
    """Test component with mocked external dependency."""
    # Create mock
    mock_client = Mock()
    mock_client.get_data.return_value = {"key": "value"}

    # Inject mock
    component = MyComponent(client=mock_client)

    # Execute
    result = component.process()

    # Verify mock was called
    mock_client.get_data.assert_called_once()
    assert result == {"key": "value"}
```

#### Patch Module-Level Functions

```python
from unittest.mock import patch

def test_with_patched_function():
    """Test with patched module-level function."""
    with patch('module.external_function', return_value=42) as mock_func:
        result = my_function_that_calls_external()

        mock_func.assert_called_once()
        assert result == 42
```

#### Mock Async Functions

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_with_async_mock():
    """Test async function with mocked async dependency."""
    mock_response = AsyncMock()
    mock_response.return_value = {"data": "result"}

    with patch('httpx.AsyncClient.post', new=mock_response):
        result = await make_async_http_call()

        assert result == {"data": "result"}
```

---

### 2. Fixture Pattern

#### Simple Fixture

```python
import pytest

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"player_id": "P01", "score": 10}

def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["player_id"] == "P01"
```

#### Fixture with Setup/Teardown

```python
import pytest

@pytest.fixture
def database_connection():
    """Provide database connection with cleanup."""
    # Setup
    conn = Database.connect()

    yield conn

    # Teardown
    conn.close()

def test_database_operation(database_connection):
    """Test database operation."""
    result = database_connection.query("SELECT * FROM players")
    assert len(result) > 0
```

#### Async Fixture

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def initialized_agent():
    """Provide initialized agent with cleanup."""
    # Setup
    agent = Agent(agent_id="P01")
    await agent.initialize()

    yield agent

    # Teardown
    await agent.shutdown()

@pytest.mark.asyncio
async def test_agent_operation(initialized_agent):
    """Test agent operation."""
    result = await initialized_agent.perform_action()
    assert result["status"] == "success"
```

#### Fixture Scope

```python
@pytest.fixture(scope="function")  # Default: new instance per test
def function_scoped():
    return "created per test"

@pytest.fixture(scope="class")  # Shared across class
def class_scoped():
    return "created per class"

@pytest.fixture(scope="module")  # Shared across module
def module_scoped():
    return "created per module"

@pytest.fixture(scope="session")  # Shared across entire test session
def session_scoped():
    return "created once"
```

---

### 3. Parametrization Pattern

#### Basic Parametrization

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (2, "even"),
    (3, "odd"),
    (4, "even"),
    (5, "odd"),
])
def test_parity_check(input, expected):
    """Test parity checking with multiple inputs."""
    assert check_parity(input) == expected
```

#### Multiple Parameters

```python
@pytest.mark.parametrize("wins,draws,losses,expected_points", [
    (3, 0, 0, 9),   # 3 wins = 9 points
    (2, 1, 0, 7),   # 2 wins + 1 draw = 7 points
    (0, 3, 0, 3),   # 3 draws = 3 points
    (0, 0, 3, 0),   # 3 losses = 0 points
])
def test_points_calculation(wins, draws, losses, expected_points):
    """Test points calculation with various records."""
    points = calculate_points(wins, draws, losses)
    assert points == expected_points
```

#### Parametrize with IDs

```python
@pytest.mark.parametrize(
    "player_choice,opponent_choice,number,expected_winner",
    [
        ("even", "odd", 2, "player"),
        ("even", "odd", 3, "opponent"),
        ("odd", "even", 3, "player"),
        ("even", "even", 2, "draw"),
    ],
    ids=["even_wins", "odd_wins", "odd_wins_2", "draw"]
)
def test_game_outcomes(player_choice, opponent_choice, number, expected_winner):
    """Test game outcomes with labeled test cases."""
    winner = determine_winner(player_choice, opponent_choice, number)
    assert winner == expected_winner
```

---

### 4. Exception Testing Pattern

#### Test Expected Exceptions

```python
import pytest

def test_raises_value_error():
    """Test function raises ValueError for invalid input."""
    with pytest.raises(ValueError):
        validate_parity_choice("invalid")
```

#### Test Exception Message

```python
def test_exception_message():
    """Test exception has correct message."""
    with pytest.raises(ValueError) as exc_info:
        validate_parity_choice("invalid")

    assert "must be 'even' or 'odd'" in str(exc_info.value)
```

#### Test Exception Attributes

```python
def test_custom_exception_attributes():
    """Test custom exception has correct attributes."""
    with pytest.raises(ProtocolError) as exc_info:
        raise_protocol_error("E011")

    assert exc_info.value.error_code == "E011"
    assert exc_info.value.message == "PROTOCOL_MISMATCH"
```

---

### 5. Async Testing Pattern

#### Basic Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result == expected_value
```

#### Async Test with Timeout

```python
@pytest.mark.asyncio
@pytest.mark.timeout(10)  # Fail if test takes >10 seconds
async def test_with_timeout():
    """Test with timeout protection."""
    result = await potentially_slow_function()
    assert result is not None
```

#### Test Concurrent Operations

```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test multiple concurrent operations."""
    # Start 10 concurrent tasks
    tasks = [async_operation(i) for i in range(10)]

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Verify all succeeded
    assert len(results) == 10
    assert all(r["status"] == "success" for r in results)
```

---

## Debugging Test Failures

### 1. Understanding Test Output

#### Test Failure Output

```bash
================================ FAILURES ================================
________________ TestGameLogic.test_winner_determination _________________

self = <tests.unit.test_referee_agent.test_game_logic.TestGameLogic object at 0x10abc1230>

    def test_winner_determination(self):
        """Test winner determination logic."""
        winner, status_a, status_b = determine_winner(
            player_a_id="P01",
            player_b_id="P02",
            choice_a="even",
            choice_b="odd",
            random_number=4
        )

>       assert winner == "P02"  # WRONG! Should be P01 (even number)
E       AssertionError: assert 'P01' == 'P02'

tests/unit/test_referee_agent/test_game_logic.py:45: AssertionError
```

**Interpreting the failure:**
1. **Test name:** `TestGameLogic.test_winner_determination`
2. **Failure location:** Line 45 in `test_game_logic.py`
3. **Assertion error:** Expected `'P02'` but got `'P01'`
4. **Root cause:** Test assertion is wrong (even number should win for "even" choice)

---

### 2. Debugging Tools

#### Print Debugging

```python
def test_with_debug_output():
    """Test with debug print statements."""
    result = calculate_points(wins=3, draws=2, losses=1)

    print(f"Result: {result}")  # Will show in output with -s flag
    print(f"Expected: 11")

    assert result == 11
```

**Run with print output:**
```bash
pytest -s tests/unit/test_scoring.py
```

#### Using `-v` for Verbose Output

```bash
# Show individual test names as they run
pytest -v

# Show test names and print statements
pytest -vs
```

**Output:**
```
tests/unit/test_scoring.py::test_calculate_points PASSED
tests/unit/test_scoring.py::test_calculate_points_with_draws PASSED
tests/unit/test_scoring.py::test_calculate_points_all_losses FAILED
```

#### Using `-l` to Show Locals

```bash
# Show local variables in tracebacks
pytest -l
```

**Output includes local variables:**
```
________________ test_calculate_points_all_losses _________________
wins = 0, draws = 0, losses = 3, result = 3, expected = 0
    def test_calculate_points_all_losses():
        wins, draws, losses = 0, 0, 3
        result = calculate_points(wins, draws, losses)
>       assert result == 0
E       assert 3 == 0
```

#### Using `--tb` for Traceback Control

```bash
# Short traceback (default)
pytest

# Long traceback (more detail)
pytest --tb=long

# No traceback (just summary)
pytest --tb=no

# Line-only traceback
pytest --tb=line
```

---

### 3. Interactive Debugging with PDB

#### Drop into Debugger on Failure

```bash
# Stop at first failure and open debugger
pytest --pdb
```

**When test fails:**
```python
(Pdb) # Interactive debugger prompt
(Pdb) p result  # Print variable
'P01'
(Pdb) p expected
'P02'
(Pdb) p choice_a, choice_b, random_number
('even', 'odd', 4)
(Pdb) c  # Continue
```

#### Insert Breakpoint in Test

```python
def test_with_breakpoint():
    """Test with manual breakpoint."""
    result = complex_calculation()

    import pdb; pdb.set_trace()  # Debugger will stop here

    assert result == expected_value
```

**Python 3.7+ built-in:**
```python
def test_with_builtin_breakpoint():
    """Test with built-in breakpoint."""
    result = complex_calculation()

    breakpoint()  # Cleaner syntax

    assert result == expected_value
```

#### Useful PDB Commands

| Command | Description |
|---------|-------------|
| `p variable` | Print variable value |
| `pp variable` | Pretty-print variable |
| `l` | List source code around current line |
| `ll` | List entire current function |
| `n` | Next line (step over) |
| `s` | Step into function |
| `c` | Continue execution |
| `q` | Quit debugger |
| `h` | Help |

---

### 4. Inspecting Failed Tests

#### Show Captured Output

```bash
# Show print statements even for passing tests
pytest -s

# Show captured output for failed tests only
pytest --capture=no
```

#### Show Detailed Assertion Information

```python
def test_with_detailed_assertion():
    """Test with helpful assertion message."""
    result = calculate_points(wins=3, draws=2, losses=1)
    expected = 11

    assert result == expected, (
        f"Points calculation failed:\n"
        f"  Wins: 3 × 3 = 9\n"
        f"  Draws: 2 × 1 = 2\n"
        f"  Expected: {expected}\n"
        f"  Got: {result}"
    )
```

#### Using pytest-sugar for Better Output

```bash
# Install pytest-sugar for enhanced output
pip install pytest-sugar

# Run tests (automatically uses pytest-sugar)
pytest
```

**Enhanced output:**
```
 tests/unit/test_scoring.py ✓✓✓✓✓✓✓✓✓✓                    45% ████▌
 tests/unit/test_game_logic.py ✓✓✓✓✓⨯✓✓✓✓                 67% ██████▋
```

---

### 5. Common Test Failure Patterns

#### Pattern: Async Test Not Awaited

**Symptom:**
```
RuntimeWarning: coroutine 'test_async_function' was never awaited
```

**Cause:**
```python
# Missing @pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

**Fix:**
```python
@pytest.mark.asyncio  # Add this!
async def test_async_function():
    result = await async_function()
    assert result == expected
```

#### Pattern: Fixture Not Found

**Symptom:**
```
fixture 'database_connection' not found
```

**Cause:** Fixture defined in wrong file or not imported

**Fix:**
- Move fixture to `conftest.py` (automatically discovered)
- Or import fixture module explicitly

#### Pattern: Mock Not Applied

**Symptom:** Test uses real HTTP instead of mock

**Cause:**
```python
# Patching wrong target
with patch('requests.post') as mock_post:
    # Component uses httpx, not requests!
    result = component.make_request()
```

**Fix:**
```python
# Patch where it's used, not where it's defined
with patch('agents.component.httpx.AsyncClient.post') as mock_post:
    result = component.make_request()
```

#### Pattern: Race Condition in Async Test

**Symptom:** Test passes sometimes, fails other times

**Cause:**
```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    # Start tasks but don't await them
    task1 = asyncio.create_task(operation1())
    task2 = asyncio.create_task(operation2())

    # Assertion runs before tasks complete!
    assert result == expected
```

**Fix:**
```python
@pytest.mark.asyncio
async def test_concurrent_operations():
    task1 = asyncio.create_task(operation1())
    task2 = asyncio.create_task(operation2())

    # Wait for both tasks
    await asyncio.gather(task1, task2)

    # Now safe to assert
    assert result == expected
```

---

### 6. Log Analysis for Failed Tests

#### Enable Detailed Logging

```python
import pytest
import logging

@pytest.fixture(autouse=True)
def setup_logging():
    """Enable detailed logging for all tests."""
    logging.basicConfig(level=logging.DEBUG)
```

#### Capture Logs in Tests

```python
def test_with_log_capture(caplog):
    """Test with log capture."""
    with caplog.at_level(logging.INFO):
        function_that_logs()

    # Check log messages
    assert "Expected log message" in caplog.text
    assert len(caplog.records) == 3
```

#### Inspect Test Logs

```bash
# Run tests with log output
pytest --log-cli-level=DEBUG

# Save logs to file
pytest --log-file=test_output.log --log-file-level=DEBUG
```

---

## CI/CD Integration

### GitHub Actions Workflow

**File:** `.github/workflows/test.yml`

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e SHARED/league_sdk

      - name: Run unit tests
        run: |
          pytest -m unit --cov=agents --cov=SHARED/league_sdk --cov-report=xml --cov-report=term

      - name: Run integration tests
        run: |
          pytest -m integration --cov=agents --cov=SHARED/league_sdk --cov-append --cov-report=xml --cov-report=term

      - name: Run protocol compliance tests
        run: |
          pytest -m protocol --cov=agents --cov=SHARED/league_sdk --cov-append --cov-report=xml --cov-report=term

      - name: Run E2E tests
        run: |
          pytest -m e2e --cov=agents --cov=SHARED/league_sdk --cov-append --cov-report=xml --cov-report=term
        timeout-minutes: 10

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=85

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
          flags: unittests
          name: codecov-umbrella

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            htmlcov/
            coverage.xml

  lint:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install black isort flake8 mypy pylint

      - name: Run black
        run: black --check .

      - name: Run isort
        run: isort --check-only .

      - name: Run flake8
        run: flake8 agents/ SHARED/league_sdk/

      - name: Run mypy
        run: mypy agents/ SHARED/league_sdk/
```

---

### Pre-commit Hooks

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m "unit and not slow"
        language: system
        pass_filenames: false
        always_run: true
```

**Install pre-commit:**
```bash
pip install pre-commit
pre-commit install
```

**Run manually:**
```bash
pre-commit run --all-files
```

---

## Test Infrastructure

### Configuration Files

#### pytest.ini

**File:** `pytest.ini`

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage
addopts =
    --cov=agents
    --cov=SHARED/league_sdk
    --cov-report=term
    --cov-report=html
    --strict-markers

# Markers
markers =
    unit: Unit tests for individual components
    integration: Integration tests between components
    e2e: End-to-end full system tests
    slow: Tests that take longer to run
    protocol: Protocol compliance tests
    edge: Edge-case tests for error handling and boundary conditions

# Asyncio mode
asyncio_mode = auto
```

#### .coveragerc

**File:** `.coveragerc`

```ini
[run]
source = agents, SHARED/league_sdk
omit =
    */main.py
    */setup.py
    */tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

precision = 2

[html]
directory = htmlcov
```

---

### Shared Fixtures (conftest.py)

**File:** `tests/conftest.py`

```python
"""
Shared pytest configuration and fixtures.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_mcp_server():
    """Provide a mock MCP server for testing."""
    mock_server = MagicMock()
    mock_server.post.return_value = {"result": "success"}
    return mock_server


def pytest_collection_modifyitems(config, items):
    """
    Automatically add markers based on test location.

    Tests in tests/unit/ get @pytest.mark.unit
    Tests in tests/integration/ get @pytest.mark.integration
    etc.
    """
    for item in items:
        # Get test file path
        test_file = str(item.fspath)

        # Add markers based on directory
        if "/tests/unit/" in test_file:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in test_file:
            item.add_marker(pytest.mark.integration)
        elif "/tests/e2e/" in test_file:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "/tests/protocol_compliance/" in test_file:
            item.add_marker(pytest.mark.protocol)
        elif "/tests/edge_cases/" in test_file:
            item.add_marker(pytest.mark.edge)


@pytest.fixture(scope="session")
def project_root():
    """Provide project root directory."""
    from pathlib import Path
    return Path(__file__).parent.parent
```

---

## Best Practices

### 1. Test Naming

✅ **Good:**
```python
def test_calculate_points_with_three_wins_returns_nine():
    """Test points calculation for 3 wins (3 × 3 = 9 points)."""
    assert calculate_points(wins=3, draws=0, losses=0) == 9
```

❌ **Bad:**
```python
def test1():
    """Test something."""
    assert calculate_points(3, 0, 0) == 9
```

**Guidelines:**
- Use descriptive names: `test_<action>_<condition>_<expected>`
- Include docstrings explaining what's being tested
- Make test names searchable

---

### 2. Test Independence

✅ **Good:**
```python
def test_player_registration():
    """Test player registration (independent)."""
    # Fresh player instance
    player = Player(player_id="P01")
    result = player.register()
    assert result["status"] == "registered"

def test_player_game_join():
    """Test player game join (independent)."""
    # Fresh player instance
    player = Player(player_id="P01")
    player.register()  # Setup within test
    result = player.join_game()
    assert result["status"] == "joined"
```

❌ **Bad:**
```python
# Global state shared between tests
player = Player(player_id="P01")

def test_player_registration():
    """Test player registration (depends on global state)."""
    result = player.register()
    assert result["status"] == "registered"

def test_player_game_join():
    """Test player game join (depends on previous test)."""
    # Fails if test_player_registration didn't run first!
    result = player.join_game()
    assert result["status"] == "joined"
```

**Guidelines:**
- Each test should be runnable in isolation
- Don't depend on test execution order
- Use fixtures for shared setup

---

### 3. Arrange-Act-Assert Pattern

✅ **Good:**
```python
def test_winner_determination():
    """Test winner determination for even number."""
    # Arrange
    player_a_id = "P01"
    player_b_id = "P02"
    choice_a = "even"
    choice_b = "odd"
    random_number = 4  # Even

    # Act
    winner, status_a, status_b = determine_winner(
        player_a_id, player_b_id, choice_a, choice_b, random_number
    )

    # Assert
    assert winner == player_a_id
    assert status_a == "WIN"
    assert status_b == "LOSS"
```

❌ **Bad:**
```python
def test_winner_determination():
    """Test winner determination."""
    assert determine_winner("P01", "P02", "even", "odd", 4)[0] == "P01"
```

**Guidelines:**
- **Arrange:** Set up test data
- **Act:** Execute the code under test
- **Assert:** Verify the results
- Keep each section distinct and readable

---

### 4. One Assertion Per Test (Usually)

✅ **Good:**
```python
def test_player_registration_returns_player_id():
    """Test registration returns player_id."""
    result = register_player()
    assert result["player_id"].startswith("P")

def test_player_registration_returns_auth_token():
    """Test registration returns auth_token."""
    result = register_player()
    assert len(result["auth_token"]) >= 32

def test_player_registration_stores_metadata():
    """Test registration stores metadata."""
    result = register_player(metadata={"team": "alpha"})
    assert result["metadata"]["team"] == "alpha"
```

⚠️ **Acceptable (related assertions):**
```python
def test_player_registration_response_structure():
    """Test registration response has required fields."""
    result = register_player()

    # All assertions validate the same concept (response structure)
    assert "player_id" in result
    assert "auth_token" in result
    assert "registered_at" in result
```

**Guidelines:**
- Prefer one logical assertion per test
- Multiple assertions OK if testing same concept
- Helps pinpoint exactly what failed

---

### 5. Use Descriptive Assertion Messages

✅ **Good:**
```python
def test_points_calculation():
    """Test points calculation."""
    result = calculate_points(wins=3, draws=2, losses=1)
    expected = 11  # (3×3) + (2×1) = 11

    assert result == expected, (
        f"Points calculation incorrect:\n"
        f"  Input: 3 wins, 2 draws, 1 loss\n"
        f"  Expected: {expected} points\n"
        f"  Got: {result} points"
    )
```

❌ **Bad:**
```python
def test_points_calculation():
    """Test points calculation."""
    assert calculate_points(3, 2, 1) == 11
```

**Guidelines:**
- Add helpful messages to assertions
- Include input values and expected output
- Makes debugging faster

---

### 6. Avoid Test Logic

❌ **Bad:**
```python
def test_with_complex_logic():
    """Test with complex logic (anti-pattern)."""
    results = []

    for i in range(10):
        if i % 2 == 0:
            result = process_even(i)
        else:
            result = process_odd(i)
        results.append(result)

    assert all(r > 0 for r in results)
```

✅ **Better:**
```python
@pytest.mark.parametrize("input,expected", [
    (0, 0),
    (2, 4),
    (4, 8),
    # ... etc
])
def test_process_even(input, expected):
    """Test process_even with various inputs."""
    assert process_even(input) == expected
```

**Guidelines:**
- Tests should be simple and readable
- Avoid loops, conditionals, complex logic
- Use parametrization instead

---

### 7. Mock at the Right Level

✅ **Good:**
```python
def test_match_conductor_with_mocked_http():
    """Test match conductor with mocked HTTP (integration level)."""
    # Mock at the HTTP boundary
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = {"result": "ACK"}

        # Real business logic executed
        result = conduct_match(...)

        assert result["state"] == "FINISHED"
```

❌ **Too much mocking (becomes unit test):**
```python
def test_match_conductor_over_mocked():
    """Test match conductor (over-mocked)."""
    # Mock everything - not testing actual integration!
    with patch('match_conductor.send_invitation') as mock_send, \
         patch('match_conductor.get_parity_choice') as mock_parity, \
         patch('match_conductor.calculate_winner') as mock_winner:

        mock_send.return_value = True
        mock_parity.return_value = "even"
        mock_winner.return_value = "P01"

        result = conduct_match(...)

        # Only testing mocks call each other!
        assert result["winner"] == "P01"
```

**Guidelines:**
- **Unit tests:** Mock all external dependencies
- **Integration tests:** Mock only network/DB boundaries
- **E2E tests:** Don't mock (use real system)

---

### 8. Clean Up Resources

✅ **Good:**
```python
@pytest.fixture
async def running_server():
    """Start server with guaranteed cleanup."""
    server = Server()
    await server.start()

    yield server

    # Always executes, even if test fails
    await server.shutdown()
```

❌ **Bad:**
```python
async def test_server():
    """Test server (no cleanup)."""
    server = Server()
    await server.start()

    # Test runs...

    await server.shutdown()  # Doesn't run if test fails!
```

**Guidelines:**
- Use fixtures with `yield` for cleanup
- Use `try/finally` in E2E tests
- Ensure resources (files, processes, connections) are released

---

## Troubleshooting

### Common Issues

#### Issue: ImportError for SDK modules

**Symptom:**
```
ImportError: No module named 'SHARED.league_sdk'
```

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH=SHARED:$PYTHONPATH
pytest

# Or run with PYTHONPATH inline
PYTHONPATH=SHARED:$PYTHONPATH pytest
```

#### Issue: Async test not running

**Symptom:**
```
RuntimeWarning: coroutine 'test_async_function' was never awaited
```

**Solution:**
```python
# Add @pytest.mark.asyncio decorator
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

#### Issue: Fixture not found

**Symptom:**
```
fixture 'my_fixture' not found
```

**Solution:**
- Move fixture to `conftest.py` (auto-discovered)
- Or ensure fixture is in same file as test
- Check for typos in fixture name

#### Issue: Tests pass individually, fail together

**Symptom:** `pytest test_a.py` passes, but `pytest test_a.py test_b.py` fails

**Solution:**
- Tests are sharing state (global variables)
- Tests modifying shared files/database
- Fix: Use fixtures to isolate test state

#### Issue: E2E tests hang

**Symptom:** E2E tests never complete

**Solution:**
```bash
# Add timeout
pytest -m e2e --timeout=60

# Check for:
# - Servers not starting
# - Infinite loops
# - Deadlocks in async code
```

#### Issue: Coverage not measuring correctly

**Symptom:** Coverage shows 0% or incorrect values

**Solution:**
```bash
# Ensure source paths correct
pytest --cov=agents --cov=SHARED/league_sdk

# Check .coveragerc [run] source setting
# Should match your package structure
```

---

### Getting Help

#### Run Tests with Maximum Verbosity

```bash
pytest -vvs --tb=long --log-cli-level=DEBUG
```

#### Check Test Collection

```bash
# See which tests would run (without running them)
pytest --collect-only

# Check markers
pytest --markers
```

#### Verify Test Configuration

```bash
# Show pytest configuration
pytest --version
pytest --fixtures

# Show coverage configuration
coverage debug config
```

---

## Summary

### Quick Reference Card

```bash
# Common Commands
pytest                                  # Run all tests
pytest -m unit                          # Unit tests only
pytest -m "not e2e"                    # Skip E2E tests
pytest -k timeout                       # Tests matching "timeout"
pytest --cov --cov-report=html          # Coverage with HTML report
pytest -vs --pdb                        # Verbose, print, debugger on fail

# Coverage
pytest --cov=agents --cov=SHARED/league_sdk --cov-report=term-missing
open htmlcov/index.html

# Specific Tests
pytest tests/unit/test_sdk/test_retry.py
pytest tests/integration/test_match_flow.py::test_successful_match_flow

# Debugging
pytest -x                               # Stop on first failure
pytest -l                               # Show local variables
pytest --pdb                            # Drop into debugger on failure
pytest --trace                          # Drop into debugger at start
```

### Test Categories Summary

| Category | Marker | Speed | Purpose | Example Count |
|----------|--------|-------|---------|---------------|
| **Unit** | `@pytest.mark.unit` | Fast (<1s) | Test components in isolation | ~350 |
| **Integration** | `@pytest.mark.integration` | Medium (1-5s) | Test component interactions | ~120 |
| **E2E** | `@pytest.mark.e2e` | Slow (30-60s) | Test complete system | ~40 |
| **Protocol** | `@pytest.mark.protocol` | Fast (<1s) | Test protocol compliance | ~40 |
| **Edge** | `@pytest.mark.edge` | Fast (<1s) | Test error handling | ~18 |

### Coverage Goals

- **Overall:** ≥85%
- **Critical paths:** ≥90%
- **Protocol models:** ≥95%

### Key Files

| File | Purpose |
|------|---------|
| `pytest.ini` | Pytest configuration |
| `.coveragerc` | Coverage configuration |
| `tests/conftest.py` | Shared fixtures |
| `htmlcov/index.html` | Coverage report |

---

## Related Documentation

- **[Developer Guide](developer_guide.md)** - Setup and development workflow
- **[Configuration Guide](configuration.md)** - System configuration
- **[Architecture Guide](architecture.md)** - System architecture
- **[Protocol Specification](../SHARED/league_sdk/protocol.py)** - league.v2 protocol

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-XX
**Maintained By:** Even/Odd League Development Team
