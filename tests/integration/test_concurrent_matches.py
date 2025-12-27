"""
Integration tests for concurrent match execution.

Tests that multiple matches can run in parallel without interference,
message cross-contamination, or deadlocks.
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
@pytest.mark.slow
class TestConcurrentMatches:
    """Integration tests for concurrent match execution."""

    @pytest.fixture
    def match_conductor(self):
        """Create a MatchConductor instance with mocked configs."""
        with patch("agents.referee_REF01.match_conductor.load_system_config") as mock_system, patch(
            "agents.referee_REF01.match_conductor.load_agents_config"
        ) as mock_agents, patch("agents.referee_REF01.match_conductor.load_json_file") as mock_league:
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
                    {"agent_id": "P03", "endpoint": "http://localhost:9003/mcp"},
                    {"agent_id": "P04", "endpoint": "http://localhost:9004/mcp"},
                ],
            }

            # Mock league config
            mock_league.return_value = {
                "game_type": "even_odd",
                "scoring": {"win_points": 3, "draw_points": 1, "loss_points": 0},
            }

            # Create logger
            logger = logging.getLogger("test_concurrent_matches")
            logger.setLevel(logging.INFO)

            conductor = MatchConductor(
                referee_id="REF01",
                auth_token="test_auth_token_12345678901234567890",
                league_id="L001",
                std_logger=logger,
            )
            return conductor

    @pytest.mark.asyncio
    async def test_two_concurrent_matches(self, match_conductor):
        """Test that 2 matches can run concurrently without interference."""

        # Mock functions for successful match flow
        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.01)  # Simulate network delay
            return {pa: True, pb: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.02)
            return {
                pa: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pa}",
                    "payload": {"status": "JOINED"},
                },
                pb: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pb}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.01)

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.02)
            # Deterministic choices based on player ID
            return {
                pa: "even",
                pb: "odd",
            }

        async def mock_send_game_over(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_send_match_result(*args, **kwargs):
            await asyncio.sleep(0.01)

        with patch.object(
            match_conductor, "_send_invitations", side_effect=mock_send_invitations
        ), patch.object(
            match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join
        ), patch.object(
            match_conductor, "_send_parity_calls", side_effect=mock_send_parity
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices
        ), patch.object(
            match_conductor, "_send_game_over", side_effect=mock_send_game_over
        ), patch.object(
            match_conductor, "_send_match_result_to_league_manager", side_effect=mock_send_match_result
        ):
            # Launch 2 matches concurrently
            queue1 = asyncio.Queue()
            queue2 = asyncio.Queue()

            match1_task = asyncio.create_task(
                match_conductor.conduct_match("M001", 1, "P01", "P02", "conv-001", queue1)
            )
            match2_task = asyncio.create_task(
                match_conductor.conduct_match("M002", 1, "P03", "P04", "conv-002", queue2)
            )

            # Wait for both to complete
            results = await asyncio.gather(match1_task, match2_task)

            # Verify both matches completed successfully
            assert len(results) == 2
            assert results[0]["match_id"] == "M001"
            assert results[1]["match_id"] == "M002"
            assert results[0]["lifecycle"]["state"] == "FINISHED"
            assert results[1]["lifecycle"]["state"] == "FINISHED"

            # Verify no cross-contamination (each match has correct players)
            assert results[0]["score"]["P01"] is not None
            assert results[0]["score"]["P02"] is not None
            assert "P03" not in results[0]["score"]
            assert "P04" not in results[0]["score"]

            assert results[1]["score"]["P03"] is not None
            assert results[1]["score"]["P04"] is not None
            assert "P01" not in results[1]["score"]
            assert "P02" not in results[1]["score"]

    @pytest.mark.asyncio
    async def test_five_concurrent_matches(self, match_conductor):
        """Test that 5 matches can run concurrently."""

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.005)
            return {pa: True, pb: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.01)
            return {
                pa: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pa}",
                    "payload": {"status": "JOINED"},
                },
                pb: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pb}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.005)

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.01)
            return {
                pa: "even",
                pb: "odd",
            }

        async def mock_send_game_over(*args, **kwargs):
            await asyncio.sleep(0.005)

        async def mock_send_match_result(*args, **kwargs):
            await asyncio.sleep(0.005)

        with patch.object(
            match_conductor, "_send_invitations", side_effect=mock_send_invitations
        ), patch.object(
            match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join
        ), patch.object(
            match_conductor, "_send_parity_calls", side_effect=mock_send_parity
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices
        ), patch.object(
            match_conductor, "_send_game_over", side_effect=mock_send_game_over
        ), patch.object(
            match_conductor, "_send_match_result_to_league_manager", side_effect=mock_send_match_result
        ):
            # Launch 5 matches concurrently (reusing players for simplicity)
            tasks = []
            for i in range(5):
                queue = asyncio.Queue()
                task = asyncio.create_task(
                    match_conductor.conduct_match(f"M{i:03d}", 1, "P01", "P02", f"conv-{i:03d}", queue)
                )
                tasks.append(task)

            # Wait for all to complete
            results = await asyncio.gather(*tasks)

            # Verify all 5 matches completed
            assert len(results) == 5
            for i, result in enumerate(results):
                assert result["match_id"] == f"M{i:03d}"
                assert result["lifecycle"]["state"] == "FINISHED"

    @pytest.mark.asyncio
    async def test_concurrent_matches_with_one_failure(self, match_conductor):
        """Test that one match failure doesn't affect other concurrent matches."""

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.01)
            return {pa: True, pb: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.02)
            # Make match M001 fail by both players timing out
            if mid == "M001":
                return {pa: None, pb: None}  # Both players timeout
            return {
                pa: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pa}",
                    "payload": {"status": "JOINED"},
                },
                pb: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pb}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            await asyncio.sleep(0.01)

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            await asyncio.sleep(0.02)
            return {
                pa: "even",
                pb: "even",
            }

        async def mock_send_game_over(*args, **kwargs):
            await asyncio.sleep(0.01)

        async def mock_send_match_result(*args, **kwargs):
            await asyncio.sleep(0.01)

        with patch.object(
            match_conductor, "_send_invitations", side_effect=mock_send_invitations
        ), patch.object(
            match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join
        ), patch.object(
            match_conductor, "_send_parity_calls", side_effect=mock_send_parity
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices
        ), patch.object(
            match_conductor, "_send_game_over", side_effect=mock_send_game_over
        ), patch.object(
            match_conductor, "_send_match_result_to_league_manager", side_effect=mock_send_match_result
        ):
            queue1 = asyncio.Queue()
            queue2 = asyncio.Queue()
            queue3 = asyncio.Queue()

            match1_task = asyncio.create_task(
                match_conductor.conduct_match("M001", 1, "P01", "P02", "conv-001", queue1)
            )
            match2_task = asyncio.create_task(
                match_conductor.conduct_match("M002", 1, "P03", "P04", "conv-002", queue2)
            )
            match3_task = asyncio.create_task(
                match_conductor.conduct_match("M003", 1, "P01", "P03", "conv-003", queue3)
            )

            results = await asyncio.gather(match1_task, match2_task, match3_task)

            # Match 1 should fail (both players timeout)
            assert results[0]["technical_loss"] is True
            assert results[0]["winner"] == "NONE"
            assert "reason" in results[0]
            assert results[0]["lifecycle"]["state"] == "FAILED"

            # Matches 2 and 3 should succeed
            assert results[1]["lifecycle"]["state"] == "FINISHED"
            assert results[2]["lifecycle"]["state"] == "FINISHED"
            assert results[1].get("technical_loss") is None or results[1].get("technical_loss") is False
            assert results[2].get("technical_loss") is None or results[2].get("technical_loss") is False

    @pytest.mark.asyncio
    async def test_concurrent_matches_no_deadlock(self, match_conductor):
        """Test that concurrent matches don't deadlock."""

        async def mock_send_invitations(mid, rid, pa, pb, cid, transcript, message_queue=None):
            # Introduce variable delays to test for race conditions
            delay = 0.005 + (int(mid[1:]) % 3) * 0.002
            await asyncio.sleep(delay)
            return {pa: True, pb: True}

        async def mock_wait_join(mid, pa, pb, cid, transcript, q):
            delay = 0.01 + (int(mid[1:]) % 3) * 0.003
            await asyncio.sleep(delay)
            return {
                pa: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pa}",
                    "payload": {"status": "JOINED"},
                },
                pb: {
                    "message_type": GAME_JOIN_ACK,
                    "sender": f"player:{pb}",
                    "payload": {"status": "JOINED"},
                },
            }

        async def mock_send_parity(mid, rid, pa, pb, cid, transcript, message_queue=None):
            delay = 0.005 + (int(mid[1:]) % 3) * 0.002
            await asyncio.sleep(delay)

        async def mock_wait_choices(mid, pa, pb, cid, transcript, q):
            delay = 0.01 + (int(mid[1:]) % 3) * 0.003
            await asyncio.sleep(delay)
            return {
                pa: "even",
                pb: "odd",
            }

        async def mock_send_game_over(*args, **kwargs):
            delay = 0.005
            await asyncio.sleep(delay)

        async def mock_send_match_result(*args, **kwargs):
            delay = 0.005
            await asyncio.sleep(delay)

        with patch.object(
            match_conductor, "_send_invitations", side_effect=mock_send_invitations
        ), patch.object(
            match_conductor, "_wait_for_join_acks", side_effect=mock_wait_join
        ), patch.object(
            match_conductor, "_send_parity_calls", side_effect=mock_send_parity
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", side_effect=mock_wait_choices
        ), patch.object(
            match_conductor, "_send_game_over", side_effect=mock_send_game_over
        ), patch.object(
            match_conductor, "_send_match_result_to_league_manager", side_effect=mock_send_match_result
        ):
            # Launch 10 matches with variable delays
            tasks = []
            for i in range(10):
                queue = asyncio.Queue()
                task = asyncio.create_task(
                    match_conductor.conduct_match(f"M{i:03d}", 1, "P01", "P02", f"conv-{i:03d}", queue)
                )
                tasks.append(task)

            # Set a timeout to detect deadlock
            try:
                results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)
                assert len(results) == 10
                for result in results:
                    assert result["lifecycle"]["state"] == "FINISHED"
            except asyncio.TimeoutError:
                pytest.fail("Concurrent matches deadlocked (timeout after 5 seconds)")
