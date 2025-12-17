"""
Unit tests for protocol models (M2.1).

Tests Pydantic models for the league.v2 protocol:
- MessageEnvelope validation
- 18 specific message type models
- JSON-RPC 2.0 wrapper
- Protocol version enforcement
- Error code handling
"""

import json

import pytest
from league_sdk.protocol import (
    ChooseParityCall,
    ChooseParityResponse,
    ErrorCode,
    GameError,
    GameInvitation,
    GameJoinAck,
    GameOver,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    LeagueCompleted,
    LeagueError,
    LeagueQuery,
    LeagueQueryResponse,
    LeagueRegisterRequest,
    LeagueRegisterResponse,
    LeagueStandingsUpdate,
    MatchResultReport,
    MessageEnvelope,
    RefereeRegisterRequest,
    RefereeRegisterResponse,
    RoundAnnouncement,
    RoundCompleted,
    unwrap_message,
    wrap_message,
)
from pydantic import ValidationError


@pytest.mark.unit
class TestJSONRPCStructure:
    """Test JSON-RPC 2.0 wrapper compliance."""

    def test_valid_jsonrpc_request(self):
        """Test creating a valid JSON-RPC request."""
        req = JSONRPCRequest(jsonrpc="2.0", method="test_method", params={"key": "value"}, id=1)
        assert req.jsonrpc == "2.0"
        assert req.method == "test_method"
        assert req.id == 1

    def test_jsonrpc_request_with_int_id(self):
        """Test request with integer ID."""
        req = JSONRPCRequest(method="test", params={}, id=123)
        assert req.id == 123

    def test_jsonrpc_request_with_string_id(self):
        """Test request with string ID."""
        req = JSONRPCRequest(method="test", params={}, id="req-123")
        assert req.id == "req-123"

    def test_jsonrpc_request_serialization(self):
        """Test serialization to JSON."""
        req = JSONRPCRequest(method="test", params={"x": 1}, id=1)
        json_str = req.model_dump_json()
        data = json.loads(json_str)
        assert data["jsonrpc"] == "2.0"
        assert data["method"] == "test"
        assert data["params"] == {"x": 1}
        assert data["id"] == 1

    def test_invalid_jsonrpc_version(self):
        """Test validation of jsonrpc version field."""
        # It defaults to "2.0" and fails if changed (Literal constraint)
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="1.0", method="test", params={}, id=1)

    def test_jsonrpc_response_success(self):
        """Test successful JSON-RPC response."""
        res = JSONRPCResponse(result={"status": "ok"}, id=1)
        assert res.result == {"status": "ok"}
        assert res.error is None

    def test_jsonrpc_response_error(self):
        """Test error JSON-RPC response."""
        error = JSONRPCError(code=-32600, message="Invalid Request")
        res = JSONRPCResponse(error=error, id=1)
        assert res.error.code == -32600
        assert res.result is None

    def test_jsonrpc_response_cannot_have_both_result_and_error(self):
        """Test validation: cannot have both result and error."""
        with pytest.raises(ValueError, match="Response cannot have both"):
            JSONRPCResponse(result={"status": "ok"}, error=JSONRPCError(code=1, message="error"), id=1)

    def test_jsonrpc_error_structure(self):
        """Test JSONRPCError structure."""
        err = JSONRPCError(code=100, message="Test error", data={"detail": "info"})
        assert err.code == 100
        assert err.message == "Test error"
        assert err.data == {"detail": "info"}

    def test_jsonrpc_error_with_data(self):
        """Test error object with optional data field."""
        err = JSONRPCError(code=1, message="error", data={"retry": True})
        assert err.data["retry"] is True


@pytest.mark.unit
class TestErrorCodes:
    """Test ErrorCode constants and helpers."""

    def test_error_code_constants(self):
        """Verify key error codes exist."""
        assert ErrorCode.TIMEOUT_ERROR == "E001"
        assert ErrorCode.AUTH_TOKEN_INVALID == "E012"
        assert ErrorCode.INVALID_ENDPOINT == "E018"

    def test_retryable_errors(self):
        """Verify retryable error classification."""
        assert ErrorCode.is_retryable(ErrorCode.INVALID_GAME_STATE) is True
        assert ErrorCode.is_retryable(ErrorCode.PLAYER_NOT_AVAILABLE) is True
        assert ErrorCode.is_retryable(ErrorCode.ROUND_NOT_ACTIVE) is True
        assert ErrorCode.is_retryable(ErrorCode.RATE_LIMIT_EXCEEDED) is True
        assert ErrorCode.is_retryable(ErrorCode.INTERNAL_SERVER_ERROR) is True
        assert ErrorCode.is_retryable(ErrorCode.SERVICE_UNAVAILABLE) is True

    def test_non_retryable_errors(self):
        """Verify non-retryable error classification."""
        assert ErrorCode.is_retryable(ErrorCode.TIMEOUT_ERROR) is False
        assert ErrorCode.is_retryable(ErrorCode.AUTHENTICATION_FAILED) is False
        assert ErrorCode.is_retryable(ErrorCode.PROTOCOL_VERSION_MISMATCH) is False


@pytest.mark.unit
class TestTwoLayerIDSystem:
    """Test the two-layer ID system (JSON-RPC ID vs Conversation ID)."""

    def test_json_rpc_id_and_conversation_id_are_separate(self):
        """Verify request ID and conversation ID are distinct fields."""
        # Create a message (inner layer)
        msg = GameInvitation(
            sender="referee:REF01",
            timestamp="2025-01-01T12:00:00Z",
            conversation_id="conv-123",  # Inner ID
            league_id="league_1",
            round_id=1,
            match_id="M1",
            game_type="even_odd",
            role_in_match="PLAYER_A",
            opponent_id="P02",
        )

        # Wrap in JSON-RPC (outer layer)
        req = wrap_message(msg, request_id=999)  # Outer ID

        assert req.id == 999
        assert req.params["conversation_id"] == "conv-123"

    def test_multiple_messages_same_conversation_different_rpc_ids(self):
        """Verify conversation ID persists across different RPC calls."""
        conv_id = "conv-match-1"

        # Message 1: Invitation
        msg1 = GameInvitation(
            sender="referee:REF01",
            timestamp="2025-01-01T12:00:00Z",
            conversation_id=conv_id,
            league_id="L1",
            round_id=1,
            match_id="M1",
            game_type="g",
            role_in_match="PLAYER_A",
            opponent_id="P2",
        )
        req1 = wrap_message(msg1, request_id=1)

        # Message 2: Ack
        msg2 = GameJoinAck(
            sender="player:P01",
            timestamp="2025-01-01T12:00:01Z",
            conversation_id=conv_id,
            match_id="M1",
            player_id="P01",
            arrival_timestamp="2025-01-01T12:00:01Z",
            accept=True,
        )
        req2 = wrap_message(msg2, request_id=2)

        assert req1.id != req2.id
        assert req1.params["conversation_id"] == req2.params["conversation_id"]


@pytest.mark.unit
class TestProtocolVersion:
    """Test protocol version enforcement."""

    def test_json_rpc_version_must_be_2_0(self):
        """Verify JSON-RPC version is strictly '2.0'."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(jsonrpc="1.0", method="test", params={}, id=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
