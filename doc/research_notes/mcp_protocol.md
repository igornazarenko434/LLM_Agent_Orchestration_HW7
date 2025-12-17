# Research Notes: MCP Protocol & JSON-RPC 2.0

**Date:** 2025-01-15
**Mission:** M5.1
**Author:** Lead Architect

---

## 1. Overview

This document summarizes the research into the Model Context Protocol (MCP) and JSON-RPC 2.0 specification. These protocols form the backbone of the communication layer for the Even/Odd League multi-agent system. The system implements a custom `league.v2` protocol that is transported via standard JSON-RPC 2.0 messages over HTTP.

## 2. JSON-RPC 2.0 Specification

JSON-RPC 2.0 is a stateless, lightweight remote procedure call (RPC) protocol. It uses JSON as the data format and is transport-agnostic (though we use HTTP).

### 2.1 Request Format
A standard request object contains:
- `jsonrpc`: A string specifying the version of the JSON-RPC protocol. MUST be exactly "2.0".
- `method`: A string containing the name of the method to be invoked.
- `params`: A structured value (array or object) that holds the parameter values to be used during the invocation of the method. (Optional)
- `id`: An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification.

**Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "GAME_INVITATION",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_INVITATION",
    "sender": "referee:REF01",
    "timestamp": "2025-01-15T10:00:00Z",
    "conversation_id": "conv-1",
    "match_id": "M1"
  },
  "id": 1
}
```

### 2.2 Response Format
A standard response object contains:
- `jsonrpc`: A string specifying the version of the JSON-RPC protocol. MUST be exactly "2.0".
- `result`: The value of this member is determined by the method invoked on the Server. This member is REQUIRED on success.
- `error`: This member is REQUIRED on error. This member MUST NOT exist if there was no error.
- `id`: This member is REQUIRED. It MUST be the same as the value of the id member in the Request Object.

**Success Example:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "accept": true
  },
  "id": 1
}
```

### 2.3 Error Object Structure
When a remote procedure call fails, the Response Object MUST contain the error member with a value that is an Object with the following members:
- `code`: A Number that indicates the error type that occurred.
- `message`: A String providing a short description of the error.
- `data`: A Primitive or Structured value that contains additional information about the error. (Optional)

**Error Example:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": { "details": "Missing required field 'sender'" }
  },
  "id": 1
}
```

---

## 3. Model Context Protocol (MCP)

**Source:** https://modelcontextprotocol.io/

### 3.1 Core Concept
MCP is an open standard that enables AI models to interact with external data and tools. It standardizes how AI assistants connect to systems like databases, file systems, and API services.

### 3.2 Key Components
1.  **MCP Host:** The AI application (e.g., Claude Desktop, IDE, or our League Manager) that initiates connections.
2.  **MCP Server:** A service that exposes resources, prompts, and tools to the Host. In our project, every agent (`Player`, `Referee`, `LeagueManager`) acts as an MCP Server.
3.  **MCP Client:** The component within the Host that speaks the protocol.

### 3.3 Message Types & Patterns
MCP defines three primary primitives:
*   **Resources:** File-like data that can be read by the client (e.g., logs, game history).
*   **Prompts:** Pre-defined templates for interacting with the server.
*   **Tools:** Executable functions that can perform actions (side effects) and return results. This is the **primary pattern** used in our League.

### 3.4 Tool Calling Pattern
The "Tool Calling" pattern in MCP maps directly to our usage of JSON-RPC 2.0.
1.  **Discovery:** The Client (Referee) asks the Server (Player) "What tools do you have?" (via `list_tools` - implicit in our config).
2.  **Call:** The Client sends a request to execute a specific tool (e.g., `choose_parity`) with arguments.
3.  **Execution:** The Server validates arguments, runs logic (e.g., random strategy), and returns a result.
4.  **Result:** The Client receives the output or an error.

**Integration in League:**
*   `handle_game_invitation` is a **Tool** exposed by the Player.
*   `conduct_match` is a **Tool** exposed by the Referee.
*   `register_player` is a **Tool** exposed by the League Manager.

---

## 4. FastAPI Integration Pattern

To implement MCP Servers using Python and FastAPI (as required by our stack):

### 4.1 Routing
We use a single endpoint (e.g., `/mcp`) to handle all JSON-RPC traffic. FastAPI does not have built-in JSON-RPC support, so we implement a custom handler or use a lightweight wrapper.

### 4.2 Implementation Pattern
```python
from fastapi import FastAPI, Request
from league_sdk.protocol import JSONRPCRequest, JSONRPCResponse

app = FastAPI()

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    # 1. Parse JSON body
    body = await request.json()
    
    # 2. Validate as JSON-RPC Request
    rpc_req = JSONRPCRequest(**body)
    
    # 3. Dispatch to Tool Handler
    if rpc_req.method == "handle_game_invitation":
        result = player_agent.handle_invitation(rpc_req.params)
    elif rpc_req.method == "choose_parity":
        result = player_agent.choose_parity(rpc_req.params)
    else:
        # Return Method Not Found error
        pass
        
    # 4. Return JSON-RPC Response
    return JSONRPCResponse(result=result, id=rpc_req.id)
```

### 4.3 Best Practices
*   **Pydantic Models:** Use Pydantic for strict schema validation of `params` (the `MessageEnvelope`).
*   **Error Handling:** Catch all exceptions in the handler and convert them to valid JSON-RPC `error` objects.
*   **Async/Await:** Use `async def` for tool handlers to allow I/O operations (like writing logs) without blocking the server.

---

## 5. Conclusion

The `league.v2` protocol is essentially a specialized application layer built on top of the standard MCP Tool Calling primitive, using JSON-RPC 2.0 as the transport. By adhering to strict JSON-RPC envelope structures and treating every agent interaction as a "Tool Call," we ensure compatibility with the broader MCP ecosystem philosophy while meeting specific project requirements.

---

## 6. league.v2 → MCP Alignment (Project-Specific Design Decisions)

- **Transport & Endpoint**: HTTP POST to a single `/mcp` route for all agents (LM, Referees, Players). No WebSocket or SSE required per PRD. Keep payloads small; use gzip if future load tests justify.
- **Method Mapping**: Each of the 18 message types maps to a JSON-RPC `method`; `params` carry the exact Pydantic model from `SHARED/league_sdk/protocol.py`. Notifications (no `id`) are only used for broadcasts (`ROUND_ANNOUNCEMENT`, `LEAGUE_STANDINGS_UPDATE`, `ROUND_COMPLETED`, `LEAGUE_COMPLETED`) to avoid unnecessary replies.
- **Envelope Enforcement**: Every `params` object MUST include `protocol`, `message_type`, `sender`, `timestamp`, `conversation_id`, and (post-registration) `auth_token`. Use `league_sdk.utils.generate_timestamp/format_sender/generate_conversation_id` to avoid format drift.
- **Authentication**: Registration messages omit `auth_token`; all others must include the issued token. Reject missing/invalid tokens with `E012` (maps to JSON-RPC error.code -32001 in our handler).
- **Error Translation**: Map league error codes to JSON-RPC error objects (`code` numeric, `message` short, `data.error_code` string). Retryable vs non-retryable is decided using `ErrorCode.is_retryable` + system retry policy (3 attempts, 2/4/8s).
- **Timeouts (Hard Requirements)**: Enforce PRD SLAs at the HTTP handler layer with per-method timeouts from `system.json` (`game_join_ack_sec` 5s, `parity_choice_sec` 30s, generic 10s). Surface timeout as `E001`.
- **Idempotency & Ordering**: Use `conversation_id` + `match_id` to dedupe late retries; do not reorder within a conversation. LM/Referee should treat duplicate `GAME_JOIN_ACK`/`CHOOSE_PARITY_RESPONSE` as no-ops but log once.
- **Batching**: JSON-RPC 2.0 batching is intentionally **not** supported to keep flow deterministic and simplify timeout handling. Reject batches with `INVALID_MESSAGE_FORMAT (E002)`.
- **Versioning**: Validate `protocol == league.v2`. Return `E011` on mismatch and include supported versions in `error.data.supported_protocols`.
- **Health & Observability**: Add `/health` (no auth) returning agent_id, status, uptime. Log all MCP requests/responses in JSONL via `league_sdk.logger.JsonLogger` with correlation on `conversation_id` and `match_id`.

## 7. FastAPI Implementation Best Practices (2025 MCP patterns)

- **Schema-first**: Use the Pydantic v2 models already defined to validate `params` and to serialize responses; reject `extra` by default except where protocol models allow `extra="allow"`.
- **Async handlers**: Keep `/mcp` async; delegate blocking I/O (file writes in repositories) to threadpool via `run_in_executor` if profiling shows event-loop stalls.
- **Central dispatcher**: One dispatcher table `{method: handler}` to avoid long if/else ladders; handlers return domain results which are wrapped into `JSONRPCResponse`.
- **Structured errors**: Catch `ValidationError` → JSON-RPC `code=-32602` + `data.error_code=E002`; timeouts → `code=-32000` + `data.error_code=E001`; auth failures → `code=-32001` + `data.error_code=E012`. Always include `message_type` and `conversation_id` in `data` for traceability.
- **Security**: Enforce `Content-Type: application/json`, cap body size (e.g., 64KB) via server config, and validate `sender` matches the registered agent endpoint to mitigate spoofing (`E003`/`E004`).
- **Retry & Circuit Breaker**: Client calls must use `retry_with_backoff` and `CircuitBreaker` from `league_sdk.retry`. Do not retry on terminal errors (E003, E004, E011, E012).
- **Logging hygiene**: Log at `INFO` for successful calls, `WARNING` for retryable errors, `ERROR` for terminal failures. Never log auth tokens in plain text; redact in logs.
- **Testing hooks**: Provide a `--dry-run`/`test_mode` flag in agents to bypass outbound HTTP and validate dispatch logic with fixtures (aligns with QG-1/QG-2 test strategy).

## 8. Compliance Checklist for M5.1 (to gate later missions)

- JSON-RPC 2.0 fields (`jsonrpc`, `method`, `params`, `id`) enforced; notifications allowed only for broadcasts.
- league.v2 envelope fields present and validated for every message; `timestamp` must end with `Z` and match regex.
- Auth token required after registration; invalid/missing tokens yield `E012`.
- Timeouts applied per `system.json`; late replies treated as technical loss per PRD.
- Error mapping consistent (`data.error_code` carries league code; `code` uses JSON-RPC range -32000 to -32099).
- No batch processing; requests >64KB rejected; content-type enforced.
- Logging is JSONL, append-only, with correlation IDs; no secrets in logs.
- Health endpoints live and unauthenticated; respond <1s.

## 9. Recent MCP/JSON-RPC Practical Tips (2024–2025)

- **Tool schemas**: Expose per-method JSON Schemas for params/results (even if only internally) to improve linting and future codegen; we can derive them from Pydantic models.
- **OpenTelemetry**: Wrap the dispatcher with tracing spans (`conversation_id` as trace id seed). Useful for load tests and concurrent match debugging.
- **Graceful shutdown**: On SIGTERM, stop accepting new `/mcp` requests, finish in-flight ones, flush logs, and persist state—matches PRD FR-015.
- **Cross-agent contract tests**: Add contract tests that instantiate minimal FastAPI clients to validate request/response shapes for each of the 18 methods.
- **Input fuzzing**: Add lightweight fuzz tests for envelope fields (invalid timestamps, missing auth) to harden validation.

## 10. References

- JSON-RPC 2.0 Spec: https://www.jsonrpc.org/specification
- Model Context Protocol: https://modelcontextprotocol.io/
- Even/Odd League PRD: PRD_EvenOddLeague.md
- System Config & Timeouts: SHARED/config/system.json
- Protocol Models: SHARED/league_sdk/protocol.py
