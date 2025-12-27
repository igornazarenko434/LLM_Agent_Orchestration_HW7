"""
Integration tests for timeout enforcement across match lifecycle.

Tests various timeout scenarios including join timeouts, choice timeouts,
and combinations thereof.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.referee_REF01.match_conductor import MatchConductor

# Message type constants
GAME_JOIN_ACK = "GAME_JOIN_ACK"
GAME_PARITY_CHOICE_ACK = "CHOOSE_PARITY_RESPONSE"


@pytest.mark.integration
class TestTimeoutEnforcement:
    """Integration tests for timeout enforcement."""

    @pytest.fixture
    def match_conductor(self):
        """Create a MatchConductor with short timeouts for testing."""
        with (
            patch("agents.referee_REF01.match_conductor.load_system_config") as mock_system,
            patch("agents.referee_REF01.match_conductor.load_agents_config") as mock_agents,
            patch("agents.referee_REF01.match_conductor.load_json_file") as mock_league,
        ):
            # Mock system config with SHORT timeouts for testing
            mock_system.return_value = MagicMock(
                timeouts=MagicMock(
                    game_join_ack_sec=1,  # 1 second for fast testing
                    parity_choice_sec=2,  # 2 seconds for fast testing
                ),
            )

            # Mock agents config
            mock_agents.return_value = {
                "league_manager": {"endpoint": "http://localhost:8000/mcp"},
                "players": [
                    {"agent_id": "P01", "endpoint": "http://localhost:9001/mcp"},
                    {"agent_id": "P02", "endpoint": "http://localhost:9002/mcp"},
                ],
            }

            # Mock league config
            mock_league.return_value = {
                "game_type": "even_odd",
                "scoring": {"win_points": 3, "draw_points": 1, "loss_points": 0},
            }

            # Create logger
            logger = logging.getLogger("test_referee_timeout")
            logger.setLevel(logging.INFO)

            conductor = MatchConductor(
                referee_id="REF01",
                auth_token="test_auth_token_12345678901234567890",
                league_id="L001",
                std_logger=logger,
            )
            return conductor

    @pytest.mark.asyncio
    async def test_join_timeout_player_a(self, match_conductor):
        """Test timeout when Player A fails to join."""
        match_id = "M_TIMEOUT_1"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-1"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            # Player A times out, Player B joins
            return {
                player_a_id: None,  # Timeout
                player_b_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"status": "JOINED"},
                },
            }

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for Player A (one player timeout)
        assert result["winner"] == player_b_id  # Player B wins
        assert result["technical_loss"] is True
        assert result["offending_player"] == player_a_id
        assert result["lifecycle"]["state"] == "FINISHED"  # Not FAILED for single timeout

    @pytest.mark.asyncio
    async def test_join_timeout_player_b(self, match_conductor):
        """Test timeout when Player B fails to join."""
        match_id = "M_TIMEOUT_2"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-2"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            # Player A joins, Player B times out
            return {
                player_a_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"status": "JOINED"},
                },
                player_b_id: None,  # Timeout
            }

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for Player B (one player timeout)
        assert result["winner"] == player_a_id  # Player A wins
        assert result["technical_loss"] is True
        assert result["offending_player"] == player_b_id
        assert result["lifecycle"]["state"] == "FINISHED"  # Not FAILED for single timeout

    @pytest.mark.asyncio
    async def test_join_timeout_both_players(self, match_conductor):
        """Test timeout when both players fail to join."""
        match_id = "M_TIMEOUT_3"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-3"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            # Both players timeout
            return {player_a_id: None, player_b_id: None}

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for both (both players timeout)
        assert result["winner"] == "NONE"
        assert result["technical_loss"] is True
        assert "reason" in result  # Only present when both timeout
        assert (
            "both players timed out" in result["reason"].lower()
            or "timed out" in result["reason"].lower()
        )
        assert result["lifecycle"]["state"] == "FAILED"  # FAILED when both timeout

    @pytest.mark.asyncio
    async def test_choice_timeout_player_a(self, match_conductor):
        """Test timeout when Player A fails to submit parity choice."""
        match_id = "M_TIMEOUT_4"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-4"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            return {
                player_a_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"status": "JOINED"},
                },
                player_b_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            # Player A times out, Player B chooses
            return {
                player_a_id: None,  # Timeout
                player_b_id: {
                    "message_type": GAME_PARITY_CHOICE_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"parity_choice": "even", "number": 4},
                },
            }

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
            patch.object(match_conductor, "_send_parity_calls", side_effect=mock_send_parity),
            patch.object(match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for Player A (one player timeout on parity choice)
        assert result["winner"] == player_b_id  # Player B wins
        assert result["technical_loss"] is True
        assert result["offending_player"] == player_a_id
        assert result["lifecycle"]["state"] == "FINISHED"  # Not FAILED for single timeout

    @pytest.mark.asyncio
    async def test_choice_timeout_player_b(self, match_conductor):
        """Test timeout when Player B fails to submit parity choice."""
        match_id = "M_TIMEOUT_5"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-5"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            return {
                player_a_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"status": "JOINED"},
                },
                player_b_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            # Player A chooses, Player B times out
            return {
                player_a_id: {
                    "message_type": GAME_PARITY_CHOICE_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"parity_choice": "odd", "number": 7},
                },
                player_b_id: None,  # Timeout
            }

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
            patch.object(match_conductor, "_send_parity_calls", side_effect=mock_send_parity),
            patch.object(match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for Player B (one player timeout on parity choice)
        assert result["winner"] == player_a_id  # Player A wins
        assert result["technical_loss"] is True
        assert result["offending_player"] == player_b_id
        assert result["lifecycle"]["state"] == "FINISHED"  # Not FAILED for single timeout

    @pytest.mark.asyncio
    async def test_choice_timeout_both_players(self, match_conductor):
        """Test timeout when both players fail to submit parity choices."""
        match_id = "M_TIMEOUT_6"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-6"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            return {
                player_a_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"status": "JOINED"},
                },
                player_b_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            # Both players timeout
            return {player_a_id: None, player_b_id: None}

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
            patch.object(match_conductor, "_send_parity_calls", side_effect=mock_send_parity),
            patch.object(match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Verify technical loss for both (both players timeout on parity choice)
        assert result["winner"] == "NONE"
        assert result["technical_loss"] is True
        assert "reason" in result  # Only present when both timeout
        assert (
            "both players timed out" in result["reason"].lower()
            or "timed out" in result["reason"].lower()
        )
        assert result["lifecycle"]["state"] == "FAILED"  # FAILED when both timeout

    @pytest.mark.asyncio
    async def test_timeout_recovery_one_player_succeeds(self, match_conductor):
        """Test that if one player times out, the other gets credited correctly."""
        match_id = "M_TIMEOUT_7"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-timeout-7"
        queue = asyncio.Queue()

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            return {
                player_a_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"status": "JOINED"},
                },
                player_b_id: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{player_b_id}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            # Player A chooses successfully, Player B times out
            return {
                player_a_id: {
                    "message_type": GAME_PARITY_CHOICE_ACK,
                    "sender": f"player:{player_a_id}",
                    "payload": {"parity_choice": "even", "number": 8},
                },
                player_b_id: None,  # Timeout
            }

        with (
            patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
            patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
            patch.object(match_conductor, "_send_parity_calls", side_effect=mock_send_parity),
            patch.object(match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices),
        ):
            result = await match_conductor.conduct_match(
                match_id, round_id, player_a_id, player_b_id, conversation_id, queue
            )

        # Player A wins because Player B timed out (one player timeout)
        assert result["winner"] == player_a_id
        assert result["technical_loss"] is True
        assert result["offending_player"] == player_b_id
        assert result["lifecycle"]["state"] == "FINISHED"
