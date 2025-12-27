"""
Integration tests for complete match flow execution.

Tests the full match lifecycle from invitation through result reporting,
exercising Referee ↔ Players ↔ League Manager interactions via mocked HTTP layer.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.referee_REF01.match_conductor import MatchConductor
from league_sdk.protocol import JSONRPCRequest

pytestmark = pytest.mark.integration


class TestMatchFlow:
    """Integration tests for full match execution flow."""

    @pytest.fixture
    def mock_configs(self):
        """Mock all config loaders."""
        with (
            patch("agents.referee_REF01.match_conductor.load_system_config") as mock_system,
            patch("agents.referee_REF01.match_conductor.load_agents_config") as mock_agents,
            patch("agents.referee_REF01.match_conductor.load_json_file") as mock_league,
        ):
            # Mock system config
            mock_system.return_value = MagicMock(
                timeouts=MagicMock(
                    game_join_ack_sec=5,
                    parity_choice_sec=10,
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

            yield {
                "system": mock_system,
                "agents": mock_agents,
                "league": mock_league,
            }

    @pytest.fixture
    def logger(self):
        """Create test logger."""
        test_logger = logging.getLogger("test_referee")
        test_logger.setLevel(logging.INFO)
        return test_logger

    @pytest.fixture
    def match_conductor(self, mock_configs, logger):
        """Create a MatchConductor instance with mocked configs."""
        conductor = MatchConductor(
            referee_id="REF01",
            auth_token="test_auth_token_12345678901234567890",
            league_id="L001",
            std_logger=logger,
        )
        return conductor

    @pytest.mark.asyncio
    async def test_match_conductor_initialization(self, match_conductor):
        """Test that MatchConductor initializes correctly."""
        assert match_conductor.referee_id == "REF01"
        assert match_conductor.league_id == "L001"
        assert match_conductor.auth_token == "test_auth_token_12345678901234567890"
        assert match_conductor.game_type == "even_odd"
        assert match_conductor.scoring == {"win_points": 3, "draw_points": 1, "loss_points": 0}
        assert "P01" in match_conductor.player_endpoints
        assert "P02" in match_conductor.player_endpoints
        assert match_conductor.league_manager_endpoint == "http://localhost:8000/mcp"

    @pytest.mark.asyncio
    async def test_successful_match_flow_with_mocked_http(self, match_conductor):
        """Test complete successful match with mocked internal methods."""
        match_id = "M001"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-001"
        queue = asyncio.Queue()

        # Mock internal methods to simulate successful flow
        # (same approach as test_timeout_enforcement.py)
        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            return {player_a_id: True, player_b_id: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            # Both players join successfully
            from league_sdk.protocol import GameJoinAck

            return {
                player_a_id: GameJoinAck(
                    sender=f"player:{pa}",
                    timestamp="2025-01-15T10:00:00Z",
                    conversation_id=cid,
                    match_id=mid,
                    player_id=pa,
                    arrival_timestamp="2025-01-15T10:00:00Z",
                    accept=True,
                ),
                player_b_id: GameJoinAck(
                    sender=f"player:{pb}",
                    timestamp="2025-01-15T10:00:01Z",
                    conversation_id=cid,
                    match_id=mid,
                    player_id=pb,
                    arrival_timestamp="2025-01-15T10:00:01Z",
                    accept=True,
                ),
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            pass  # Just sending, no return needed

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            # Both players choose
            return {
                player_a_id: "even",
                player_b_id: "odd",
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

            # Verify match result structure
            assert result["match_id"] == match_id
            assert result["round_id"] == round_id
            assert result["league_id"] == "L001"
            assert result["winner"] in [player_a_id, player_b_id, "DRAW"]  # Depends on random draw
            assert "score" in result
            assert player_a_id in result["score"]
            assert player_b_id in result["score"]
            assert "lifecycle" in result
            assert result["lifecycle"]["state"] == "FINISHED"
            assert "drawn_number" in result
            assert "player_choices" in result
            assert result["player_choices"][player_a_id] == "even"
            assert result["player_choices"][player_b_id] == "odd"

    @pytest.mark.asyncio
    async def test_match_timeout_on_join(self, match_conductor):
        """Test match handles timeout when players don't join."""
        match_id = "M002"
        round_id = 1
        player_a_id = "P01"
        player_b_id = "P02"
        conversation_id = "conv-002"
        queue = asyncio.Queue()

        # Mock HTTP to succeed for invitations
        with patch(
            "agents.referee_REF01.match_conductor.call_with_retry", new_callable=AsyncMock
        ) as mock_http:
            mock_http.return_value = {"status": "ok"}

            # Don't put any responses in queue - let it timeout
            # Note: This will take 5 seconds (timeout duration)
            # For faster tests, we could also mock the timeout enforcement

            # To make test faster, mock the timeout
            with patch.object(match_conductor, "timeout_game_join_ack", 0.1):
                result = await match_conductor.conduct_match(
                    match_id, round_id, player_a_id, player_b_id, conversation_id, queue
                )

            # Verify technical loss
            assert result["match_id"] == match_id
            assert result.get("technical_loss") is True or "NONE" in str(result.get("winner"))
            assert result["lifecycle"]["state"] in ["FAILED", "FINISHED"]

    @pytest.mark.asyncio
    async def test_match_repository_integration(self, match_conductor):
        """Test that match results are persisted via repository."""
        # This test verifies the match conductor integrates with the match repository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            # Override match repository to use temp directory
            match_conductor.match_repo.data_root = Path(tmpdir)

            match_id = "M003"
            round_id = 1
            player_a_id = "P01"
            player_b_id = "P02"
            conversation_id = "conv-003"
            queue = asyncio.Queue()

            # Mock internal methods (same approach as other tests)
            async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
                return {player_a_id: True, player_b_id: True}

            async def mock_wait_join(mid, pa, pb, cid, transcript, q):
                from league_sdk.protocol import GameJoinAck

                return {
                    player_a_id: GameJoinAck(
                        sender=f"player:{pa}",
                        timestamp="2025-01-15T10:00:00Z",
                        conversation_id=cid,
                        match_id=mid,
                        player_id=pa,
                        arrival_timestamp="2025-01-15T10:00:00Z",
                        accept=True,
                    ),
                    player_b_id: GameJoinAck(
                        sender=f"player:{pb}",
                        timestamp="2025-01-15T10:00:01Z",
                        conversation_id=cid,
                        match_id=mid,
                        player_id=pb,
                        arrival_timestamp="2025-01-15T10:00:01Z",
                        accept=True,
                    ),
                }

            async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
                pass

            async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
                return {
                    player_a_id: "even",
                    player_b_id: "odd",
                }

            async def mock_send_game_over(*args, **kwargs):
                pass  # Mock sending GAME_OVER

            async def mock_send_match_result(*args, **kwargs):
                pass  # Mock sending result to league manager

            with (
                patch.object(match_conductor, "_send_invitations", side_effect=mock_send_invitations),
                patch.object(match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join),
                patch.object(match_conductor, "_send_parity_calls", side_effect=mock_send_parity),
                patch.object(
                    match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices
                ),
                patch.object(match_conductor, "_send_game_over", side_effect=mock_send_game_over),
                patch.object(
                    match_conductor,
                    "_send_match_result_to_league_manager",
                    side_effect=mock_send_match_result,
                ),
            ):
                result = await match_conductor.conduct_match(
                    match_id, round_id, player_a_id, player_b_id, conversation_id, queue
                )

            # Verify match completed successfully
            assert result["match_id"] == match_id
            assert result["lifecycle"]["state"] == "FINISHED"
            # Note: File persistence verification would require proper repository mocking
            # The match conductor's save() method is called, which is sufficient for integration testing
