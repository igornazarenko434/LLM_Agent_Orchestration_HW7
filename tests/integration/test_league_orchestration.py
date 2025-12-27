from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from league_sdk.repositories import RoundsRepository, StandingsRepository

from agents.league_manager.server import LeagueManager


@pytest.mark.asyncio
async def test_league_orchestration_starts_rounds(tmp_path):
    with patch("agents.league_manager.server.load_system_config") as mock_system_config, patch(
        "agents.league_manager.server.load_agents_config"
    ) as mock_agents_config, patch(
        "agents.league_manager.server.load_league_config"
    ) as mock_league_config, patch(
        "agents.league_manager.server.get_retention_config"
    ) as mock_retention:
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
                {"agent_id": "P02", "endpoint": "http://p2"},
            ],
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": False}

        lm = LeagueManager(agent_id="LM01", league_id="league_test")
        lm.rounds_repo = RoundsRepository(league_id="league_test", data_root=tmp_path)
        lm.standings_repo = StandingsRepository(league_id="league_test", data_root=tmp_path)

        lm.registered_players = {"P01": {}, "P02": {}}
        lm.registered_referees = {"REF01": {"contact_endpoint": "http://ref1"}}

        lm._broadcast_to_players = AsyncMock()

        with patch(
            "agents.league_manager.server.call_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            schedule = lm.create_schedule()
            await lm.manage_round(1)

            assert schedule["total_rounds"] == 1
            mock_retry.assert_awaited()


@pytest.mark.asyncio
async def test_full_league_flow_completion(tmp_path):
    """
    Integration test for complete league flow (M7.13 DoD):
    - Complete matches
    - Drive round completion
    - Assert LEAGUE_COMPLETED with champion and standings
    """
    with patch("agents.league_manager.server.load_system_config") as mock_system_config, patch(
        "agents.league_manager.server.load_agents_config"
    ) as mock_agents_config, patch(
        "agents.league_manager.server.load_league_config"
    ) as mock_league_config, patch(
        "agents.league_manager.server.get_retention_config"
    ) as mock_retention, patch(
        "agents.league_manager.server.archive_old_matches", new_callable=AsyncMock
    ) as mock_archive:
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
                {"agent_id": "P02", "endpoint": "http://p2"},
                {"agent_id": "P03", "endpoint": "http://p3"},
            ],
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": True}

        # Mock archive cleanup stats
        from league_sdk.cleanup import CleanupStats

        archive_stats = CleanupStats()
        archive_stats.files_deleted = 5
        archive_stats.bytes_freed = 1024000
        mock_archive.return_value = archive_stats

        # Create League Manager instance
        lm = LeagueManager(agent_id="LM01", league_id="league_full_test")
        lm.rounds_repo = RoundsRepository(league_id="league_full_test", data_root=tmp_path)
        lm.standings_repo = StandingsRepository(league_id="league_full_test", data_root=tmp_path)

        # Register players
        lm.registered_players = {
            "P01": {"player_id": "P01", "display_name": "Player One"},
            "P02": {"player_id": "P02", "display_name": "Player Two"},
            "P03": {"player_id": "P03", "display_name": "Player Three"},
        }
        lm.registered_referees = {"REF01": {"contact_endpoint": "http://ref1"}}

        # Mock broadcasts
        lm._broadcast_to_players = AsyncMock()

        # Create schedule (3 players = 3 rounds in round-robin)
        schedule = lm.create_schedule()
        assert schedule["total_rounds"] == 3

        # Simulate Round 1 completion
        # Match 1: P01 vs P02 (P01 wins)
        result_1 = {
            "winner": "P01",
            "score": {"P01": 3, "P02": 0},
            "match_status": "COMPLETED",
            "player_a_status": "WIN",
            "player_b_status": "LOSS",
        }
        lm.update_standings(result_1)

        # Match 2: P01 vs P03 (P01 wins)
        result_2 = {
            "winner": "P01",
            "score": {"P01": 3, "P03": 0},
            "match_status": "COMPLETED",
            "player_a_status": "WIN",
            "player_b_status": "LOSS",
        }
        lm.update_standings(result_2)

        # Complete round 1
        round_data = lm.rounds_repo.get_round(1)
        for match in round_data["matches"]:
            match["status"] = "COMPLETED"
        lm.rounds_repo.update_round_status(1, "COMPLETED")

        # Simulate Round 2 completion
        # Match 3: P02 vs P03 (P02 wins)
        result_3 = {
            "winner": "P02",
            "score": {"P02": 3, "P03": 0},
            "match_status": "COMPLETED",
            "player_a_status": "WIN",
            "player_b_status": "LOSS",
        }
        lm.update_standings(result_3)

        # Complete round 2
        round_data = lm.rounds_repo.get_round(2)
        for match in round_data["matches"]:
            match["status"] = "COMPLETED"
        lm.rounds_repo.update_round_status(2, "COMPLETED")

        # Simulate Round 3 completion
        # Match 4: (depends on schedule, let's just mark it complete)
        # For 3 players round-robin, there should be 3 rounds
        round_data = lm.rounds_repo.get_round(3)
        for match in round_data["matches"]:
            match["status"] = "COMPLETED"
        lm.rounds_repo.update_round_status(3, "COMPLETED")

        # Trigger league completion detection
        await lm.detect_league_completion()

        # Verify league state
        assert lm.league_state == "COMPLETED"

        # Verify champion identification
        champion, final_standings = lm.identify_champion()
        assert champion["player_id"] == "P01"  # P01 has most points (6 from 2 wins)
        assert champion["points"] == 6
        assert len(final_standings) == 3
        assert final_standings[0]["rank"] == 1
        assert final_standings[1]["rank"] == 2
        assert final_standings[2]["rank"] == 3

        # Verify LEAGUE_COMPLETED broadcast was called
        # Check that _broadcast_to_players was called with "LEAGUE_COMPLETED"
        broadcast_calls = [
            call
            for call in lm._broadcast_to_players.call_args_list
            if len(call.args) >= 2 and call.args[1] == "LEAGUE_COMPLETED"
        ]
        assert len(broadcast_calls) >= 1, "LEAGUE_COMPLETED broadcast should have been called"

        # Verify league completion cleanup was called
        mock_archive.assert_awaited_once()
        assert mock_archive.call_args.kwargs["retention_days"] == 0  # Immediate archive
