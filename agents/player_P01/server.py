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
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from league_sdk.cleanup import get_retention_config
from league_sdk.config_loader import load_agents_config, load_json_file
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.protocol import (
    ChooseParityCall,
    ErrorCode,
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

        self._method_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "GAME_INVITATION": lambda params: handlers.handle_game_invitation(
                self.agent_id, params, self.auth_token
            ),
            "CHOOSE_PARITY_CALL": lambda params: handlers.handle_choose_parity(
                self.agent_id, params, self.auth_token
            ),
            "GAME_OVER": lambda params: handlers.handle_game_over(
                params, self.history_repo, self.auth_token
            ),
            "MATCH_RESULT_REPORT": lambda params: handlers.handle_match_result(
                params, self.history_repo, self.auth_token
            ),
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
            except TimeoutError as exc:  # pragma: no cover - defensive
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
        if params.get("protocol") != "league.v2":
            return self._error_response(
                rpc_request.id,
                code=-32602,
                message="Protocol mismatch",
                error_code=ErrorCode.PROTOCOL_VERSION_MISMATCH,
                status=400,
                payload=rpc_request.model_dump(),
                extra_data={"supported_protocols": ["league.v2"]},
            )

        try:
            if rpc_request.method == "GAME_INVITATION":
                GameInvitation(**rpc_request.params)
            elif rpc_request.method == "CHOOSE_PARITY_CALL":
                ChooseParityCall(**rpc_request.params)
            elif rpc_request.method == "GAME_OVER":
                GameOver(**rpc_request.params)
            elif rpc_request.method == "MATCH_RESULT_REPORT":
                MatchResultReport(**rpc_request.params)
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
        if not auth_token:
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

    def registration_endpoint(self) -> str:
        host = self.config.network.host
        port = self.config.network.league_manager_port
        return f"http://{host}:{port}/mcp"

    async def send_registration_request(self) -> Dict[str, Any]:
        """Send LEAGUE_REGISTER_REQUEST to League Manager with retry policy (async)."""
        self._transition("REGISTERING")
        conversation_id = self._conversation_id()
        player_meta = {
            "display_name": (
                self.agent_record.get("display_name", self.agent_id)
                if self.agent_record
                else self.agent_id
            ),
            "version": self.agent_record.get("version", "1.0.0") if self.agent_record else "1.0.0",
            "game_types": (
                self.agent_record.get("game_types", ["even_odd"]) if self.agent_record else ["even_odd"]
            ),
            "contact_endpoint": f"http://{self.host}:{self.port}/mcp",
        }
        request = LeagueRegisterRequest(
            sender=f"player:{self.agent_id}",
            timestamp=self._utc_timestamp(),
            conversation_id=conversation_id,
            protocol="league.v2",
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
        if "error" in response:
            self._transition("INIT")
            return response

        try:
            reg = LeagueRegisterResponse(**response)
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
            return response

        # Store player_id and optional auth_token
        self.agent_id = reg.player_id
        self.sender = f"player:{self.agent_id}"
        if hasattr(reg, "auth_token"):
            self.auth_token = getattr(reg, "auth_token")

        self._transition("REGISTERED", conversation_id=getattr(reg, "conversation_id", None))
        self._transition("ACTIVE", conversation_id=getattr(reg, "conversation_id", None))
        return response

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
