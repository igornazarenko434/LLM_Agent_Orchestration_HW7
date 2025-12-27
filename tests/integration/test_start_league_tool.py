from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from agents.league_manager.server import LeagueManager


def test_start_league_tool_invokes_orchestration():
    with patch("agents.league_manager.server.load_system_config") as mock_system_config, patch(
        "agents.league_manager.server.load_agents_config"
    ) as mock_agents_config, patch(
        "agents.league_manager.server.load_league_config"
    ) as mock_league_config, patch(
        "agents.league_manager.server.get_retention_config"
    ) as mock_retention:
        mock_system_config.return_value = MagicMock(
            network=MagicMock(request_timeout_sec=10),
            timeouts=MagicMock(generic_sec=5),
            protocol_version="league.v2",
            security=MagicMock(require_auth=True, allow_start_league_without_auth=False),
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
        lm.start_league = AsyncMock(return_value={"total_rounds": 1})

        client = TestClient(lm.app)
        payload = {
            "jsonrpc": "2.0",
            "method": "start_league",
            "params": {
                "protocol": "league.v2",
                "sender": "referee:REF01",
                "auth_token": "tok-ref",
                "league_id": "league_2025_even_odd",
            },
            "id": 1,
        }
        resp = client.post("/mcp", json=payload)
        assert resp.status_code == 200
        lm.start_league.assert_awaited_once()
