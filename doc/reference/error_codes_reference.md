# Error Codes Reference

**Version:** 2.0.0
**Date:** 2025-12-27
**Protocol:** league.v2
**Source of Truth:** `SHARED/league_sdk/protocol.py` + `SHARED/league_sdk/retry.py`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Reference Table](#2-quick-reference-table)
3. [Exit Code Mapping](#3-exit-code-mapping)
4. [Detailed Error Codes](#4-detailed-error-codes)
5. [Retry and Circuit Breaker](#5-retry-and-circuit-breaker)
6. [Troubleshooting Guide](#6-troubleshooting-guide)
7. [Error Response Formats](#7-error-response-formats)
8. [Logging Best Practices](#8-logging-best-practices)

---

## 1. Overview

This document is the **authoritative reference** for all error codes (E001-E018) in the Even/Odd League multi-agent system. All agents, scripts, and documentation must align with the definitions in this file.

### Key Principles

- **18 Standardized Error Codes** (E001-E018) defined in `SHARED/league_sdk/protocol.py`
- **7 Retryable Errors** with exponential backoff: E001, E005, E006, E009, E014, E015, E016
- **Circuit Breaker Pattern** for failing services (E016, E018)
- **Structured Logging** with correlation IDs and error context

### Retryability Rules (from code)

**Retryable errors** (defined in `SHARED/league_sdk/retry.py`):
- E001 (TIMEOUT_ERROR) - Added per user requirements
- E005 (INVALID_GAME_STATE)
- E006 (PLAYER_NOT_AVAILABLE)
- E009 (ROUND_NOT_ACTIVE)
- E014 (RATE_LIMIT_EXCEEDED)
- E015 (INTERNAL_SERVER_ERROR)
- E016 (SERVICE_UNAVAILABLE)

**Non-retryable errors**: All others (E002, E003, E004, E007, E008, E010, E011, E012, E013, E017, E018)

---

## 2. Quick Reference Table

| Code | Name | Severity | Retryable | Category | CLI Exit Code |
|------|------|----------|-----------|----------|---------------|
| **E001** | TIMEOUT_ERROR | High | ✅ Yes | Timeout | 0 (tech loss) |
| **E002** | INVALID_MESSAGE_FORMAT | Medium | ❌ No | Validation | 1 |
| **E003** | AUTHENTICATION_FAILED | High | ❌ No | Auth | 3 |
| **E004** | AGENT_NOT_REGISTERED | High | ❌ No | Registration | 3 |
| **E005** | INVALID_GAME_STATE | Medium | ✅ Yes | Game State | 4 |
| **E006** | PLAYER_NOT_AVAILABLE | Medium | ✅ Yes | Availability | 4 |
| **E007** | MATCH_NOT_FOUND | Medium | ❌ No | Not Found | 1 |
| **E008** | LEAGUE_NOT_FOUND | High | ❌ No | Configuration | 1 |
| **E009** | ROUND_NOT_ACTIVE | Medium | ✅ Yes | Game State | 4 |
| **E010** | INVALID_MOVE | Low | ❌ No | Validation | 0 (tech loss) |
| **E011** | PROTOCOL_VERSION_MISMATCH | High | ❌ No | Configuration | 1 |
| **E012** | AUTH_TOKEN_INVALID | High | ❌ No | Auth | 3 |
| **E013** | CONVERSATION_ID_MISMATCH | Medium | ❌ No | Validation | 4 |
| **E014** | RATE_LIMIT_EXCEEDED | Medium | ✅ Yes | Rate Limit | 4 |
| **E015** | INTERNAL_SERVER_ERROR | High | ✅ Yes | Server Error | 4 |
| **E016** | SERVICE_UNAVAILABLE | High | ✅ Yes | Network | 2 |
| **E017** | DUPLICATE_REGISTRATION | Medium | ❌ No | Registration | 3 |
| **E018** | INVALID_ENDPOINT | High | ❌ No | Network | 2 |

---

## 3. Exit Code Mapping

CLI agents (players, referees, league manager) use these exit codes:

| Exit Code | Meaning | Associated Error Codes |
|-----------|---------|------------------------|
| **0** | Success OR technical loss handled gracefully | E001, E010 (technical loss) |
| **1** | Configuration/validation error | E002, E007, E008, E011 |
| **2** | Network error | E016, E018 |
| **3** | Registration/authentication error | E003, E004, E012, E017 |
| **4** | Runtime error | E005, E006, E009, E013, E014, E015 |

**Usage in CLI:**
```bash
# Exit code 0 - Success or graceful tech loss
python -m agents.player_P01.main --help  # Exit 0

# Exit code 1 - Configuration error
python -m agents.player_P01.main --port 100  # Exit 2 (argparse)

# Exit code 2 - Network error (E016, E018)
# Exit code 3 - Registration error (E004, E012)
# Exit code 4 - Runtime error (E015)
```

---

## 4. Detailed Error Codes

### E001: TIMEOUT_ERROR

**Severity:** High
**Retryable:** ✅ Yes (added per user requirements)
**Defined in:** `SHARED/league_sdk/protocol.py:67`

**Description:**
Response not received within the configured timeout period. Applicable to game joins, parity choices, or any request-response interaction.

**Timeout Values (from `system.json`):**
- `game_join_ack_sec`: 5 seconds
- `parity_choice_sec`: 30 seconds
- `generic_sec`: 10 seconds
- `request_timeout_sec`: 10 seconds

**Common Causes:**
- Player agent offline or crashed
- Network latency or packet loss
- Player agent processing too slowly
- Player agent deadlocked or busy

**Consequences:**
- **Game Context:** Referee awards **technical loss** to non-responsive player
- **Non-Game Context:** Request fails after max retries (3 attempts with backoff)

**Resolution Steps:**
1. **Check player health:** `curl http://localhost:8101/health`
2. **Review player logs:** Look for processing delays or exceptions
3. **Check network:** `ping localhost`, network stats
4. **Monitor retry attempts:** Max 3 attempts with 2s/4s/8s backoff
5. **If persistent:** Restart player agent, check system resources

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T10:16:00Z",
  "conversation_id": "conv-r1m1-001",
  "match_id": "R1M1",
  "error_code": "E001",
  "error_description": "TIMEOUT_ERROR",
  "affected_player": "P02",
  "action_required": "CHOOSE_PARITY_RESPONSE",
  "retry_info": {
    "retry_count": 3,
    "max_retries": 3,
    "total_delay_sec": 14
  },
  "consequence": "Technical loss awarded to P02"
}
```

**Related Errors:** E006 (player unavailable), E016 (service unavailable)

---

### E002: INVALID_MESSAGE_FORMAT

**Severity:** Medium
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:68`

**Description:**
JSON parsing failed, schema validation failed (Pydantic), or required fields missing.

**Common Causes:**
- Malformed JSON (syntax error)
- Missing required fields (`protocol`, `message_type`, `sender`, `timestamp`)
- Type mismatch (e.g., string instead of integer)
- Invalid enum value (e.g., `parity_choice: "maybe"` instead of `"even"/"odd"`)
- Extra fields not allowed by schema

**Consequences:**
- Request **rejected immediately**
- Sender must fix the message payload
- No retry attempted (non-retryable)

**Resolution Steps:**
1. **Validate JSON syntax:** `python3 -m json.tool < message.json`
2. **Check Pydantic model:** Review `SHARED/league_sdk/protocol.py` for schema
3. **Inspect error details:** Pydantic includes field-level validation errors
4. **Use schema validator:** Test with `JSONRPCRequest.model_validate(data)`
5. **Review protocol version:** Ensure `"protocol": "league.v2"`

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:05:30Z",
  "conversation_id": "conv-error-001",
  "error_code": "E002",
  "error_description": "INVALID_MESSAGE_FORMAT",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "validation_errors": [
      "Field 'auth_token' missing",
      "Field 'agent_id' must be non-empty string"
    ]
  }
}
```

**Related Errors:** E010 (invalid move), E011 (protocol mismatch)

---

### E003: AUTHENTICATION_FAILED

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:69`

**Description:**
Initial authentication failed due to invalid credentials or missing authentication header.

**Common Causes:**
- Missing `auth_token` in registration request
- Invalid credentials during initial registration
- League Manager authentication check failed
- Sender identity cannot be verified

**Consequences:**
- Registration **rejected**
- Agent must re-authenticate or provide valid credentials
- Cannot proceed until authentication succeeds

**Resolution Steps:**
1. **Check credentials:** Verify `auth_token` is included in request
2. **Review League Manager logs:** Look for authentication failures
3. **Verify sender identity:** Ensure `sender` field matches agent identity
4. **Re-register:** Use correct credentials
5. **Check config:** Verify `security.require_auth` in `system.json`

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:05:30Z",
  "conversation_id": "conv-reg-001",
  "error_code": "E003",
  "error_description": "AUTHENTICATION_FAILED",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "reason": "Invalid credentials provided"
  }
}
```

**Related Errors:** E012 (token invalid), E004 (not registered)

---

### E004: AGENT_NOT_REGISTERED

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:70`

**Description:**
Agent ID not found in the registry. Agent must register before sending requests.

**Common Causes:**
- Agent never registered with League Manager
- Registration expired or was revoked
- Agent ID mismatch (typo in `sender` field)
- League Manager restarted and lost registration state

**Consequences:**
- Request **rejected**
- Agent must register via `PLAYER_REGISTER` or `REFEREE_REGISTER`
- Cannot proceed until registered

**Resolution Steps:**
1. **Check registration status:** Review League Manager's `registered_players` or `registered_referees`
2. **Register agent:** Use MCP tool `manual_register` or auto-register on startup
3. **Verify agent ID:** Ensure `sender` field matches registered ID (e.g., `"player:P01"`)
4. **Check League Manager health:** `curl http://localhost:8000/health`
5. **Review logs:** Look for registration success/failure events

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:10:00Z",
  "conversation_id": "conv-query-001",
  "error_code": "E004",
  "error_description": "AGENT_NOT_REGISTERED",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "sender": "player:P05",
    "registered_players": ["P01", "P02", "P03", "P04"]
  }
}
```

**Related Errors:** E017 (duplicate registration), E012 (token invalid)

---

### E005: INVALID_GAME_STATE

**Severity:** Medium
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:71`

**Description:**
Operation not allowed in the current game state. For example, trying to submit a move before the game starts, or after it's already finished.

**Common Causes:**
- Race condition (state changed between request and processing)
- Player sent choice before receiving `GAME_INVITATION`
- Player sent choice after `GAME_OVER` received
- Match lifecycle state mismatch

**Consequences:**
- Request **rejected with retry**
- Retry with exponential backoff (2s, 4s, 8s)
- State may change after retry delay

**Resolution Steps:**
1. **Wait for state transition:** Game state may become valid after delay
2. **Review match lifecycle:** Check current state (PENDING → ACTIVE → FINISHED)
3. **Retry automatically:** SDK handles retry with backoff
4. **Check conversation_id:** Ensure request matches current conversation
5. **Review Referee logs:** Look for state transition events

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T10:20:00Z",
  "conversation_id": "conv-r1m1-002",
  "match_id": "R1M1",
  "error_code": "E005",
  "error_description": "INVALID_GAME_STATE",
  "affected_player": "P01",
  "context": {
    "current_state": "PENDING",
    "required_state": "ACTIVE",
    "action_attempted": "CHOOSE_PARITY_RESPONSE"
  }
}
```

**Related Errors:** E009 (round not active), E007 (match not found)

---

### E006: PLAYER_NOT_AVAILABLE

**Severity:** Medium
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:72`

**Description:**
Player agent is offline, busy, or otherwise unreachable. Differs from E001 (timeout) in that the issue is known before attempting to contact the player.

**Common Causes:**
- Player agent not running
- Player agent health check failed
- Player endpoint unreachable (network issue)
- Player marked as unavailable in registry

**Consequences:**
- **Retry with backoff:** 3 attempts with 2s/4s/8s delays
- **If retries exhausted:** Referee may award technical loss
- **Circuit breaker:** After 5 consecutive failures, fail fast with E016

**Resolution Steps:**
1. **Check player health:** `curl http://localhost:8101/health`
2. **Start player agent:** `python -m agents.player_P01.main`
3. **Check network:** Verify player endpoint in `agents_config.json`
4. **Review player logs:** Look for crashes or exceptions
5. **Monitor retry attempts:** Max 3 attempts before tech loss

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T10:25:00Z",
  "conversation_id": "conv-r1m1-003",
  "match_id": "R1M1",
  "error_code": "E006",
  "error_description": "PLAYER_NOT_AVAILABLE",
  "affected_player": "P03",
  "retry_info": {
    "retry_count": 2,
    "max_retries": 3
  },
  "context": {
    "health_check_status": "FAILED",
    "last_seen": "2025-12-27T10:20:00Z"
  }
}
```

**Related Errors:** E001 (timeout), E016 (service unavailable)

---

### E007: MATCH_NOT_FOUND

**Severity:** Medium
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:73`

**Description:**
Requested match ID does not exist in the system.

**Common Causes:**
- Typo in match_id (e.g., `"R1M99"` instead of `"R1M1"`)
- Match not yet created (race condition)
- Match ID from different league
- Match already purged/archived

**Consequences:**
- Request **rejected immediately**
- Sender must verify match ID
- Check schedule or create match first

**Resolution Steps:**
1. **Verify match ID:** Check against schedule in `data/schedule/<league_id>.json`
2. **Query schedule:** Use `LEAGUE_QUERY` to get active matches
3. **Check league ID:** Ensure match belongs to current league
4. **Review Referee logs:** Look for match creation events
5. **Correct match ID:** Update request with valid ID

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:30:00Z",
  "conversation_id": "conv-result-001",
  "error_code": "E007",
  "error_description": "MATCH_NOT_FOUND",
  "original_message_type": "MATCH_RESULT_REPORT",
  "context": {
    "requested_match_id": "R1M99",
    "available_matches": ["R1M1", "R1M2", "R1M3"]
  }
}
```

**Related Errors:** E008 (league not found), E009 (round not active)

---

### E008: LEAGUE_NOT_FOUND

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:74`

**Description:**
Requested league ID does not exist in the system.

**Common Causes:**
- Typo in league_id (e.g., `"league_01"` instead of `"league_1"`)
- League config file missing (`SHARED/config/leagues/<league_id>.json`)
- Environment variable `LEAGUE_ID` not set or incorrect
- Wrong config directory specified

**Consequences:**
- Request **rejected immediately**
- Fatal configuration error (Exit code 1)
- Cannot proceed until league exists

**Resolution Steps:**
1. **Check league config:** Verify `SHARED/config/leagues/<league_id>.json` exists
2. **Validate league ID:** Ensure matches config filename (without `.json`)
3. **Set environment variable:** `export LEAGUE_ID=league_1`
4. **Use CLI argument:** `--league-id league_1`
5. **Create league config:** Copy from template if missing

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:35:00Z",
  "conversation_id": "conv-reg-002",
  "error_code": "E008",
  "error_description": "LEAGUE_NOT_FOUND",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "requested_league_id": "league_99",
    "available_leagues": ["league_1"]
  }
}
```

**Related Errors:** E002 (invalid format), E011 (protocol mismatch)

---

### E009: ROUND_NOT_ACTIVE

**Severity:** Medium
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:75`

**Description:**
Round not started yet or already finished. Operations like match creation or result reporting require an active round.

**Common Causes:**
- League not started yet (before `start_league` command)
- Round already completed (all matches finished)
- Race condition (round state changed)
- Scheduler hasn't started new round yet

**Consequences:**
- Request **rejected with retry**
- Retry with exponential backoff (2s, 4s, 8s)
- Round may become active after retry delay

**Resolution Steps:**
1. **Check round status:** Query League Manager for current round state
2. **Wait for round start:** `start_league` command triggers round 1
3. **Retry automatically:** SDK handles retry with backoff
4. **Review schedule:** Check `data/schedule/<league_id>.json`
5. **Monitor League Manager:** Look for round transition events

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:40:00Z",
  "conversation_id": "conv-result-002",
  "error_code": "E009",
  "error_description": "ROUND_NOT_ACTIVE",
  "original_message_type": "MATCH_RESULT_REPORT",
  "context": {
    "current_round": null,
    "league_state": "PENDING",
    "available_actions": ["Start league via start_league command"]
  }
}
```

**Related Errors:** E005 (invalid game state), E008 (league not found)

---

### E010: INVALID_MOVE

**Severity:** Low
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:76`

**Description:**
Player submitted an invalid parity choice. Must be exactly `"even"` or `"odd"` (case-sensitive).

**Common Causes:**
- Typo in choice (e.g., `"Even"`, `"EVEN"`, `"even "`)
- Wrong value (e.g., `"maybe"`, `"1"`, `null`)
- Missing `parity_choice` field
- Type error (sent integer instead of string)

**Consequences:**
- **Technical loss awarded** to offending player
- Match result reflects violation
- No retry (non-retryable)

**Resolution Steps:**
1. **Validate choice:** Must be `"even"` or `"odd"` (lowercase, exact match)
2. **Check Pydantic model:** `ChooseParityResponse` schema
3. **Review player logic:** Fix strategy to only send valid choices
4. **Test locally:** Validate before sending to Referee
5. **Update player code:** Add input validation

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T10:45:00Z",
  "conversation_id": "conv-r1m1-004",
  "match_id": "R1M1",
  "error_code": "E010",
  "error_description": "INVALID_MOVE",
  "affected_player": "P04",
  "context": {
    "invalid_choice": "Even",
    "valid_choices": ["even", "odd"]
  },
  "consequence": "Technical loss awarded to P04"
}
```

**Related Errors:** E002 (invalid format), E005 (invalid state)

---

### E011: PROTOCOL_VERSION_MISMATCH

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:77`

**Description:**
Protocol version in message does not match expected version (`league.v2`).

**Common Causes:**
- Agent using old protocol version (e.g., `"league.v1"`)
- Missing `protocol` field in message
- Typo in protocol field (e.g., `"leage.v2"`)
- Agent software out of date

**Consequences:**
- **Fatal error** (Exit code 1)
- Message rejected immediately
- Agent must upgrade to compatible version
- No retry (non-retryable)

**Resolution Steps:**
1. **Check protocol field:** Must be `"protocol": "league.v2"`
2. **Upgrade agent software:** Update to latest version
3. **Review message schema:** Ensure all messages include protocol field
4. **Check config:** Verify `system.json` has correct protocol version
5. **Consult API docs:** Review protocol specification

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:50:00Z",
  "conversation_id": "conv-reg-003",
  "error_code": "E011",
  "error_description": "PROTOCOL_VERSION_MISMATCH",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "received_protocol": "league.v1",
    "supported_protocols": ["league.v2"]
  }
}
```

**Related Errors:** E002 (invalid format), E008 (league not found)

---

### E012: AUTH_TOKEN_INVALID

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:78`

**Description:**
Auth token validation failed. Token may be expired, corrupted, or belong to different agent.

**Common Causes:**
- Token expired (time-based expiration)
- Token hash mismatch
- Token for different agent ID
- Token corrupted in transit
- League Manager restarted and tokens invalidated

**Consequences:**
- Request **rejected** (Exit code 3)
- Agent must re-register to get new token
- No retry (non-retryable)

**Resolution Steps:**
1. **Re-register:** Use `manual_register` MCP tool or auto-register
2. **Check token storage:** Ensure token saved correctly after registration
3. **Verify token format:** Should be 40-character alphanumeric string
4. **Review League Manager logs:** Look for token validation failures
5. **Check security config:** Verify `security.require_auth` setting

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:55:00Z",
  "conversation_id": "conv-query-002",
  "error_code": "E012",
  "error_description": "AUTH_TOKEN_INVALID",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "reason": "Token validation failed",
    "agent_id": "P01"
  }
}
```

**Related Errors:** E003 (auth failed), E004 (not registered)

---

### E013: CONVERSATION_ID_MISMATCH

**Severity:** Medium
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:79`

**Description:**
Conversation ID in response does not match the request. Used for correlation and thread tracking.

**Common Causes:**
- Player sent response to wrong conversation
- Player mixing up multiple concurrent matches
- Copy-paste error in conversation_id field
- Agent state corruption

**Consequences:**
- Response **rejected**
- Agent must send correct conversation_id
- May cause match desynchronization

**Resolution Steps:**
1. **Track conversation IDs:** Store ID from `GAME_INVITATION`
2. **Echo in responses:** Use same ID from incoming message
3. **Review player state:** Check for state corruption
4. **Use message envelopes:** Ensure envelope has correct ID
5. **Debug logs:** Log all conversation IDs for tracing

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T11:00:00Z",
  "conversation_id": "conv-r1m1-correct",
  "match_id": "R1M1",
  "error_code": "E013",
  "error_description": "CONVERSATION_ID_MISMATCH",
  "affected_player": "P02",
  "context": {
    "expected_conversation_id": "conv-r1m1-correct",
    "received_conversation_id": "conv-r1m2-wrong"
  }
}
```

**Related Errors:** E007 (match not found), E005 (invalid state)

---

### E014: RATE_LIMIT_EXCEEDED

**Severity:** Medium
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:80`

**Description:**
Too many requests sent in a short time period. Rate limiting protects against accidental or malicious flooding.

**Common Causes:**
- Agent sending requests in tight loop
- Retry logic without proper delays
- Multiple concurrent requests from same agent
- Misconfigured request rate

**Consequences:**
- Request **rejected with retry**
- Retry with exponential backoff (2s, 4s, 8s)
- Must slow down request rate

**Resolution Steps:**
1. **Add delays:** Space out requests by at least 100ms
2. **Check retry logic:** Ensure exponential backoff implemented
3. **Review concurrency:** Limit concurrent requests per agent
4. **Monitor request rate:** Log request timestamps
5. **Adjust config:** Increase `max_connections` if needed

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T11:05:00Z",
  "conversation_id": "conv-query-003",
  "error_code": "E014",
  "error_description": "RATE_LIMIT_EXCEEDED",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "current_rate": "50 requests/sec",
    "limit": "10 requests/sec",
    "retry_after_sec": 5
  }
}
```

**Related Errors:** E016 (service unavailable), E015 (internal error)

---

### E015: INTERNAL_SERVER_ERROR

**Severity:** High
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:81`

**Description:**
Unhandled exception or internal error in server/agent. Indicates a bug or unexpected condition.

**Common Causes:**
- Uncaught exception in handler
- Null pointer / AttributeError
- Database connection failure
- File system error
- Memory exhaustion

**Consequences:**
- Request **rejected with retry**
- Retry with exponential backoff (2s, 4s, 8s)
- Server logs contain stack trace
- May indicate critical bug

**Resolution Steps:**
1. **Check server logs:** Look for stack traces and error details
2. **Review exception:** Identify root cause (null pointer, type error, etc.)
3. **Fix bug:** Update code to handle error condition
4. **Add error handling:** Wrap risky operations in try/except
5. **Test fix:** Reproduce error and verify resolution

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T11:10:00Z",
  "conversation_id": "conv-standings-001",
  "error_code": "E015",
  "error_description": "INTERNAL_SERVER_ERROR",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "exception": "AttributeError: 'NoneType' object has no attribute 'get'",
    "component": "standings_processor",
    "correlation_id": "req-12345"
  }
}
```

**Related Errors:** E016 (service unavailable), E014 (rate limit)

---

### E016: SERVICE_UNAVAILABLE

**Severity:** High
**Retryable:** ✅ Yes
**Defined in:** `SHARED/league_sdk/protocol.py:82`

**Description:**
Service temporarily unavailable. Circuit breaker may be OPEN, or service is restarting.

**Common Causes:**
- Agent crashed or restarting
- Circuit breaker OPEN (5 consecutive failures)
- Network partition
- Service maintenance
- System overload

**Consequences:**
- Request **rejected with retry**
- Circuit breaker opens after 5 failures (fail fast for 60s)
- Retry with exponential backoff (2s, 4s, 8s)
- May escalate to technical loss if persistent

**Resolution Steps:**
1. **Check service health:** `curl http://localhost:8000/health`
2. **Review service logs:** Look for crashes or restart events
3. **Check circuit breaker:** Monitor open/half-open state
4. **Wait for recovery:** Circuit breaker auto-recovers after 60s
5. **Restart service:** If crashed, restart manually

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T11:15:00Z",
  "conversation_id": "conv-reg-004",
  "error_code": "E016",
  "error_description": "SERVICE_UNAVAILABLE",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "circuit_breaker_state": "OPEN",
    "failure_count": 5,
    "retry_after_sec": 60
  }
}
```

**Related Errors:** E006 (player unavailable), E018 (invalid endpoint)

---

### E017: DUPLICATE_REGISTRATION

**Severity:** Medium
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:83`

**Description:**
Agent already registered with this league. Cannot register twice.

**Common Causes:**
- Agent restarted and auto-registered again
- Registration called multiple times
- Agent ID collision (two agents with same ID)
- Forgot to deregister before re-registering

**Consequences:**
- Registration **rejected**
- Use existing registration
- No action required (already registered)

**Resolution Steps:**
1. **Check registration status:** Agent is already registered (success!)
2. **Use existing auth token:** No need to re-register
3. **Deregister first:** If you want to re-register, call deregister
4. **Verify agent ID:** Ensure no ID collision with other agents
5. **Proceed normally:** Registration already complete

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T11:20:00Z",
  "conversation_id": "conv-reg-005",
  "error_code": "E017",
  "error_description": "DUPLICATE_REGISTRATION",
  "original_message_type": "PLAYER_REGISTER",
  "context": {
    "agent_id": "P01",
    "existing_registration": {
      "registered_at": "2025-12-27T11:00:00Z",
      "auth_token": "abc123...def456"
    }
  }
}
```

**Related Errors:** E004 (not registered), E012 (token invalid)

---

### E018: INVALID_ENDPOINT

**Severity:** High
**Retryable:** ❌ No
**Defined in:** `SHARED/league_sdk/protocol.py:84`

**Description:**
Contact endpoint unreachable or invalid. DNS resolution failed, connection refused, or invalid URL format.

**Common Causes:**
- Typo in endpoint URL (`http://localhot:8101`)
- Wrong port number
- Agent not listening on specified port
- Firewall blocking connection
- Invalid URL format (missing `http://` prefix)

**Consequences:**
- **Fatal for operation** (Exit code 2)
- Request cannot be sent
- Must fix endpoint configuration
- No retry (non-retryable)

**Resolution Steps:**
1. **Validate URL format:** Must be `http://host:port/path`
2. **Check DNS resolution:** `ping hostname`
3. **Verify port:** Ensure agent listening on specified port
4. **Update config:** Fix endpoint in `agents_config.json`
5. **Test connection:** `curl -v http://localhost:8101/health`

**Example:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T11:25:00Z",
  "conversation_id": "conv-r1m1-005",
  "match_id": "R1M1",
  "error_code": "E018",
  "error_description": "INVALID_ENDPOINT",
  "affected_player": "P01",
  "context": {
    "endpoint": "http://localhot:8101/mcp",
    "error": "Name or service not known",
    "valid_example": "http://localhost:8101/mcp"
  }
}
```

**Related Errors:** E016 (service unavailable), E006 (player unavailable)

---

## 5. Retry and Circuit Breaker

### 5.1 Retry Policy

**Configuration** (from `SHARED/config/system.json`):
```json
{
  "retry": {
    "max_retries": 3,
    "initial_delay_sec": 2,
    "max_delay_sec": 10,
    "exponential_base": 2,
    "retryable_errors": ["E001", "E005", "E006", "E009", "E014", "E015", "E016"]
  }
}
```

**Retry Delays:**
- Attempt 1: 2 seconds
- Attempt 2: 4 seconds
- Attempt 3: 8 seconds
- **Total max wait:** ~14 seconds

**Implementation:**
```python
from league_sdk.retry import retry_with_backoff, is_error_retryable

@retry_with_backoff(max_retries=3, initial_delay=2.0)
async def send_request(endpoint, message):
    # Will retry E001, E005, E006, E009, E014, E015, E016 automatically
    response = await call_with_retry(endpoint, message)
    return response
```

### 5.2 Circuit Breaker

**Configuration:**
- **Failure threshold:** 5 consecutive failures
- **Timeout:** 60 seconds (OPEN state)
- **Half-open:** Allow 1 test request after timeout
- **Reset:** After successful request in HALF_OPEN state

**States:**
1. **CLOSED:** Normal operation, requests pass through
2. **OPEN:** Fail fast with E016 (no network calls for 60s)
3. **HALF_OPEN:** Test with 1 request, reset if succeeds

**Triggers:**
- E016 (SERVICE_UNAVAILABLE)
- E018 (INVALID_ENDPOINT)
- Network timeout (no response)

**Implementation:**
```python
from league_sdk.retry import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    reset_timeout=60,
    success_threshold=1
)

async def call_with_circuit_breaker(endpoint, message):
    if breaker.is_open():
        return {"error_code": "E016", "error_description": "SERVICE_UNAVAILABLE"}

    try:
        response = await send_request(endpoint, message)
        breaker.record_success()
        return response
    except Exception as e:
        breaker.record_failure()
        raise
```

---

## 6. Troubleshooting Guide

### Common Scenarios

#### Scenario 1: Player Times Out (E001)

**Symptoms:**
- Referee logs `E001: TIMEOUT_ERROR`
- Player didn't respond within timeout
- Technical loss awarded

**Debug Steps:**
1. Check player health: `curl http://localhost:8101/health`
2. Review player logs for processing delays
3. Check network latency: `ping localhost`
4. Verify timeout values in `system.json`
5. Monitor retry attempts (max 3)

**Resolution:**
- Increase timeout if justified (edit `system.json`)
- Optimize player processing (reduce computation time)
- Fix network issues
- Restart player if crashed

---

#### Scenario 2: Registration Failed (E004)

**Symptoms:**
- Player cannot send requests
- League Manager returns `E004: AGENT_NOT_REGISTERED`

**Debug Steps:**
1. Check registration status: Review League Manager logs
2. Verify agent_id in config
3. Test registration: Use `manual_register` MCP tool
4. Check auth token: Ensure token saved after registration

**Resolution:**
- Register manually: `manual_register` tool
- Enable auto-register: Set `metadata.auto_register: true` in config
- Fix agent_id: Ensure matches `agents_config.json`

---

#### Scenario 3: Invalid Message (E002)

**Symptoms:**
- Request rejected immediately
- Pydantic validation error in logs

**Debug Steps:**
1. Validate JSON: `python3 -m json.tool < message.json`
2. Check schema: Review Pydantic model in `protocol.py`
3. Inspect validation errors: Check `context.validation_errors`
4. Test with curl: Send sample request

**Resolution:**
- Fix JSON syntax
- Add missing required fields
- Correct field types
- Use valid enum values

---

#### Scenario 4: Service Unavailable (E016)

**Symptoms:**
- Circuit breaker OPEN
- All requests fail fast with E016
- 5+ consecutive failures

**Debug Steps:**
1. Check service health: `curl http://localhost:8000/health`
2. Review service logs for crashes
3. Monitor circuit breaker state
4. Wait 60 seconds for auto-recovery

**Resolution:**
- Restart crashed service
- Wait for circuit breaker reset (60s)
- Fix underlying issue causing failures
- Check system resources (CPU, memory)

---

### Quick Diagnosis Table

| Symptom | Likely Error | First Action |
|---------|--------------|--------------|
| "Agent not registered" | E004 | Register with League Manager |
| "Timeout error" | E001 | Check player health, network |
| "Invalid message format" | E002 | Validate JSON syntax |
| "Auth token invalid" | E012 | Re-register to get new token |
| "Service unavailable" | E016 | Check health, restart service |
| "Invalid move" | E010 | Must be "even" or "odd" |
| "Protocol version mismatch" | E011 | Update to league.v2 |
| "Rate limit exceeded" | E014 | Slow down requests, add delays |

---

## 7. Error Response Formats

### 7.1 LEAGUE_ERROR (System-Level)

Used by League Manager for registration, authentication, and league-level errors.

```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-12-27T10:05:30Z",
  "conversation_id": "conv-error-001",
  "error_code": "E012",
  "error_description": "AUTH_TOKEN_INVALID",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "provided_token": "tok-invalid-xxx"
  }
}
```

### 7.2 GAME_ERROR (Match-Level)

Used by Referees for match-specific errors (timeouts, invalid moves).

```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-12-27T10:16:00Z",
  "conversation_id": "conv-r1m1-001",
  "match_id": "R1M1",
  "error_code": "E001",
  "error_description": "TIMEOUT_ERROR",
  "affected_player": "P02",
  "action_required": "CHOOSE_PARITY_RESPONSE",
  "retry_info": {
    "retry_count": 3,
    "max_retries": 3
  },
  "consequence": "Technical loss awarded to P02"
}
```

### 7.3 JSON-RPC Error Wrapper

All errors are wrapped in JSON-RPC 2.0 responses:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "TIMEOUT_ERROR",
    "data": {
      "error_code": "E001",
      "message_type": "GAME_ERROR",
      "conversation_id": "conv-r1m1-001",
      "match_id": "R1M1",
      "affected_player": "P02",
      "deadline_sec": 30
    }
  }
}
```

**JSON-RPC Error Code Mapping:**
- `-32000`: Timeout (E001)
- `-32001`: Auth failure (E003, E012)
- `-32002`: Invalid params (E002, E010)
- `-32600`: Protocol mismatch (E011)
- `-32603`: Internal error (E015)

---

## 8. Logging Best Practices

### 8.1 Structured Logging

All error logs must use JSONL format with structured fields:

```python
from league_sdk.logger import JsonLogger

logger = JsonLogger(component="player", agent_id="P01")

# Log error event
logger.log_error_event(
    error_code="E001",
    error_message="Timeout waiting for parity choice",
    match_id="R1M1",
    conversation_id="conv-r1m1-001",
    timeout_sec=30
)
```

### 8.2 Required Fields

Every error log entry MUST include:
- `error_code`: E001-E018
- `conversation_id`: For correlation
- `sender`: Who caused the error
- `timestamp`: ISO 8601 format
- `component`: Which agent/service logged it

### 8.3 Log Levels

- **ERROR:** Non-retryable errors (E002, E003, E004, E007, E008, E010, E011, E012, E013, E017, E018)
- **WARNING:** Retryable errors (E001, E005, E006, E009, E014, E015, E016) with attempt count
- **INFO:** Successful recovery after retry

### 8.4 Security

- **Redact auth tokens:** Never log full tokens, use hash if needed
- **Redact PII:** No personal information in logs
- **Log token hash:** For correlation without exposing token

**Example:**
```json
{
  "timestamp": "2025-12-27T11:30:00Z",
  "level": "ERROR",
  "component": "league_manager",
  "event_type": "ERROR",
  "error_code": "E012",
  "message": "Auth token validation failed",
  "context": {
    "agent_id": "P01",
    "token_hash": "abc123...def456",  // Hashed, not full token
    "conversation_id": "conv-reg-006"
  }
}
```

---

## Appendix A: Exit Code to Error Code Mapping

| Exit Code | Error Codes | Agent Response |
|-----------|-------------|----------------|
| 0 | E001 (tech loss), E010 (tech loss) | Graceful exit after tech loss |
| 1 | E002, E007, E008, E011 | Configuration/validation error |
| 2 | E016, E018 | Network error |
| 3 | E003, E004, E012, E017 | Auth/registration error |
| 4 | E005, E006, E009, E013, E014, E015 | Runtime error |

---

## Appendix B: Retryable vs Non-Retryable Summary

**✅ Retryable (7 codes):**
- E001: TIMEOUT_ERROR
- E005: INVALID_GAME_STATE
- E006: PLAYER_NOT_AVAILABLE
- E009: ROUND_NOT_ACTIVE
- E014: RATE_LIMIT_EXCEEDED
- E015: INTERNAL_SERVER_ERROR
- E016: SERVICE_UNAVAILABLE

**❌ Non-Retryable (11 codes):**
- E002: INVALID_MESSAGE_FORMAT
- E003: AUTHENTICATION_FAILED
- E004: AGENT_NOT_REGISTERED
- E007: MATCH_NOT_FOUND
- E008: LEAGUE_NOT_FOUND
- E010: INVALID_MOVE
- E011: PROTOCOL_VERSION_MISMATCH
- E012: AUTH_TOKEN_INVALID
- E013: CONVERSATION_ID_MISMATCH
- E017: DUPLICATE_REGISTRATION
- E018: INVALID_ENDPOINT

---

## Appendix C: Error Code Quick Lookup

```bash
# Quick grep for error code usage
grep -r "E001" SHARED/league_sdk/
grep -r "TIMEOUT_ERROR" agents/

# Validate retry configuration
cat SHARED/config/system.json | jq '.retry.retryable_errors'

# Check error code definitions
grep "class ErrorCode" SHARED/league_sdk/protocol.py -A 20
```

---

**Document Ownership:** System Architecture
**Last Updated:** 2025-12-27
**Contributors:** League SDK Team
**Related Docs:** `error_handling_strategy.md`, `system_integration_verification_plan.md`, `api_reference.md`
