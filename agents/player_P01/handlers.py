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
)


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


def handle_match_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MATCH_RESULT_REPORT notification by validating and returning ack."""
    report = MatchResultReport(**params)
    # Business logic placeholder: could update local strategy/learning here.
    return {"status": "ack", "match_id": report.match_id, "message_type": report.message_type}
