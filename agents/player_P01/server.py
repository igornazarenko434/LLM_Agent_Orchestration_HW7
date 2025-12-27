"""
Player agent MCP server setup (Mission 7.2).

Exposes /mcp JSON-RPC 2.0 endpoint with dispatch to required tools:
- GAME_INVITATION  -> GAME_JOIN_ACK
- CHOOSE_PARITY_CALL -> CHOOSE_PARITY_RESPONSE
- MATCH_RESULT_REPORT -> ack/log
"""

from __future__ import annotations

import asyncio
import gzip
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from league_sdk.cleanup import get_retention_config
from league_sdk.config_loader import load_agents_config, load_json_file
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.method_aliases import translate_pdf_method_to_message_type
from league_sdk.protocol import (
    ChooseParityCall,
    ErrorCode,
    GameError,
    GameInvitation,
    GameOver,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    LeagueRegisterRequest,
    LeagueRegisterResponse,
    MatchResultReport,
)
from league_sdk.repositories import PlayerHistoryRepository
from league_sdk.retry import call_with_retry

from agents.base import BaseAgent
from agents.player_P01 import handlers

AGENTS_CONFIG_PATH = "SHARED/config/agents/agents_config.json"
GAMES_REGISTRY_PATH = "SHARED/config/games/games_registry.json"


class PlayerAgent(BaseAgent):
    """Player MCP server with JSON-RPC dispatch."""

    def __init__(
        self,
        agent_id: str = "P01",
        league_id: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        super().__init__(
            agent_id=agent_id,
            agent_type="player",
            league_id=league_id,
            host=host,
            port=port,
        )
        self.agents_config = load_agents_config(AGENTS_CONFIG_PATH)
        self.game_registry = load_json_file(GAMES_REGISTRY_PATH)
        self.auth_token: Optional[str] = None

        self.agent_record = self._get_player_record(agent_id)
        if self.agent_record and not port:
            self.port = self.agent_record.get("port", self.port)

        self.allowed_senders = self._build_sender_index()
        self.supported_game_types = {g["game_type"] for g in self.game_registry.get("games", [])}
        self.history_repo = PlayerHistoryRepository(self.agent_id)
        self.state: str = "INIT"

        # P0/P1/P2: Registration tracking (correlation IDs, retry attempts, status)
        self.registration_attempts: int = 0
        self.registration_failures: int = 0
        self.last_registration_attempt: Optional[float] = None
        self.last_registration_error: Optional[str] = None

        self._method_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "ROUND_ANNOUNCEMENT": lambda params: self._handle_round_announcement(params),
            "GAME_INVITATION": lambda params: handlers.handle_game_invitation(
                self.agent_id, params, self.auth_token
            ),
            "CHOOSE_PARITY_CALL": lambda params: handlers.handle_choose_parity(
                self.agent_id,
                params,
                self.auth_token,
                self._valid_choices_for_game(params.get("game_type")),
            ),
            "GAME_OVER": lambda params: handlers.handle_game_over(
                params, self.history_repo, self.auth_token, self.agent_id
            ),
            "MATCH_RESULT_REPORT": lambda params: handlers.handle_match_result(
                params, self.history_repo, self.auth_token, self.agent_id
            ),
            "GAME_ERROR": lambda params: self._handle_game_error(params),
            "LEAGUE_STANDINGS_UPDATE": lambda params: self._handle_standings_update(params),
            "ROUND_COMPLETED": lambda params: self._handle_round_completed(params),
            "LEAGUE_COMPLETED": lambda params: self._handle_league_completed(params),
            "get_player_state": self._handle_get_player_state,
            "get_registration_status": self._handle_get_registration_status,  # P1: Debug tool
            "manual_register": self._handle_manual_register,  # type: ignore[dict-item]
        }
        self._register_mcp_route()

    def _get_player_record(self, agent_id: str) -> Optional[Dict[str, Any]]:
        for player in self.agents_config.get("players", []):
            if player.get("agent_id") == agent_id:
                return player
        return None

    def _build_sender_index(self) -> Dict[str, str]:
        senders: Dict[str, str] = {}
        lm = self.agents_config.get("league_manager", {})
        if lm:
            senders[f"league_manager:{lm.get('agent_id')}"] = "league_manager"
        for ref in self.agents_config.get("referees", []):
            senders[f"referee:{ref.get('agent_id')}"] = "referee"
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

    def _valid_choices_for_game(self, game_type: Optional[str]) -> list[str]:
        """Get valid choices for a game from the registry."""
        if not game_type:
            return ["even", "odd"]

        for game in self.game_registry.get("games", []):
            if game.get("game_type") == game_type:
                config = game.get("game_specific_config", {})
                choices = config.get("valid_choices", [])
                return choices if choices else ["even", "odd"]

        return ["even", "odd"]

    async def cleanup_player_data(self) -> None:
        """Cleanup player data on unregister/shutdown."""
        config = get_retention_config()
        if not config.get("archive_enabled", True):
            return

        # Archive player history before shutdown
        history_file = Path(f"SHARED/data/players/{self.agent_id}/history.json")
        archive_path = Path(config.get("archive_path", "SHARED/archive"))
        archive_file = archive_path / "players" / self.agent_id / "history_shutdown.json.gz"

        if history_file.exists():
            archive_file.parent.mkdir(parents=True, exist_ok=True)
            with open(history_file, "rb") as f_in:
                with gzip.open(archive_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            self.logger.info(f"Player data archived to {archive_file}")

    def shutdown(self) -> None:
        """Cleanup and shutdown player agent."""
        asyncio.run(self.cleanup_player_data())
        self._transition("SHUTDOWN")
        self.stop()

    def _register_mcp_route(self) -> None:
        """Attach /mcp JSON-RPC endpoint to the FastAPI app."""

        @self.app.post("/mcp")
        async def mcp(request: Request):
            body = await request.json()
            rpc_request = self._parse_rpc(body)
            if isinstance(rpc_request, JSONResponse):
                return rpc_request

            # PDF COMPATIBILITY LAYER: Translate PDF-style method names to message types
            # Enables both 'handle_game_invitation' (PDF) and 'GAME_INVITATION' (ours)
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

            validation_error = self._validate_params(rpc_request)
            if validation_error:
                return validation_error

            handler = self._method_map.get(rpc_request.method)
            if not handler:
                return self._error_response(
                    rpc_request.id,
                    code=-32601,
                    message="Method not found",
                    error_code=ErrorCode.INVALID_ENDPOINT,
                    status=404,
                    payload=rpc_request.model_dump(),
                )

            try:
                log_message_received(self.std_logger, rpc_request.model_dump())
                timeout = self._timeout_for_method(rpc_request.method)
                result = await asyncio.wait_for(
                    self._execute_handler(handler, rpc_request.params), timeout=timeout
                )
                rpc_response = JSONRPCResponse(id=rpc_request.id, result=result)
                log_message_sent(self.std_logger, result)
                return JSONResponse(status_code=200, content=rpc_response.model_dump())
            except (TimeoutError, asyncio.TimeoutError) as exc:  # pragma: no cover - defensive
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Timeout",
                    error_code=ErrorCode.TIMEOUT_ERROR,
                    status=504,
                    payload=rpc_request.model_dump(),
                    extra_data={"error": str(exc), "method": rpc_request.method},
                )
            except Exception as exc:  # pragma: no cover - defensive
                return self._error_response(
                    rpc_request.id,
                    code=-32000,
                    message="Server error",
                    error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                    status=500,
                    payload=rpc_request.model_dump(),
                    extra_data={"error": str(exc), "method": rpc_request.method},
                )

    def _log_error(self, error: JSONRPCError, payload: Dict[str, Any]) -> None:
        """Helper to log structured errors."""
        details = error.data if isinstance(error.data, dict) else {"details": error.data}
        details.update(
            {
                "message": error.message,
                "jsonrpc_code": error.code,
                "message_type": payload.get("method"),
                "conversation_id": payload.get("params", {}).get("conversation_id"),
            }
        )
        log_error(self.std_logger, details.get("error_code", ErrorCode.INTERNAL_SERVER_ERROR), details)

    def _handle_get_player_state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return player history and stats for debug tooling."""
        history = self.history_repo.load()
        return {
            "message_type": "get_player_state",
            "conversation_id": params.get("conversation_id"),
            "player_id": self.agent_id,
            "history": history.get("matches", []),
            "stats": history.get("stats", {}),
            "last_updated": history.get("last_updated"),
        }

    def _handle_round_announcement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle ROUND_ANNOUNCEMENT from League Manager.

        This is informational - player learns which matches are scheduled.
        No action required, just acknowledge receipt.
        """
        round_id = params.get("round_id")
        matches = params.get("matches", [])

        self.std_logger.info(
            f"Round {round_id} announced with {len(matches)} matches",
            extra={"round_id": round_id, "matches": matches, "player_id": self.agent_id},
        )

        return {
            "message_type": "ROUND_ANNOUNCEMENT",
            "conversation_id": params.get("conversation_id"),
            "sender": f"player:{self.agent_id}",
            "status": "acknowledged",
            "player_id": self.agent_id,
            "round_id": round_id,
        }

    def _handle_standings_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle LEAGUE_STANDINGS_UPDATE from League Manager.

        Informational message about current league standings.
        """
        round_id = params.get("round_id")
        standings = params.get("standings", [])

        self.std_logger.info(
            f"Standings update after round {round_id}",
            extra={"round_id": round_id, "standings": standings, "player_id": self.agent_id},
        )

        return {
            "message_type": "LEAGUE_STANDINGS_UPDATE",
            "conversation_id": params.get("conversation_id"),
            "sender": f"player:{self.agent_id}",
            "status": "acknowledged",
            "player_id": self.agent_id,
        }

    def _handle_round_completed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle ROUND_COMPLETED from League Manager.

        Informational message that a round has finished.
        """
        round_id = params.get("round_id")

        self.std_logger.info(
            f"Round {round_id} completed", extra={"round_id": round_id, "player_id": self.agent_id}
        )

        return {
            "message_type": "ROUND_COMPLETED",
            "conversation_id": params.get("conversation_id"),
            "sender": f"player:{self.agent_id}",
            "status": "acknowledged",
            "player_id": self.agent_id,
            "round_id": round_id,
        }

    def _handle_league_completed(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle LEAGUE_COMPLETED from League Manager.

        Final message with league results and champion.
        """
        champion = params.get("champion")
        final_standings = params.get("final_standings", [])

        self.std_logger.info(
            f"League completed! Champion: {champion}",
            extra={
                "champion": champion,
                "final_standings": final_standings,
                "player_id": self.agent_id,
            },
        )

        return {
            "message_type": "LEAGUE_COMPLETED",
            "conversation_id": params.get("conversation_id"),
            "sender": f"player:{self.agent_id}",
            "status": "acknowledged",
            "player_id": self.agent_id,
            "champion": champion,
        }

    def _error_response(
        self,
        request_id: int | str,
        code: int,
        message: str,
        error_code: str,
        status: int,
        payload: Dict[str, Any],
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        data = {"error_code": error_code, **(extra_data or {})}
        error = JSONRPCError(code=code, message=message, data=data)
        self._log_error(error=error, payload=payload)
        return JSONResponse(
            status_code=status,
            content=JSONRPCResponse(id=request_id, error=error).model_dump(),
        )

    def _parse_rpc(self, body: Dict[str, Any]) -> JSONRPCRequest | JSONResponse:
        try:
            return JSONRPCRequest(**body)
        except Exception as exc:
            error = JSONRPCError(
                code=-32600,
                message="Invalid Request",
                data={"details": str(exc), "error_code": ErrorCode.INVALID_MESSAGE_FORMAT},
            )
            self._log_error(error=error, payload=body)
            return JSONResponse(
                status_code=400,
                content=JSONRPCResponse(id=body.get("id", 1), error=error).model_dump(),
            )

    def _validate_params(self, rpc_request: JSONRPCRequest) -> Optional[JSONResponse]:
        params = rpc_request.params
        if params.get("protocol") != self.config.protocol_version:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Protocol mismatch",
                error_code=ErrorCode.PROTOCOL_VERSION_MISMATCH,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"supported_protocols": [self.config.protocol_version]},
            )

        if rpc_request.method == "get_player_state":
            sender = params.get("sender")
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
            if self.config.security.require_auth:
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
            return None

        try:
            if rpc_request.method == "GAME_INVITATION":
                GameInvitation(**rpc_request.params)
            elif rpc_request.method == "CHOOSE_PARITY_CALL":
                ChooseParityCall(**rpc_request.params)
            elif rpc_request.method == "GAME_OVER":
                GameOver(**rpc_request.params)
            elif rpc_request.method == "MATCH_RESULT_REPORT":
                MatchResultReport(**rpc_request.params)
            elif rpc_request.method == "GAME_ERROR":
                GameError(**rpc_request.params)
        except Exception as exc:
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Invalid params",
                error_code=ErrorCode.INVALID_MESSAGE_FORMAT,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"details": str(exc)},
            )

        sender = params.get("sender")
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

        auth_token = params.get("auth_token")

        # DEBUG: Log exact auth_token value received
        self.std_logger.info(
            f"Auth token validation for {rpc_request.method}",
            extra={
                "method": rpc_request.method,
                "auth_token_in_params": "auth_token" in params,
                "auth_token_value": repr(auth_token),
                "auth_token_length": len(auth_token) if auth_token else 0,
                "require_auth": self.config.security.require_auth,
            },
        )

        if self.config.security.require_auth and not auth_token:
            return self._error_response(
                rpc_request.id,
                code=-32001,
                message="Missing auth token",
                error_code=ErrorCode.AUTH_TOKEN_INVALID,
                status=401,
                payload=rpc_request.model_dump(),
            )
        # stash for responses
        self.auth_token = auth_token
        return None

    def _handle_game_error(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GAME_ERROR messages from referee (informational)."""
        game_error = GameError(**params)
        self.std_logger.warning(
            "Game error received",
            extra={
                "match_id": game_error.match_id,
                "error_code": game_error.error_code,
                "error_description": game_error.error_description,
                "affected_player": game_error.affected_player,
                "action_required": game_error.action_required,
                "conversation_id": game_error.conversation_id,
            },
        )
        return {
            "message_type": "GAME_ERROR",
            "conversation_id": game_error.conversation_id,
            "sender": f"player:{self.agent_id}",
            "status": "acknowledged",
            "match_id": game_error.match_id,
            "player_id": self.agent_id,
        }

    def registration_endpoint(self) -> str:
        lm_config = self.agents_config.get("league_manager", {})
        endpoint = lm_config.get("endpoint")
        if endpoint:
            return endpoint

        host = self.config.network.host
        port = self.config.network.league_manager_port
        return f"http://{host}:{port}/mcp"

    async def send_registration_request(self) -> Dict[str, Any]:
        """Send LEAGUE_REGISTER_REQUEST to League Manager with retry policy (async)."""
        self._transition("REGISTERING")
        conversation_id = self._conversation_id()
        player_meta = {
            "display_name": (
                self._get_config_with_warning(
                    self.agent_record,
                    "display_name",
                    self.agent_id,
                    f"agents_config player {self.agent_id}",
                )
                if self.agent_record
                else self.agent_id
            ),
            "version": (
                self._get_config_with_warning(
                    self.agent_record, "version", "1.0.0", f"agents_config player {self.agent_id}"
                )
                if self.agent_record
                else "1.0.0"
            ),
            "game_types": (
                self._get_config_with_warning(
                    self.agent_record,
                    "game_types",
                    sorted(self.supported_game_types),
                    f"agents_config player {self.agent_id}",
                )
                if self.agent_record
                else sorted(self.supported_game_types)
            ),
            "contact_endpoint": f"http://{self.host}:{self.port}/mcp",
        }
        request = LeagueRegisterRequest(
            sender=f"player:{self.agent_id}",
            timestamp=self._utc_timestamp(),
            conversation_id=conversation_id,
            protocol=self.config.protocol_version,
            player_meta=player_meta,
        )
        payload = request.model_dump()
        response = await call_with_retry(
            endpoint=self.registration_endpoint(),
            method=payload["message_type"],
            params=payload,
            timeout=self.config.network.request_timeout_sec,
            logger=self.std_logger,
            circuit_breaker=self.circuit_breaker,
        )
        return self.handle_registration_response(response)

    def handle_registration_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and persist registration response."""
        # Check if error is not just present but also not None (JSON-RPC may include error: null)
        if response.get("error"):
            self._transition("INIT")
            return response

        # Extract result from JSON-RPC response format
        result = response.get("result", response)

        try:
            reg = LeagueRegisterResponse(**result)
        except Exception as exc:
            self._transition("INIT")
            return {
                "error": {
                    "error_code": ErrorCode.INVALID_MESSAGE_FORMAT,
                    "error_description": str(exc),
                }
            }

        if reg.status != "ACCEPTED":
            self._transition("INIT")
            return result  # Return extracted result, not JSON-RPC wrapper

        # Store player_id and optional auth_token
        self.agent_id = reg.player_id
        self.sender = f"player:{self.agent_id}"
        if hasattr(reg, "auth_token"):
            self.auth_token = getattr(reg, "auth_token")

        self._transition("REGISTERED", conversation_id=getattr(reg, "conversation_id", None))
        self._transition("ACTIVE", conversation_id=getattr(reg, "conversation_id", None))
        return result  # Return extracted result so retry logic can find "status" field

    async def send_deregistration_request(self) -> Dict[str, Any]:
        """
        Send LEAGUE_DEREGISTER_REQUEST to League Manager (P0 fix).

        Clean shutdown: De-register from League Manager so it knows agent is unavailable.
        Uses call_with_retry for resilience.
        """
        if self.state not in ("REGISTERED", "ACTIVE"):
            self.std_logger.info(
                "Skipping de-registration - agent not registered", extra={"state": self.state}
            )
            return {"status": "SKIPPED", "reason": "Not registered"}

        correlation_id = f"dereg-{self.agent_id}-{uuid.uuid4().hex[:8]}"

        self.std_logger.info(
            "Initiating de-registration",
            extra={"correlation_id": correlation_id, "agent_id": self.agent_id, "state": self.state},
        )

        request_params = {
            "protocol": self.config.protocol_version,
            "message_type": "LEAGUE_DEREGISTER_REQUEST",
            "sender": f"player:{self.agent_id}",
            "timestamp": self._utc_timestamp(),
            "conversation_id": correlation_id,
            "player_id": self.agent_id,
            "auth_token": self.auth_token,
        }

        try:
            response = await call_with_retry(
                endpoint=self.registration_endpoint(),
                method="LEAGUE_DEREGISTER_REQUEST",
                params=request_params,
                timeout=self.config.timeouts.generic_sec,
                logger=self.std_logger,
                circuit_breaker=self.circuit_breaker,
            )

            self._transition("INIT")
            self.auth_token = None

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
                "player_id": self.agent_id,
                "auth_token": self.auth_token,
            }

        # Use retry policy from config (no hardcoding!)
        max_attempts = max_attempts or self.config.retry_policy.max_retries + 1
        initial_delay = self.config.retry_policy.initial_delay_sec
        max_delay = self.config.retry_policy.max_delay_sec

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
                response = await asyncio.wait_for(
                    self.send_registration_request(), timeout=self.config.timeouts.registration_sec
                )

                # Check if registration succeeded
                if response.get("status") == "ACCEPTED":
                    self.std_logger.info(
                        "Registration successful",
                        extra={
                            "correlation_id": correlation_id,
                            "attempt": attempt,
                            "player_id": self.agent_id,
                            "auth_token_received": bool(response.get("auth_token")),
                        },
                    )
                    return {**response, "correlation_id": correlation_id, "attempts": attempt}

                # Check if error is DUPLICATE_REGISTRATION (E017) - means already registered!
                error_data = response.get("error", {}).get("data", {})
                error_code = error_data.get("error_code", "")
                if error_code == ErrorCode.DUPLICATE_REGISTRATION or error_code == "E017":
                    # Already registered! Check if we have auth_token from earlier attempt
                    if self.auth_token:
                        self.std_logger.info(
                            "Already registered (409 Conflict) - using existing auth_token",
                            extra={
                                "correlation_id": correlation_id,
                                "attempt": attempt,
                                "player_id": self.agent_id,
                                "state": self.state,
                            },
                        )
                        return {
                            "status": "ACCEPTED",
                            "player_id": self.agent_id,
                            "auth_token": self.auth_token,
                            "correlation_id": correlation_id,
                            "attempts": attempt,
                            "note": "Already registered (409 Conflict)",
                        }
                    # If no auth_token yet, this is a real error - continue to retry logic below

                # Registration rejected for other reasons (E013, etc.)
                self.registration_failures += 1
                self.last_registration_error = response.get("error", {}).get(
                    "error_description", "Unknown"
                )

                log_error(
                    self.std_logger,
                    ErrorCode.AGENT_NOT_REGISTERED,
                    {
                        "message": f"Registration rejected (attempt {attempt}/{max_attempts})",
                        "correlation_id": correlation_id,
                        "response": response,
                        "error_code": error_code,
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
                        "timeout_sec": self.config.timeouts.registration_sec,
                        "will_retry": attempt < max_attempts,
                    },
                )

            except ConnectionRefusedError:
                self.registration_failures += 1
                self.last_registration_error = "League Manager unavailable"

                log_error(
                    self.std_logger,
                    ErrorCode.SERVICE_UNAVAILABLE,
                    {
                        "message": f"League Manager unavailable (attempt {attempt}/{max_attempts})",
                        "correlation_id": correlation_id,
                        "endpoint": self.registration_endpoint(),
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
                delay = min(delay * 2.0, max_delay)  # Exponential backoff with cap

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

    def _handle_get_registration_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Debug tool: Get current registration status (P1 fix).

        Returns detailed registration state for debugging and monitoring.
        Uses protocol error codes and comprehensive logging.
        """
        try:
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

            return result

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
            raise

    async def _handle_manual_register(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Debug tool: Manually trigger registration with retry (P2 fix).

        Allows operators to manually trigger registration for debugging or recovery.
        Useful when auto_register is disabled or failed.
        Uses protocol error codes and comprehensive logging.
        """
        try:
            max_attempts = params.get("max_attempts", self.config.retry_policy.max_retries + 1)
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

            result = await self.register_with_retry(max_attempts=max_attempts)

            response = {
                "message_type": "manual_register",
                "conversation_id": params.get("conversation_id"),
                "registration_result": result,
                "current_state": self.state,
                "registered": self.state in ("REGISTERED", "ACTIVE"),
            }

            self.std_logger.info(
                "Manual registration completed",
                extra={
                    "success": result.get("status") == "ACCEPTED",
                    "final_state": self.state,
                    "attempts": result.get("attempts"),
                },
            )

            return response

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
            raise

    def _transition(self, new_state: str, conversation_id: Optional[str] = None) -> None:
        """Log and update state machine."""
        prev = self.state
        self.state = new_state
        self.std_logger.info(
            "State transition",
            extra={
                "event_type": "STATE_TRANSITION",
                "from": prev,
                "to": new_state,
                "conversation_id": conversation_id,
            },
        )

    async def _execute_handler(
        self, handler: Callable[[Dict[str, Any]], Dict[str, Any]], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = handler(params)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    def _timeout_for_method(self, method: str) -> float:
        if method == "GAME_INVITATION":
            return float(self.config.timeouts.game_join_ack_sec)
        if method == "CHOOSE_PARITY_CALL":
            return float(self.config.timeouts.parity_choice_sec)
        if method in {"GAME_OVER", "MATCH_RESULT_REPORT"}:
            return float(self.config.timeouts.game_over_sec)
        return float(self.config.timeouts.generic_sec)


def build_player_agent(agent_id: str = "P01") -> PlayerAgent:
    """Factory to build a PlayerAgent (useful for tests)."""
    return PlayerAgent(agent_id=agent_id)
