"""
Referee agent MCP server (Mission 7.5-7.8).

Implements complete referee with:
- Match conductor (M7.5)
- Timeout enforcement (M7.6)
- Even/Odd game logic (M7.7)
- Registration with League Manager (M7.8)
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from league_sdk.config_loader import load_agents_config, load_json_file, load_system_config
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.protocol import (
    ErrorCode,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    RefereeRegisterRequest,
    RefereeRegisterResponse,
)
from league_sdk.retry import call_with_retry

from agents.base import BaseAgent
from agents.referee_REF01.match_conductor import MatchConductor

AGENTS_CONFIG_PATH = "SHARED/config/agents/agents_config.json"
SYSTEM_CONFIG_PATH = "SHARED/config/system.json"


class RefereeAgent(BaseAgent):
    """
    Referee MCP server with JSON-RPC dispatch and match conductor.

    Thread Safety (CRITICAL):
    - All endpoints async (non-blocking)
    - Can handle 50+ concurrent matches via MatchConductor
    - Each match isolated by unique conversation_id
    """

    def __init__(
        self,
        agent_id: str = "REF01",
        league_id: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type="referee",
            league_id=league_id or "league_2025_even_odd",
            host=host,
            port=port,
        )

        # Load configs (no hardcoding!)
        self.agents_config = load_agents_config(AGENTS_CONFIG_PATH)
        self.system_config = load_system_config(SYSTEM_CONFIG_PATH)

        # Get referee metadata from config
        self.agent_record = self._get_referee_record(agent_id)
        if self.agent_record and not port:
            self.port = self.agent_record.get("port", self.port)

        # State management
        self.auth_token: Optional[str] = None
        self.referee_id: Optional[str] = None
        self.state: str = "INIT"

        # Match conductor (will be initialized after registration)
        self.match_conductor: Optional[MatchConductor] = None

        # Active matches tracking (conversation_id -> match_task)
        self.active_matches: Dict[str, asyncio.Task] = {}

        self._register_mcp_route()

    def _get_referee_record(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get referee record from agents config."""
        for referee in self.agents_config.get("referees", []):
            if referee.get("agent_id") == agent_id:
                return referee
        return None

    def _register_mcp_route(self) -> None:
        """
        Attach /mcp JSON-RPC endpoint.

        Thread Safety: async endpoint, handles concurrent requests safely.
        """

        @self.app.post("/mcp")
        async def mcp(request: Request):
            body = await request.json()
            rpc_request = self._parse_rpc(body)
            if isinstance(rpc_request, JSONResponse):
                return rpc_request

            # Route to handler based on method
            if rpc_request.method == "START_MATCH":
                return await self._handle_start_match(rpc_request)
            else:
                return self._error_response(
                    rpc_request.id,
                    code=-32601,
                    message="Method not found",
                    error_code=ErrorCode.INVALID_ENDPOINT,
                    status=404,
                    payload=rpc_request.model_dump(),
                )

    async def _handle_start_match(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Handle START_MATCH request to initiate a match.

        Thread Safety: Creates async task for match, doesn't block.

        Expected params:
        {
            "match_id": "R1M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
            "conversation_id": "conv-r1m1-001"
        }
        """
        try:
            params = rpc_request.params
            log_message_received(self.std_logger, params)

            # Validate required fields
            required_fields = ["match_id", "round_id", "player_a_id", "player_b_id", "conversation_id"]
            for field in required_fields:
                if field not in params:
                    return self._error_response(
                        rpc_request.id,
                        code=-32602,
                        message=f"Missing required parameter: {field}",
                        error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                        status=400,
                        payload=params,
                    )

            if not self.match_conductor:
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Referee not registered - cannot conduct matches",
                    error_code=ErrorCode.AGENT_NOT_REGISTERED,
                    status=403,
                    payload=params,
                )

            # Start match in background (Thread Safety: non-blocking)
            conversation_id = params["conversation_id"]
            match_task = asyncio.create_task(
                self.match_conductor.conduct_match(
                    match_id=params["match_id"],
                    round_id=params["round_id"],
                    player_a_id=params["player_a_id"],
                    player_b_id=params["player_b_id"],
                    conversation_id=conversation_id,
                )
            )
            self.active_matches[conversation_id] = match_task

            # Return immediate acknowledgment (match continues in background)
            result = {
                "status": "MATCH_STARTED",
                "match_id": params["match_id"],
                "conversation_id": conversation_id,
            }
            rpc_response = JSONRPCResponse(id=rpc_request.id, result=result)
            log_message_sent(self.std_logger, result)
            return JSONResponse(status_code=200, content=rpc_response.model_dump())

        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Server error",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(exc)},
            )

    async def register_with_league_manager(self) -> bool:
        """
        Register referee with League Manager (Mission 7.8).

        Uses 10s timeout from system.json config.
        Retries on failure with exponential backoff.

        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Get League Manager endpoint from config (no hardcoding!)
            lm_config = self.agents_config.get("league_manager", {})
            lm_endpoint = lm_config.get("endpoint")
            if not lm_endpoint:
                self.std_logger.error("League Manager endpoint not found in agents config")
                return False

            # Get registration timeout from system config
            timeout = self.system_config.timeouts.registration_sec

            # Build registration request per protocol
            # Type guard for agent_record
            if not self.agent_record:
                raise ValueError("agent_record must be loaded from config")

            agent_record = self.agent_record  # Narrow type for mypy

            referee_meta = {
                "display_name": agent_record.get("display_name", f"Referee {self.agent_id}"),
                "version": agent_record.get("version", "1.0.0"),
                "game_types": agent_record.get("game_types", ["even_odd"]),
                "contact_endpoint": f"http://{self.host}:{self.port}/mcp",
                "max_concurrent_matches": agent_record.get("max_concurrent_matches", 10),
            }

            registration_request = RefereeRegisterRequest(
                sender=f"referee:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=f"reg-{self.agent_id}",
                referee_meta=referee_meta,
            )

            self.std_logger.info(f"Registering with League Manager at {lm_endpoint}")
            log_message_sent(self.std_logger, registration_request.model_dump())

            # Send registration request with retry (M7.8: retry on failure)
            # Using async call_with_retry with new signature (M7.9.1)
            response = await call_with_retry(
                endpoint=lm_endpoint,
                method="REFEREE_REGISTER_REQUEST",
                params=registration_request.model_dump(),
                timeout=timeout,
                logger=self.std_logger,
            )

            log_message_received(self.std_logger, response)

            # Parse response
            if "result" in response:
                result = response["result"]
                if result.get("status") == "ACCEPTED":
                    self.referee_id = result.get("referee_id")
                    self.auth_token = result.get("auth_token")
                    self._transition("REGISTERED")

                    # Initialize match conductor now that we're registered
                    # Type guard: ensure credentials are set
                    if not self.referee_id or not self.auth_token or not self.league_id:
                        raise ValueError("Credentials must be set after registration")

                    self.match_conductor = MatchConductor(
                        referee_id=self.referee_id,
                        auth_token=self.auth_token,
                        league_id=self.league_id,
                        std_logger=self.std_logger,
                    )

                    self.std_logger.info(
                        f"Successfully registered as {self.referee_id}",
                        extra={
                            "referee_id": self.referee_id,
                            "auth_token_length": len(self.auth_token) if self.auth_token else 0,
                        },
                    )
                    return True
                else:
                    reason = result.get("reason", "Unknown reason")
                    self.std_logger.error(f"Registration rejected: {reason}")
                    return False
            else:
                error = response.get("error", {})
                self.std_logger.error(f"Registration failed: {error.get('message', 'Unknown error')}")
                return False

        except Exception as exc:
            self.std_logger.error(f"Registration error: {exc}", exc_info=True)
            return False

    def _transition(self, new_state: str) -> None:
        """Transition referee to new state."""
        old_state = self.state
        self.state = new_state
        self.std_logger.info(
            f"State transition: {old_state} → {new_state}",
            extra={"old_state": old_state, "new_state": new_state},
        )

    def _timestamp(self) -> str:
        """Generate ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _parse_rpc(self, body: Dict[str, Any]) -> JSONRPCRequest | JSONResponse:
        """Parse JSON-RPC request from body."""
        try:
            return JSONRPCRequest(**body)
        except Exception as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request",
                        "data": {"error": str(exc)},
                    },
                    "id": body.get("id"),
                },
            )

    def _error_response(
        self,
        request_id: Any,
        code: int,
        message: str,
        error_code: ErrorCode,
        status: int,
        payload: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Build JSON-RPC error response."""
        error_data = {"error_code": error_code.value, "payload": payload}
        if extra_data:
            error_data.update(extra_data)

        error = JSONRPCError(code=code, message=message, data=error_data)
        self._log_error(error, payload)

        return JSONResponse(
            status_code=status,
            content={
                "jsonrpc": "2.0",
                "error": error.model_dump(),
                "id": request_id,
            },
        )

    def _log_error(self, error: JSONRPCError, payload: Dict[str, Any]) -> None:
        """Helper to log structured errors."""
        details = error.data if isinstance(error.data, dict) else {"details": error.data}
        details.update(
            {
                "message": error.message,
                "jsonrpc_code": error.code,
                "method": payload.get("method"),
            }
        )
        log_error(self.std_logger, details.get("error_code", ErrorCode.INTERNAL_SERVER_ERROR), details)
