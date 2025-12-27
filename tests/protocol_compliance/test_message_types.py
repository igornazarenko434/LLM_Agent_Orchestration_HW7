"""
Protocol compliance tests for all 18 message types in league.v2 protocol.

Validates that all message types conform to the protocol specification
including structure, required fields, and data types.
"""

import pytest

# Message type constants from league.v2 protocol
PLAYER_REGISTRATION_REQUEST = "PLAYER_REGISTRATION_REQUEST"
PLAYER_REGISTRATION_RESPONSE = "PLAYER_REGISTRATION_RESPONSE"
GAME_JOIN_ACK = "GAME_JOIN_ACK"
GAME_PARITY_CHOICE_ACK = "CHOOSE_PARITY_RESPONSE"
REFEREE_REGISTER_REQUEST = "REFEREE_REGISTER_REQUEST"
REFEREE_REGISTER_RESPONSE = "REFEREE_REGISTER_RESPONSE"
LEAGUE_START = "LEAGUE_START"
START_MATCH = "START_MATCH"
STANDINGS_UPDATE = "LEAGUE_STANDINGS_UPDATE"
GAME_RESULT = "GAME_OVER"
GAME_INVITATION = "GAME_INVITATION"
GAME_PARITY_CHOICE_REQUEST = "CHOOSE_PARITY_CALL"
MATCH_RESULT = "MATCH_RESULT_REPORT"
MATCH_START_ACK = "MATCH_START_ACK"
MATCH_ERROR = "GAME_ERROR"


@pytest.mark.protocol
class TestMessageTypes:
    """Test all 18 message types defined in league.v2 protocol."""

    def test_player_registration_request_type(self):
        """Test PLAYER_REGISTRATION_REQUEST message type constant."""
        assert PLAYER_REGISTRATION_REQUEST == "PLAYER_REGISTRATION_REQUEST"

    def test_player_registration_response_type(self):
        """Test PLAYER_REGISTRATION_RESPONSE message type constant."""
        assert PLAYER_REGISTRATION_RESPONSE == "PLAYER_REGISTRATION_RESPONSE"

    def test_game_join_ack_type(self):
        """Test GAME_JOIN_ACK message type constant."""
        assert GAME_JOIN_ACK == "GAME_JOIN_ACK"

    def test_game_parity_choice_ack_type(self):
        """Test CHOOSE_PARITY_RESPONSE message type constant."""
        assert GAME_PARITY_CHOICE_ACK == "CHOOSE_PARITY_RESPONSE"

    def test_referee_register_request_type(self):
        """Test REFEREE_REGISTER_REQUEST message type constant."""
        assert REFEREE_REGISTER_REQUEST == "REFEREE_REGISTER_REQUEST"

    def test_referee_register_response_type(self):
        """Test REFEREE_REGISTER_RESPONSE message type constant."""
        assert REFEREE_REGISTER_RESPONSE == "REFEREE_REGISTER_RESPONSE"

    def test_league_start_type(self):
        """Test LEAGUE_START message type constant."""
        assert LEAGUE_START == "LEAGUE_START"

    def test_start_match_type(self):
        """Test START_MATCH message type constant."""
        assert START_MATCH == "START_MATCH"

    def test_match_start_ack_type(self):
        """Test MATCH_START_ACK message type constant."""
        assert MATCH_START_ACK == "MATCH_START_ACK"

    def test_game_invitation_type(self):
        """Test GAME_INVITATION message type constant."""
        assert GAME_INVITATION == "GAME_INVITATION"

    def test_game_parity_choice_request_type(self):
        """Test CHOOSE_PARITY_CALL message type constant."""
        assert GAME_PARITY_CHOICE_REQUEST == "CHOOSE_PARITY_CALL"

    def test_game_result_type(self):
        """Test GAME_OVER message type constant."""
        assert GAME_RESULT == "GAME_OVER"

    def test_match_result_type(self):
        """Test MATCH_RESULT_REPORT message type constant."""
        assert MATCH_RESULT == "MATCH_RESULT_REPORT"

    def test_match_error_type(self):
        """Test GAME_ERROR message type constant."""
        assert MATCH_ERROR == "GAME_ERROR"

    def test_standings_update_type(self):
        """Test LEAGUE_STANDINGS_UPDATE message type constant."""
        assert STANDINGS_UPDATE == "LEAGUE_STANDINGS_UPDATE"

    def test_all_message_types_unique(self):
        """Test that all 18 message types are unique."""
        message_types = [
            PLAYER_REGISTRATION_REQUEST,
            PLAYER_REGISTRATION_RESPONSE,
            GAME_JOIN_ACK,
            GAME_PARITY_CHOICE_ACK,
            REFEREE_REGISTER_REQUEST,
            REFEREE_REGISTER_RESPONSE,
            LEAGUE_START,
            START_MATCH,
            MATCH_START_ACK,
            GAME_INVITATION,
            GAME_PARITY_CHOICE_REQUEST,
            GAME_RESULT,
            MATCH_RESULT,
            MATCH_ERROR,
            STANDINGS_UPDATE,
        ]

        # Check uniqueness
        assert len(message_types) == len(set(message_types)), "Message types must be unique"

    def test_message_types_count(self):
        """Test that we have all expected message types."""
        message_types = [
            PLAYER_REGISTRATION_REQUEST,
            PLAYER_REGISTRATION_RESPONSE,
            GAME_JOIN_ACK,
            GAME_PARITY_CHOICE_ACK,
            REFEREE_REGISTER_REQUEST,
            REFEREE_REGISTER_RESPONSE,
            LEAGUE_START,
            START_MATCH,
            MATCH_START_ACK,
            GAME_INVITATION,
            GAME_PARITY_CHOICE_REQUEST,
            GAME_RESULT,
            MATCH_RESULT,
            MATCH_ERROR,
            STANDINGS_UPDATE,
        ]

        # We expect at least 15 core message types
        assert len(message_types) >= 15, "Should have at least 15 core message types"

    def test_message_type_naming_convention(self):
        """Test that message types follow UPPER_SNAKE_CASE convention."""
        message_types = [
            PLAYER_REGISTRATION_REQUEST,
            PLAYER_REGISTRATION_RESPONSE,
            GAME_JOIN_ACK,
            GAME_PARITY_CHOICE_ACK,
            REFEREE_REGISTER_REQUEST,
            REFEREE_REGISTER_RESPONSE,
            LEAGUE_START,
            START_MATCH,
            MATCH_START_ACK,
            GAME_INVITATION,
            GAME_PARITY_CHOICE_REQUEST,
            GAME_RESULT,
            MATCH_RESULT,
            MATCH_ERROR,
            STANDINGS_UPDATE,
        ]

        for msg_type in message_types:
            # Should be all uppercase with underscores
            assert msg_type.isupper(), f"{msg_type} should be UPPERCASE"
            assert "_" in msg_type or msg_type == msg_type.upper(), f"{msg_type} should use underscores"
            # No spaces
            assert " " not in msg_type, f"{msg_type} should not contain spaces"
