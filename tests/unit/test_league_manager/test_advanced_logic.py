import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.league_manager.server import LeagueManager

from league_sdk.repositories import StandingsRepository


@pytest.fixture
def repo():
    # Setup mock repo with basic functionality
    mock_repo = MagicMock(spec=StandingsRepository)
    mock_repo.load.return_value = {"standings": []}
    return mock_repo


def test_standings_sorting_tiebreaker(repo):
    """Test that standings sort by points (primary) and wins (tiebreaker)."""

    # We'll mock atomic_write to avoid actual file I/O
    with patch("league_sdk.repositories.atomic_write") as mock_write, patch(
        "league_sdk.repositories.StandingsRepository.load"
    ) as mock_load:
        # Setup initial unordered state
        mock_load.return_value = {
            "standings": [
                {"player_id": "P2", "points": 3, "wins": 0},  # High points, low wins
                {"player_id": "P3", "points": 3, "wins": 1},  # High points, high wins (Winner)
                {"player_id": "P1", "points": 1, "wins": 0},  # Low points
            ]
        }

        # Create instance (using the patched class logic if possible, or just the method)
        # Note: We are testing the logic in the repo method.
        real_repo = StandingsRepository("test_league")

        # Trigger update (dummy update to trigger sort)
        real_repo.update_player("P1", "LOSS", 0)

        # Capture what was saved
        # atomic_write is called inside save()
        assert mock_write.called
        args = mock_write.call_args[0]
        saved_data = args[1]
        standings = saved_data["standings"]

        print(f"DEBUG: Saved standings order: {[s['player_id'] for s in standings]}")

        # Check order: P3 (3 pts, 1 win) -> P2 (3 pts, 0 wins) -> P1 (1 pt, 0 wins)
        # Note: P1 is updated, so its stats might change slightly but sort logic should hold.
        # P1 started with 1 pt, 0 wins. Added 0 pts. Total 1 pt.

        assert standings[0]["player_id"] == "P3"
        assert standings[1]["player_id"] == "P2"
        assert standings[2]["player_id"] == "P1"


@pytest.mark.asyncio
async def test_round_completion_broadcast():
    """Test that League Manager broadcasts ROUND_COMPLETED when all matches finish."""

    with patch("agents.league_manager.server.load_system_config"), patch(
        "agents.league_manager.server.load_agents_config"
    ) as mock_agents_config, patch("agents.league_manager.server.load_league_config"):
        # Mock agents config to have players
        mock_agents_config.return_value = {
            "players": [
                {"agent_id": "P01", "endpoint": "http://p1"},
                {"agent_id": "P02", "endpoint": "http://p2"},
            ]
        }

        lm = LeagueManager(agent_id="LM01")
        lm.rounds_repo = MagicMock()
        # Mock round completion broadcast to verify it's called
        lm._broadcast_round_completed = AsyncMock()

        # Populate registered players so broadcast has targets
        lm.registered_players = {"P01": {"endpoint": "http://p1"}, "P02": {"endpoint": "http://p2"}}

        # Setup round data: 2 matches, one already completed
        lm.rounds_repo.get_round.return_value = {
            "round_id": 1,
            "status": "PENDING",
            "matches": [
                {"match_id": "M1", "status": "COMPLETED"},
                {"match_id": "M2", "status": "PENDING"},
            ],
        }

        # Call update for the second match (M2) completing it
        await lm._update_round_and_check_completion(round_id=1, match_id="M2")

        # Verify repo updated status to COMPLETED
        lm.rounds_repo.update_round_status.assert_called_with(1, "COMPLETED")

        # Verify broadcast
        lm._broadcast_round_completed.assert_awaited()
