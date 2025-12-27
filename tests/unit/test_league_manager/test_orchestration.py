from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.league_manager.server import LeagueManager


@pytest.fixture
def league_manager():
    with (
        patch("agents.league_manager.server.load_system_config") as mock_system_config,
        patch("agents.league_manager.server.load_agents_config") as mock_agents_config,
        patch("agents.league_manager.server.load_league_config") as mock_league_config,
        patch("agents.league_manager.server.get_retention_config") as mock_retention,
    ):
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            protocol_version="league.v2",
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {
            "league_manager": {"port": 8000},
            "referees": [{"agent_id": "REF01", "endpoint": "http://ref1"}],
            "players": [{"agent_id": "P01", "endpoint": "http://p1"}],
        }
        mock_league_config.return_value = MagicMock(
            participants={"min_players": 2},
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0},
            game_type="even_odd",
        )
        mock_retention.return_value = {"enabled": False}

        lm = LeagueManager(agent_id="LM01", league_id="league_test")
        return lm


@pytest.mark.asyncio
async def test_start_league_requires_min_players(league_manager):
    league_manager.registered_players = {"P01": {}}
    league_manager.registered_referees = {"REF01": {}}
    with pytest.raises(ValueError):
        await league_manager.start_league()


@pytest.mark.asyncio
async def test_start_league_calls_manage_round(league_manager):
    league_manager.registered_players = {"P01": {}, "P02": {}}
    league_manager.registered_referees = {"REF01": {"contact_endpoint": "http://ref1"}}
    league_manager.create_schedule = MagicMock(return_value={"schedule": []})
    league_manager.manage_round = AsyncMock()

    result = await league_manager.start_league()

    assert result["schedule"] == []
    league_manager.manage_round.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_broadcast_round_announcement_payload(league_manager):
    league_manager.rounds_repo.get_round = MagicMock(
        return_value={
            "round_id": 1,
            "matches": [
                {
                    "match_id": "R1M1",
                    "game_type": "even_odd",
                    "player_a_id": "P01",
                    "player_b_id": "P02",
                    "referee_id": "REF01",
                }
            ],
        }
    )
    league_manager.registered_referees = {"REF01": {"contact_endpoint": "http://ref1"}}
    league_manager._broadcast_to_players = AsyncMock()

    await league_manager.broadcast_round_announcement(1)

    league_manager._broadcast_to_players.assert_awaited()
    payload = league_manager._broadcast_to_players.call_args[0][0]
    assert payload["round_id"] == 1
    assert payload["matches"][0]["referee_endpoint"] == "http://ref1"


@pytest.mark.asyncio
async def test_manage_round_starts_matches(league_manager):
    league_manager.rounds_repo.get_round = MagicMock(
        return_value={
            "round_id": 1,
            "matches": [
                {
                    "match_id": "R1M1",
                    "player_a_id": "P01",
                    "player_b_id": "P02",
                    "referee_id": "REF01",
                }
            ],
        }
    )
    league_manager.rounds_repo.update_round_status = MagicMock()
    league_manager.registered_referees = {"REF01": {"contact_endpoint": "http://ref1"}}
    league_manager.broadcast_round_announcement = AsyncMock()

    with patch("agents.league_manager.server.call_with_retry", new_callable=AsyncMock) as mock_retry:
        await league_manager.manage_round(1)
        league_manager.rounds_repo.update_round_status.assert_called_with(1, "IN_PROGRESS")
        mock_retry.assert_awaited()


@pytest.mark.asyncio
async def test_detect_league_completion(league_manager):
    league_manager.rounds_repo.load = MagicMock(
        return_value={"rounds": [{"round_id": 1, "status": "COMPLETED", "matches": []}]}
    )
    league_manager.identify_champion = MagicMock(return_value=({}, []))
    league_manager.broadcast_league_completed = AsyncMock()
    league_manager._on_league_completed_cleanup = AsyncMock()

    await league_manager.detect_league_completion()

    league_manager.broadcast_league_completed.assert_awaited_once()
    league_manager._on_league_completed_cleanup.assert_awaited_once()
