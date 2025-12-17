# Even/Odd League - Complete Project Guide
## Multi-Agent System with MCP Protocol

---

## TABLE OF CONTENTS
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Protocol Specifications](#protocol-specifications)
4. [Agent Implementations](#agent-implementations)
5. [Data Layer](#data-layer)
6. [Execution Flow](#execution-flow)
7. [Implementation Checklist](#implementation-checklist)

---

## SYSTEM OVERVIEW

You are building a **Multi-Agent League System** where autonomous AI agents compete in an "Even/Odd" game using the **Model Context Protocol (MCP)**. This is a production-ready distributed system that demonstrates:

- AI agent orchestration
- JSON-RPC 2.0 over HTTP
- Multi-agent communication patterns
- Resilience and error handling
- Structured data management

### Key Characteristics
- **Protocol Version**: league.v2
- **Communication**: JSON-RPC 2.0 over HTTP/localhost
- **Architecture**: Server-Client hybrid (agents are both)
- **Game Type**: Even/Odd (simple but demonstrates full protocol)
- **League Format**: Round-Robin tournament

---

## ARCHITECTURE

### Three Agent Types

#### 1. League Manager (Port 8000)
**Role**: Central orchestrator - "The Architect"

**Responsibilities**:
- Register referees and players
- Create round-robin match schedules (n*(n-1)/2 matches for n players)
- Calculate standings (Win=3pts, Draw=1pt, Loss=0pts)
- Broadcast round announcements
- Publish standings updates
- Declare league completion and champion

**Acts As**:
- MCP Server: Exposes tools for registration
- MCP Client: Calls players/referees to orchestrate

**Endpoint**: `http://localhost:8000/mcp`

**Required Tools**:
- `register_referee` - Accept referee registrations
- `register_player` - Accept player registrations
- `report_match_result` - Receive match results from referees
- `get_standings` - Query current standings

---

#### 2. Referee Agents (Ports 8001-8002)
**Role**: Game conductors - "The Dynamic Implementer"

**Responsibilities**:
- Register with League Manager at startup
- Manage individual matches from invitation to completion
- Enforce game rules (Even/Odd logic)
- Handle timeouts (5 sec for join, 30 sec for moves)
- Draw random numbers (1-10)
- Determine winners based on parity
- Report results to League Manager
- Handle player errors and disconnections

**Acts As**:
- MCP Server: Exposes game management tools
- MCP Client: Calls player tools to conduct games

**Endpoint**: `http://localhost:8001/mcp` (REF01), `http://localhost:8002/mcp` (REF02)

**Required Tools**:
- `start_match` - Initiate a match
- `collect_choices` - Gather player decisions

**Match States**:
- WAITING_FOR_PLAYERS
- COLLECTING_CHOICES
- DRAWING_NUMBER
- FINISHED

---

#### 3. Player Agents (Ports 8101-8104)
**Role**: Game participants - "The Reactive Agents"

**Responsibilities**:
- Register with League Manager at startup
- Respond to game invitations within 5 seconds
- Choose "even" or "odd" within 30 seconds when prompted
- Update internal state/history after matches
- Implement playing strategy (random, history-based, or LLM-guided)

**Acts As**:
- MCP Server: Exposes tools that referee calls

**Endpoints**:
- `http://localhost:8101/mcp` (P01)
- `http://localhost:8102/mcp` (P02)
- `http://localhost:8103/mcp` (P03)
- `http://localhost:8104/mcp` (P04)

**Required Tools** (MANDATORY):
1. **`handle_game_invitation`**
   - Input: Game invitation details (match_id, opponent_id, referee, etc.)
   - Output: GAME_JOIN_ACK with acceptance status
   - Timeout: 5 seconds

2. **`choose_parity`**
   - Input: Game context (opponent_id, round_id, standings, etc.)
   - Output: Choice of "even" or "odd"
   - Timeout: 30 seconds

3. **`notify_match_result`**
   - Input: Match result (winner, drawn_number, choices, etc.)
   - Output: Acknowledgment
   - Purpose: Update internal state/history

---

## PROTOCOL SPECIFICATIONS

### Core Protocol: league.v2

All agents MUST implement:
- **JSON-RPC 2.0** message format
- **HTTP POST** to `/mcp` endpoint
- **Standard message envelope** with mandatory fields

### Message Envelope Structure

**Every message MUST include these fields**:

```json
{
  "protocol": "league.v2",
  "message_type": "MESSAGE_TYPE",
  "sender": "agent_type:agent_id",
  "timestamp": "2025-01-15T10:15:30Z",
  "conversation_id": "conv-unique-id",
  "auth_token": "tok-agent-xyz123"
}
```

**Field Requirements**:
- `protocol`: Always "league.v2"
- `message_type`: One of 18 defined types (see below)
- `sender`: Format is "{agent_type}:{agent_id}" (e.g., "player:P01", "referee:REF01")
- `timestamp`: ISO 8601 format in UTC/GMT timezone (MUST end with 'Z')
- `conversation_id`: Unique per conversation thread
- `auth_token`: Received during registration, used for authentication

---

### 18 Message Types

#### Registration Messages
1. **REFEREE_REGISTER_REQUEST** - Referee → League Manager
2. **REFEREE_REGISTER_RESPONSE** - League Manager → Referee (returns referee_id, auth_token)
3. **LEAGUE_REGISTER_REQUEST** - Player → League Manager
4. **LEAGUE_REGISTER_RESPONSE** - League Manager → Player (returns player_id, auth_token)

#### Game Flow Messages
5. **ROUND_ANNOUNCEMENT** - League Manager → All Players (broadcast)
6. **GAME_INVITATION** - Referee → Players (invite to match)
7. **GAME_JOIN_ACK** - Player → Referee (confirm arrival)
8. **CHOOSE_PARITY_CALL** - Referee → Player (request choice)
9. **CHOOSE_PARITY_RESPONSE** - Player → Referee (return "even" or "odd")
10. **GAME_OVER** - Referee → Players (announce result)
11. **MATCH_RESULT_REPORT** - Referee → League Manager (report outcome)

#### Standings & Completion Messages
12. **LEAGUE_STANDINGS_UPDATE** - League Manager → All Players (broadcast standings)
13. **ROUND_COMPLETED** - League Manager → All Players (round finished)
14. **LEAGUE_COMPLETED** - League Manager → All Players (league finished, announce champion)

#### Query Messages
15. **LEAGUE_QUERY** - Any Agent → League Manager (request info)
16. **LEAGUE_QUERY_RESPONSE** - League Manager → Requester (return standings/info)

#### Error Messages
17. **LEAGUE_ERROR** - League Manager → Agent (league-level error)
18. **GAME_ERROR** - Referee → Player (game-level error)

---

### Response Timeouts (CRITICAL)

| Action | Timeout | Consequence of Failure |
|--------|---------|------------------------|
| GAME_JOIN_ACK | 5 seconds | Technical loss for match |
| CHOOSE_PARITY_RESPONSE | 30 seconds | Technical loss for match |
| Other responses | 10 seconds | Retry up to 3 times |

---

### Error Codes (18 Defined)

| Code | Description | Severity |
|------|-------------|----------|
| E001 | TIMEOUT_ERROR | High |
| E002 | INVALID_MESSAGE_FORMAT | Medium |
| E003 | AUTHENTICATION_FAILED | High |
| E004 | AGENT_NOT_REGISTERED | High |
| E005 | INVALID_GAME_STATE | Medium |
| E006 | PLAYER_NOT_AVAILABLE | Medium |
| E007 | MATCH_NOT_FOUND | Medium |
| E008 | LEAGUE_NOT_FOUND | High |
| E009 | ROUND_NOT_ACTIVE | Medium |
| E010 | INVALID_MOVE | Low |
| E011 | PROTOCOL_VERSION_MISMATCH | High |
| E012 | AUTH_TOKEN_INVALID | High |
| E013 | CONVERSATION_ID_MISMATCH | Medium |
| E014 | RATE_LIMIT_EXCEEDED | Medium |
| E015 | INTERNAL_SERVER_ERROR | High |
| E016 | SERVICE_UNAVAILABLE | High |
| E017 | DUPLICATE_REGISTRATION | Medium |
| E018 | INVALID_ENDPOINT | High |

---

### Retry Policy (MANDATORY)

**Configuration**:
- Max retries: 3
- Backoff strategy: Exponential
- Initial delay: 2 seconds
- Max delay: 10 seconds

**Implementation**:
```python
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = 2 ** attempt  # Exponential backoff
            time.sleep(delay)
```

---

## AGENT IMPLEMENTATIONS

### Agent Lifecycle States

Every agent goes through these states:

```
INIT → REGISTERED → ACTIVE → SUSPENDED → SHUTDOWN
```

**State Descriptions**:
- **INIT**: Agent starting up, loading configuration
- **REGISTERED**: Successfully registered with League Manager
- **ACTIVE**: Participating in games
- **SUSPENDED**: Temporarily inactive (errors, timeouts)
- **SHUTDOWN**: Gracefully terminating

---

### Player Agent Implementation Guide

#### Minimal MCP Server Structure

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: int = 1

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    # Route to appropriate handler
    if request.method == "handle_game_invitation":
        return handle_game_invitation(request.params)
    elif request.method == "choose_parity":
        return choose_parity(request.params)
    elif request.method == "notify_match_result":
        return notify_match_result(request.params)
    else:
        return {"error": "Unknown method"}

def handle_game_invitation(params):
    # Implementation
    return {
        "jsonrpc": "2.0",
        "result": {
            "protocol": "league.v2",
            "message_type": "GAME_JOIN_ACK",
            "sender": "player:P01",
            "timestamp": get_utc_timestamp(),
            "conversation_id": params["conversation_id"],
            "auth_token": MY_AUTH_TOKEN,
            "match_id": params["match_id"],
            "player_id": "P01",
            "accept": True
        },
        "id": params.get("id", 1)
    }
```

#### Required Tool #1: handle_game_invitation

**Purpose**: Respond to game invitation from referee

**Input Parameters**:
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_INVITATION",
  "sender": "referee:REF01",
  "timestamp": "2025-01-15T10:15:00Z",
  "conversation_id": "conv-r1m1-001",
  "auth_token": "tok-ref01-abc123",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "match_id": "R1M1",
  "game_type": "even_odd",
  "role_in_match": "PLAYER_A",
  "opponent_id": "P02"
}
```

**Expected Output** (within 5 seconds):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P01",
    "timestamp": "2025-01-15T10:15:01Z",
    "conversation_id": "conv-r1m1-001",
    "auth_token": "tok-p01-xyz789",
    "match_id": "R1M1",
    "player_id": "P01",
    "arrival_timestamp": "2025-01-15T10:15:01Z",
    "accept": true
  },
  "id": 1
}
```

#### Required Tool #2: choose_parity

**Purpose**: Choose "even" or "odd" when prompted by referee

**Input Parameters**:
```json
{
  "protocol": "league.v2",
  "message_type": "CHOOSE_PARITY_CALL",
  "sender": "referee:REF01",
  "timestamp": "2025-01-15T10:15:05Z",
  "conversation_id": "conv-r1m1-001",
  "auth_token": "tok-ref01-abc123",
  "match_id": "R1M1",
  "player_id": "P01",
  "game_type": "even_odd",
  "context": {
    "opponent_id": "P02",
    "round_id": 1,
    "your_standings": {
      "wins": 0,
      "losses": 0,
      "draws": 0
    }
  },
  "deadline": "2025-01-15T10:15:35Z"
}
```

**Expected Output** (within 30 seconds):
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "sender": "player:P01",
    "timestamp": "2025-01-15T10:15:10Z",
    "conversation_id": "conv-r1m1-001",
    "auth_token": "tok-p01-xyz789",
    "match_id": "R1M1",
    "player_id": "P01",
    "parity_choice": "even"
  },
  "id": 1
}
```

**Strategy Options**:
1. **Random**: `choice = random.choice(["even", "odd"])`
2. **History-based**: Analyze opponent's past choices
3. **LLM-guided**: Use LLM to decide based on context

#### Required Tool #3: notify_match_result

**Purpose**: Receive match result and update internal state

**Input Parameters**:
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_OVER",
  "sender": "referee:REF01",
  "timestamp": "2025-01-15T10:15:30Z",
  "conversation_id": "conv-r1m1-001",
  "auth_token": "tok-ref01-abc123",
  "match_id": "R1M1",
  "game_type": "even_odd",
  "game_result": {
    "status": "WIN",
    "winner_player_id": "P01",
    "drawn_number": 8,
    "number_parity": "even",
    "choices": {
      "P01": "even",
      "P02": "odd"
    },
    "reason": "P01 chose even, number was 8 (even)"
  }
}
```

**Expected Output**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "acknowledged"
  },
  "id": 1
}
```

**Internal Actions**:
- Update match history
- Update statistics (wins, losses, draws)
- Store opponent's choice for future strategy
- Log the result

---

### Referee Agent Implementation Guide

#### Core Responsibilities

1. **Register to League Manager**
```python
def register_to_league():
    payload = {
        "jsonrpc": "2.0",
        "method": "register_referee",
        "params": {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_REQUEST",
            "sender": "referee:REF01",
            "timestamp": get_utc_timestamp(),
            "conversation_id": generate_unique_id(),
            "referee_meta": {
                "display_name": "Referee Alpha",
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": "http://localhost:8001/mcp",
                "max_concurrent_matches": 2
            }
        },
        "id": 1
    }
    response = requests.post("http://localhost:8000/mcp", json=payload)
    # Store referee_id and auth_token from response
```

2. **Conduct Match** (6-step flow)

```python
def conduct_match(match_id, player_a_id, player_b_id):
    # Step 1: Send invitations
    invite_player(player_a_id, match_id, "PLAYER_A", player_b_id)
    invite_player(player_b_id, match_id, "PLAYER_B", player_a_id)

    # Step 2: Wait for acknowledgments (5 sec timeout)
    ack_a = wait_for_ack(player_a_id, timeout=5)
    ack_b = wait_for_ack(player_b_id, timeout=5)

    if not (ack_a and ack_b):
        handle_timeout_error()
        return

    # Step 3: Collect choices (30 sec timeout)
    choice_a = call_choose_parity(player_a_id, timeout=30)
    choice_b = call_choose_parity(player_b_id, timeout=30)

    # Step 4: Draw random number
    drawn_number = random.randint(1, 10)
    number_parity = "even" if drawn_number % 2 == 0 else "odd"

    # Step 5: Determine winner
    winner = determine_winner(player_a_id, choice_a, player_b_id, choice_b, number_parity)

    # Step 6: Report results
    notify_players(player_a_id, player_b_id, winner, drawn_number, choices)
    report_to_league_manager(match_id, winner, scores)
```

3. **Winner Logic**
```python
def determine_winner(player_a_id, choice_a, player_b_id, choice_b, number_parity):
    if choice_a == choice_b:
        return {"status": "DRAW"}
    elif choice_a == number_parity:
        return {"status": "WIN", "winner": player_a_id, "loser": player_b_id}
    else:
        return {"status": "WIN", "winner": player_b_id, "loser": player_a_id}
```

---

### League Manager Implementation Guide

#### Core Responsibilities

1. **Player/Referee Registration**
```python
registered_players = {}
registered_referees = {}

def register_player(player_meta):
    player_id = generate_player_id()  # e.g., "P01"
    auth_token = generate_token()

    registered_players[player_id] = {
        "player_id": player_id,
        "display_name": player_meta["display_name"],
        "endpoint": player_meta["contact_endpoint"],
        "auth_token": auth_token,
        "status": "REGISTERED"
    }

    return {
        "status": "ACCEPTED",
        "player_id": player_id,
        "auth_token": auth_token,
        "league_id": CURRENT_LEAGUE_ID
    }
```

2. **Round-Robin Schedule Creation**
```python
def create_round_robin_schedule(players):
    """
    For n players:
    - Total matches = n * (n-1) / 2
    - Distribute matches across rounds
    """
    n = len(players)
    schedule = []

    for i in range(n):
        for j in range(i+1, n):
            match = {
                "match_id": f"R{round_num}M{match_num}",
                "player_A_id": players[i],
                "player_B_id": players[j],
                "referee_endpoint": assign_referee()
            }
            schedule.append(match)

    return schedule
```

**Example Schedule for 4 players**:
```
Round 1: P01 vs P02, P03 vs P04
Round 2: P01 vs P03, P02 vs P04
Round 3: P01 vs P04, P02 vs P03
Total: 6 matches
```

3. **Standings Calculation**
```python
def update_standings(match_result):
    winner = match_result["winner"]
    loser = match_result["loser"]

    if match_result["status"] == "WIN":
        standings[winner]["points"] += 3
        standings[winner]["wins"] += 1
        standings[loser]["losses"] += 1
    elif match_result["status"] == "DRAW":
        standings[winner]["points"] += 1
        standings[loser]["points"] += 1
        standings[winner]["draws"] += 1
        standings[loser]["draws"] += 1

    # Sort by points, then wins
    sorted_standings = sorted(standings.items(),
                             key=lambda x: (x[1]["points"], x[1]["wins"]),
                             reverse=True)

    broadcast_standings_update(sorted_standings)
```

---

## DATA LAYER

### 3-Layer Architecture

```
/SHARED/
├── config/     # Configuration Layer (static, read-only)
├── data/       # Runtime Data Layer (dynamic, read/write)
└── logs/       # Logging Layer (append-only)
```

---

### Layer 1: Configuration (`/config`)

**Purpose**: Static settings loaded at startup

#### `config/system.json` - Global System Settings
```json
{
  "schema_version": "1.0.0",
  "system_id": "league_system_prod",
  "protocol_version": "league.v2",
  "timeouts": {
    "move_timeout_sec": 30,
    "generic_response_timeout_sec": 10,
    "game_join_ack_timeout_sec": 5
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_strategy": "exponential"
  },
  "network": {
    "base_host": "localhost",
    "default_league_manager_port": 8000,
    "default_referee_port_range": [8001, 8002],
    "default_player_port_range": [8101, 8104]
  }
}
```

#### `config/agents/agents_config.json` - All Agents Registry
```json
{
  "schema_version": "1.0.0",
  "league_manager": {
    "agent_id": "league_manager",
    "endpoint": "http://localhost:8000/mcp",
    "version": "1.0.0"
  },
  "referees": [
    {
      "referee_id": "REF01",
      "display_name": "Referee Alpha",
      "endpoint": "http://localhost:8001/mcp",
      "game_types": ["even_odd"],
      "max_concurrent_matches": 2,
      "active": true
    }
  ],
  "players": [
    {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "endpoint": "http://localhost:8101/mcp",
      "game_types": ["even_odd"],
      "active": true
    }
  ]
}
```

#### `config/leagues/league_2025_even_odd.json` - League Configuration
```json
{
  "schema_version": "1.0.0",
  "league_id": "league_2025_even_odd",
  "display_name": "2025 Even/Odd League",
  "game_type": "even_odd",
  "status": "ACTIVE",
  "scoring": {
    "win_points": 3,
    "draw_points": 1,
    "loss_points": 0,
    "technical_loss_points": 0
  },
  "participants": {
    "min_players": 2,
    "max_players": 10000
  }
}
```

#### `config/games/games_registry.json` - Game Types Registry
```json
{
  "schema_version": "1.0.0",
  "games": [
    {
      "game_type": "even_odd",
      "display_name": "Even/Odd Game",
      "rules_module": "games.even_odd",
      "max_round_time_sec": 60,
      "supports_draw": true
    }
  ]
}
```

---

### Layer 2: Runtime Data (`/data`)

**Purpose**: Dynamic data updated during league execution

#### `data/leagues/<league_id>/standings.json` - Current Standings
```json
{
  "schema_version": "1.0.0",
  "league_id": "league_2025_even_odd",
  "version": 12,
  "last_updated": "2025-01-15T10:20:00Z",
  "rounds_completed": 3,
  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "played": 3,
      "wins": 2,
      "draws": 1,
      "losses": 0,
      "points": 7
    }
  ]
}
```

#### `data/leagues/<league_id>/rounds.json` - Round History
```json
{
  "schema_version": "1.0.0",
  "league_id": "league_2025_even_odd",
  "rounds": [
    {
      "round_id": 1,
      "status": "COMPLETED",
      "started_at": "2025-01-15T10:10:00Z",
      "completed_at": "2025-01-15T10:20:00Z",
      "matches": ["R1M1", "R1M2"]
    }
  ]
}
```

#### `data/matches/<league_id>/<match_id>.json` - Match Details
```json
{
  "schema_version": "1.0.0",
  "match_id": "R1M1",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "lifecycle": {
    "state": "FINISHED",
    "created_at": "2025-01-15T10:15:00Z",
    "started_at": "2025-01-15T10:15:02Z",
    "completed_at": "2025-01-15T10:15:30Z"
  },
  "participants": {
    "player_A_id": "P01",
    "player_B_id": "P02",
    "referee_id": "REF01"
  },
  "transcript": [
    {
      "timestamp": "2025-01-15T10:15:00Z",
      "message_type": "GAME_INVITATION",
      "from": "referee:REF01",
      "to": "player:P01"
    }
  ],
  "result": {
    "status": "WIN",
    "winner_player_id": "P01",
    "score": {
      "P01": 3,
      "P02": 0
    },
    "details": {
      "drawn_number": 8,
      "number_parity": "even",
      "choices": {
        "P01": "even",
        "P02": "odd"
      }
    }
  }
}
```

#### `data/players/<player_id>/history.json` - Player Match History
```json
{
  "schema_version": "1.0.0",
  "player_id": "P01",
  "stats": {
    "total_matches": 20,
    "wins": 12,
    "losses": 5,
    "draws": 3
  },
  "matches": [
    {
      "match_id": "R1M1",
      "league_id": "league_2025_even_odd",
      "timestamp": "2025-01-15T10:15:30Z",
      "opponent_id": "P02",
      "result": "WIN",
      "my_choice": "even",
      "opponent_choice": "odd",
      "drawn_number": 8
    }
  ]
}
```

---

### Layer 3: Logs (`/logs`)

**Purpose**: Audit trail for debugging and monitoring

**Format**: JSON Lines (one JSON object per line)

#### `logs/league/<league_id>/league.log.jsonl` - Central League Log
```jsonl
{"timestamp":"2025-01-15T10:00:00Z","component":"league_manager","event_type":"LEAGUE_STARTED","level":"INFO","league_id":"league_2025_even_odd"}
{"timestamp":"2025-01-15T10:00:05Z","component":"league_manager","event_type":"REFEREE_REGISTERED","level":"INFO","referee_id":"REF01"}
{"timestamp":"2025-01-15T10:10:00Z","component":"league_manager","event_type":"ROUND_ANNOUNCEMENT_SENT","level":"INFO","round_id":1,"matches_count":2}
```

#### `logs/agents/<agent_id>.log.jsonl` - Per-Agent Log
```jsonl
{"timestamp":"2025-01-15T10:15:00Z","component":"player:P01","event_type":"GAME_INVITATION_RECEIVED","level":"DEBUG","match_id":"R1M1"}
{"timestamp":"2025-01-15T10:15:01Z","component":"player:P01","event_type":"MESSAGE_SENT","level":"DEBUG","message_type":"GAME_JOIN_ACK","recipient":"referee:REF01"}
```

---

## EXECUTION FLOW

### Complete League Flow

```
START
  │
  ├─ Step 1: Launch League Manager (port 8000)
  │    └─ Load configuration from /config
  │
  ├─ Step 2: Launch Referees (ports 8001-8002)
  │    ├─ REF01 registers to League Manager
  │    └─ REF02 registers to League Manager
  │
  ├─ Step 3: Launch Players (ports 8101-8104)
  │    ├─ P01 registers to League Manager
  │    ├─ P02 registers to League Manager
  │    ├─ P03 registers to League Manager
  │    └─ P04 registers to League Manager
  │
  ├─ Step 4: League Manager creates round-robin schedule
  │    └─ Generates 6 matches for 4 players
  │
  ├─ Step 5: For each round (1-3):
  │    ├─ 5.1: League Manager broadcasts ROUND_ANNOUNCEMENT
  │    ├─ 5.2: Referees conduct matches (in parallel)
  │    │    ├─ 5.2.1: Send GAME_INVITATION to players
  │    │    ├─ 5.2.2: Collect GAME_JOIN_ACK (5 sec timeout)
  │    │    ├─ 5.2.3: Call choose_parity on both players (30 sec timeout)
  │    │    ├─ 5.2.4: Draw random number (1-10)
  │    │    ├─ 5.2.5: Determine winner
  │    │    ├─ 5.2.6: Send GAME_OVER to players
  │    │    └─ 5.2.7: Send MATCH_RESULT_REPORT to League Manager
  │    ├─ 5.3: League Manager updates standings
  │    ├─ 5.4: League Manager broadcasts LEAGUE_STANDINGS_UPDATE
  │    └─ 5.5: League Manager sends ROUND_COMPLETED
  │
  └─ Step 6: League completion
       ├─ Calculate final standings
       ├─ Identify champion
       └─ Broadcast LEAGUE_COMPLETED with champion
END
```

---

### Detailed Match Flow (Example: R1M1)

```
MATCH R1M1: Player P01 vs Player P02, Referee REF01

Timeline:
10:15:00 - Referee sends GAME_INVITATION to P01
10:15:00 - Referee sends GAME_INVITATION to P02
10:15:01 - P01 sends GAME_JOIN_ACK
10:15:02 - P02 sends GAME_JOIN_ACK
10:15:05 - Referee calls choose_parity on P01
10:15:05 - Referee calls choose_parity on P02
10:15:10 - P01 responds "even"
10:15:12 - P02 responds "odd"
10:15:13 - Referee draws number: 8 (even)
10:15:13 - Referee determines: P01 wins (chose "even", number is even)
10:15:14 - Referee sends GAME_OVER to P01 (status: WIN)
10:15:14 - Referee sends GAME_OVER to P02 (status: LOSS)
10:15:15 - Referee sends MATCH_RESULT_REPORT to League Manager
10:15:16 - League Manager updates standings: P01 +3 points
10:15:17 - League Manager broadcasts LEAGUE_STANDINGS_UPDATE

Result: P01 wins, P01 gets 3 points, P02 gets 0 points
```

---

### Error Handling Scenarios

#### Scenario 1: Player Timeout on GAME_JOIN_ACK
```
1. Referee sends GAME_INVITATION to P01, P02
2. P01 responds within 5 seconds ✓
3. P02 DOES NOT respond within 5 seconds ✗
4. Referee logs TIMEOUT_ERROR (E001)
5. Referee awards technical WIN to P01
6. Referee sends GAME_ERROR to P02 (error_code: E001)
7. Referee reports match result to League Manager
8. League Manager updates standings: P01 +3 points
```

#### Scenario 2: Player Timeout on CHOOSE_PARITY
```
1. Referee collects GAME_JOIN_ACK from both players ✓
2. Referee calls choose_parity on P01, P02
3. P01 responds "even" within 30 seconds ✓
4. P02 DOES NOT respond within 30 seconds ✗
5. Referee implements retry policy:
   - Retry 1 after 2 seconds ✗
   - Retry 2 after 4 seconds ✗
   - Retry 3 after 8 seconds ✗
6. Referee logs TIMEOUT_ERROR (E001) after 3 failed retries
7. Referee awards technical WIN to P01
8. Continue as in Scenario 1
```

#### Scenario 3: Authentication Failure
```
1. Player sends message with invalid auth_token
2. Receiver validates token → FAILS
3. Receiver returns LEAGUE_ERROR (error_code: E012, AUTH_TOKEN_INVALID)
4. Player logs error and attempts to re-register
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Setup & Configuration

- [ ] Create project directory structure:
  ```
  L07/
  ├── SHARED/
  │   ├── config/
  │   ├── data/
  │   ├── logs/
  │   └── league_sdk/
  ├── agents/
  │   ├── league_manager/
  │   ├── referee_REF01/
  │   └── player_P01/
  └── doc/
  ```

- [ ] Create configuration files:
  - [ ] `SHARED/config/system.json`
  - [ ] `SHARED/config/agents/agents_config.json`
  - [ ] `SHARED/config/leagues/league_2025_even_odd.json`
  - [ ] `SHARED/config/games/games_registry.json`
  - [ ] `SHARED/config/defaults/referee.json`
  - [ ] `SHARED/config/defaults/player.json`

- [ ] Set up Python SDK (optional but recommended):
  - [ ] `SHARED/league_sdk/__init__.py`
  - [ ] `SHARED/league_sdk/config_models.py`
  - [ ] `SHARED/league_sdk/config_loader.py`
  - [ ] `SHARED/league_sdk/repositories.py`
  - [ ] `SHARED/league_sdk/logger.py`

---

### Phase 2: Player Agent Implementation (MANDATORY)

- [ ] **Basic MCP Server**:
  - [ ] HTTP server listening on specified port
  - [ ] POST endpoint at `/mcp`
  - [ ] JSON-RPC 2.0 request parsing
  - [ ] Method routing (handle_game_invitation, choose_parity, notify_match_result)

- [ ] **Tool 1: handle_game_invitation**:
  - [ ] Parse GAME_INVITATION message
  - [ ] Validate message structure
  - [ ] Return GAME_JOIN_ACK within 5 seconds
  - [ ] Include all mandatory envelope fields

- [ ] **Tool 2: choose_parity**:
  - [ ] Parse CHOOSE_PARITY_CALL message
  - [ ] Implement strategy (random/history-based/LLM)
  - [ ] Return choice ("even" or "odd") within 30 seconds
  - [ ] Include all mandatory envelope fields

- [ ] **Tool 3: notify_match_result**:
  - [ ] Parse GAME_OVER message
  - [ ] Update internal match history
  - [ ] Update statistics (wins/losses/draws)
  - [ ] Return acknowledgment

- [ ] **Registration Logic**:
  - [ ] Send LEAGUE_REGISTER_REQUEST to League Manager at startup
  - [ ] Store received player_id and auth_token
  - [ ] Use auth_token in all subsequent messages

- [ ] **Error Handling**:
  - [ ] Handle network errors gracefully
  - [ ] Implement retry logic for transient failures
  - [ ] Log all errors to agent log file
  - [ ] Respond to GAME_ERROR messages

- [ ] **Logging**:
  - [ ] Structured JSON logging
  - [ ] Log to `SHARED/logs/agents/<player_id>.log.jsonl`
  - [ ] Include timestamp, component, event_type, level

---

### Phase 3: Referee Agent Implementation (OPTIONAL)

- [ ] **Basic MCP Server**:
  - [ ] HTTP server listening on specified port
  - [ ] POST endpoint at `/mcp`
  - [ ] MCP tools for match management

- [ ] **Registration**:
  - [ ] Send REFEREE_REGISTER_REQUEST to League Manager at startup
  - [ ] Store referee_id and auth_token

- [ ] **Match Conductor**:
  - [ ] Receive match assignments from League Manager
  - [ ] Send GAME_INVITATION to players
  - [ ] Wait for GAME_JOIN_ACK (5 sec timeout per player)
  - [ ] Call choose_parity on both players (30 sec timeout each)
  - [ ] Draw random number (1-10)
  - [ ] Determine winner based on parity logic
  - [ ] Send GAME_OVER to both players
  - [ ] Send MATCH_RESULT_REPORT to League Manager

- [ ] **Even/Odd Game Logic**:
  - [ ] Implement parity checking
  - [ ] Handle draw scenarios (both choose same)
  - [ ] Calculate scores (Win=3, Draw=1, Loss=0)

- [ ] **Timeout Handling**:
  - [ ] Implement 5-second timeout for GAME_JOIN_ACK
  - [ ] Implement 30-second timeout for CHOOSE_PARITY_RESPONSE
  - [ ] Award technical loss for timeouts
  - [ ] Send GAME_ERROR to offending player

- [ ] **State Management**:
  - [ ] Track match state (WAITING_FOR_PLAYERS, COLLECTING_CHOICES, etc.)
  - [ ] Maintain conversation context
  - [ ] Log match transcript

---

### Phase 4: League Manager Implementation (OPTIONAL)

- [ ] **Basic MCP Server**:
  - [ ] HTTP server on port 8000
  - [ ] POST endpoint at `/mcp`
  - [ ] Tools for registration and reporting

- [ ] **Registration System**:
  - [ ] Accept REFEREE_REGISTER_REQUEST
  - [ ] Accept LEAGUE_REGISTER_REQUEST
  - [ ] Generate unique IDs (REF01, P01, etc.)
  - [ ] Generate auth tokens
  - [ ] Store agent metadata and endpoints

- [ ] **Schedule Creator**:
  - [ ] Implement round-robin algorithm
  - [ ] For n players, generate n*(n-1)/2 matches
  - [ ] Assign referees to matches
  - [ ] Distribute matches across rounds

- [ ] **Round Management**:
  - [ ] Broadcast ROUND_ANNOUNCEMENT to all players
  - [ ] Track match completion
  - [ ] Send ROUND_COMPLETED after all matches finish

- [ ] **Standings Calculator**:
  - [ ] Receive MATCH_RESULT_REPORT from referees
  - [ ] Update standings table:
    - Win: +3 points, +1 win
    - Draw: +1 point, +1 draw
    - Loss: +0 points, +1 loss
  - [ ] Sort by points (primary), wins (tiebreaker)
  - [ ] Broadcast LEAGUE_STANDINGS_UPDATE after each match

- [ ] **League Completion**:
  - [ ] Detect when all rounds complete
  - [ ] Identify champion (highest points)
  - [ ] Broadcast LEAGUE_COMPLETED

- [ ] **Query Handling**:
  - [ ] Respond to LEAGUE_QUERY requests
  - [ ] Return current standings
  - [ ] Return league status

---

### Phase 5: Testing & Validation

- [ ] **Local Testing**:
  - [ ] Run league with 4 players locally
  - [ ] Verify all message types are handled
  - [ ] Check standings calculations
  - [ ] Validate JSON structure against protocol

- [ ] **Timeout Testing**:
  - [ ] Test player timeout on GAME_JOIN_ACK
  - [ ] Test player timeout on CHOOSE_PARITY_RESPONSE
  - [ ] Verify technical loss assignment

- [ ] **Error Testing**:
  - [ ] Test invalid message formats
  - [ ] Test authentication failures
  - [ ] Test network disconnections
  - [ ] Verify retry logic

- [ ] **Protocol Compliance**:
  - [ ] All messages include mandatory envelope fields
  - [ ] All timestamps in UTC/GMT with 'Z' suffix
  - [ ] auth_token included in all messages
  - [ ] conversation_id maintained throughout conversations

- [ ] **Data Validation**:
  - [ ] Verify standings.json updates correctly
  - [ ] Check match history files
  - [ ] Validate log file formats

---

### Phase 6: Advanced Features (OPTIONAL)

- [ ] **Advanced Player Strategies**:
  - [ ] History-based strategy (analyze opponent patterns)
  - [ ] LLM-guided strategy (use LLM to make decisions)
  - [ ] Adaptive strategy (change based on standings)

- [ ] **Resilience Patterns**:
  - [ ] Circuit Breaker implementation
  - [ ] Health checks for agents
  - [ ] Graceful degradation

- [ ] **Monitoring & Analytics**:
  - [ ] Dashboard for live standings
  - [ ] Match statistics visualization
  - [ ] Agent performance metrics

- [ ] **Multi-Game Support**:
  - [ ] Implement additional game types (Tic-Tac-Toe, etc.)
  - [ ] Game registry system
  - [ ] Modular game rules

---

## QUICK START COMMANDS

### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install fastapi uvicorn pydantic requests

# Install SDK (if using)
cd SHARED
pip install -e league_sdk/
```

### Launch League System
```bash
# Terminal 1: League Manager
cd agents/league_manager
python main.py --league-id league_2025_even_odd

# Terminal 2: Referee
cd agents/referee_REF01
python main.py --referee-id REF01 --league-id league_2025_even_odd

# Terminal 3-6: Players
cd agents/player_P01
python main.py --player-id P01 --league-id league_2025_even_odd
# Repeat for P02, P03, P04
```

---

## DEBUGGING TIPS

1. **Check Logs**: Always start with log files when debugging
   ```bash
   tail -f SHARED/logs/league/league_2025_even_odd/league.log.jsonl
   tail -f SHARED/logs/agents/P01.log.jsonl
   ```

2. **Validate JSON**: Use online validators or jq to check message format
   ```bash
   cat message.json | jq .
   ```

3. **Test Endpoints**: Use curl to manually test MCP endpoints
   ```bash
   curl -X POST http://localhost:8101/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"choose_parity","params":{...},"id":1}'
   ```

4. **Monitor Network**: Use netstat to check port availability
   ```bash
   netstat -an | grep 810
   ```

5. **Validate Timestamps**: Ensure all timestamps end with 'Z' (UTC)
   ```python
   from datetime import datetime
   timestamp = datetime.utcnow().isoformat() + "Z"
   ```

---

## COMMON PITFALLS TO AVOID

1. ❌ **Forgetting auth_token**: Every message after registration MUST include auth_token
2. ❌ **Wrong timezone**: MUST use UTC/GMT, timestamps MUST end with 'Z'
3. ❌ **Timeout violations**: Respond to GAME_JOIN_ACK in 5 sec, CHOOSE_PARITY in 30 sec
4. ❌ **Missing envelope fields**: protocol, message_type, sender, timestamp, conversation_id, auth_token
5. ❌ **Incorrect sender format**: Must be "agent_type:agent_id" (e.g., "player:P01")
6. ❌ **Not implementing retry logic**: Transient failures should retry up to 3 times
7. ❌ **Ignoring error codes**: Check for LEAGUE_ERROR and GAME_ERROR messages
8. ❌ **Hardcoding ports**: Use configuration files for flexibility
9. ❌ **Not logging**: Structured JSON logs are essential for debugging
10. ❌ **Breaking on errors**: Agents should handle errors gracefully and continue

---

## SUCCESS CRITERIA

Your implementation is successful when:

✅ Player agent responds to all 3 required tools
✅ Player registers successfully with League Manager
✅ Player completes full 4-player local league
✅ All message types handled correctly
✅ JSON structure complies with league.v2 protocol
✅ Timeouts respected (5 sec, 30 sec)
✅ Standings calculated correctly (Win=3, Draw=1, Loss=0)
✅ Error handling works (timeouts, invalid messages)
✅ Logs written in JSON Lines format
✅ Agent runs without crashes throughout league

---

## RESOURCES & REFERENCES

### Protocol Documentation
- Main document: HW7_Instructions_section1_5.pdf (Sections 1-5)
- Homework requirements: HW7_Instructions_section6_11.pdf (Sections 6-11)

### Key Concepts
- **MCP Protocol**: Model Context Protocol by Anthropic
- **JSON-RPC 2.0**: Remote procedure call protocol
- **Round-Robin**: Tournament where each player plays everyone else once
- **Agent Lifecycle**: State management for autonomous agents

### Example Files Location
All example files available in:
```
L07/SHARED/
```

---

## FINAL NOTES

This is a **production-ready multi-agent orchestration system** that demonstrates:
- Real-world distributed system design
- Protocol-based agent communication
- Resilience patterns and error handling
- Scalable architecture (designed for thousands of agents)

Focus on:
1. **Protocol compliance**: Follow league.v2 exactly
2. **Timeouts**: Respect all timing constraints
3. **Error handling**: Graceful degradation, retry logic
4. **Testing**: Validate with 4-player local league
5. **Logging**: Structured logs for debugging

Good luck building your Even/Odd League system! 🎲
