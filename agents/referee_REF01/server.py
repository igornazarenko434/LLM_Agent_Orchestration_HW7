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
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base import BaseAgent
from agents.referee_REF01.match_conductor import MatchConductor
from fastapi import Request
from fastapi.responses import JSONResponse

from league_sdk.config_loader import load_agents_config, load_json_file, load_system_config
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.method_aliases import translate_pdf_method_to_message_type
from league_sdk.protocol import (
    ErrorCode,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    RefereeRegisterRequest,
    RefereeRegisterResponse,
)
from league_sdk.repositories import MatchRepository
from league_sdk.retry import call_with_retry

AGENTS_CONFIG_PATH = "SHARED/config/agents/agents_config.json"
SYSTEM_CONFIG_PATH = "SHARED/config/system.json"
GAMES_REGISTRY_PATH = "SHARED/config/games/games_registry.json"


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
        """Initialize referee state, configs, and match conductor wiring.

        Args:
            agent_id: Referee agent identifier.
            league_id: League identifier for match context.
            host: Optional host override.
            port: Optional port override.
        """
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
        self.game_registry = load_json_file(GAMES_REGISTRY_PATH)
        self.supported_game_types = {g["game_type"] for g in self.game_registry.get("games", [])}
        self.allowed_senders = self._build_sender_index()

        # Get referee metadata from config
        self.agent_record = self._get_referee_record(agent_id)
        if self.agent_record and not port:
            self.port = self.agent_record.get("port", self.port)

        # State management
        self.auth_token: Optional[str] = None
        self.referee_id: Optional[str] = None
        self.state: str = "INIT"

        # P0/P1/P2: Registration tracking (correlation IDs, retry attempts, status)
        self.registration_attempts: int = 0
        self.registration_failures: int = 0
        self.last_registration_attempt: Optional[float] = None
        self.last_registration_error: Optional[str] = None

        # Match conductor (will be initialized after registration)
        self.match_conductor: Optional[MatchConductor] = None

        # Active matches tracking (conversation_id -> match_task)
        self.active_matches: Dict[str, asyncio.Task] = {}

        # Message queues for active matches (conversation_id -> queue)
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.match_repo = MatchRepository()

        self._register_mcp_route()

    def _get_referee_record(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get referee record from agents config."""
        for referee in self.agents_config.get("referees", []):
            if referee.get("agent_id") == agent_id:
                return referee
        return None

    def _build_sender_index(self) -> Dict[str, str]:
        senders: Dict[str, str] = {}
        lm = self.agents_config.get("league_manager", {})
        if lm:
            senders[f"league_manager:{lm.get('agent_id')}"] = "league_manager"
        for player in self.agents_config.get("players", []):
            senders[f"player:{player.get('agent_id')}"] = "player"
        return senders

    def _get_config_with_warning(
        self, config_dict: Dict[str, Any], key: str, default: Any, config_name: str
    ) -> Any:
        """
        Get config value with warning if missing (P2.1 best practice).

        Args:
            config_dict: Configuration dictionary to query
            key: Configuration key to retrieve
            default: Default value if key is missing
            config_name: Human-readable config name for warning message

        Returns:
            Configuration value or default
        """
        value = config_dict.get(key)
        if value is None:
            self.std_logger.warning(
                f"Config key '{key}' not found in {config_name}, using default: {default}. "
                f"Add '{key}' to config for explicit control."
            )
            return default
        return value

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

            # PDF COMPATIBILITY LAYER: Translate PDF-style method names to message types
            original_method = rpc_request.method
            rpc_request.method = translate_pdf_method_to_message_type(rpc_request.method)

            # Log translation if PDF-style method was used
            if original_method != rpc_request.method:
                self.std_logger.debug(
                    f"Translated PDF method '{original_method}' → '{rpc_request.method}'",
                    extra={
                        "pdf_method": original_method,
                        "message_type": rpc_request.method,
                        "compatibility_layer": True,
                    },
                )

            # Route to handler based on method
            if rpc_request.method == "START_MATCH":
                validation_error = self._validate_request(rpc_request, require_player_auth=False)
                if validation_error:
                    return validation_error
                return await self._handle_start_match(rpc_request)
            elif rpc_request.method in ["GAME_JOIN_ACK", "CHOOSE_PARITY_RESPONSE"]:
                validation_error = self._validate_request(rpc_request, require_player_auth=True)
                if validation_error:
                    return validation_error
                return await self._route_player_response(rpc_request)
            elif rpc_request.method == "get_match_state":
                validation_error = self._validate_request(rpc_request, require_player_auth=True)
                if validation_error:
                    return validation_error
                return self._handle_get_match_state(rpc_request)
            elif rpc_request.method == "get_registration_status":
                # P1: Debug tool for registration status
                return self._handle_get_registration_status(rpc_request)
            elif rpc_request.method == "manual_register":
                # P2: Manual registration debug tool
                return await self._handle_manual_register(rpc_request)
            else:
                return self._error_response(
                    rpc_request.id,
                    code=-32601,
                    message="Method not found",
                    error_code=ErrorCode.INVALID_ENDPOINT,
                    status=404,
                    payload=rpc_request.model_dump(),
                )

    async def _route_player_response(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Route player response to the appropriate match queue."""
        params = rpc_request.params
        conversation_id = params.get("conversation_id")
        sender = params.get("sender", "")

        if not sender.startswith("player:"):
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Invalid sender format",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=params,
            )
        if sender not in self.allowed_senders:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Sender not registered",
                error_code=ErrorCode.AGENT_NOT_REGISTERED,
                status=400,
                payload=params,
                extra_data={"sender": sender},
            )

        if not conversation_id:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Missing conversation_id",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=params,
            )

        queue = self.message_queues.get(conversation_id)
        if queue:
            await queue.put(rpc_request)
            # Return generic success, the match conductor will validate the content
            return JSONResponse(
                status_code=200,
                content=JSONRPCResponse(id=rpc_request.id, result={"status": "RECEIVED"}).model_dump(),
            )
        else:
            self.std_logger.warning(
                f"Received message for unknown/inactive conversation: {conversation_id}"
            )
            return self._error_response(
                rpc_request.id,
                code=-32000,
                message="Match not active or conversation unknown",
                error_code=ErrorCode.INVALID_GAME_STATE,
                status=404,
                payload=params,
            )

    def _handle_get_match_state(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """Return stored match state for debug tooling."""
        params = rpc_request.params
        match_id = params.get("match_id")
        if not match_id:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Missing match_id",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=rpc_request.model_dump(),
            )

        match_data = self.match_repo.load(match_id)
        rpc_response = JSONRPCResponse(
            id=rpc_request.id,
            result={
                "message_type": "get_match_state",
                "conversation_id": params.get("conversation_id"),
                "match": match_data,
            },
        )
        log_message_sent(self.std_logger, rpc_response.result)
        return JSONResponse(status_code=200, content=rpc_response.model_dump())

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
            log_message_received(self.std_logger, rpc_request.model_dump())

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

            # Create message queue for this match
            conversation_id = params["conversation_id"]
            match_queue: asyncio.Queue = asyncio.Queue()
            self.message_queues[conversation_id] = match_queue

            # Start match in background (Thread Safety: non-blocking)
            # Use a wrapper to clean up the queue when done
            async def run_match():
                try:
                    await self.match_conductor.conduct_match(
                        match_id=params["match_id"],
                        round_id=params["round_id"],
                        player_a_id=params["player_a_id"],
                        player_b_id=params["player_b_id"],
                        conversation_id=conversation_id,
                        message_queue=match_queue,
                    )
                finally:
                    # Cleanup queue
                    if conversation_id in self.message_queues:
                        del self.message_queues[conversation_id]
                    if conversation_id in self.active_matches:
                        del self.active_matches[conversation_id]

            match_task = asyncio.create_task(run_match())
            self.active_matches[conversation_id] = match_task

            # Return immediate acknowledgment (match continues in background)
            result = {
                "message_type": "START_MATCH_ACK",
                "conversation_id": conversation_id,
                "status": "MATCH_STARTED",
                "match_id": params["match_id"],
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
                "display_name": self._get_config_with_warning(
                    agent_record,
                    "display_name",
                    f"Referee {self.agent_id}",
                    f"agents_config referee {self.agent_id}",
                ),
                "version": self._get_config_with_warning(
                    agent_record, "version", "1.0.0", f"agents_config referee {self.agent_id}"
                ),
                "game_types": self._get_config_with_warning(
                    agent_record,
                    "game_types",
                    sorted(self.supported_game_types),
                    f"agents_config referee {self.agent_id}",
                ),
                "contact_endpoint": f"http://{self.host}:{self.port}/mcp",
                "max_concurrent_matches": self._get_config_with_warning(
                    agent_record, "max_concurrent_matches", 10, f"agents_config referee {self.agent_id}"
                ),
            }

            registration_request = RefereeRegisterRequest(
                sender=f"referee:{self.agent_id}",
                timestamp=self._timestamp(),
                conversation_id=self._conversation_id(),
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
                        "Match conductor initialized",
                        extra={
                            "event_type": "MATCH_CONDUCTOR_READY",
                            "referee_id": self.referee_id,
                            "league_id": self.league_id,
                        },
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

    async def send_deregistration_request(self) -> Dict[str, Any]:
        """
        Send REFEREE_DEREGISTER_REQUEST to League Manager (P0 fix).

        Clean shutdown: De-register from League Manager so it knows referee is unavailable.
        Uses call_with_retry for resilience.
        """
        if self.state not in ("REGISTERED", "ACTIVE"):
            self.std_logger.info(
                "Skipping de-registration - referee not registered", extra={"state": self.state}
            )
            return {"status": "SKIPPED", "reason": "Not registered"}

        correlation_id = f"dereg-{self.agent_id}-{uuid.uuid4().hex[:8]}"

        self.std_logger.info(
            "Initiating de-registration",
            extra={"correlation_id": correlation_id, "agent_id": self.agent_id, "state": self.state},
        )

        lm_config = self.agents_config.get("league_manager", {})
        lm_endpoint = lm_config.get("endpoint")
        if not lm_endpoint:
            return {"status": "FAILED", "reason": "League Manager endpoint not configured"}

        request_params = {
            "protocol": self.system_config.protocol_version,
            "message_type": "REFEREE_DEREGISTER_REQUEST",
            "sender": f"referee:{self.agent_id}",
            "timestamp": self._timestamp(),
            "conversation_id": correlation_id,
            "referee_id": self.referee_id or self.agent_id,
            "auth_token": self.auth_token,
        }

        try:
            response = await call_with_retry(
                endpoint=lm_endpoint,
                method="REFEREE_DEREGISTER_REQUEST",
                params=request_params,
                timeout=self.system_config.timeouts.generic_sec,
                logger=self.std_logger,
                circuit_breaker=self.circuit_breaker,
            )

            self._transition("INIT")
            self.auth_token = None
            self.referee_id = None

            self.std_logger.info(
                "De-registration successful",
                extra={"correlation_id": correlation_id, "response": response},
            )
            return response

        except Exception as e:
            log_error(
                self.std_logger,
                ErrorCode.INTERNAL_SERVER_ERROR,
                {
                    "message": "De-registration failed",
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return {"status": "FAILED", "reason": str(e), "correlation_id": correlation_id}

    async def register_with_retry(
        self, max_attempts: Optional[int] = None, correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register with League Manager with exponential backoff retry (P0 fix).

        Non-blocking registration that:
        - Uses retry_policy from system.json
        - Logs all attempts with correlation IDs (P2)
        - Handles all exceptions gracefully (P0)
        - Returns detailed status even on failure (P1)

        Args:
            max_attempts: Override config max_retries (for testing)
            correlation_id: Optional correlation ID for tracking

        Returns:
            Registration response with status and correlation_id
        """
        # P1: Check if already registered with valid token
        if self.state in ("REGISTERED", "ACTIVE") and self.auth_token:
            self.std_logger.info(
                "Already registered - skipping re-registration",
                extra={
                    "agent_id": self.agent_id,
                    "state": self.state,
                    "has_token": bool(self.auth_token),
                },
            )
            return {
                "status": "ALREADY_REGISTERED",
                "referee_id": self.referee_id or self.agent_id,
                "auth_token": self.auth_token,
            }

        # Use retry policy from config (no hardcoding!)
        max_attempts = max_attempts or self.system_config.retry_policy.max_retries + 1
        initial_delay = self.system_config.retry_policy.initial_delay_sec
        max_delay = self.system_config.retry_policy.max_delay_sec

        # P2: Generate correlation ID for tracking all retry attempts
        correlation_id = correlation_id or f"reg-{self.agent_id}-{uuid.uuid4().hex[:8]}"

        self.std_logger.info(
            "Starting registration with retry",
            extra={
                "correlation_id": correlation_id,
                "agent_id": self.agent_id,
                "max_attempts": max_attempts,
                "initial_delay_sec": initial_delay,
                "max_delay_sec": max_delay,
            },
        )

        delay = initial_delay

        for attempt in range(1, max_attempts + 1):
            self.registration_attempts += 1
            self.last_registration_attempt = time.time()

            self.std_logger.info(
                f"Registration attempt {attempt}/{max_attempts}",
                extra={
                    "correlation_id": correlation_id,
                    "attempt": attempt,
                    "total_attempts": self.registration_attempts,
                    "total_failures": self.registration_failures,
                },
            )

            try:
                success = await asyncio.wait_for(
                    self.register_with_league_manager(),
                    timeout=self.system_config.timeouts.registration_sec,
                )

                if success:
                    self.std_logger.info(
                        "Registration successful",
                        extra={
                            "correlation_id": correlation_id,
                            "attempt": attempt,
                            "referee_id": self.referee_id,
                            "auth_token_received": bool(self.auth_token),
                        },
                    )
                    return {
                        "status": "ACCEPTED",
                        "referee_id": self.referee_id,
                        "auth_token": self.auth_token,
                        "correlation_id": correlation_id,
                        "attempts": attempt,
                    }
                else:
                    self.registration_failures += 1
                    self.last_registration_error = "Registration rejected by League Manager"

                    log_error(
                        self.std_logger,
                        ErrorCode.AGENT_NOT_REGISTERED,
                        {
                            "message": f"Registration rejected (attempt {attempt}/{max_attempts})",
                            "correlation_id": correlation_id,
                            "will_retry": attempt < max_attempts,
                        },
                    )

            except asyncio.TimeoutError:
                self.registration_failures += 1
                self.last_registration_error = "Registration timeout"

                log_error(
                    self.std_logger,
                    ErrorCode.TIMEOUT_ERROR,
                    {
                        "message": f"Registration timeout (attempt {attempt}/{max_attempts})",
                        "correlation_id": correlation_id,
                        "timeout_sec": self.system_config.timeouts.registration_sec,
                        "will_retry": attempt < max_attempts,
                    },
                )

            except ConnectionRefusedError:
                self.registration_failures += 1
                self.last_registration_error = "League Manager unavailable"

                lm_endpoint = self.agents_config.get("league_manager", {}).get("endpoint", "unknown")
                log_error(
                    self.std_logger,
                    ErrorCode.SERVICE_UNAVAILABLE,
                    {
                        "message": f"League Manager unavailable (attempt {attempt}/{max_attempts})",
                        "correlation_id": correlation_id,
                        "endpoint": lm_endpoint,
                        "will_retry": attempt < max_attempts,
                    },
                )

            except Exception as e:
                self.registration_failures += 1
                self.last_registration_error = str(e)

                log_error(
                    self.std_logger,
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    {
                        "message": f"Registration error (attempt {attempt}/{max_attempts})",
                        "correlation_id": correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "will_retry": attempt < max_attempts,
                    },
                )

            # Exponential backoff (if not last attempt)
            if attempt < max_attempts:
                self.std_logger.debug(
                    f"Retrying in {delay:.1f}s...",
                    extra={"correlation_id": correlation_id, "delay_sec": delay},
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2.0, max_delay)

        # All attempts failed
        self.std_logger.warning(
            "Registration failed after all attempts",
            extra={
                "correlation_id": correlation_id,
                "total_attempts": max_attempts,
                "last_error": self.last_registration_error,
                "agent_state": "UNREGISTERED",
            },
        )

        return {
            "status": "FAILED",
            "reason": self.last_registration_error,
            "correlation_id": correlation_id,
            "attempts": max_attempts,
            "agent_id": self.agent_id,
        }

    def _handle_get_registration_status(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Debug tool: Get current registration status (P1 fix).

        Returns detailed registration state for debugging and monitoring.
        Uses protocol error codes and comprehensive logging.
        """
        try:
            params = rpc_request.params

            self.std_logger.info(
                "Registration status requested",
                extra={
                    "requester": params.get("sender"),
                    "current_state": self.state,
                    "registration_attempts": self.registration_attempts,
                },
            )

            result = {
                "message_type": "get_registration_status",
                "conversation_id": params.get("conversation_id"),
                "agent_id": self.agent_id,
                "referee_id": self.referee_id,
                "state": self.state,
                "registered": self.state in ("REGISTERED", "ACTIVE"),
                "has_auth_token": bool(self.auth_token),
                "registration_stats": {
                    "total_attempts": self.registration_attempts,
                    "total_failures": self.registration_failures,
                    "last_attempt_timestamp": self.last_registration_attempt,
                    "last_error": self.last_registration_error,
                },
                "league_id": self.league_id,
                "endpoint": f"http://{self.host}:{self.port}/mcp",
                "auth_token": self.auth_token,  # Return actual token for debugging
            }

            self.std_logger.debug(
                "Registration status retrieved successfully", extra={"result": result}
            )

            return JSONResponse(
                status_code=200, content=JSONRPCResponse(id=rpc_request.id, result=result).model_dump()
            )

        except Exception as e:
            # Use E015 INTERNAL_SERVER_ERROR per protocol
            log_error(
                self.std_logger,
                ErrorCode.INTERNAL_SERVER_ERROR,
                {
                    "message": "Failed to retrieve registration status",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            return self._error_response(
                rpc_request.id,
                code=-32603,
                message="Internal error retrieving registration status",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(e)},
            )

    async def _handle_manual_register(self, rpc_request: JSONRPCRequest) -> JSONResponse:
        """
        Debug tool: Manually trigger registration with retry (P2 fix).

        Allows operators to manually trigger registration for debugging or recovery.
        Useful when auto_register is disabled or failed.
        Uses protocol error codes and comprehensive logging.
        """
        try:
            params = rpc_request.params
            max_attempts = params.get("max_attempts", self.system_config.retry_policy.max_retries + 1)
            force = params.get("force", False)

            self.std_logger.info(
                "Manual registration requested",
                extra={
                    "requester": params.get("sender"),
                    "max_attempts": max_attempts,
                    "force": force,
                    "current_state": self.state,
                },
            )

            # Allow force re-registration even if already registered
            if force and self.state in ("REGISTERED", "ACTIVE"):
                self.std_logger.info(
                    "Force re-registration requested",
                    extra={"current_state": self.state, "has_token": bool(self.auth_token)},
                )
                self._transition("INIT")
                self.auth_token = None
                self.referee_id = None

            result_data = await self.register_with_retry(max_attempts=max_attempts)

            response_result = {
                "message_type": "manual_register",
                "conversation_id": params.get("conversation_id"),
                "registration_result": result_data,
                "current_state": self.state,
                "registered": self.state in ("REGISTERED", "ACTIVE"),
            }

            self.std_logger.info(
                "Manual registration completed",
                extra={
                    "success": result_data.get("status") == "ACCEPTED",
                    "final_state": self.state,
                    "attempts": result_data.get("attempts"),
                },
            )

            return JSONResponse(
                status_code=200,
                content=JSONRPCResponse(id=rpc_request.id, result=response_result).model_dump(),
            )

        except Exception as e:
            # Use E015 INTERNAL_SERVER_ERROR per protocol
            log_error(
                self.std_logger,
                ErrorCode.INTERNAL_SERVER_ERROR,
                {
                    "message": "Manual registration failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            return self._error_response(
                rpc_request.id,
                code=-32603,
                message="Internal error during manual registration",
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                status=500,
                payload=rpc_request.model_dump(),
                extra_data={"error": str(e)},
            )

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
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _validate_request(
        self, rpc_request: JSONRPCRequest, require_player_auth: bool
    ) -> Optional[JSONResponse]:
        """Validate protocol, sender, auth token, and game_type when present."""
        params = rpc_request.params

        if params.get("protocol") and params.get("protocol") != self.system_config.protocol_version:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Protocol mismatch",
                error_code=ErrorCode.PROTOCOL_VERSION_MISMATCH,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"supported_protocols": [self.system_config.protocol_version]},
            )

        sender = params.get("sender")
        if not sender:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Missing sender",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=rpc_request.model_dump(),
            )
        if sender not in self.allowed_senders:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Sender not registered",
                error_code=ErrorCode.AGENT_NOT_REGISTERED,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"sender": sender},
            )

        if require_player_auth and self.system_config.security.require_auth:
            auth_token = params.get("auth_token")
            if not auth_token:
                return self._error_response(
                    rpc_request.id,
                    code=-32001,
                    message="Missing auth token",
                    error_code=ErrorCode.AUTH_TOKEN_INVALID,
                    status=401,
                    payload=rpc_request.model_dump(),
                )

        game_type = params.get("game_type")
        if game_type and game_type not in self.supported_game_types:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Unsupported game_type",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"game_type": game_type, "supported": list(self.supported_game_types)},
            )

        return None

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
        error_code: ErrorCode | str,
        status: int,
        payload: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Build JSON-RPC error response."""
        # ErrorCode is a class of string constants, so use the value directly
        code_val = error_code if isinstance(error_code, str) else str(error_code)
        error_data = {"error_code": code_val, "payload": payload}
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
        """Log structured errors."""
        details = error.data if isinstance(error.data, dict) else {"details": error.data}
        details.update(
            {
                "message": error.message,
                "jsonrpc_code": error.code,
                "method": payload.get("method"),
            }
        )
        log_error(self.std_logger, details.get("error_code", ErrorCode.INTERNAL_SERVER_ERROR), details)
