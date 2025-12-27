"""
Integration test for League Manager match result reporting (M7.12).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from league_sdk.protocol import JSONRPCRequest
from league_sdk.repositories import RoundsRepository, StandingsRepository

from agents.league_manager.server import LeagueManager


@pytest.mark.asyncio
async def test_match_result_reporting_updates_standings_and_rounds(tmp_path):
    """Match result report is accepted, processed, and updates standings/rounds."""
    with patch("agents.league_manager.server.load_system_config") as mock_system_config, patch(
        "agents.league_manager.server.load_agents_config"
    ) as mock_agents_config, patch(
        "agents.league_manager.server.load_league_config"
    ) as mock_league_config, patch(
        "agents.league_manager.server.get_retention_config"
    ) as mock_retention, patch(
        "agents.league_manager.server.StandingsRepository"
    ) as mock_standings_repo, patch(
        "agents.league_manager.server.RoundsRepository"
    ) as mock_rounds_repo:
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {}
        mock_league_config.return_value = MagicMock(
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0}
        )
        mock_retention.return_value = {"enabled": False}

        mock_standings_repo.side_effect = lambda league_id: StandingsRepository(
            league_id=league_id, data_root=tmp_path
        )
        mock_rounds_repo.side_effect = lambda league_id: RoundsRepository(
            league_id=league_id, data_root=tmp_path
        )

        lm = LeagueManager(agent_id="LM01", league_id="league_test")
        lm._broadcast_to_players = AsyncMock()
        lm._broadcast_round_completed = AsyncMock()

        lm.registered_referees = {
            "REF01": {
                "referee_id": "REF01",
                "sender": "referee:REF01",
                "auth_token": "token-1",
            }
        }

        lm.rounds_repo.add_round(
            round_id=1,
            matches=[
                {
                    "match_id": "R1M1",
                    "league_id": "league_test",
                    "round_id": 1,
                    "game_type": "even_odd",
                    "player_a_id": "P01",
                    "player_b_id": "P02",
                    "referee_id": "REF01",
                    "status": "PENDING",
                }
            ],
        )

        await lm.standings_processor.start()

        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="MATCH_RESULT_REPORT",
            params={
                "sender": "referee:REF01",
                "auth_token": "token-1",
                "protocol": "league.v2",
                "message_type": "MATCH_RESULT_REPORT",
                "timestamp": "2025-01-01T00:00:00Z",
                "conversation_id": "conv-1",
                "league_id": "league_test",
                "round_id": 1,
                "match_id": "R1M1",
                "game_type": "even_odd",
                "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}},
            },
            id=1,
        )

        response = await lm._handle_match_result_report(request)
        assert response.status_code == 200

        await lm.standings_processor.queue.join()

        standings = lm.standings_repo.load()
        assert len(standings.get("standings", [])) == 2

        round_data = lm.rounds_repo.get_round(1)
        assert round_data["status"] == "COMPLETED"
        assert round_data["matches"][0]["status"] == "COMPLETED"

        lm._broadcast_to_players.assert_awaited()
        lm._broadcast_round_completed.assert_awaited_once()

        await lm.standings_processor.stop(timeout=1.0)
