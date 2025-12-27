from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from league_sdk.protocol import JSONRPCRequest

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
            network=MagicMock(request_timeout_sec=10),
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

        lm = LeagueManager(agent_id="LM01", league_id="league_2025_even_odd")
        lm.registered_players = {"P01": {"sender": "player:P01", "auth_token": "tok-p01"}}
        lm.registered_referees = {"REF01": {"sender": "referee:REF01", "auth_token": "tok-ref"}}
        lm.standings_repo = MagicMock()
        lm.standings_repo.load.return_value = {"standings": [{"player_id": "P01", "points": 3}]}
        return lm


@pytest.mark.asyncio
async def test_league_query_get_standings(league_manager):
    request = JSONRPCRequest(
        id=1,
        method="LEAGUE_QUERY",
        params={
            "protocol": "league.v2",
            "message_type": "LEAGUE_QUERY",
            "sender": "player:P01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-q-1",
            "auth_token": "tok-p01",
            "league_id": "league_2025_even_odd",
            "query_type": "GET_STANDINGS",
            "query_params": {},
        },
    )

    response = await league_manager._handle_league_query(request)
    assert response.status_code == 200
    body = response.body.decode()
    assert "LEAGUE_QUERY_RESPONSE" in body
    assert "standings" in body


@pytest.mark.asyncio
async def test_get_standings_tool(league_manager):
    request = JSONRPCRequest(
        id=2,
        method="get_standings",
        params={
            "protocol": "league.v2",
            "sender": "player:P01",
            "auth_token": "tok-p01",
        },
    )

    response = await league_manager._handle_get_standings(request)
    assert response.status_code == 200
    body = response.body.decode()
    assert "standings" in body


@pytest.mark.asyncio
async def test_start_league_tool_triggers_start(league_manager):
    league_manager.start_league = AsyncMock(return_value={"total_rounds": 1})
    request = JSONRPCRequest(
        id=3,
        method="start_league",
        params={
            "protocol": "league.v2",
            "sender": "referee:REF01",
            "auth_token": "tok-ref",
            "league_id": "league_2025_even_odd",
        },
    )

    response = await league_manager._handle_start_league(request)
    assert response.status_code == 200
    league_manager.start_league.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_league_status_tool(league_manager):
    request = JSONRPCRequest(
        id=4,
        method="get_league_status",
        params={
            "protocol": "league.v2",
            "sender": "referee:REF01",
            "auth_token": "tok-ref",
        },
    )

    response = await league_manager._handle_get_league_status(request)
    assert response.status_code == 200
    body = response.body.decode()
    assert "get_league_status" in body


@pytest.mark.asyncio
async def test_get_league_status_missing_auth_returns_401(league_manager):
    request = JSONRPCRequest(
        id=5,
        method="get_league_status",
        params={
            "protocol": "league.v2",
            "sender": "referee:REF01",
        },
    )

    response = await league_manager._handle_get_league_status(request)
    assert response.status_code == 401
    body = response.body.decode()
    assert "Missing auth token" in body


@pytest.mark.asyncio
async def test_get_standings_missing_sender_returns_400(league_manager):
    league_manager.system_config.security.allow_start_league_without_auth = False
    request = JSONRPCRequest(
        id=6,
        method="get_standings",
        params={
            "protocol": "league.v2",
        },
    )

    response = await league_manager._handle_get_standings(request)
    assert response.status_code == 400
    body = response.body.decode()
    assert "Missing sender" in body
