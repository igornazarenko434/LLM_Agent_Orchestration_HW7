# Error Handling Strategy

**Version:** 1.0.0
**Date:** 2025-01-15
**Protocol:** league.v2

---

## 1. Overview

This document defines the comprehensive error handling strategy for the Even/Odd League multi-agent system. It ensures robust communication, resilience against transient failures, and clear debugging pathways.

The strategy is built around:
1.  **18 Standardized Error Codes** (E001-E018)
2.  **Retry Policy with Exponential Backoff**
3.  **Circuit Breaker Pattern** for failing services
4.  **Structured Error Responses** (LEAGUE_ERROR and GAME_ERROR)

---

## 2. Error Codes Registry

All agents must strictly adhere to these error codes.

| Code | Name | Severity | Retryable | Description | Recovery / Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E001** | TIMEOUT_ERROR | High | No | Response not received within timeout | Referee awards technical loss; Log incident |
| **E002** | INVALID_MESSAGE_FORMAT | Medium | No | JSON parsing or schema validation failed | Reject message; Sender must fix payload |
| **E003** | AUTHENTICATION_FAILED | High | No | Invalid credentials or auth token | Reject; Sender must re-authenticate |
| **E004** | AGENT_NOT_REGISTERED | High | No | Agent ID not found in registry | Reject; Sender must register first |
| **E005** | INVALID_GAME_STATE | Medium | **Yes** | Operation not allowed in current state | Retry with backoff (state may change) |
| **E006** | PLAYER_NOT_AVAILABLE | Medium | **Yes** | Player offline or busy | Retry with backoff; Check player health |
| **E007** | MATCH_NOT_FOUND | Medium | No | Match ID does not exist | Reject; Verify Match ID |
| **E008** | LEAGUE_NOT_FOUND | High | No | League ID does not exist | Reject; Verify League ID |
| **E009** | ROUND_NOT_ACTIVE | Medium | **Yes** | Round not started or already finished | Retry; Wait for round start |
| **E010** | INVALID_MOVE | Low | No | Choice not "even" or "odd" | Reject; Referee awards technical loss |
| **E011** | PROTOCOL_VERSION_MISMATCH | High | No | Protocol version incompatible | Fatal; Upgrade agent software |
| **E012** | AUTH_TOKEN_INVALID | High | No | Token validation failed | Reject; Re-register to get new token |
| **E013** | CONVERSATION_ID_MISMATCH | Medium | No | conversation_id does not match | Reject; Check thread tracking |
| **E014** | RATE_LIMIT_EXCEEDED | Medium | **Yes** | Too many requests | Retry with exponential backoff |
| **E015** | INTERNAL_SERVER_ERROR | High | **Yes** | Unhandled exception | Retry; Check server logs |
| **E016** | SERVICE_UNAVAILABLE | High | **Yes** | Agent temporarily down | Retry; Check agent health |
| **E017** | DUPLICATE_REGISTRATION | Medium | No | Agent already registered | Reject; Use existing registration |
| **E018** | INVALID_ENDPOINT | High | No | Contact endpoint unreachable | Fatal for operation; Update config |

---

## 3. Resilience Patterns

### 3.1 Retry Policy
For errors marked **Retryable**, agents implement the following policy:
*   **Max Retries:** 3 attempts
*   **Strategy:** Exponential Backoff
*   **Delays:**
    *   Attempt 1: 2 seconds
    *   Attempt 2: 4 seconds
    *   Attempt 3: 8 seconds
*   **Total Max Wait:** ~14 seconds

### 3.2 Circuit Breaker
To prevent cascading failures when an agent is down (E016, E018):
*   **Threshold:** 5 consecutive failures
*   **Timeout:** 60 seconds (Open state)
*   **Half-Open:** Allow 1 test request after timeout
*   **Fallback:** Fail fast with `E016 SERVICE_UNAVAILABLE` without network call

---

## 4. Error Response Structure

Errors are reported using standard message envelopes.

### 4.1 System/League Level Error (`LEAGUE_ERROR`)
Sent by League Manager or generic infrastructure.

```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_ERROR",
  "sender": "league_manager",
  "timestamp": "2025-01-15T10:05:30Z",
  "conversation_id": "conv-error-001",
  "error_code": "E012",
  "error_description": "AUTH_TOKEN_INVALID",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "provided_token": "tok-invalid-xxx"
  }
}
```

### 4.2 Game Level Error (`GAME_ERROR`)
Sent by Referees regarding specific match incidents (timeouts, illegal moves).

```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "2025-01-15T10:16:00Z",
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

---

## 5. Logging Strategy

*   **Retryable Errors:** Log at `WARNING` level with attempt count.
*   **Non-Retryable Errors:** Log at `ERROR` level.
*   **Context:** All error logs MUST include:
    *   `error_code`
    *   `conversation_id`
    *   `sender` (of the failed request)
    *   Stack trace (if internal exception)

**Example Log Entry:**
```json
{
  "timestamp": "2025-01-15T10:16:00Z",
  "level": "ERROR",
  "component": "referee",
  "event_type": "ERROR",
  "error_code": "E001",
  "message": "Player P02 timed out during parity choice",
  "context": {
    "match_id": "R1M1",
    "conversation_id": "conv-r1m1-001"
  }
}
```

---

## 6. league.v2 + JSON-RPC Error Mapping

- **Transport**: All errors are wrapped in JSON-RPC responses: `error.code` (numeric), `error.message` (short), `error.data.error_code` (league code), `error.data.message_type`, `conversation_id`.
- **HTTP status**: Always 200 for logical errors; use 5xx only for transport/server faults that prevent JSON-RPC formation.
- **Timeouts**: Map to `E001` and JSON-RPC `code=-32000`; include `data.deadline_sec`.
- **Validation failures**: `E002` and JSON-RPC `code=-32602` with Pydantic validation details.
- **Auth failures**: `E003/E012` and JSON-RPC `code=-32001`; redact tokens in logs.
- **Protocol mismatch**: `E011` and JSON-RPC `code=-32600`; include supported versions in `data.supported_protocols=["league.v2"]`.

---

## 7. Agent-Specific Handling

- **League Manager**
  - Reject unregistered senders (`E004`), invalid league IDs (`E008`), duplicate registrations (`E017`).
  - On `MATCH_RESULT_REPORT`, if match not found → `E007`; if round not active → `E009` (retryable).
  - Standings update failures → `E015` (retryable) and logged with stack trace.

- **Referee**
  - Enforce join (5s) and parity (30s) deadlines; late → `E001` + technical loss.
  - Invalid move `"even"/"odd"` check → `E010`; award technical loss.
  - Player unavailable/unreachable → `E006` (retryable) with backoff before declaring tech loss if retries exhausted.
  - Service outage (self) → `E016`; let Circuit Breaker fail fast to callers.

- **Player**
  - Validate envelopes; malformed → `E002`.
  - Auth token missing/invalid → `E012`.
  - If asked to act on unknown match_id → `E007`.
  - Must respond within timeouts or accept referee’s `GAME_ERROR` decision.

---

## 8. Retry & Circuit Breaker (Implementation Notes)

- Use `league_sdk.retry.retry_with_backoff` and `CircuitBreaker` for outbound HTTP calls.
- **Retryable set** (per `ErrorCode.is_retryable` + `system.json`): `E005`, `E006`, `E009`, `E014`, `E015`, `E016`.
- **Do NOT retry**: Auth (`E003`, `E012`), registration (`E004`, `E017`), protocol (`E011`), invalid input (`E002`, `E010`, `E018`), timeouts (`E001`), missing match/league (`E007`, `E008`).
- Retries capped at 3 with delays 2s/4s/8s. Log each attempt with attempt number.
- Circuit breaker trips after 5 consecutive failures (open 60s); in open state, short-circuit with `E016` without network calls.

---

## 9. Observability & Forensics

- **Correlation**: Every log entry must include `conversation_id`, `match_id` (if applicable), and `sender`.
- **No secrets**: Redact auth tokens and PII; log token hash if needed.
- **Structured JSONL**: Use `league_sdk.logger.JsonLogger`; include `error_code`, `event_type`, `component`, `latency_ms`.
- **Metrics**: Track timeout rate (E001), auth failures (E003/E012), retry success rate, and circuit breaker open/half-open transitions.
- **Persistence**: Persist `GAME_ERROR`/`LEAGUE_ERROR` context into `data/matches/<league_id>/<match_id>.json` when match-affecting.

---

## 10. Recovery Playbooks

- **Timeout (E001)**: Declare technical loss for offending player, continue match flow, report via `MATCH_RESULT_REPORT`.
- **Invalid move (E010)**: Mark technical loss, include violation in `GAME_OVER`.
- **Auth failures (E003/E012)**: Stop processing; instruct re-registration if applicable.
- **Service down (E016)**: Circuit breaker open; escalate health checks; optionally failover to alternate referee if configured.
- **Rate limit (E014)**: Apply backoff; if still failing after max retries, surface error to caller.

---

## 11. Compliance Checklist (M5.4)

- Error codes E001–E018 implemented exactly as `SHARED/league_sdk/protocol.py`.
- Retryable set matches `ErrorCode.is_retryable` and `system.json`.
- JSON-RPC error mapping uses numeric codes with `data.error_code` carrying league code.
- Timeouts enforced per `system.json` (5s join, 30s parity, 10s generic); late responses yield `E001`.
- Technical loss rules applied for E001/E010; standings and reports updated accordingly.
- Logging via JsonLogger with correlation IDs; tokens redacted.
- Circuit breaker thresholds match `system.json` (failure_threshold=5, reset_timeout=60).
- No retries on auth, protocol, validation, or registration errors.
