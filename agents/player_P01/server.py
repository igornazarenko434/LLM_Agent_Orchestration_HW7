"""
Player agent MCP server setup (Mission 7.2).

Exposes /mcp JSON-RPC 2.0 endpoint with dispatch to required tools:
- GAME_INVITATION  -> GAME_JOIN_ACK
- CHOOSE_PARITY_CALL -> CHOOSE_PARITY_RESPONSE
- MATCH_RESULT_REPORT -> ack/log
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from agents.base import BaseAgent
from agents.player_P01 import handlers
from league_sdk.config_loader import load_agents_config, load_json_file
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.protocol import (
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    MatchResultReport,
    ChooseParityCall,
    GameInvitation,
    ErrorCode,
    GameOver,
)

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
        self.match_history: list[Dict[str, Any]] = []

        self._method_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "GAME_INVITATION": lambda params: handlers.handle_game_invitation(self.agent_id, params, self.auth_token),
            "CHOOSE_PARITY_CALL": lambda params: handlers.handle_choose_parity(self.agent_id, params, self.auth_token),
            "GAME_OVER": lambda params: handlers.handle_game_over(params, self.match_history, self.auth_token),
            "MATCH_RESULT_REPORT": handlers.handle_match_result,
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
                result = handler(rpc_request.params)
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


def build_player_agent(agent_id: str = "P01") -> PlayerAgent:
    """Factory to build a PlayerAgent (useful for tests)."""
    return PlayerAgent(agent_id=agent_id)
