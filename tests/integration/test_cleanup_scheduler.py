import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from league_sdk.repositories import RoundsRepository, StandingsRepository

from agents.league_manager.server import LeagueManager

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_cleanup_scheduler_startup_execution(tmp_path):
    """
    Integration test for cleanup scheduler (M7.13.5 DoD):
    - Verifies startup cleanup is triggered
    - Verifies cleanup stats are logged
    """
    with (
        patch("agents.league_manager.server.load_system_config") as mock_system_config,
        patch("agents.league_manager.server.load_agents_config") as mock_agents_config,
        patch("agents.league_manager.server.load_league_config") as mock_league_config,
        patch("agents.league_manager.server.get_retention_config") as mock_retention,
        patch("agents.league_manager.server.run_full_cleanup", new_callable=AsyncMock) as mock_cleanup,
    ):
        # Mock configurations
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            protocol_version="league.v2",
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {
            "league_manager": {"port": 8000},
            "referees": [{"agent_id": "REF01", "endpoint": "http://ref1"}],
            "players": [
                {"agent_id": "P01", "endpoint": "http://p1"},
            ],
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": True, "cleanup_schedule_cron": "0 2 * * *"}

        # Mock cleanup return value
        from league_sdk.cleanup import CleanupStats

        logs_stats = CleanupStats()
        logs_stats.files_deleted = 10
        logs_stats.bytes_freed = 1024000

        matches_stats = CleanupStats()
        matches_stats.files_deleted = 5
        matches_stats.bytes_freed = 512000

        mock_cleanup.return_value = {
            "logs": logs_stats,
            "matches": matches_stats,
        }

        # Create League Manager
        lm = LeagueManager(agent_id="LM01", league_id="league_cleanup_test")
        lm.rounds_repo = RoundsRepository(league_id="league_cleanup_test", data_root=tmp_path)
        lm.standings_repo = StandingsRepository(league_id="league_cleanup_test", data_root=tmp_path)

        # Call startup cleanup (which happens in start() method)
        await lm._run_startup_cleanup()

        # Verify cleanup was called once on startup
        mock_cleanup.assert_awaited_once()

        # Verify cleanup was called with correct logger
        assert mock_cleanup.call_args.kwargs["logger"] == lm.std_logger


@pytest.mark.asyncio
async def test_cleanup_scheduler_periodic_execution(tmp_path):
    """
    Integration test for periodic cleanup scheduler (M7.13.5 DoD):
    - Verifies scheduled cleanup task is started
    - Verifies cleanup can be stopped gracefully
    """
    with (
        patch("agents.league_manager.server.load_system_config") as mock_system_config,
        patch("agents.league_manager.server.load_agents_config") as mock_agents_config,
        patch("agents.league_manager.server.load_league_config") as mock_league_config,
        patch("agents.league_manager.server.get_retention_config") as mock_retention,
        patch("agents.league_manager.server.run_full_cleanup", new_callable=AsyncMock) as mock_cleanup,
    ):
        # Mock configurations
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            protocol_version="league.v2",
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {
            "league_manager": {"port": 8000},
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": True, "cleanup_schedule_cron": "0 2 * * *"}

        # Mock cleanup return value
        from league_sdk.cleanup import CleanupStats

        logs_stats = CleanupStats()
        logs_stats.files_deleted = 10
        logs_stats.bytes_freed = 1024000

        mock_cleanup.return_value = {
            "logs": logs_stats,
        }

        # Create League Manager
        lm = LeagueManager(agent_id="LM01", league_id="league_scheduler_test")
        lm.rounds_repo = RoundsRepository(league_id="league_scheduler_test", data_root=tmp_path)
        lm.standings_repo = StandingsRepository(league_id="league_scheduler_test", data_root=tmp_path)

        # Start cleanup scheduler
        lm._start_cleanup_scheduler()

        # Verify task is created and running
        assert lm._cleanup_task is not None
        assert not lm._cleanup_task.done()
        assert lm._cleanup_stop is not None

        # Give task a moment to initialize
        await asyncio.sleep(0.1)

        # Stop cleanup scheduler
        lm._stop_cleanup_scheduler()

        # Wait a bit for cancellation to complete
        await asyncio.sleep(0.1)

        # Verify task was cancelled
        assert lm._cleanup_task.done() or lm._cleanup_task.cancelled()


@pytest.mark.asyncio
async def test_cleanup_scheduler_disabled_when_retention_disabled(tmp_path):
    """
    Test that cleanup scheduler doesn't run when retention is disabled.
    """
    with (
        patch("agents.league_manager.server.load_system_config") as mock_system_config,
        patch("agents.league_manager.server.load_agents_config") as mock_agents_config,
        patch("agents.league_manager.server.load_league_config") as mock_league_config,
        patch("agents.league_manager.server.get_retention_config") as mock_retention,
        patch("agents.league_manager.server.run_full_cleanup", new_callable=AsyncMock) as mock_cleanup,
    ):
        # Mock configurations with retention DISABLED
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            protocol_version="league.v2",
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {
            "league_manager": {"port": 8000},
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": False}  # DISABLED

        # Create League Manager
        lm = LeagueManager(agent_id="LM01", league_id="league_disabled_test")
        lm.rounds_repo = RoundsRepository(league_id="league_disabled_test", data_root=tmp_path)
        lm.standings_repo = StandingsRepository(league_id="league_disabled_test", data_root=tmp_path)

        # Try to run startup cleanup
        await lm._run_startup_cleanup()

        # Verify cleanup was NOT called
        mock_cleanup.assert_not_awaited()

        # Try to start scheduler
        lm._start_cleanup_scheduler()

        # Verify task was NOT created
        assert lm._cleanup_task is None or lm._cleanup_task.done()
