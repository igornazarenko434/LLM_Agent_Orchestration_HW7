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
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.protocol import (
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    MatchResultReport,
    ChooseParityCall,
    GameInvitation,
    ErrorCode,
)


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
        self._method_map: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "GAME_INVITATION": lambda params: handlers.handle_game_invitation(self.agent_id, params),
            "CHOOSE_PARITY_CALL": lambda params: handlers.handle_choose_parity(self.agent_id, params),
            "MATCH_RESULT_REPORT": handlers.handle_match_result,
        }
        self._register_mcp_route()

    def _register_mcp_route(self) -> None:
        """Attach /mcp JSON-RPC endpoint to the FastAPI app."""

        @self.app.post("/mcp")
        async def mcp(request: Request):
            body = await request.json()
            try:
                rpc_request = JSONRPCRequest(**body)
            except Exception as exc:
                error = JSONRPCError(code=-32600, message="Invalid Request", data={"details": str(exc)})
                self._log_error(error=error, payload=body)
                return JSONResponse(status_code=400, content=JSONRPCResponse(id=body.get("id", 1), error=error).model_dump())

            # Validate params against league message schema
            if rpc_request.method == "GAME_INVITATION":
                GameInvitation(**rpc_request.params)
            elif rpc_request.method == "CHOOSE_PARITY_CALL":
                ChooseParityCall(**rpc_request.params)
            elif rpc_request.method == "MATCH_RESULT_REPORT":
                MatchResultReport(**rpc_request.params)

            handler = self._method_map.get(rpc_request.method)
            if not handler:
                error = JSONRPCError(
                    code=-32601,
                    message="Method not found",
                    data={"error_code": ErrorCode.INVALID_ENDPOINT, "method": rpc_request.method},
                )
                self._log_error(error=error, payload=rpc_request.model_dump())
                return JSONResponse(
                    status_code=404,
                    content=JSONRPCResponse(id=rpc_request.id, error=error).model_dump(),
                )

            try:
                log_message_received(self.std_logger, rpc_request.model_dump())
                result = handler(rpc_request.params)
                rpc_response = JSONRPCResponse(id=rpc_request.id, result=result)
                log_message_sent(self.std_logger, result)
                return JSONResponse(status_code=200, content=rpc_response.model_dump())
            except Exception as exc:  # pragma: no cover - defensive
                error = JSONRPCError(
                    code=-32000,
                    message="Server error",
                    data={"error": str(exc), "method": rpc_request.method},
                )
                self._log_error(error=error, payload=rpc_request.model_dump())
                return JSONResponse(
                    status_code=500,
                    content=JSONRPCResponse(id=rpc_request.id, error=error).model_dump(),
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


def build_player_agent(agent_id: str = "P01") -> PlayerAgent:
    """Factory to build a PlayerAgent (useful for tests)."""
    return PlayerAgent(agent_id=agent_id)
