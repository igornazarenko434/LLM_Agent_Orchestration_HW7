import pytest
from fastapi.testclient import TestClient

from agents.player_P01.server import PlayerAgent


@pytest.fixture
def player_agent():
    return PlayerAgent(agent_id="P99")


def test_player_registers_successfully(monkeypatch, player_agent):
    def fake_call_with_retry(endpoint, method, params, timeout, logger, circuit_breaker=None):
        return {
            "message_type": "LEAGUE_REGISTER_RESPONSE",
            "sender": "league_manager:LM01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": params.get("conversation_id"),
            "status": "ACCEPTED",
            "player_id": params.get("sender").split(":")[1],
            "reason": None,
            "protocol": "league.v2",
            "auth_token": "tok-issue",
        }

    monkeypatch.setattr("agents.player_P01.server.call_with_retry", fake_call_with_retry)

    resp = player_agent.send_registration_request()
    assert resp["status"] == "ACCEPTED"
    assert player_agent.state == "ACTIVE"
    assert player_agent.auth_token == "tok-issue"

    # Ensure MCP still responds with stored auth_token in tools
    client = TestClient(player_agent.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-int-1",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
            "auth_token": "tok-ref",
        },
        "id": 1,
    }
    resp2 = client.post("/mcp", json=payload)
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["result"]["auth_token"] == player_agent.auth_token
