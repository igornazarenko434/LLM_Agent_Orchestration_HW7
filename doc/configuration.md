# Configuration Guide

**Document Version:** 1.0.0
**Date:** 2025-01-15
**Status:** Complete
**Mission:** M8.3

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Configuration (system.json)](#2-system-configuration-systemjson)
3. [Agent Registry (agents_config.json)](#3-agent-registry-agents_configjson)
4. [League Configuration](#4-league-configuration)
5. [Game Types Registry](#5-game-types-registry)
6. [Default Templates](#6-default-templates)
7. [Environment Variable Overrides](#7-environment-variable-overrides)
8. [Configuration Validation](#8-configuration-validation)
9. [Common Configuration Tasks](#9-common-configuration-tasks)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

The Even/Odd League system uses a **hierarchical configuration system** with JSON files and environment variable overrides. All configuration files are located in the `SHARED/config/` directory.

### Configuration Hierarchy (Priority Order)

```
1. CLI Arguments (highest priority)
   ↓
2. Environment Variables
   ↓
3. JSON Configuration Files
   ↓
4. Hardcoded Defaults (lowest priority)
```

### Configuration Files Structure

```
SHARED/config/
├── system.json                    # Global system settings
├── agents/
│   └── agents_config.json         # Agent registry (LM, referees, players)
├── defaults/
│   ├── player.json                # Player agent template
│   └── referee.json               # Referee agent template
├── games/
│   └── games_registry.json        # Game type definitions
└── leagues/
    └── league_2025_even_odd.json  # League instance configuration
```

### Key Principles

- **Type Safety**: Pydantic validation ensures all values match expected types
- **Environment Flexibility**: Override any setting via environment variables
- **Extensibility**: Add agents, leagues, and games without code changes
- **Clear Defaults**: Template files provide standard configurations
- **Audit Trail**: `last_updated` timestamps track modifications

---

## 2. System Configuration (system.json)

**Location**: `SHARED/config/system.json`

**Purpose**: Global system-wide configuration applying to all agents and leagues.

### Schema Structure

```json
{
  "schema_version": "1.0.0",
  "system_id": "league_system_prod",
  "protocol_version": "league.v2",
  "last_updated": "2025-12-20T00:00:00Z",
  "timeouts": {...},
  "retry_policy": {...},
  "circuit_breaker": {...},
  "security": {...},
  "network": {...},
  "logging": {...},
  "data_retention": {...}
}
```

### 2.1 Timeouts Configuration

Controls maximum wait time for each operation type.

| Setting | Type | Default | Range | Purpose |
|---------|------|---------|-------|---------|
| `registration_sec` | int | 10 | 1-60 | REFEREE/LEAGUE_REGISTER operations |
| `game_join_ack_sec` | int | 5 | 1-60 | GAME_JOIN_ACK response deadline |
| `parity_choice_sec` | int | 30 | 1-120 | CHOOSE_PARITY decision timeout |
| `game_over_sec` | int | 5 | 1-60 | GAME_OVER message handling |
| `match_result_sec` | int | 10 | 1-60 | MATCH_RESULT_REPORT submission |
| `league_query_sec` | int | 10 | 1-60 | LEAGUE_QUERY operations |
| `generic_sec` | int | 10 | 1-60 | Default for unmapped operations |

**Example Configuration**:

```json
{
  "timeouts": {
    "registration_sec": 10,
    "game_join_ack_sec": 5,
    "parity_choice_sec": 30,
    "game_over_sec": 5,
    "match_result_sec": 10,
    "league_query_sec": 10,
    "generic_sec": 10
  }
}
```

**When to Adjust**:
- **Slow networks**: Increase timeouts by 50-100%
- **Fast local networks**: Decrease timeouts by 20-30%
- **LLM-powered players**: Increase `parity_choice_sec` to 60-120 seconds

### 2.2 Retry Policy Configuration

Controls resilience behavior for transient failures.

| Setting | Type | Default | Validation | Purpose |
|---------|------|---------|-----------|---------|
| `max_retries` | int | 3 | 0-10 | Maximum retry attempts |
| `backoff_strategy` | string | "exponential" | exponential/linear/fixed | Delay calculation |
| `initial_delay_sec` | float | 2.0 | 0.1-60.0 | First retry delay |
| `max_delay_sec` | float | 10.0 | 0.1-120.0 | Maximum delay cap |
| `retryable_errors` | array | (see below) | Error codes | Transient errors |

**Retryable Error Codes**:
```json
["E001", "E005", "E006", "E009", "E014", "E015", "E016"]
```

- `E001`: Generic communication error
- `E005`: Referee not available
- `E006`: Player not available
- `E009`: Match data inconsistency
- `E014`: League not found
- `E015`: Agent registration failed
- `E016`: Timeout during operation

**Retry Sequence Example** (Exponential Backoff):
```
Attempt 1: Immediate
Attempt 2: 2.0 seconds wait
Attempt 3: 4.0 seconds wait (2.0 * 2)
Attempt 4: 8.0 seconds wait (4.0 * 2, capped at max_delay_sec)
```

**Example Configuration**:

```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential",
    "initial_delay_sec": 2.0,
    "max_delay_sec": 10.0,
    "retryable_errors": ["E001", "E005", "E006", "E009", "E014", "E015", "E016"]
  }
}
```

### 2.3 Circuit Breaker Configuration

Prevents cascading failures by temporarily isolating failing endpoints.

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `failure_threshold` | int | 5 | Consecutive failures before opening circuit |
| `reset_timeout_sec` | int | 60 | Time before attempting recovery |

**Circuit Breaker States**:
1. **CLOSED**: Normal operation, requests pass through
2. **OPEN**: Failures exceeded threshold, fail fast without retries
3. **HALF_OPEN**: Testing recovery after reset timeout

**Example Configuration**:

```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "reset_timeout_sec": 60
  }
}
```

### 2.4 Security Configuration

Authentication and authorization settings.

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `auth_token_length` | int | 32 | Minimum token length (characters) |
| `token_ttl_minutes` | int | 1440 | Token lifetime (24 hours) |
| `require_auth` | bool | true | Enforce authentication |
| `allow_start_league_without_auth` | bool | true | Admin override |
| `allowed_origins` | array | ["*"] | CORS origins |

**Example Configuration**:

```json
{
  "security": {
    "auth_token_length": 32,
    "token_ttl_minutes": 1440,
    "require_auth": true,
    "allow_start_league_without_auth": true,
    "allowed_origins": ["*"]
  }
}
```

### 2.5 Network Configuration

Port allocation and connectivity settings.

| Setting | Type | Default | Range | Purpose |
|---------|------|---------|-------|---------|
| `host` | string | "localhost" | Valid hostname | Binding address |
| `league_manager_port` | int | 8000 | 1024-65535 | League Manager port |
| `referee_port_start` | int | 8001 | 1024-65535 | First referee port |
| `referee_port_end` | int | 8002 | 1024-65535 | Last referee port |
| `player_port_start` | int | 8101 | 1024-65535 | First player port |
| `player_port_end` | int | 9100 | 1024-65535 | Last player port |
| `max_connections` | int | 100 | 1+ | Concurrent connections |
| `request_timeout_sec` | int | 30 | 1-300 | HTTP request deadline |

**Port Capacity Calculation**:
- **Referees**: `referee_port_end - referee_port_start + 1` = 2 (ports 8001-8002)
- **Players**: `player_port_end - player_port_start + 1` = 999 (ports 8101-9100)

**Example Configuration**:

```json
{
  "network": {
    "host": "localhost",
    "league_manager_port": 8000,
    "referee_port_start": 8001,
    "referee_port_end": 8002,
    "player_port_start": 8101,
    "player_port_end": 9100,
    "max_connections": 100,
    "request_timeout_sec": 30
  }
}
```

**Scaling to 10,000 Players**:

```json
{
  "network": {
    "player_port_start": 8101,
    "player_port_end": 18100
  }
}
```

This allocates 8101-18100 = 10,000 ports for players.

### 2.6 Logging Configuration

Structured logging settings.

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `level` | string | "INFO" | Log verbosity |
| `format` | string | "json" | Output format |
| `max_file_size_mb` | int | 100 | Rotation threshold |
| `backup_count` | int | 5 | Rotated backups to keep |

**Log Levels** (least to most verbose):
- `CRITICAL`: System failures only
- `ERROR`: Errors and above
- `WARNING`: Warnings and above
- `INFO`: Informational and above (default)
- `DEBUG`: All messages including debug info

**Example Configuration**:

```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "max_file_size_mb": 100,
    "backup_count": 5
  }
}
```

### 2.7 Data Retention Configuration

Data lifecycle management and cleanup policies.

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `enabled` | bool | true | Enable retention policies |
| `logs_retention_days` | int | 30 | Days before purging logs |
| `match_data_retention_days` | int | 365 | Days before purging matches |
| `player_history_retention_days` | int | 365 | Days before purging histories |
| `rounds_retention_days` | int | 365 | Days before purging rounds |
| `standings_retention` | string | "permanent" | Never purge standings |
| `cleanup_schedule_cron` | string | "0 2 * * *" | Cleanup schedule (2 AM daily) |
| `archive_enabled` | bool | true | Archive before deletion |
| `archive_path` | string | "SHARED/archive/" | Archive location |
| `archive_compression` | string | "gzip" | Compression method |

**Example Configuration**:

```json
{
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

---

## 3. Agent Registry (agents_config.json)

**Location**: `SHARED/config/agents/agents_config.json`

**Purpose**: Central registry of all agents (League Manager, Referees, Players) with endpoints, capabilities, and metadata.

### Schema Structure

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T00:00:00Z",
  "league_manager": {...},
  "referees": [...],
  "players": [...]
}
```

### 3.1 League Manager Entry

**Singleton** - Only one League Manager per system.

```json
{
  "league_manager": {
    "agent_id": "LM01",
    "agent_type": "league_manager",
    "display_name": "League Manager",
    "endpoint": "http://localhost:8000/mcp",
    "port": 8000,
    "active": true,
    "version": "1.0.0",
    "capabilities": [
      "register_referee",
      "register_player",
      "report_match_result",
      "get_standings",
      "start_league",
      "league_query"
    ],
    "game_types": ["even_odd"],
    "metadata": {
      "max_concurrent_leagues": 10,
      "max_players_per_league": 10000,
      "supported_game_types": ["even_odd"]
    }
  }
}
```

### 3.2 Referee Entry Template

```json
{
  "agent_id": "REF01",
  "agent_type": "referee",
  "display_name": "Referee 01",
  "endpoint": "http://localhost:8001/mcp",
  "port": 8001,
  "active": true,
  "version": "1.0.0",
  "capabilities": [
    "conduct_match",
    "enforce_timeouts",
    "determine_winner",
    "report_results",
    "get_match_state"
  ],
  "game_types": ["even_odd"],
  "max_concurrent_matches": 10,
  "metadata": {
    "match_timeout_enforcement": true,
    "supports_draw": true,
    "specialization": "even_odd",
    "auto_register": true
  }
}
```

**Referee Fields**:

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `agent_id` | string | Yes | Unique ID (e.g., REF01, REF02) |
| `agent_type` | string | Yes | Must be "referee" |
| `display_name` | string | Yes | Human-readable name |
| `endpoint` | string | Yes | MCP server URL |
| `port` | int | Yes | Port number (must match network config) |
| `active` | bool | Yes | Enabled/disabled status |
| `version` | string | Yes | Agent software version |
| `capabilities` | array | Yes | Available operations |
| `game_types` | array | Yes | Supported games |
| `max_concurrent_matches` | int | No | Parallel match limit |
| `metadata` | object | No | Additional settings |

### 3.3 Player Entry Template

```json
{
  "agent_id": "P01",
  "agent_type": "player",
  "display_name": "Player 01",
  "endpoint": "http://localhost:8101/mcp",
  "port": 8101,
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
    "team": "alpha",
    "skill_level": "beginner",
    "auto_register": true
  }
}
```

**Player Metadata Fields**:

| Field | Type | Options | Purpose |
|-------|------|---------|---------|
| `strategy` | string | random, history_based, llm, ml | Decision algorithm |
| `team` | string | Any string | Team assignment |
| `skill_level` | string | beginner, intermediate, advanced | Competency level |
| `auto_register` | bool | true, false | Automatically register with LM |

**Current Players**:

| Agent ID | Port | Strategy | Team | Skill Level |
|----------|------|----------|------|-------------|
| P01 | 8101 | random | alpha | beginner |
| P02 | 8102 | history_based | beta | intermediate |
| P03 | 8103 | random | gamma | beginner |
| P04 | 8104 | random | delta | beginner |

### 3.4 Adding a New Agent

#### Adding a Referee

1. Ensure port is within referee range (8001-8002, or extend `referee_port_end`)
2. Copy referee template from `SHARED/config/defaults/referee.json`
3. Update fields:
   - `agent_id`: "REF03" (increment)
   - `port`: 8003 (next available, requires extending port_end)
   - `endpoint`: Update port in URL
4. Add to `referees` array in `agents_config.json`

**Example**:

```json
{
  "referees": [
    {
      "agent_id": "REF01",
      "port": 8001,
      ...
    },
    {
      "agent_id": "REF02",
      "port": 8002,
      ...
    },
    {
      "agent_id": "REF03",
      "port": 8003,
      "endpoint": "http://localhost:8003/mcp",
      ...
    }
  ]
}
```

#### Adding a Player

1. Ensure port is within player range (8101-9100)
2. Copy player template from `SHARED/config/defaults/player.json`
3. Update fields:
   - `agent_id`: "P05" (increment)
   - `port`: 8105 (next available)
   - `endpoint`: Update port in URL
   - `metadata.strategy`: Choose strategy
   - `metadata.team`: Assign team
4. Add to `players` array in `agents_config.json`

**Example**:

```json
{
  "players": [
    {
      "agent_id": "P01",
      ...
    },
    {
      "agent_id": "P05",
      "port": 8105,
      "endpoint": "http://localhost:8105/mcp",
      "metadata": {
        "strategy": "llm",
        "team": "epsilon",
        "skill_level": "advanced",
        "auto_register": true
      }
    }
  ]
}
```

---

## 4. League Configuration

**Location**: `SHARED/config/leagues/<league_id>.json`

**Purpose**: Configuration for a specific league instance.

### Schema Structure

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T00:00:00Z",
  "league_id": "league_2025_even_odd",
  "display_name": "2025 Even/Odd Championship League",
  "game_type": "even_odd",
  "status": "ACTIVE",
  "scoring": {...},
  "schedule_type": "round_robin",
  "participants": {...},
  "registration_deadline": null,
  "start_time": null,
  "registered_players": [],
  "assigned_referees": [],
  "metadata": {...}
}
```

### 4.1 League Fields

| Field | Type | Required | Validation | Purpose |
|-------|------|----------|-----------|---------|
| `league_id` | string | Yes | ^[a-z0-9_]+$ | Unique identifier |
| `display_name` | string | Yes | min_length: 1 | Human-readable name |
| `game_type` | string | Yes | Must exist in games_registry.json | Game type |
| `status` | enum | Yes | PENDING, ACTIVE, PAUSED, COMPLETED | League state |
| `schedule_type` | enum | Yes | round_robin, elimination, swiss | Tournament format |
| `registration_deadline` | ISO 8601 | No | ISO 8601 or null | Registration cutoff |
| `start_time` | ISO 8601 | No | ISO 8601 or null | League start time |
| `registered_players` | array | No | Array of player IDs | Enrolled players |
| `assigned_referees` | array | No | Array of referee IDs | Assigned referees |

### 4.2 Scoring Configuration

```json
{
  "scoring": {
    "win_points": 3,
    "draw_points": 1,
    "loss_points": 0,
    "technical_loss_points": 0,
    "tiebreaker_order": ["points", "wins", "head_to_head", "random"]
  }
}
```

| Setting | Type | Default | Purpose |
|---------|------|---------|---------|
| `win_points` | int | 3 | Points for victory |
| `draw_points` | int | 1 | Points for tie |
| `loss_points` | int | 0 | Points for defeat |
| `technical_loss_points` | int | 0 | Penalty points (forfeit) |
| `tiebreaker_order` | array | (see above) | Ranking tie resolution |

### 4.3 Participants Configuration

```json
{
  "participants": {
    "min_players": 2,
    "max_players": 10000
  }
}
```

### 4.4 Creating a New League

1. Create file: `SHARED/config/leagues/league_<year>_<game_type>.json`
2. Use template:

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T00:00:00Z",
  "league_id": "league_2025_new_game",
  "display_name": "2025 New Game Championship",
  "game_type": "rock_paper_scissors",
  "status": "PENDING",
  "scoring": {
    "win_points": 3,
    "draw_points": 1,
    "loss_points": 0,
    "technical_loss_points": 0,
    "tiebreaker_order": ["points", "wins", "head_to_head", "random"]
  },
  "schedule_type": "round_robin",
  "participants": {
    "min_players": 2,
    "max_players": 10000
  },
  "registration_deadline": null,
  "start_time": null,
  "registered_players": [],
  "assigned_referees": [],
  "metadata": {
    "description": "Your league description",
    "season": "2025",
    "division": "main",
    "created_at": "2025-01-15T00:00:00Z",
    "created_by": "league_manager:LM01"
  }
}
```

3. Validate game_type exists in `games_registry.json`
4. Start league with:

```bash
./scripts/trigger_league_start.sh --league-id league_2025_new_game
```

---

## 5. Game Types Registry

**Location**: `SHARED/config/games/games_registry.json`

**Purpose**: Registry of all available game types with rules and implementation details.

### Schema Structure

```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T00:00:00Z",
  "games": [
    {...game entry...}
  ]
}
```

### 5.1 Game Entry Template

```json
{
  "game_type": "even_odd",
  "display_name": "Even/Odd",
  "description": "Players choose 'even' or 'odd'. A random number (1-10) is drawn. The player who chose the correct parity wins.",
  "rules_module": "agents.referee.games.even_odd",
  "supports_draw": true,
  "max_round_time_sec": 60,
  "min_players": 2,
  "max_players": 2,
  "game_specific_config": {
    "random_range_min": 1,
    "random_range_max": 10,
    "valid_choices": ["even", "odd"],
    "draw_method": "cryptographic",
    "rules": {
      "win_condition": "Player's choice matches the parity of the drawn number",
      "draw_condition": "Both players choose the same parity",
      "parity_definition": {
        "even": [2, 4, 6, 8, 10],
        "odd": [1, 3, 5, 7, 9]
      }
    }
  }
}
```

### 5.2 Game Configuration Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `game_type` | string | Yes | Unique identifier (lowercase + underscores) |
| `display_name` | string | Yes | Human-readable name |
| `description` | string | No | Game overview |
| `rules_module` | string | Yes | Python module path |
| `supports_draw` | bool | Yes | Whether ties are possible |
| `max_round_time_sec` | int | Yes | Maximum seconds per round |
| `min_players` | int | Yes | Minimum players |
| `max_players` | int | Yes | Maximum players |
| `game_specific_config` | object | Yes | Game-specific settings |

### 5.3 Adding a New Game Type

**Step 1**: Add game entry to `games_registry.json`

```json
{
  "games": [
    {
      "game_type": "rock_paper_scissors",
      "display_name": "Rock/Paper/Scissors",
      "description": "Players choose rock, paper, or scissors. Rock beats scissors, scissors beats paper, paper beats rock.",
      "rules_module": "agents.referee.games.rps",
      "supports_draw": true,
      "max_round_time_sec": 30,
      "min_players": 2,
      "max_players": 2,
      "game_specific_config": {
        "valid_choices": ["rock", "paper", "scissors"],
        "draw_method": "cryptographic",
        "rules": {
          "beats": {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
          }
        }
      }
    }
  ]
}
```

**Step 2**: Implement game logic in `agents/referee_REF01/games/rps.py`

**Step 3**: Update agents to support new game type in `agents_config.json`

```json
{
  "game_types": ["even_odd", "rock_paper_scissors"]
}
```

**Step 4**: Create league config for new game

```bash
cp SHARED/config/leagues/league_2025_even_odd.json \
   SHARED/config/leagues/league_2025_rps.json

# Edit new file to set game_type: "rock_paper_scissors"
```

---

## 6. Default Templates

**Location**: `SHARED/config/defaults/`

**Purpose**: Template configurations for new agents.

### 6.1 defaults/referee.json

```json
{
  "agent_type": "referee",
  "version": "1.0.0",
  "log_level": "INFO",
  "game_types": ["even_odd"],
  "capabilities": [
    "conduct_match",
    "enforce_timeouts",
    "determine_winner",
    "report_results",
    "get_match_state"
  ],
  "max_concurrent_matches": 10,
  "metadata": {
    "match_timeout_enforcement": true,
    "supports_draw": true,
    "specialization": "even_odd",
    "auto_register": true
  }
}
```

### 6.2 defaults/player.json

```json
{
  "agent_type": "player",
  "version": "1.0.0",
  "log_level": "INFO",
  "game_types": ["even_odd"],
  "capabilities": [
    "handle_game_invitation",
    "choose_parity",
    "notify_match_result",
    "get_player_state"
  ],
  "metadata": {
    "strategy": "random",
    "team": "default",
    "skill_level": "beginner",
    "auto_register": true
  }
}
```

---

## 7. Environment Variable Overrides

Environment variables override JSON defaults. Copy `.env.example` to `.env` and set variables.

### 7.1 Network Configuration

| Variable | JSON Path | Type | Default |
|----------|-----------|------|---------|
| `BASE_HOST` | system.network.host | string | localhost |
| `LEAGUE_MANAGER_PORT` | system.network.league_manager_port | int | 8000 |
| `REFEREE_PORT_START` | system.network.referee_port_start | int | 8001 |
| `REFEREE_PORT_END` | system.network.referee_port_end | int | 8002 |
| `PLAYER_PORT_START` | system.network.player_port_start | int | 8101 |
| `PLAYER_PORT_END` | system.network.player_port_end | int | 9100 |

**Example**:

```bash
export BASE_HOST=0.0.0.0  # Bind to all interfaces
export LEAGUE_MANAGER_PORT=9000
export PLAYER_PORT_END=10000  # 1900 player slots
```

### 7.2 Timeout Configuration

| Variable | JSON Path | Type | Default |
|----------|-----------|------|---------|
| `TIMEOUT_REGISTRATION` | system.timeouts.registration_sec | int | 10 |
| `TIMEOUT_GAME_JOIN_ACK` | system.timeouts.game_join_ack_sec | int | 5 |
| `TIMEOUT_PARITY_CHOICE` | system.timeouts.parity_choice_sec | int | 30 |
| `TIMEOUT_MATCH_RESULT` | system.timeouts.match_result_sec | int | 10 |

**Example**:

```bash
export TIMEOUT_PARITY_CHOICE=60  # Extend for LLM players
export TIMEOUT_MATCH_RESULT=20
```

### 7.3 Retry Policy Configuration

| Variable | JSON Path | Type | Default |
|----------|-----------|------|---------|
| `RETRY_MAX_RETRIES` | system.retry_policy.max_retries | int | 3 |
| `RETRY_INITIAL_DELAY_SEC` | system.retry_policy.initial_delay_sec | float | 2.0 |
| `RETRY_MAX_DELAY_SEC` | system.retry_policy.max_delay_sec | float | 10.0 |

**Example**:

```bash
export RETRY_MAX_RETRIES=5
export RETRY_INITIAL_DELAY_SEC=3.0
```

### 7.4 Logging Configuration

| Variable | JSON Path | Type | Default |
|----------|-----------|------|---------|
| `LOG_LEVEL` | system.logging.level | string | INFO |

**Example**:

```bash
export LOG_LEVEL=DEBUG  # Verbose logging
```

### 7.5 League Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `LEAGUE_ID` | Override default league | (none) |
| `DATA_DIR` | Data storage path | SHARED/data |
| `LOG_DIR` | Logs storage path | SHARED/logs |

**Example**:

```bash
export LEAGUE_ID=league_2025_even_odd
```

---

## 8. Configuration Validation

The system uses **Pydantic models** (`SHARED/league_sdk/config_models.py`) for validation.

### 8.1 Validation Rules

1. **Type Checking**: All values match expected types
2. **Range Validation**: Numeric fields within bounds
3. **Pattern Validation**: String IDs follow naming conventions
4. **Enum Validation**: Limited to allowed values
5. **Required Fields**: Mandatory properties must exist

### 8.2 Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Pattern validation failed | agent_id contains lowercase | Use uppercase (P01, REF02) |
| Value out of range | Port outside 1024-65535 | Use valid port |
| Enum validation failed | Invalid status value | Use PENDING/ACTIVE/PAUSED/COMPLETED |
| Field required | Missing property | Add field to JSON |
| Type validation failed | Wrong type | Convert to correct type |

### 8.3 Validation Commands

```bash
# Validate all configs
./scripts/verify_configs.sh --verbose

# Test config loading
PYTHONPATH=SHARED:$PYTHONPATH python -c "
from league_sdk.config_loader import load_system_config
config = load_system_config('SHARED/config/system.json')
print('✅ System config valid')
"

# Validate agent registry
PYTHONPATH=SHARED:$PYTHONPATH python -c "
from league_sdk.config_loader import load_agents_config
config = load_agents_config('SHARED/config/agents/agents_config.json')
print(f'✅ {len(config.players)} players, {len(config.referees)} referees')
"
```

---

## 9. Common Configuration Tasks

### 9.1 Scaling to 1000 Players

**Step 1**: Extend player port range

```json
// SHARED/config/system.json
{
  "network": {
    "player_port_start": 8101,
    "player_port_end": 9100  // 8101-9100 = 999 players
  }
}
```

**Step 2**: Add players to agent registry

```bash
# Generate player entries programmatically
for i in {5..1000}; do
  cat >> SHARED/config/agents/agents_config.json <<EOF
  {
    "agent_id": "P$(printf %03d $i)",
    "port": $((8100 + i)),
    "endpoint": "http://localhost:$((8100 + i))/mcp",
    ...
  },
EOF
done
```

### 9.2 Adjusting Performance for Slow Networks

```bash
# Increase all timeouts by 2x
export TIMEOUT_REGISTRATION=20
export TIMEOUT_GAME_JOIN_ACK=10
export TIMEOUT_PARITY_CHOICE=60
export TIMEOUT_MATCH_RESULT=20

# Increase retry delays
export RETRY_INITIAL_DELAY_SEC=4.0
export RETRY_MAX_DELAY_SEC=20.0
```

### 9.3 Enabling Debug Logging

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Or edit system.json
{
  "logging": {
    "level": "DEBUG"
  }
}
```

### 9.4 Changing Scoring System

```json
// SHARED/config/leagues/league_2025_even_odd.json
{
  "scoring": {
    "win_points": 5,      // Changed from 3
    "draw_points": 2,     // Changed from 1
    "loss_points": 0,
    "technical_loss_points": -1  // Penalty for forfeit
  }
}
```

---

## 10. Troubleshooting

### 10.1 Port Conflicts

**Problem**: `Address already in use`

**Solution**:

```bash
# Find process using port
lsof -i :8101

# Kill process
kill -9 <PID>

# Or change port in config
export LEAGUE_MANAGER_PORT=9000
```

### 10.2 Config File Not Found

**Problem**: `FileNotFoundError: SHARED/config/system.json`

**Solution**:

```bash
# Verify current directory
pwd  # Should be project root

# Check config exists
ls SHARED/config/system.json

# Run from correct directory
cd /path/to/LLM_Agent_Orchestration_HW7
```

### 10.3 Validation Errors

**Problem**: `Pydantic ValidationError`

**Solution**:

```bash
# Validate config manually
PYTHONPATH=SHARED:$PYTHONPATH python -c "
from league_sdk.config_loader import load_system_config
try:
    config = load_system_config('SHARED/config/system.json')
    print('✅ Config valid')
except Exception as e:
    print(f'❌ Validation error: {e}')
"
```

### 10.4 Environment Variables Not Applied

**Problem**: Environment variables ignored

**Solution**:

```bash
# Check if .env loaded
cat .env | grep LOG_LEVEL

# Manually export
export LOG_LEVEL=DEBUG

# Verify override works
env | grep LOG_LEVEL
```

### 10.5 Agent Not Auto-Registering

**Problem**: Agent starts but doesn't register with League Manager

**Solution**:

```json
// Check metadata.auto_register in agents_config.json
{
  "metadata": {
    "auto_register": true  // Must be true
  }
}
```

---

## Summary

This configuration system provides:

- **Centralized Control**: All settings in structured JSON files
- **Environment Flexibility**: Override defaults via environment variables
- **Type Safety**: Pydantic validation ensures correctness
- **Extensibility**: Add agents, leagues, games without code changes
- **Clear Defaults**: Template files for standard configurations
- **Audit Trail**: Timestamps track modifications

For further information, see:
- [Extensibility Guide](usability_extensibility.md) - Extension points
- [Developer Guide](developer_guide.md) - Setup and development workflow
- [Architecture Documentation](architecture.md) - System design
