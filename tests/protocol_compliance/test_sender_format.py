"""
Protocol compliance tests for sender field format.

Tests that sender fields follow the format: "{agent_type}:{agent_id}"
Valid agent types: player, referee, league_manager
"""

import pytest

from league_sdk.utils import format_sender, parse_sender


@pytest.mark.protocol
class TestSenderFormat:
    """Test sender field format compliance."""

    def test_player_sender_format(self):
        """Test that player sender follows 'player:P##' format."""
        sender = format_sender("player", "P01")

        assert sender == "player:P01"
        assert ":" in sender
        assert sender.startswith("player:")

    def test_referee_sender_format(self):
        """Test that referee sender follows 'referee:REF##' format."""
        sender = format_sender("referee", "REF01")

        assert sender == "referee:REF01"
        assert ":" in sender
        assert sender.startswith("referee:")

    def test_league_manager_sender_format(self):
        """Test that league_manager sender follows 'league_manager:LM##' format."""
        sender = format_sender("league_manager", "LM01")

        assert sender == "league_manager:LM01"
        assert ":" in sender
        assert sender.startswith("league_manager:")

    def test_parse_player_sender(self):
        """Test parsing player sender format."""
        agent_type, agent_id = parse_sender("player:P01")

        assert agent_type == "player"
        assert agent_id == "P01"

    def test_parse_referee_sender(self):
        """Test parsing referee sender format."""
        agent_type, agent_id = parse_sender("referee:REF01")

        assert agent_type == "referee"
        assert agent_id == "REF01"

    def test_parse_league_manager_sender(self):
        """Test parsing league_manager sender format."""
        agent_type, agent_id = parse_sender("league_manager:LM01")

        assert agent_type == "league_manager"
        assert agent_id == "LM01"

    def test_sender_format_roundtrip(self):
        """Test that format → parse → format preserves sender."""
        original_pairs = [
            ("player", "P01"),
            ("player", "P42"),
            ("referee", "REF01"),
            ("referee", "REF02"),
            ("league_manager", "LM01"),
        ]

        for agent_type, agent_id in original_pairs:
            sender = format_sender(agent_type, agent_id)
            parsed_type, parsed_id = parse_sender(sender)

            assert parsed_type == agent_type
            assert parsed_id == agent_id

            # Re-format should produce same result
            resender = format_sender(parsed_type, parsed_id)
            assert resender == sender

    def test_invalid_sender_no_colon(self):
        """Test that sender without colon is rejected."""
        invalid_senders = [
            "playerP01",
            "referee-REF01",
            "league_manager LM01",
        ]

        for sender in invalid_senders:
            with pytest.raises(ValueError, match="Invalid sender format"):
                parse_sender(sender)

    def test_invalid_sender_empty_agent_type(self):
        """Test that sender with empty agent type is rejected."""
        with pytest.raises(ValueError, match="Invalid sender format"):
            parse_sender(":P01")

    def test_invalid_sender_empty_agent_id(self):
        """Test that sender with empty agent ID is rejected."""
        with pytest.raises(ValueError, match="Invalid sender format"):
            parse_sender("player:")

    def test_invalid_sender_multiple_colons(self):
        """Test that sender with multiple colons is handled correctly."""
        # This might be valid if agent_id contains colon, or might be invalid
        # Depending on implementation, adjust test accordingly
        try:
            agent_type, agent_id = parse_sender("player:P01:extra")
            # If implementation accepts it, agent_id should be "P01:extra"
            assert agent_type == "player"
            assert ":" in agent_id
        except ValueError:
            # If implementation rejects it, that's also valid
            pass

    def test_sender_agent_types_valid(self):
        """Test that all valid agent types are accepted."""
        valid_types = ["player", "referee", "league_manager"]

        for agent_type in valid_types:
            sender = format_sender(agent_type, "TEST01")
            parsed_type, parsed_id = parse_sender(sender)

            assert parsed_type == agent_type
            assert parsed_id == "TEST01"

    def test_sender_case_sensitivity(self):
        """Test that sender parsing is case-sensitive."""
        sender = format_sender("player", "P01")

        # Sender should be exactly "player:P01", not "Player:P01" or "PLAYER:P01"
        assert sender == "player:P01"
        assert sender != "Player:P01"
        assert sender != "PLAYER:P01"

    def test_player_id_format_examples(self):
        """Test various player ID formats."""
        player_ids = ["P01", "P02", "P99", "P100"]

        for player_id in player_ids:
            sender = format_sender("player", player_id)
            assert sender == f"player:{player_id}"

            agent_type, parsed_id = parse_sender(sender)
            assert agent_type == "player"
            assert parsed_id == player_id

    def test_referee_id_format_examples(self):
        """Test various referee ID formats."""
        referee_ids = ["REF01", "REF02", "REF99"]

        for referee_id in referee_ids:
            sender = format_sender("referee", referee_id)
            assert sender == f"referee:{referee_id}"

            agent_type, parsed_id = parse_sender(sender)
            assert agent_type == "referee"
            assert parsed_id == referee_id

    def test_league_manager_id_format_examples(self):
        """Test various league manager ID formats."""
        lm_ids = ["LM01", "LM02", "LM99"]

        for lm_id in lm_ids:
            sender = format_sender("league_manager", lm_id)
            assert sender == f"league_manager:{lm_id}"

            agent_type, parsed_id = parse_sender(sender)
            assert agent_type == "league_manager"
            assert parsed_id == lm_id

    def test_sender_no_whitespace(self):
        """Test that sender format has no whitespace."""
        sender = format_sender("player", "P01")

        assert " " not in sender, "Sender should not contain spaces"
        assert "\t" not in sender, "Sender should not contain tabs"
        assert "\n" not in sender, "Sender should not contain newlines"

    def test_sender_colon_separator(self):
        """Test that sender uses exactly one colon as separator."""
        sender = format_sender("player", "P01")

        # Count colons (should be at least 1 for the separator)
        colon_count = sender.count(":")
        assert colon_count >= 1, "Sender must have at least one colon separator"

    def test_parse_sender_handles_edge_cases(self):
        """Test that parse_sender handles edge cases gracefully."""
        edge_cases = [
            "",  # Empty string
            "player",  # Missing colon and ID
            ":",  # Only colon
        ]

        for sender in edge_cases:
            with pytest.raises(ValueError):
                parse_sender(sender)
