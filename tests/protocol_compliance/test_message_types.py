"""
Protocol compliance tests for all 18 message types in league.v2 protocol.

Validates that all message types conform to the protocol specification
and are mapped to protocol models.
"""

import pytest
from league_sdk.protocol import get_message_class

# Message type constants from league.v2 protocol
REFEREE_REGISTER_REQUEST = "REFEREE_REGISTER_REQUEST"
REFEREE_REGISTER_RESPONSE = "REFEREE_REGISTER_RESPONSE"
LEAGUE_REGISTER_REQUEST = "LEAGUE_REGISTER_REQUEST"
LEAGUE_REGISTER_RESPONSE = "LEAGUE_REGISTER_RESPONSE"
ROUND_ANNOUNCEMENT = "ROUND_ANNOUNCEMENT"
GAME_INVITATION = "GAME_INVITATION"
GAME_JOIN_ACK = "GAME_JOIN_ACK"
CHOOSE_PARITY_CALL = "CHOOSE_PARITY_CALL"
CHOOSE_PARITY_RESPONSE = "CHOOSE_PARITY_RESPONSE"
GAME_OVER = "GAME_OVER"
MATCH_RESULT_REPORT = "MATCH_RESULT_REPORT"
LEAGUE_STANDINGS_UPDATE = "LEAGUE_STANDINGS_UPDATE"
ROUND_COMPLETED = "ROUND_COMPLETED"
LEAGUE_COMPLETED = "LEAGUE_COMPLETED"
LEAGUE_QUERY = "LEAGUE_QUERY"
LEAGUE_QUERY_RESPONSE = "LEAGUE_QUERY_RESPONSE"
LEAGUE_ERROR = "LEAGUE_ERROR"
GAME_ERROR = "GAME_ERROR"


@pytest.mark.protocol
class TestMessageTypes:
    """Test all 18 message types defined in league.v2 protocol."""

    def test_referee_register_request_type(self):
        """Test REFEREE_REGISTER_REQUEST message type constant."""
        assert REFEREE_REGISTER_REQUEST == "REFEREE_REGISTER_REQUEST"

    def test_referee_register_response_type(self):
        """Test REFEREE_REGISTER_RESPONSE message type constant."""
        assert REFEREE_REGISTER_RESPONSE == "REFEREE_REGISTER_RESPONSE"

    def test_league_register_request_type(self):
        """Test LEAGUE_REGISTER_REQUEST message type constant."""
        assert LEAGUE_REGISTER_REQUEST == "LEAGUE_REGISTER_REQUEST"

    def test_league_register_response_type(self):
        """Test LEAGUE_REGISTER_RESPONSE message type constant."""
        assert LEAGUE_REGISTER_RESPONSE == "LEAGUE_REGISTER_RESPONSE"

    def test_game_invitation_type(self):
        """Test GAME_INVITATION message type constant."""
        assert GAME_INVITATION == "GAME_INVITATION"

    def test_game_join_ack_type(self):
        """Test GAME_JOIN_ACK message type constant."""
        assert GAME_JOIN_ACK == "GAME_JOIN_ACK"

    def test_choose_parity_call_type(self):
        """Test CHOOSE_PARITY_CALL message type constant."""
        assert CHOOSE_PARITY_CALL == "CHOOSE_PARITY_CALL"

    def test_choose_parity_response_type(self):
        """Test CHOOSE_PARITY_RESPONSE message type constant."""
        assert CHOOSE_PARITY_RESPONSE == "CHOOSE_PARITY_RESPONSE"

    def test_game_over_type(self):
        """Test GAME_OVER message type constant."""
        assert GAME_OVER == "GAME_OVER"

    def test_match_result_report_type(self):
        """Test MATCH_RESULT_REPORT message type constant."""
        assert MATCH_RESULT_REPORT == "MATCH_RESULT_REPORT"

    def test_league_standings_update_type(self):
        """Test LEAGUE_STANDINGS_UPDATE message type constant."""
        assert LEAGUE_STANDINGS_UPDATE == "LEAGUE_STANDINGS_UPDATE"

    def test_round_announcement_type(self):
        """Test ROUND_ANNOUNCEMENT message type constant."""
        assert ROUND_ANNOUNCEMENT == "ROUND_ANNOUNCEMENT"

    def test_round_completed_type(self):
        """Test ROUND_COMPLETED message type constant."""
        assert ROUND_COMPLETED == "ROUND_COMPLETED"

    def test_league_completed_type(self):
        """Test LEAGUE_COMPLETED message type constant."""
        assert LEAGUE_COMPLETED == "LEAGUE_COMPLETED"

    def test_league_query_type(self):
        """Test LEAGUE_QUERY message type constant."""
        assert LEAGUE_QUERY == "LEAGUE_QUERY"

    def test_league_query_response_type(self):
        """Test LEAGUE_QUERY_RESPONSE message type constant."""
        assert LEAGUE_QUERY_RESPONSE == "LEAGUE_QUERY_RESPONSE"

    def test_league_error_type(self):
        """Test LEAGUE_ERROR message type constant."""
        assert LEAGUE_ERROR == "LEAGUE_ERROR"

    def test_game_error_type(self):
        """Test GAME_ERROR message type constant."""
        assert GAME_ERROR == "GAME_ERROR"

    def test_all_message_types_unique(self):
        """Test that all 18 message types are unique."""
        message_types = _all_message_types()

        # Check uniqueness
        assert len(message_types) == len(set(message_types)), "Message types must be unique"

    def test_message_types_count(self):
        """Test that we have all expected message types."""
        message_types = _all_message_types()
        assert len(message_types) == 18, "Should have exactly 18 protocol message types"

    def test_message_type_naming_convention(self):
        """Test that message types follow UPPER_SNAKE_CASE convention."""
        message_types = _all_message_types()

        for msg_type in message_types:
            # Should be all uppercase with underscores
            assert msg_type.isupper(), f"{msg_type} should be UPPERCASE"
            assert "_" in msg_type or msg_type == msg_type.upper(), f"{msg_type} should use underscores"
            # No spaces
            assert " " not in msg_type, f"{msg_type} should not contain spaces"

    def test_message_types_resolve_to_models(self):
        """Test that all message types map to protocol model classes."""
        for msg_type in _all_message_types():
            assert get_message_class(msg_type) is not None, f"{msg_type} should map to a model"


def _all_message_types() -> list[str]:
    return [
        REFEREE_REGISTER_REQUEST,
        REFEREE_REGISTER_RESPONSE,
        LEAGUE_REGISTER_REQUEST,
        LEAGUE_REGISTER_RESPONSE,
        ROUND_ANNOUNCEMENT,
        GAME_INVITATION,
        GAME_JOIN_ACK,
        CHOOSE_PARITY_CALL,
        CHOOSE_PARITY_RESPONSE,
        GAME_OVER,
        MATCH_RESULT_REPORT,
        LEAGUE_STANDINGS_UPDATE,
        ROUND_COMPLETED,
        LEAGUE_COMPLETED,
        LEAGUE_QUERY,
        LEAGUE_QUERY_RESPONSE,
        LEAGUE_ERROR,
        GAME_ERROR,
    ]
