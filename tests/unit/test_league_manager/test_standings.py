import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.league_manager.server import LeagueManager
from league_sdk.protocol import JSONRPCRequest


@pytest.fixture
def league_manager():
    # Mock configs to avoid loading files
    with (
        patch("agents.league_manager.server.load_system_config") as mock_system_config,
        patch("agents.league_manager.server.load_agents_config") as mock_agents_config,
        patch("agents.league_manager.server.load_league_config") as mock_league_config,
    ):
        mock_system_config.return_value = MagicMock(
            network=MagicMock(max_connections=100, request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=10),
            security=MagicMock(require_auth=True),
        )
        mock_agents_config.return_value = {}
        mock_league_config.return_value = MagicMock(
            scoring={"win_points": 3, "draw_points": 1, "loss_points": 0}
        )

        lm = LeagueManager(agent_id="LM01", league_id="test_league")
        # Mock repository
        lm.standings_repo = MagicMock()
        lm.standings_repo.load.return_value = {"standings": []}
        return lm


@pytest.mark.asyncio
async def test_handle_match_result_enqueues(league_manager):
    """Test that MATCH_RESULT_REPORT enqueues the task."""

    # Mock processor
    league_manager.standings_processor = AsyncMock()
    league_manager.registered_referees = {
        "REF01": {
            "referee_id": "REF01",
            "sender": "referee:REF01",
            "auth_token": "token-1",
        }
    }

    params = {
        "sender": "referee:REF01",
        "auth_token": "token-1",
        "match_id": "M1",
        "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}},
    }

    request = JSONRPCRequest(jsonrpc="2.0", method="MATCH_RESULT_REPORT", params=params, id=1)

    response = await league_manager._handle_match_result_report(request)

    assert response.status_code == 200
    league_manager.standings_processor.enqueue.assert_awaited_once_with(params)


@pytest.mark.asyncio
async def test_handle_match_result_rejects_unregistered_referee(league_manager):
    """Reject match results from unregistered referees."""
    league_manager.standings_processor = AsyncMock()

    params = {
        "sender": "referee:REF99",
        "auth_token": "token-unknown",
        "match_id": "M1",
        "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}},
    }

    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="MATCH_RESULT_REPORT",
        params=params,
        id=1,
    )

    response = await league_manager._handle_match_result_report(request)

    assert response.status_code == 403
    assert b"E004" in response.body
    league_manager.standings_processor.enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_match_result_rejects_invalid_token(league_manager):
    """Reject match results with invalid auth token."""
    league_manager.standings_processor = AsyncMock()
    league_manager.registered_referees = {
        "REF01": {
            "referee_id": "REF01",
            "sender": "referee:REF01",
            "auth_token": "token-good",
        }
    }

    params = {
        "sender": "referee:REF01",
        "auth_token": "token-bad",
        "match_id": "M1",
        "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}},
    }

    request = JSONRPCRequest(
        jsonrpc="2.0",
        method="MATCH_RESULT_REPORT",
        params=params,
        id=1,
    )

    response = await league_manager._handle_match_result_report(request)

    assert response.status_code == 401
    assert b"E012" in response.body
    league_manager.standings_processor.enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_match_result_updates_repo(league_manager):
    """Test that processing a result updates the repository."""

    # Mock broadcast to avoid network calls
    league_manager._broadcast_standings_update = AsyncMock()
    league_manager._update_round_and_check_completion = AsyncMock()
    league_manager.update_standings = MagicMock(return_value=["P01", "P02"])
    # Mock match validation to return True (match exists)
    league_manager._match_exists_in_schedule = MagicMock(return_value=True)

    report_data = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_REPORT",
        "sender": "referee:REF01",
        "timestamp": "2025-01-01T00:00:00Z",
        "conversation_id": "conv-1",
        "auth_token": "token",
        "league_id": "league_1",
        "round_id": 1,
        "match_id": "M1",
        "game_type": "even_odd",
        "result": {
            "winner": "P01",
            "score": {"P01": 3, "P02": 0},
            "match_status": "COMPLETED",
            "player_a_status": "WIN",
            "player_b_status": "LOSS",
        },
    }

    await league_manager._process_match_result(report_data)

    league_manager.update_standings.assert_called_once()
    league_manager._broadcast_standings_update.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_process_match_result_draw(league_manager):
    """Test processing a draw result."""

    league_manager._broadcast_standings_update = AsyncMock()
    league_manager._update_round_and_check_completion = AsyncMock()
    league_manager.update_standings = MagicMock(return_value=["P01", "P02"])
    # Mock match validation to return True (match exists)
    league_manager._match_exists_in_schedule = MagicMock(return_value=True)

    report_data = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_REPORT",
        "sender": "referee:REF01",
        "timestamp": "2025-01-01T00:00:00Z",
        "conversation_id": "conv-1",
        "auth_token": "token",
        "league_id": "league_1",
        "round_id": 1,
        "match_id": "M1",
        "game_type": "even_odd",
        "result": {
            "winner": "DRAW",
            "score": {"P01": 1, "P02": 1},
            "match_status": "COMPLETED",
            "player_a_status": "DRAW",
            "player_b_status": "DRAW",
        },
    }

    await league_manager._process_match_result(report_data)

    league_manager.update_standings.assert_called_once()
    league_manager._broadcast_standings_update.assert_awaited_once_with(1)


def test_update_standings_updates_repo(league_manager):
    """Test update_standings applies scoring and updates repository."""
    result = {"winner": "P01", "score": {"P01": 3, "P02": 0}}

    players = league_manager.update_standings(result)

    assert players == ["P01", "P02"]
    assert league_manager.standings_repo.update_player.call_count == 2

    calls = league_manager.standings_repo.update_player.call_args_list
    assert calls[0].kwargs["player_id"] == "P01"
    assert calls[0].kwargs["result"] == "WIN"
    assert calls[0].kwargs["points"] == 3
    assert calls[1].kwargs["player_id"] == "P02"
    assert calls[1].kwargs["result"] == "LOSS"
    assert calls[1].kwargs["points"] == 0
