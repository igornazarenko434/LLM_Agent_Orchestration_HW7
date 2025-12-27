# API Reference (M6.4)

This document lists the MCP tools and message types exposed by each agent.
All calls use JSON-RPC 2.0 over HTTP at each agent's `/mcp` endpoint.

Protocol: `league.v2`
Transport: HTTP POST JSON-RPC 2.0
Auth: token-based when `security.require_auth=true` (see `SHARED/config/system.json`)

---

## 1) JSON-RPC Envelope

All requests follow this envelope:

```json
{
  "jsonrpc": "2.0",
  "method": "LEAGUE_REGISTER_REQUEST",
  "params": {
    "protocol": "league.v2",
    "sender": "player:P01",
    "timestamp": "2025-01-15T12:00:00Z",
    "conversation_id": "conv-001",
    "auth_token": "token-if-required"
  },
  "id": 1
}
```

Responses are JSON-RPC success or error:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "message_type": "LEAGUE_REGISTER_RESPONSE",
    "conversation_id": "conv-001",
    "status": "ACCEPTED"
  },
  "id": 1
}
```

Error response example:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Missing sender",
    "data": {
      "error_code": "E002",
      "payload": { "method": "get_standings", "params": {} },
      "jsonrpc_code": -32602
    }
  },
  "id": 1
}
```

---

## 2) PDF Tool Name Compatibility

The system accepts PDF-style method names and maps them to message types via
`SHARED/league_sdk/method_aliases.py`.

| PDF Tool Name | Internal Message Type |
|--------------|-----------------------|
| `register_referee` | `REFEREE_REGISTER_REQUEST` |
| `register_player` | `LEAGUE_REGISTER_REQUEST` |
| `report_match_result` | `MATCH_RESULT_REPORT` |
| `handle_game_invitation` | `GAME_INVITATION` |
| `choose_parity` | `CHOOSE_PARITY_CALL` |
| `notify_match_result` | `GAME_OVER` |
| `league_query` | `LEAGUE_QUERY` |

All examples below show the PDF name and message type where relevant.

---

## 3) League Manager (LM01)

### 3.1 register_referee / REFEREE_REGISTER_REQUEST

**Description:** Referee registration.
**Sender:** Referee → League Manager

**Request params:**
- `protocol`, `sender`, `timestamp`, `conversation_id`
- `referee_meta` (display_name, version, game_types, contact_endpoint, max_concurrent_matches)

**Response:**
`REFEREE_REGISTER_RESPONSE` with `status`, `referee_id`, `auth_token`, `league_id`.

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "register_referee",
  "params": {
    "protocol": "league.v2",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T12:00:00Z",
    "conversation_id": "conv-ref-reg-1",
    "referee_meta": {
      "display_name": "Referee 01",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8001/mcp",
      "max_concurrent_matches": 10
    }
  },
  "id": 1
}
```

**Example response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "message_type": "REFEREE_REGISTER_RESPONSE",
    "sender": "league_manager:LM01",
    "timestamp": "2025-01-15T12:00:01Z",
    "conversation_id": "conv-ref-reg-1",
    "status": "ACCEPTED",
    "referee_id": "REF01",
    "auth_token": "generated-token",
    "league_id": "league_2025_even_odd"
  },
  "id": 1
}
```

### 3.2 register_player / LEAGUE_REGISTER_REQUEST

**Description:** Player registration.
**Sender:** Player → League Manager

**Request params:**
- `protocol`, `sender`, `timestamp`, `conversation_id`
- `player_meta` (display_name, version, game_types, contact_endpoint)

**Response:**
`LEAGUE_REGISTER_RESPONSE` with `status`, `player_id`, `auth_token`, `league_id`.

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "register_player",
  "params": {
    "protocol": "league.v2",
    "sender": "player:P01",
    "timestamp": "2025-01-15T12:00:00Z",
    "conversation_id": "conv-player-reg-1",
    "player_meta": {
      "display_name": "Player 01",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8101/mcp"
    }
  },
  "id": 1
}
```

### 3.3 report_match_result / MATCH_RESULT_REPORT

**Description:** Referee reports match result.
**Sender:** Referee → League Manager

**Request params:**
- `protocol`, `sender`, `timestamp`, `conversation_id`, `auth_token`
- `league_id`, `round_id`, `match_id`, `game_type`
- `result` object (winner, score, match_status, player_a_status, player_b_status)

**Response:**
`MATCH_RESULT_REPORT_ACK` with `status=ACCEPTED`.

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "report_match_result",
  "params": {
    "protocol": "league.v2",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T12:05:00Z",
    "conversation_id": "conv-r1m1",
    "auth_token": "ref-token",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "result": {
      "winner": "P01",
      "score": { "P01": 3, "P02": 0 },
      "match_status": "COMPLETED",
      "player_a_status": "WIN",
      "player_b_status": "LOSS"
    }
  },
  "id": 1
}
```

### 3.4 get_standings (debug tool)

**Description:** Returns standings from `StandingsRepository`.
**Sender:** Any registered agent (auth required unless `allow_start_league_without_auth=true`).

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_standings",
  "params": {
    "protocol": "league.v2",
    "sender": "player:P01",
    "auth_token": "player-token",
    "conversation_id": "conv-standings-1"
  },
  "id": 1
}
```

**Additional LM tools (implemented):**
- `start_league`
- `league_query` (alias for `LEAGUE_QUERY`)
- `get_league_status`

---

## 4) Referee Agent

### 4.1 start_match / START_MATCH

**Description:** LM assigns a match to a referee.
**Sender:** League Manager → Referee

**Request params:**
- `match_id`, `round_id`, `player_a_id`, `player_b_id`, `conversation_id`

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "START_MATCH",
  "params": {
    "protocol": "league.v2",
    "sender": "league_manager:LM01",
    "timestamp": "2025-01-15T12:10:00Z",
    "conversation_id": "conv-r1m1",
    "match_id": "R1M1",
    "round_id": 1,
    "player_a_id": "P01",
    "player_b_id": "P02"
  },
  "id": 1
}
```

### 4.2 collect_choices (implemented as CHOOSE_PARITY_CALL/CHOOSE_PARITY_RESPONSE)

**Description:** Referee requests parity choice from players.
**Flow:** Referee → Player `CHOOSE_PARITY_CALL`, Player → Referee `CHOOSE_PARITY_RESPONSE`.

**Example call (referee → player):**
```json
{
  "jsonrpc": "2.0",
  "method": "CHOOSE_PARITY_CALL",
  "params": {
    "protocol": "league.v2",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T12:10:10Z",
    "conversation_id": "conv-r1m1",
    "auth_token": "ref-token",
    "match_id": "R1M1",
    "player_id": "P01",
    "game_type": "even_odd",
    "context": {
      "opponent_id": "P02",
      "round_id": 1
    },
    "deadline": "2025-01-15T12:10:40Z"
  },
  "id": 1
}
```

**Example response (player → referee):**
```json
{
  "jsonrpc": "2.0",
  "method": "CHOOSE_PARITY_RESPONSE",
  "params": {
    "protocol": "league.v2",
    "sender": "player:P01",
    "timestamp": "2025-01-15T12:10:12Z",
    "conversation_id": "conv-r1m1",
    "auth_token": "player-token",
    "match_id": "R1M1",
    "player_id": "P01",
    "parity_choice": "even"
  },
  "id": 1
}
```

**Additional Referee tools (implemented):**
- `get_match_state`
- `get_registration_status`
- `manual_register`

---

## 5) Player Agent

### 5.1 handle_game_invitation / GAME_INVITATION

**Description:** Referee invites player to a match.
**Sender:** Referee → Player

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "handle_game_invitation",
  "params": {
    "protocol": "league.v2",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T12:10:00Z",
    "conversation_id": "conv-r1m1",
    "auth_token": "ref-token",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "role_in_match": "PLAYER_A",
    "opponent_id": "P02"
  },
  "id": 1
}
```

**Response:** `GAME_JOIN_ACK`

### 5.2 choose_parity / CHOOSE_PARITY_CALL

**Description:** Player receives parity request and responds with choice.
**Sender:** Referee → Player → Referee

**Response:** `CHOOSE_PARITY_RESPONSE`

### 5.3 notify_match_result / GAME_OVER

**Description:** Referee informs player of result.
**Sender:** Referee → Player

**Example request:**
```json
{
  "jsonrpc": "2.0",
  "method": "notify_match_result",
  "params": {
    "protocol": "league.v2",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T12:10:30Z",
    "conversation_id": "conv-r1m1",
    "auth_token": "ref-token",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "game_result": {
      "status": "WIN",
      "winner_player_id": "P01",
      "drawn_number": 6,
      "number_parity": "even",
      "player_choices": { "P01": "even", "P02": "odd" },
      "opponent_id": "P02",
      "points_awarded": 3
    }
  },
  "id": 1
}
```

**Additional Player tools (implemented):**
- `get_player_state`
- `get_registration_status`
- `manual_register`

---

## 6) Error Responses

All agents return JSON-RPC errors with protocol error codes (E001–E018) in
`error.data.error_code`. Common errors:

- `E002` Invalid message format (missing sender/params)
- `E004` Agent not registered
- `E011` Protocol version mismatch
- `E012` Auth token invalid
- `E018` Invalid endpoint / method not found

See [error_codes_reference.md](error_codes_reference.md) for the full list.
