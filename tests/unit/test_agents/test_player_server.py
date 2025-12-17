import pytest
from fastapi.testclient import TestClient

from agents.player_P01.server import PlayerAgent


@pytest.fixture(scope="module")
def player_client():
    agent = PlayerAgent(agent_id="P99")
    client = TestClient(agent.app)
    return client


def test_handle_game_invitation(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-1",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
        },
        "id": 1,
    }

    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["message_type"] == "GAME_JOIN_ACK"
    assert body["result"]["player_id"] == "P99"
    assert body["id"] == 1


def test_handle_choose_parity(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "CHOOSE_PARITY_CALL",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-2",
            "match_id": "R1M1",
            "player_id": "P99",
            "game_type": "even_odd",
            "context": {"opponent_id": "P02", "round_id": 1},
            "deadline": "2025-01-01T00:00:30Z",
        },
        "id": 2,
    }

    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["message_type"] == "CHOOSE_PARITY_RESPONSE"
    assert body["result"]["player_id"] == "P99"
    assert body["result"]["parity_choice"] in ["even", "odd"]
    assert body["id"] == 2


def test_unknown_method_returns_error(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "UNKNOWN_METHOD",
        "params": {"message_type": "UNKNOWN_METHOD", "protocol": "league.v2", "sender": "referee:REF01", "timestamp": "2025-01-01T00:00:00Z", "conversation_id": "conv-x"},
        "id": 3,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32601
    assert body["id"] == 3
