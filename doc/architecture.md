# Architecture Documentation (M8.2)

This document describes the system architecture, data flow, and design
decisions for the Even/Odd League system. It is aligned to the current
implementation in `agents/` and `SHARED/league_sdk/`.

---

## 1) C4-1 Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Even/Odd League                            │
│  Users/Operators                                                     │
│  - Start/stop agents via scripts                                     │
│  - Trigger league and query state                                    │
└─────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Multi-Agent System                            │
│  League Manager (LM01)                                               │
│  Referees (REF01, REF02)                                             │
│  Players (P01–P04)                                                   │
│  Shared SDK (protocol/config/logging/retry/repos/cleanup)            │
└─────────────────────────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         File System Layer                            │
│  SHARED/config/  SHARED/data/  SHARED/logs/  SHARED/archive/          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2) C4-2 Container Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            League Manager                            │
│  FastAPI server + JSON-RPC (/mcp)                                    │
│  - Registration, scheduling, standings, orchestration               │
└─────────────────────────────────────────────────────────────────────┘
                 ▲                     ▲
                 │ JSON-RPC over HTTP  │ JSON-RPC over HTTP
                 ▼                     ▼
┌───────────────────────────┐   ┌────────────────────────────┐
│         Referees          │   │          Players           │
│  FastAPI server + client  │   │  FastAPI server + client    │
│  Conducts matches         │   │  Responds to invitations    │
└───────────────────────────┘   └────────────────────────────┘
                 ▲                     ▲
                 └─────────────┬───────┘
                               ▼
                    Shared SDK (league_sdk)
```

---

## 3) C4-3 Component Views

### 3.1 League Manager

- MCP Server (`/mcp`)
  - Handlers: `REFEREE_REGISTER_REQUEST`, `LEAGUE_REGISTER_REQUEST`,
    `MATCH_RESULT_REPORT`, `LEAGUE_QUERY`, `get_standings`,
    `get_league_status`, `start_league`
- Scheduler (round-robin)
- Standings processor (sequential queue)
- Cleanup scheduler (async)

### 3.2 Referee

- MCP Server (`/mcp`)
  - Handlers: `START_MATCH`, `GAME_JOIN_ACK`, `CHOOSE_PARITY_RESPONSE`,
    `get_match_state`, `get_registration_status`, `manual_register`
- Match conductor (timeouts, parity, winner)
- Game logic (even/odd rules)

### 3.3 Player

- MCP Server (`/mcp`)
  - Handlers: `GAME_INVITATION`, `CHOOSE_PARITY_CALL`, `GAME_OVER`,
    `MATCH_RESULT_REPORT`, `get_player_state`, `get_registration_status`,
    `manual_register`
- Strategy (random/history)
- Player history repository

### 3.4 Shared SDK

- `protocol.py`: 18 message types, error codes
- `config_loader.py`: config parsing and validation
- `retry.py`: async httpx retry + circuit breaker
- `repositories.py`: standings, rounds, matches, player history
- `logger.py`: JSONL structured logs
- `cleanup.py`: retention and archive
- `queue_processor.py`: sequential async processing
- `method_aliases.py`: PDF tool aliases

---

## 4) Sequence Diagrams

### 4.1 Registration Flow (Referee + Player)

```
Referee            League Manager             Player
  | REFEREE_REGISTER_REQUEST  |                |
  |-------------------------->|                |
  | REFEREE_REGISTER_RESPONSE |                |
  |<--------------------------|                |
  |                            | LEAGUE_REGISTER_REQUEST
  |                            |<---------------|
  |                            | LEAGUE_REGISTER_RESPONSE
  |                            |--------------->|
```

### 4.2 Match Flow (Single Match)

```
League Manager       Referee                Player A         Player B
      | START_MATCH    |                      |                |
      |--------------->|                      |                |
      |                | GAME_INVITATION      |                |
      |                |--------------------->|                |
      |                | GAME_INVITATION      |                |
      |                |------------------------------------->|
      |                | GAME_JOIN_ACK        |                |
      |                |<---------------------|                |
      |                | GAME_JOIN_ACK        |                |
      |                |<-------------------------------------|
      |                | CHOOSE_PARITY_CALL   |                |
      |                |--------------------->|                |
      |                | CHOOSE_PARITY_CALL   |                |
      |                |------------------------------------->|
      |                | CHOOSE_PARITY_RESPONSE               |
      |                |<---------------------|                |
      |                | CHOOSE_PARITY_RESPONSE               |
      |                |<-------------------------------------|
      |                | GAME_OVER            |                |
      |                |--------------------->|                |
      |                | GAME_OVER            |                |
      |                |------------------------------------->|
      | MATCH_RESULT_REPORT                   |                |
      |<--------------|                       |                |
```

---

## 5) State Machines

### 5.1 Player Lifecycle

```
INIT -> REGISTERING -> REGISTERED -> ACTIVE -> SHUTDOWN
            ^              |
            |              v
        FAILED <-----------+
```

### 5.2 Referee Lifecycle

```
INIT -> REGISTERING -> REGISTERED -> ACTIVE -> SHUTDOWN
            ^              |
            |              v
        FAILED <-----------+
```

### 5.3 League Manager

```
INIT -> ACTIVE -> COMPLETED
   ^        |
   +--------+
```

---

## 6) Data Flow Diagram

```
SHARED/config/ -> Agents -> SHARED/data/ -> SHARED/logs/ -> SHARED/archive/
     (load)       (runtime)    (persist)     (append)        (cleanup)
```

---

## 7) API and Data Contracts

- JSON-RPC methods and message schemas are defined in [SHARED/league_sdk/protocol.py](../SHARED/league_sdk/protocol.py).
- Persisted JSON schemas are defined in [SHARED/league_sdk/repositories.py](../SHARED/league_sdk/repositories.py):
  - `StandingsRepository` -> [SHARED/data/leagues/<league_id>/standings.json](../SHARED/data/leagues/)
  - `RoundsRepository` -> [SHARED/data/leagues/<league_id>/rounds.json](../SHARED/data/leagues/)
  - `MatchRepository` -> [SHARED/data/matches/<match_id>.json](../SHARED/data/matches/)
  - `PlayerHistoryRepository` -> [SHARED/data/players/<player_id>/history.json](../SHARED/data/players/)

---

## 8) Concurrency Model

- **HTTP I/O:** async via `httpx.AsyncClient`
- **Broadcasts:** `asyncio.gather(..., return_exceptions=True)`
- **Standings Processing:** `SequentialQueueProcessor` (single consumer)
- **Cleanup:** async background task scheduled daily

Thread safety is described in [architecture/thread_safety.md](architecture/thread_safety.md).

---

## 9) ADR Index

See [architecture/adr/](architecture/adr/) for architecture decisions:

- [ADR-0001](architecture/adr/0001-use-fastapi-jsonrpc.md): Use FastAPI + JSON-RPC over HTTP
- [ADR-0002](architecture/adr/0002-async-httpx-client.md): Async httpx for inter-agent calls
- [ADR-0003](architecture/adr/0003-file-based-storage.md): File-based JSON storage with repositories
- [ADR-0004](architecture/adr/0004-structured-jsonl-logging.md): Structured JSONL logging
- [ADR-0005](architecture/adr/0005-retry-and-circuit-breaker.md): Retry + circuit breaker
- [ADR-0006](architecture/adr/0006-method-alias-layer.md): Method alias compatibility layer
- [ADR-0007](architecture/adr/0007-cleanup-scheduler.md): Scheduled cleanup and retention policy
- [ADR-0008](architecture/adr/0008-separate-referee-agents.md): Separate referee agents for match execution
- [ADR-0009](architecture/adr/0009-shared-sdk-structure.md): Shared SDK in SHARED/ directory
- [ADR-0010](architecture/adr/0010-round-robin-scheduling.md): Round-robin scheduling
- [ADR-0011](architecture/adr/0011-timeout-enforcement-referee.md): Timeout enforcement at referee level
- [ADR-0012](architecture/adr/0012-iso-8601-utc-timestamps.md): ISO 8601 UTC timestamps with Z suffix
