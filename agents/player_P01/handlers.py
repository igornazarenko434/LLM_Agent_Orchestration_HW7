"""
Player agent MCP tool handlers.

Implements the three required tools:
- handle_game_invitation -> GAME_JOIN_ACK
- choose_parity -> CHOOSE_PARITY_RESPONSE
- notify_match_result -> acknowledgement/logging hook
"""

import random
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from league_sdk.protocol import (
    ChooseParityCall,
    ChooseParityResponse,
    GameInvitation,
    GameJoinAck,
    MatchResultReport,
    GameOver,
)
from league_sdk.repositories import PlayerHistoryRepository


def _utc_timestamp() -> str:
    """Return ISO 8601 UTC timestamp without microseconds."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def handle_game_invitation(agent_id: str, params: Dict[str, Any], auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Respond to GAME_INVITATION with GAME_JOIN_ACK."""
    invitation = GameInvitation(**params)
    ack = GameJoinAck(
        sender=f"player:{agent_id}",
        conversation_id=invitation.conversation_id,
        league_id=invitation.league_id,
        protocol=invitation.protocol,
        timestamp=_utc_timestamp(),
        match_id=invitation.match_id,
        player_id=agent_id,
        arrival_timestamp=_utc_timestamp(),
        accept=True,
    )
    payload = ack.model_dump()
    if auth_token:
        payload["auth_token"] = auth_token
    return payload


def handle_choose_parity(agent_id: str, params: Dict[str, Any], auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Respond to CHOOSE_PARITY_CALL with CHOOSE_PARITY_RESPONSE (random strategy)."""
    call = ChooseParityCall(**params)
    parity_choice = random.choice(["even", "odd"])
    response = ChooseParityResponse(
        sender=f"player:{agent_id}",
        conversation_id=call.conversation_id,
        protocol=call.protocol,
        timestamp=_utc_timestamp(),
        match_id=call.match_id,
        player_id=agent_id,
        parity_choice=parity_choice,
    )
    payload = response.model_dump()
    if auth_token:
        payload["auth_token"] = auth_token
    return payload


def handle_match_result(
    params: Dict[str, Any], history: Optional[PlayerHistoryRepository | list[Dict[str, Any]]] = None, auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """Handle MATCH_RESULT_REPORT notification by validating, storing, and returning ack."""
    if "game_result" in params and "result" not in params:
        params = dict(params)
        params["result"] = params.pop("game_result")
    report = MatchResultReport(**params)
    record = report.model_dump()
    if auth_token:
        record["auth_token"] = auth_token
    if history is not None:
        if isinstance(history, PlayerHistoryRepository):
            details = record.get("result", {})
            history.add_match(
                match_id=report.match_id,
                league_id=record.get("league_id", ""),
                round_id=record.get("round_id", 0),
                opponent_id=details.get("opponent_id", ""),
                result=details.get("status", ""),
                points=details.get("points_awarded", 0),
                details=details,
            )
        else:
            history.append(record)
    return {
        "status": "ack",
        "match_id": report.match_id,
        "message_type": report.message_type,
        "auth_token": auth_token,
    }


def handle_game_over(params: Dict[str, Any], history: list[Dict[str, Any]], auth_token: Optional[str] = None) -> Dict[str, Any]:
    """Handle GAME_OVER notification: store in history and acknowledge."""
    game_over = GameOver(**params)
    record = game_over.model_dump()
    if auth_token:
        record["auth_token"] = auth_token
    if isinstance(history, PlayerHistoryRepository):
        details = record.get("game_result", {})
        history.add_match(
            match_id=game_over.match_id,
            league_id=record.get("league_id", ""),
            round_id=record.get("round_id", 0),
            opponent_id=details.get("opponent_id", ""),
            result=details.get("status", ""),
            points=details.get("points_awarded", 0),
            details=details,
        )
    else:
        history.append(record)
    return {
        "status": "ack",
        "match_id": game_over.match_id,
        "message_type": game_over.message_type,
        "auth_token": auth_token,
    }
