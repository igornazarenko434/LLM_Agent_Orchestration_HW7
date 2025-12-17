# Mission 2 Implementation Prompt Log
**Date:** 2025-12-16
**Mission Section:** M2: Setup & Architecture
**Missions Covered:** M2.0 - M2.5

---

## Original User Prompt

```
proceed to mission 2.0. you are the best full stack builder and developer. you have deep
expertise in creating the required modules according to the overall projects' definitions
and goals. you have deep expertise in backend development, architecture thinking and module
design for any kind of multiagent systems that includes using MCP client and servers and
make sure they all integrated in the best possible way together. make sure you now implement
and follow all the mission inside section2 according to those principles, and make sure you
creating all according to what we defined on our prd file and all perfectly consistent.

before you start implementing mission 2.1 i want you to add in the doc folder, prompt_log
folder and add these all the full prompt we write now as the prompt that we wrote for
starting implementing mission 2. write in this document the full prompt and how it helped
you to start implementing mission 2.
```

---

## Context Leading to Mission 2

### Completed Missions Prior to M2:
1. **M0.1:** Environment Setup - Python 3.14.0, virtual environment, git initialization
2. **M0.2:** Project Structure Creation - Complete directory tree (SHARED/, agents/, tests/, doc/, scripts/)
3. **M0.3:** Dependency Installation - All packages installed (FastAPI, Pydantic, pytest, etc.)
4. **M1.1:** PRD Document Verification - 17 sections, 15 KPIs, 16 FRs, 15 NFRs, 12 ADRs, 35 evidence entries
5. **M1.2:** Missions Document Verification - 53 missions, 5 Quality Gates, complete dependency graph

### Current State:
- ✅ Development environment ready
- ✅ Directory structure in place
- ✅ All dependencies installed
- ✅ PRD and Missions documents verified and complete
- ⏳ Ready to implement core SDK architecture

---

## How This Prompt Guides Mission 2 Implementation

### 1. **Full Stack Builder & Developer Expertise**
This directive emphasizes:
- **End-to-end thinking:** Each module must integrate seamlessly with others
- **Production quality:** Code must be robust, tested, and maintainable
- **System-level view:** Understanding how SDK, agents, and data layers interact

**Applied to M2:**
- Design SDK modules that serve all three agent types (League Manager, Referee, Player)
- Create reusable, DRY components in SHARED/league_sdk/
- Ensure backwards compatibility and extensibility

### 2. **Backend Development Expertise**
This guides:
- **Data layer design:** File-based repositories with atomic operations
- **Configuration management:** Schema validation, environment flexibility
- **Logging infrastructure:** Structured JSON Lines for observability
- **Error handling:** Retry policies with exponential backoff

**Applied to M2:**
- M2.2: Configuration Models & Loader - Pydantic schemas with validation
- M2.3: Data Repository Layer - Atomic writes using temp file + rename
- M2.4: Structured Logging Setup - JSON Lines with rotation
- M2.5: Retry Policy Implementation - Exponential backoff decorator

### 3. **Architecture Thinking**
This ensures:
- **Separation of concerns:** Protocol, config, data, logging are independent modules
- **Modularity:** Each SDK component has single responsibility
- **Testability:** Modules designed for easy unit testing
- **Scalability:** Architecture supports 10,000+ agents

**Applied to M2:**
- Clear module boundaries: protocol.py, config_loader.py, repositories.py, logger.py, retry.py
- Dependency injection ready: Repositories take config as parameters
- Interface-based design: Abstract base classes for extensibility

### 4. **Multi-Agent Systems Design**
This requires:
- **Protocol compliance:** league.v2 envelope with 6 mandatory fields
- **Message validation:** Pydantic models for all 18 message types
- **Agent coordination:** Shared SDK enables consistent communication
- **State management:** Data persistence for matches, standings, history

**Applied to M2:**
- M2.1: Protocol Models Definition - MessageEnvelope base + 18 message types
- Message validation with regex for sender/timestamp formats
- Conversation tracking via conversation_id
- Authentication via auth_token in all messages

### 5. **MCP Client & Server Integration**
This focuses on:
- **JSON-RPC 2.0 over HTTP:** FastAPI servers, requests clients
- **Tool calling pattern:** method, params, result/error structure
- **Endpoint design:** /mcp endpoints on all agents
- **Request-response flow:** Synchronous calls with timeout enforcement

**Applied to M2:**
- Protocol models compatible with JSON-RPC 2.0
- Envelope structure supports tool invocation tracking
- Timeout configurations in system.json
- Retry policy for transient network failures

### 6. **PRD Consistency & Alignment**
This mandates:
- **Protocol version:** All messages must include "protocol": "league.v2"
- **Mandatory fields:** protocol, message_type, sender, timestamp, conversation_id, auth_token
- **Timeout compliance:** 5s join, 30s moves, 10s generic
- **Error codes:** 18 error codes (E001-E018) with severity and retryable flags
- **Retry policy:** 3 retries, exponential backoff (2s, 4s, 8s)

**Applied to M2:**
- Literal type enforcement for protocol field
- Regex validation for sender format: `{agent_type}:{agent_id}`
- ISO 8601 timestamp format: `YYYY-MM-DDTHH:MM:SSZ`
- Config models align with PRD Section 6 (Technical Specifications)

---

## Mission 2 Implementation Plan

### **M2.0: Shared SDK Package Structure** (1 hour)
**Goal:** Create installable Python package structure

**Tasks:**
1. Create `SHARED/league_sdk/__init__.py` with version and exports
2. Create `SHARED/league_sdk/setup.py` for pip install -e
3. Create module stubs: config_loader.py, config_models.py, protocol.py, repositories.py, logger.py, utils.py, retry.py
4. Define package metadata: name="league-sdk", version="1.0.0"
5. Make package installable in editable mode

**Success Criteria:**
- `pip install -e SHARED/league_sdk/` succeeds
- `import league_sdk; print(league_sdk.__version__)` outputs "1.0.0"
- All module stubs importable

---

### **M2.1: Protocol Models Definition** (3 hours)
**Goal:** Define Pydantic models for all 18 message types and MessageEnvelope

**Key Components:**
1. **MessageEnvelope (Base Model):**
   - `protocol: Literal["league.v2"]` - Enforces protocol version
   - `message_type: str` - One of 18 defined types
   - `sender: str` - Regex: `^(player|referee|league_manager):[A-Z0-9]+$`
   - `timestamp: str` - Regex: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`
   - `conversation_id: str` - Thread tracking
   - `auth_token: str` - Min 32 characters

2. **18 Message Type Models:**
   - REFEREE_REGISTER_REQUEST / RESPONSE
   - LEAGUE_REGISTER_REQUEST / RESPONSE
   - ROUND_ANNOUNCEMENT
   - GAME_INVITATION
   - GAME_JOIN_ACK
   - CHOOSE_PARITY_CALL
   - CHOOSE_PARITY_RESPONSE
   - GAME_OVER
   - MATCH_RESULT_REPORT
   - LEAGUE_STANDINGS_UPDATE
   - ROUND_COMPLETED
   - LEAGUE_COMPLETED
   - LEAGUE_QUERY / RESPONSE
   - LEAGUE_ERROR
   - GAME_ERROR

**Architecture Decisions:**
- Use Pydantic v2 BaseModel for validation
- Inheritance: All messages extend MessageEnvelope
- Field validators: Custom validators for timestamp, sender format
- Comprehensive docstrings: Purpose, fields, examples

**Success Criteria:**
- All 18 message models importable
- Validation tests pass (valid accepted, invalid rejected)
- Regex patterns correctly validate sender and timestamp

---

### **M2.2: Configuration Models & Loader** (2 hours)
**Goal:** Implement configuration loading and validation

**Configuration Files:**
1. `SHARED/config/system.json` - System-wide settings
2. `SHARED/config/agents/agents_config.json` - Agent registry
3. `SHARED/config/leagues/league_2025_even_odd.json` - League settings
4. `SHARED/config/games/games_registry.json` - Game type definitions

**Pydantic Models:**
- `SystemConfig` - protocol_version, timeouts, retry_policy, network
- `AgentConfig` - agent_id, agent_type, endpoint, active, metadata
- `LeagueConfig` - league_id, game_type, scoring, participants, status
- `GameConfig` - game_type, display_name, rules_module, max_round_time, supports_draw

**Loader Functions:**
- `load_system_config(path: str) -> SystemConfig`
- `load_league_config(path: str) -> LeagueConfig`
- `load_agents_config(path: str) -> dict[str, list[AgentConfig]]`
- `validate_config_schema(config: dict, schema: Type[BaseModel])`

**Error Handling:**
- FileNotFoundError with helpful message
- JSONDecodeError with line number
- ValidationError with field-level details

**Success Criteria:**
- Valid configs load successfully
- Invalid configs raise ValidationError with clear messages
- All config types tested

---

### **M2.3: Data Repository Layer** (2 hours)
**Goal:** Implement file-based data access layer with atomic writes

**Repository Classes:**

1. **StandingsRepository:**
   - `get_standings(league_id: str) -> list[dict]`
   - `update_standings(league_id: str, standings: list[dict])`
   - Path: `SHARED/data/leagues/{league_id}/standings.json`

2. **MatchRepository:**
   - `save_match(league_id: str, match_id: str, match_data: dict)`
   - `get_match(league_id: str, match_id: str) -> dict`
   - `list_matches(league_id: str, round_num: int = None) -> list[str]`
   - Path: `SHARED/data/matches/{league_id}/{match_id}.json`

3. **PlayerHistoryRepository:**
   - `get_history(player_id: str) -> dict`
   - `update_history(player_id: str, match_result: dict)`
   - Path: `SHARED/data/players/{player_id}/history.json`

**Atomic Write Pattern:**
```python
import tempfile, os

def atomic_write(path: str, data: dict):
    # Write to temp file
    fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, indent=2)
    # Atomic rename
    os.replace(temp_path, path)
```

**Success Criteria:**
- All repository classes importable
- Atomic write tests pass (no partial writes on crash)
- Directories auto-created if missing

---

### **M2.4: Structured Logging Setup** (1.5 hours)
**Goal:** Implement JSON Lines logging with structured formatting

**Logger Configuration:**
```python
def setup_logger(component: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(component)
    handler = logging.FileHandler(log_file)
    formatter = JSONFormatter()  # Custom formatter
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
```

**Log Entry Format:**
```json
{
  "timestamp": "2025-01-15T10:15:30Z",
  "component": "player:P01",
  "event_type": "message_received",
  "level": "INFO",
  "message": "Received GAME_INVITATION",
  "conversation_id": "conv-r1m1-001",
  "message_type": "GAME_INVITATION",
  "sender": "referee:REF01"
}
```

**Helper Functions:**
- `log_message_sent(logger, message: dict)`
- `log_message_received(logger, message: dict)`
- `log_error(logger, error_code: str, details: dict)`

**Log Rotation:**
- Max file size: 100MB
- Use RotatingFileHandler
- Keep 5 backup files

**Success Criteria:**
- Logger writes valid JSONL (parseable by jq)
- Log entries have all required fields
- Log rotation works (tested with mock)

---

### **M2.5: Retry Policy Implementation** (1.5 hours)
**Goal:** Implement retry decorator with exponential backoff

**Retry Decorator:**
```python
def retry_with_backoff(
    max_retries: int = 3,
    retryable_errors: tuple = (ConnectionError, TimeoutError),
    logger: logging.Logger = None
):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_errors as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = 2 ** attempt  # 2, 4, 8
                    if logger:
                        logger.warning(f"Retry {attempt+1}/{max_retries} after {delay}s")
                    time.sleep(delay)
        return wrapper
    return decorator
```

**Retryable vs Non-Retryable Errors:**
- **Retryable:** E005, E006, E009, E014, E015, E016 (transient failures)
- **Non-Retryable:** E001, E002, E003, E004, E011, E012 (terminal errors)

**Usage Example:**
```python
@retry_with_backoff(max_retries=3, logger=agent_logger)
def send_message(endpoint: str, message: dict):
    response = requests.post(endpoint, json=message, timeout=10)
    response.raise_for_status()
    return response.json()
```

**Success Criteria:**
- Decorator retries transient failures
- Non-retryable errors raise immediately
- Backoff delays measured correctly (2s, 4s, 8s)

---

## Quality Gate QG-1: Foundation Quality Gate

**Triggers After:** M2.2 (Protocol Implementation)
**Must Pass Before:** M7.x (Agent Implementation)

**Criteria:**
- ✅ All configuration files created and validated
- ✅ Shared SDK installed and importable
- ✅ Protocol models defined with Pydantic
- ✅ Unit tests for SDK modules: 100% pass rate
- ✅ Code quality: flake8 passes with 0 errors

**Verification Command:**
```bash
pytest tests/unit/test_sdk/ -v && \
flake8 SHARED/league_sdk/ && \
python -c "from league_sdk import protocol; print('SDK OK')"
```

---

## Architecture Principles Applied

### 1. **Separation of Concerns**
- **Protocol:** Message structure and validation (protocol.py)
- **Configuration:** System settings and schemas (config_loader.py, config_models.py)
- **Data:** Persistence layer (repositories.py)
- **Observability:** Logging infrastructure (logger.py)
- **Resilience:** Error handling (retry.py)

### 2. **DRY (Don't Repeat Yourself)**
- Shared SDK prevents code duplication across agents
- MessageEnvelope base class for all messages
- Common retry decorator used by all agents
- Centralized logging setup

### 3. **SOLID Principles**
- **Single Responsibility:** Each module has one job
- **Open/Closed:** Extensible via inheritance (e.g., new message types)
- **Dependency Inversion:** Agents depend on SDK abstractions, not implementations

### 4. **12-Factor App Methodology**
- **Config:** Externalized in JSON files, not hardcoded
- **Logs:** Treat logs as event streams (JSON Lines)
- **Disposability:** Fast startup, graceful shutdown
- **Dev/Prod Parity:** Same code runs in all environments

---

## PRD Alignment Checklist

| PRD Section | Mission 2 Coverage | Status |
|-------------|-------------------|--------|
| Section 6.1: Technology Stack | Pydantic 2.0+, Python logging | ✅ |
| Section 6.3: Protocol Specification | 18 message types, MessageEnvelope | ✅ |
| Section 6.4: Retry Policy | 3 retries, exponential backoff | ✅ |
| Section 8.1: Message Envelope | 6 mandatory fields with validation | ✅ |
| Section 8.2: Error Codes | Retryable/non-retryable classification | ✅ |
| ADR-002: File-Based Storage | Atomic writes, 3-layer architecture | ✅ |
| ADR-004: Exponential Backoff | 2/4/8s delays, configurable | ✅ |
| ADR-006: JSON Lines Logging | Structured logs, streaming-friendly | ✅ |
| NFR-004: Code Quality | Modular design, type hints, docstrings | ✅ |
| NFR-006: Observability | Structured logging, correlation IDs | ✅ |

---

## Expected Deliverables After Mission 2

1. **Installable SDK Package:** `league_sdk` installable via pip
2. **Protocol Models:** 18 message types + MessageEnvelope (protocol.py)
3. **Configuration System:** 4 config models + loaders (config_loader.py, config_models.py)
4. **Data Layer:** 3 repositories with atomic writes (repositories.py)
5. **Logging Infrastructure:** JSON Lines logger with rotation (logger.py)
6. **Retry Mechanism:** Decorator with exponential backoff (retry.py)
7. **Unit Tests:** ≥85% coverage for all SDK modules
8. **Documentation:** Docstrings for all public APIs

---

## Success Metrics

- **Code Quality:** flake8 passes, mypy strict mode passes
- **Test Coverage:** ≥90% for SDK modules
- **Import Success:** `from league_sdk import protocol, config_loader, repositories, logger, retry`
- **Validation Works:** Invalid messages rejected with clear errors
- **Atomic Writes:** No partial writes under failure conditions
- **Log Integrity:** All JSONL files parseable by `jq`
- **Retry Behavior:** Exponential backoff measured in tests

---

## Next Steps After Mission 2

After completing M2 and passing QG-1:
1. **M3: Configuration Layer** - Create actual config files
2. **M4: Testing Infrastructure** - Set up pytest, fixtures, test templates
3. **M5: Research & Protocol Design** - Document MCP patterns, game rules
4. **M6: UX & Developer Experience** - CLI args, operational scripts
5. **M7: Agent Implementation** - Build League Manager, Referee, Player agents

---

## Conclusion

This prompt establishes the foundation for a production-grade multi-agent system by:
- Emphasizing **architectural thinking** over quick implementation
- Ensuring **PRD consistency** at every decision point
- Applying **best practices** from distributed systems and backend development
- Creating **reusable, testable, maintainable** components
- Setting up **observability and resilience** from day one

The Mission 2 implementation will serve as the bedrock for all agent implementations, ensuring consistency, reliability, and scalability across the entire Even/Odd League system.

**Total Estimated Time for Mission 2:** 11.5 hours
**Critical Path Impact:** Foundation for all subsequent missions (M3-M9)
**Quality Gate:** QG-1 must pass before proceeding to agent implementation

---

**Document Created:** 2025-12-16
**Author:** Claude Sonnet 4.5 (Development Agent)
**Purpose:** Capture implementation guidance for Mission 2 (Setup & Architecture)
