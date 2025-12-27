"""
Protocol models for league.v2 specification - EXACT ASSIGNMENT FORMAT.

This module defines Pydantic models matching the EXACT JSON format required by the assignment.
All field names, structures, and values match the specification precisely.

Protocol Version: league.v2
CRITICAL: Do NOT modify field names - they must match assignment specification exactly!
"""

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "MessageEnvelope",
    # Registration Messages
    "RefereeRegisterRequest",
    "RefereeRegisterResponse",
    "LeagueRegisterRequest",
    "LeagueRegisterResponse",
    # League Orchestration Messages
    "RoundAnnouncement",
    "RoundCompleted",
    "LeagueCompleted",
    "LeagueStandingsUpdate",
    # Match Flow Messages
    "GameInvitation",
    "GameJoinAck",
    "ChooseParityCall",
    "ChooseParityResponse",
    "GameOver",
    "MatchResultReport",
    # Query Messages
    "LeagueQuery",
    "LeagueQueryResponse",
    # Error Messages
    "LeagueError",
    "GameError",
    # Error Code Enum
    "ErrorCode",
    # JSON-RPC 2.0 Wrapper
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "wrap_message",
    "unwrap_message",
]

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

SENDER_PATTERN = r"^(player|referee|league_manager):[A-Z0-9]+$"
TIMESTAMP_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"


# ============================================================================
# ERROR CODES
# ============================================================================


class ErrorCode:
    """Error codes as defined in assignment specification."""

    TIMEOUT_ERROR = "E001"
    INVALID_MESSAGE_FORMAT = "E002"
    AUTHENTICATION_FAILED = "E003"
    AGENT_NOT_REGISTERED = "E004"
    INVALID_GAME_STATE = "E005"
    PLAYER_NOT_AVAILABLE = "E006"
    MATCH_NOT_FOUND = "E007"
    LEAGUE_NOT_FOUND = "E008"
    ROUND_NOT_ACTIVE = "E009"
    INVALID_MOVE = "E010"
    PROTOCOL_VERSION_MISMATCH = "E011"
    AUTH_TOKEN_INVALID = "E012"
    CONVERSATION_ID_MISMATCH = "E013"
    RATE_LIMIT_EXCEEDED = "E014"
    INTERNAL_SERVER_ERROR = "E015"
    SERVICE_UNAVAILABLE = "E016"
    DUPLICATE_REGISTRATION = "E017"
    INVALID_ENDPOINT = "E018"

    @classmethod
    def is_retryable(cls, error_code: str) -> bool:
        """Check if error code represents a retryable error."""
        retryable_codes = {
            cls.INVALID_GAME_STATE,
            cls.PLAYER_NOT_AVAILABLE,
            cls.ROUND_NOT_ACTIVE,
            cls.RATE_LIMIT_EXCEEDED,
            cls.INTERNAL_SERVER_ERROR,
            cls.SERVICE_UNAVAILABLE,
        }
        return error_code in retryable_codes


# ============================================================================
# BASE MESSAGE ENVELOPE
# ============================================================================


class MessageEnvelope(BaseModel):
    """
    Base message envelope for league.v2 protocol messages.

    MANDATORY FIELDS (must include in every message):
    - protocol: "league.v2" (always)
    - message_type: One of 18 defined types
    - sender: Format "{agent_type}:{agent_id}"
    - timestamp: ISO 8601 UTC format (YYYY-MM-DDTHH:MM:SSZ)
    - conversation_id: Thread tracking ID

    OPTIONAL CONTEXT FIELDS (can be included in any message):
    - auth_token: Authentication token (mandatory after registration, empty during registration)
    - league_id: League identifier
    - round_id: Round number
    - match_id: Match identifier
    """

    protocol: Literal["league.v2"] = Field(
        default="league.v2", description="Protocol version - must be 'league.v2'"
    )

    message_type: str = Field(..., description="One of 18 defined message types")

    sender: str = Field(..., description="Agent identifier: {agent_type}:{agent_id}")

    timestamp: str = Field(..., description="ISO 8601 UTC: YYYY-MM-DDTHH:MM:SSZ")

    conversation_id: str = Field(..., description="Conversation tracking ID")

    # Optional context fields that can appear in any message
    auth_token: str = Field(
        default="", description="Auth token (mandatory after registration, empty during registration)"
    )

    league_id: Optional[str] = Field(
        default=None, description="League identifier (optional context field)"
    )

    round_id: Optional[int] = Field(default=None, description="Round number (optional context field)")

    match_id: Optional[str] = Field(
        default=None, description="Match identifier (optional context field)"
    )

    @field_validator("sender")
    @classmethod
    def validate_sender_format(cls, v: str) -> str:
        """Validate sender format."""
        if not re.match(SENDER_PATTERN, v):
            raise ValueError(f"Invalid sender format: '{v}'")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_format(cls, v: str) -> str:
        """Validate timestamp is ISO 8601 UTC."""
        if not re.match(TIMESTAMP_PATTERN, v):
            raise ValueError(f"Invalid timestamp format: '{v}'")
        return v

    class Config:
        """Pydantic configuration for message envelopes."""

        extra = "allow"


# ============================================================================
# REGISTRATION MESSAGES (EXACT ASSIGNMENT FORMAT)
# ============================================================================


class RefereeRegisterRequest(MessageEnvelope):
    """
    Referee registration request - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "REFEREE_REGISTER_REQUEST",
        "referee_meta": {
            "display_name": "Referee Alpha",
            "version": "1.0.0",
            "game_types": ["even_odd"],
            "contact_endpoint": "http://localhost:8001/mcp",
            "max_concurrent_matches": 2
        }
    }
    """

    message_type: Literal["REFEREE_REGISTER_REQUEST"] = "REFEREE_REGISTER_REQUEST"
    auth_token: str = ""  # Empty for registration

    referee_meta: dict[str, Any] = Field(..., description="Referee metadata object")


class RefereeRegisterResponse(MessageEnvelope):
    """
    Referee registration response - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "status": "ACCEPTED",
        "referee_id": "REF01",
        "reason": null
    }
    """

    message_type: Literal["REFEREE_REGISTER_RESPONSE"] = "REFEREE_REGISTER_RESPONSE"

    status: Literal["ACCEPTED", "REJECTED"] = Field(..., description="Registration status")
    referee_id: str = Field(..., description="Assigned referee ID")
    reason: Optional[str] = Field(default=None, description="Rejection reason if applicable")


class LeagueRegisterRequest(MessageEnvelope):
    """
    Player registration request - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "LEAGUE_REGISTER_REQUEST",
        "player_meta": {
            "display_name": "Agent Alpha",
            "version": "1.0.0",
            "game_types": ["even_odd"],
            "contact_endpoint": "http://localhost:8101/mcp"
        }
    }
    """

    message_type: Literal["LEAGUE_REGISTER_REQUEST"] = "LEAGUE_REGISTER_REQUEST"
    auth_token: str = ""  # Empty for registration

    player_meta: dict[str, Any] = Field(..., description="Player metadata object")


class LeagueRegisterResponse(MessageEnvelope):
    """
    Player registration response - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "LEAGUE_REGISTER_RESPONSE",
        "status": "ACCEPTED",
        "player_id": "P01",
        "reason": null
    }
    """

    message_type: Literal["LEAGUE_REGISTER_RESPONSE"] = "LEAGUE_REGISTER_RESPONSE"

    status: Literal["ACCEPTED", "REJECTED"] = Field(..., description="Registration status")
    player_id: str = Field(..., description="Assigned player ID")
    reason: Optional[str] = Field(default=None, description="Rejection reason if applicable")


# ============================================================================
# LEAGUE ORCHESTRATION MESSAGES (EXACT ASSIGNMENT FORMAT)
# ============================================================================


class RoundAnnouncement(MessageEnvelope):
    """
    Round announcement - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "ROUND_ANNOUNCEMENT",
        "league_id": "league_2025_even_odd",
        "round_id": 1,
        "matches": [
            {
                "match_id": "R1M1",
                "game_type": "even_odd",
                "player_A_id": "P01",
                "player_B_id": "P02",
                "referee_endpoint": "http://localhost:8001/mcp"
            }
        ]
    }
    """

    message_type: Literal["ROUND_ANNOUNCEMENT"] = "ROUND_ANNOUNCEMENT"

    league_id: str = Field(..., description="League identifier")
    round_id: int = Field(..., ge=1, description="Round number")
    matches: list[dict[str, Any]] = Field(..., description="List of matches in this round")


class LeagueStandingsUpdate(MessageEnvelope):
    """
    League standings update - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "LEAGUE_STANDINGS_UPDATE",
        "league_id": "league_2025_even_odd",
        "round_id": 1,
        "standings": [
            {
                "rank": 1,
                "player_id": "P01",
                "display_name": "Agent Alpha",
                "played": 2,
                "wins": 2,
                "draws": 0,
                "losses": 0,
                "points": 6
            }
        ]
    }
    """

    message_type: Literal["LEAGUE_STANDINGS_UPDATE"] = "LEAGUE_STANDINGS_UPDATE"

    league_id: str = Field(..., description="League identifier")
    round_id: int = Field(..., ge=1, description="Round number")
    standings: list[dict[str, Any]] = Field(..., description="Standings array")


class RoundCompleted(MessageEnvelope):
    """
    Round completed notification - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "protocol": "league.v2",
        "message_type": "ROUND_COMPLETED",
        "sender": "league_manager",
        "timestamp": "2025-01-15T12:00:00Z",
        "conversation_id": "conv-round1-complete",
        "league_id": "league_2025_even_odd",
        "round_id": 1,
        "matches_completed": 2,
        "next_round_id": 2,
        "summary": {
            "total_matches": 2,
            "wins": 1,
            "draws": 1,
            "technical_losses": 0
        }
    }
    """

    message_type: Literal["ROUND_COMPLETED"] = "ROUND_COMPLETED"

    league_id: str = Field(..., description="League identifier")
    round_id: int = Field(..., ge=1, description="Completed round number")
    matches_completed: int = Field(..., ge=0, description="Number of matches completed")
    next_round_id: Optional[int] = Field(
        default=None, description="Next round ID (null if league complete)"
    )
    summary: dict[str, Any] = Field(..., description="Round summary statistics")


class LeagueCompleted(MessageEnvelope):
    """
    League completed notification - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "protocol": "league.v2",
        "message_type": "LEAGUE_COMPLETED",
        "sender": "league_manager",
        "timestamp": "2025-01-20T18:00:00Z",
        "conversation_id": "conv-league-complete",
        "league_id": "league_2025_even_odd",
        "total_rounds": 3,
        "total_matches": 6,
        "champion": {
            "player_id": "P01",
            "display_name": "Agent Alpha",
            "points": 9
        },
        "final_standings": [
            {"rank": 1, "player_id": "P01", "points": 9}
        ]
    }
    """

    message_type: Literal["LEAGUE_COMPLETED"] = "LEAGUE_COMPLETED"

    league_id: str = Field(..., description="League identifier")
    total_rounds: int = Field(..., ge=1, description="Total rounds played")
    total_matches: int = Field(..., ge=0, description="Total matches played")
    champion: dict[str, Any] = Field(..., description="Champion information")
    final_standings: list[dict[str, Any]] = Field(..., description="Final standings")


# ============================================================================
# MATCH FLOW MESSAGES (EXACT ASSIGNMENT FORMAT)
# ============================================================================


class GameInvitation(MessageEnvelope):
    """
    Game invitation - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "GAME_INVITATION",
        "league_id": "league_2025_even_odd",
        "round_id": 1,
        "match_id": "R1M1",
        "game_type": "even_odd",
        "role_in_match": "PLAYER_A",
        "opponent_id": "P02",
        "conversation_id": "conv-r1m1-001"
    }
    """

    message_type: Literal["GAME_INVITATION"] = "GAME_INVITATION"

    league_id: str = Field(..., description="League identifier")
    round_id: int = Field(..., ge=1, description="Round number")
    match_id: str = Field(..., description="Match identifier")
    game_type: str = Field(..., description="Game type")
    role_in_match: Literal["PLAYER_A", "PLAYER_B"] = Field(..., description="Player's role")
    opponent_id: str = Field(..., description="Opponent player ID")


class GameJoinAck(MessageEnvelope):
    """
    Game join acknowledgment - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "GAME_JOIN_ACK",
        "match_id": "R1M1",
        "player_id": "P01",
        "arrival_timestamp": "2025-01-15T10:30:00Z",
        "accept": true
    }
    """

    message_type: Literal["GAME_JOIN_ACK"] = "GAME_JOIN_ACK"

    match_id: str = Field(..., description="Match identifier")
    player_id: str = Field(..., description="Player ID")
    arrival_timestamp: str = Field(..., description="ISO 8601 arrival time")
    accept: bool = Field(..., description="Accept invitation (true/false)")


class ChooseParityCall(MessageEnvelope):
    """
    Request for parity choice - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "CHOOSE_PARITY_CALL",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_type": "even_odd",
        "context": {
            "opponent_id": "P02",
            "round_id": 1,
            "your_standings": {
                "wins": 2,
                "losses": 1,
                "draws": 0
            }
        },
        "deadline": "2025-01-15T10:30:30Z"
    }
    """

    message_type: Literal["CHOOSE_PARITY_CALL"] = "CHOOSE_PARITY_CALL"

    match_id: str = Field(..., description="Match identifier")
    player_id: str = Field(..., description="Player ID being asked")
    game_type: str = Field(..., description="Game type")
    context: dict[str, Any] = Field(..., description="Game context (opponent, standings)")
    deadline: str = Field(..., description="ISO 8601 deadline for response")


class ChooseParityResponse(MessageEnvelope):
    """
    Parity choice response - EXACT FORMAT FROM ASSIGNMENT.

    CRITICAL: parity_choice MUST be "even" or "odd" (lowercase only!)

    Example:
    {
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "match_id": "R1M1",
        "player_id": "P01",
        "parity_choice": "even"
    }
    """

    message_type: Literal["CHOOSE_PARITY_RESPONSE"] = "CHOOSE_PARITY_RESPONSE"

    match_id: str = Field(..., description="Match identifier")
    player_id: str = Field(..., description="Player ID")
    parity_choice: Literal["even", "odd"] = Field(
        ..., description="Parity choice: 'even' or 'odd' ONLY"
    )


class GameOver(MessageEnvelope):
    """
    Game over notification - EXACT FORMAT FROM ASSIGNMENT.

    CRITICAL: status MUST be "WIN", "DRAW", or "TECHNICAL_LOSS"

    Example:
    {
        "message_type": "GAME_OVER",
        "match_id": "R1M1",
        "game_type": "even_odd",
        "game_result": {
            "status": "WIN",
            "winner_player_id": "P01",
            "drawn_number": 8,
            "number_parity": "even",
            "choices": {
                "P01": "even",
                "P02": "odd"
            },
            "reason": "P01 chose even, number was 8 (even)"
        }
    }
    """

    message_type: Literal["GAME_OVER"] = "GAME_OVER"

    match_id: str = Field(..., description="Match identifier")
    game_type: str = Field(..., description="Game type")
    game_result: dict[str, Any] = Field(..., description="Complete game result object")


class MatchResultReport(MessageEnvelope):
    """
    Match result report to league manager - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "message_type": "MATCH_RESULT_REPORT",
        "league_id": "league_2025_even_odd",
        "round_id": 1,
        "match_id": "R1M1",
        "game_type": "even_odd",
        "result": {
            "winner": "P01",
            "score": {
                "P01": 3,
                "P02": 0
            },
            "details": {
                "drawn_number": 8,
                "choices": {
                    "P01": "even",
                    "P02": "odd"
                }
            }
        }
    }
    """

    message_type: Literal["MATCH_RESULT_REPORT"] = "MATCH_RESULT_REPORT"

    league_id: str = Field(..., description="League identifier")
    round_id: int = Field(..., ge=1, description="Round number")
    match_id: str = Field(..., description="Match identifier")
    game_type: str = Field(..., description="Game type")
    result: dict[str, Any] = Field(..., description="Match result object")


# ============================================================================
# QUERY MESSAGES (EXACT ASSIGNMENT FORMAT)
# ============================================================================


class LeagueQuery(MessageEnvelope):
    """
    League query - EXACT FORMAT FROM ASSIGNMENT.

    Valid query_type values:
    - GET_STANDINGS
    - GET_SCHEDULE
    - GET_NEXT_MATCH
    - GET_PLAYER_STATS

    Example:
    {
        "protocol": "league.v2",
        "message_type": "LEAGUE_QUERY",
        "sender": "player:P01",
        "timestamp": "2025-01-15T14:00:00Z",
        "conversation_id": "conv-query-001",
        "auth_token": "tok_p01_abc123...",
        "league_id": "league_2025_even_odd",
        "query_type": "GET_NEXT_MATCH",
        "query_params": {
            "player_id": "P01"
        }
    }
    """

    message_type: Literal["LEAGUE_QUERY"] = "LEAGUE_QUERY"

    league_id: str = Field(..., description="League identifier")
    query_type: Literal["GET_STANDINGS", "GET_SCHEDULE", "GET_NEXT_MATCH", "GET_PLAYER_STATS"] = Field(
        ..., description="Query type"
    )
    query_params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")


class LeagueQueryResponse(MessageEnvelope):
    """
    League query response - EXACT FORMAT FROM ASSIGNMENT.

    Example:
    {
        "protocol": "league.v2",
        "message_type": "LEAGUE_QUERY_RESPONSE",
        "sender": "league_manager",
        "timestamp": "2025-01-15T14:00:01Z",
        "conversation_id": "conv-query-001",
        "query_type": "GET_NEXT_MATCH",
        "success": true,
        "data": {
            "next_match": {
                "match_id": "R2M1",
                "round_id": 2,
                "opponent_id": "P03",
                "referee_endpoint": "http://localhost:8001/mcp"
            }
        }
    }
    """

    message_type: Literal["LEAGUE_QUERY_RESPONSE"] = "LEAGUE_QUERY_RESPONSE"

    query_type: str = Field(..., description="Query type that was answered")
    success: bool = Field(..., description="Whether query succeeded")
    data: dict[str, Any] = Field(..., description="Query result data")


# ============================================================================
# ERROR MESSAGES (EXACT ASSIGNMENT FORMAT)
# ============================================================================


class LeagueError(MessageEnvelope):
    """
    League error - EXACT FORMAT FROM ASSIGNMENT.

    Example:
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
            "provided_token": "tok-invalid-xxx",
            "expected_format": "tok-{agent_id}-{hash}"
        }
    }
    """

    message_type: Literal["LEAGUE_ERROR"] = "LEAGUE_ERROR"

    error_code: str = Field(..., description="Error code (E001-E018)")
    error_description: str = Field(..., description="Error description")
    original_message_type: Optional[str] = Field(default=None, description="Original message type")
    context: dict[str, Any] = Field(default_factory=dict, description="Error context")


class GameError(MessageEnvelope):
    """
    Game error - EXACT FORMAT FROM ASSIGNMENT.

    Example:
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
            "retry_count": 1,
            "max_retries": 3,
            "next_retry_at": "2025-01-15T10:16:02Z"
        },
        "consequence": "Technical loss if max retries exceeded"
    }
    """

    message_type: Literal["GAME_ERROR"] = "GAME_ERROR"

    match_id: str = Field(..., description="Match identifier")
    error_code: str = Field(..., description="Error code (E001-E018)")
    error_description: str = Field(..., description="Error description")
    affected_player: str = Field(..., description="Affected player ID")
    action_required: str = Field(..., description="Required action")
    retry_info: dict[str, Any] = Field(..., description="Retry information")
    consequence: str = Field(..., description="Consequence of error")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def validate_message_envelope(message: dict) -> MessageEnvelope:
    """Validate message envelope."""
    return MessageEnvelope(**message)


def get_message_class(message_type: str) -> type[MessageEnvelope] | None:
    """Get Pydantic model class for message type."""
    message_type_map = {
        "REFEREE_REGISTER_REQUEST": RefereeRegisterRequest,
        "REFEREE_REGISTER_RESPONSE": RefereeRegisterResponse,
        "LEAGUE_REGISTER_REQUEST": LeagueRegisterRequest,
        "LEAGUE_REGISTER_RESPONSE": LeagueRegisterResponse,
        "ROUND_ANNOUNCEMENT": RoundAnnouncement,
        "GAME_INVITATION": GameInvitation,
        "GAME_JOIN_ACK": GameJoinAck,
        "CHOOSE_PARITY_CALL": ChooseParityCall,
        "CHOOSE_PARITY_RESPONSE": ChooseParityResponse,
        "GAME_OVER": GameOver,
        "MATCH_RESULT_REPORT": MatchResultReport,
        "LEAGUE_STANDINGS_UPDATE": LeagueStandingsUpdate,
        "ROUND_COMPLETED": RoundCompleted,
        "LEAGUE_COMPLETED": LeagueCompleted,
        "LEAGUE_QUERY": LeagueQuery,
        "LEAGUE_QUERY_RESPONSE": LeagueQueryResponse,
        "LEAGUE_ERROR": LeagueError,
        "GAME_ERROR": GameError,
    }
    return message_type_map.get(message_type)


# ============================================================================
# JSON-RPC 2.0 WRAPPER (for MCP communication)
# ============================================================================


class JSONRPCError(BaseModel):
    """
    JSON-RPC 2.0 Error object.

    Used when a request fails or encounters an error.
    """

    code: int = Field(..., description="Error code (standard JSON-RPC codes)")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(default=None, description="Additional error data")


class JSONRPCRequest(BaseModel):
    """
    JSON-RPC 2.0 Request wrapper.

    All league.v2 messages are sent wrapped in this format:
    {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {...MessageEnvelope fields...},
        "id": 1
    }

    The MessageEnvelope (and all its subclasses) goes inside the `params` field.
    """

    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="Message type (e.g., 'GAME_INVITATION')")
    params: dict[str, Any] = Field(..., description="Message envelope parameters")
    id: int | str = Field(..., description="Request ID for matching responses")

    class Config:
        """Pydantic configuration for JSON-RPC requests."""

        extra = "forbid"


class JSONRPCResponse(BaseModel):
    """
    JSON-RPC 2.0 Response wrapper.

    All responses from agents are wrapped in this format:
    {
        "jsonrpc": "2.0",
        "result": {...MessageEnvelope fields...},
        "id": 1
    }

    OR for errors:
    {
        "jsonrpc": "2.0",
        "error": {"code": -32600, "message": "Invalid Request"},
        "id": 1
    }
    """

    jsonrpc: Literal["2.0"] = Field(default="2.0", description="JSON-RPC version")
    result: Optional[dict[str, Any]] = Field(default=None, description="Success result")
    error: Optional[JSONRPCError] = Field(default=None, description="Error object")
    id: int | str = Field(..., description="Request ID matching the request")

    @field_validator("result", "error")
    @classmethod
    def validate_result_or_error(cls, v, info):
        """Ensure either result or error is present, but not both."""
        values = info.data
        result = values.get("result")
        error = values.get("error")

        # If this is the error field being validated
        if info.field_name == "error":
            if result is not None and v is not None:
                raise ValueError("Response cannot have both 'result' and 'error'")
            if result is None and v is None:
                raise ValueError("Response must have either 'result' or 'error'")

        return v

    class Config:
        """Pydantic configuration for JSON-RPC responses."""

        extra = "forbid"


# ============================================================================
# HELPER FUNCTIONS FOR JSON-RPC 2.0 WRAPPING
# ============================================================================


def wrap_message(message: MessageEnvelope, request_id: int | str = 1) -> JSONRPCRequest:
    """
    Wrap a MessageEnvelope in JSON-RPC 2.0 request format.

    Args:
        message: Any MessageEnvelope subclass instance
        request_id: Request ID for matching responses (default: 1)

    Returns:
        JSONRPCRequest with message wrapped in params

    Example:
        >>> invitation = GameInvitation(...)
        >>> rpc_request = wrap_message(invitation, request_id=123)
        >>> rpc_request.model_dump_json()
        '{"jsonrpc": "2.0", "method": "GAME_INVITATION", "params": {...}, "id": 123}'
    """
    return JSONRPCRequest(
        jsonrpc="2.0", method=message.message_type, params=message.model_dump(), id=request_id
    )


def unwrap_message(rpc_request: JSONRPCRequest | dict) -> MessageEnvelope:
    """
    Unwrap a JSON-RPC 2.0 request to extract the MessageEnvelope.

    Args:
        rpc_request: JSONRPCRequest instance or dict with JSON-RPC format

    Returns:
        MessageEnvelope subclass instance (typed based on message_type)

    Raises:
        ValueError: If message_type is unknown or params are invalid

    Example:
        >>> rpc_dict = {"jsonrpc": "2.0", "method": "GAME_INVITATION", "params": {...}, "id": 1}
        >>> message = unwrap_message(rpc_dict)
        >>> isinstance(message, GameInvitation)
        True
    """
    # Convert dict to JSONRPCRequest if needed
    if isinstance(rpc_request, dict):
        rpc_request = JSONRPCRequest(**rpc_request)

    # Get the message class based on method (message_type)
    message_class = get_message_class(rpc_request.method)
    if message_class is None:
        raise ValueError(f"Unknown message type: {rpc_request.method}")

    # Instantiate the message from params
    return message_class(**rpc_request.params)
