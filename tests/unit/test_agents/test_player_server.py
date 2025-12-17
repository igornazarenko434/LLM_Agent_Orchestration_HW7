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
            "auth_token": "tok-ref",
        },
        "id": 1,
    }

    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["message_type"] == "GAME_JOIN_ACK"
    assert body["result"]["player_id"] == "P99"
    assert body["result"]["auth_token"] == "tok-ref"
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
            "auth_token": "tok-ref",
        },
        "id": 2,
    }

    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["message_type"] == "CHOOSE_PARITY_RESPONSE"
    assert body["result"]["player_id"] == "P99"
    assert body["result"]["parity_choice"] in ["even", "odd"]
    assert body["result"]["auth_token"] == "tok-ref"
    assert body["id"] == 2


def test_handle_game_over(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_OVER",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:01:00Z",
            "conversation_id": "conv-test-3",
            "match_id": "R1M1",
            "game_type": "even_odd",
            "game_result": {
                "status": "WIN",
                "winner_player_id": "P99",
                "drawn_number": 8,
                "number_parity": "even",
                "choices": {"P99": "even", "P02": "odd"},
            },
            "auth_token": "tok-ref",
        },
        "id": 3,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["status"] == "ack"
    assert body["result"]["match_id"] == "R1M1"
    assert body["result"]["auth_token"] == "tok-ref"
    assert body["id"] == 3


def test_unknown_method_returns_error(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "UNKNOWN_METHOD",
        "params": {"message_type": "UNKNOWN_METHOD", "protocol": "league.v2", "sender": "referee:REF01", "timestamp": "2025-01-01T00:00:00Z", "conversation_id": "conv-x", "auth_token": "tok-ref"},
        "id": 3,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32601
    assert body["id"] == 3


def test_missing_auth_token_returns_e012(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-4",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
        },
        "id": 4,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E012"


def test_protocol_mismatch_returns_e011(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v1",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-5",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
            "auth_token": "tok-ref",
        },
        "id": 5,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E011"


def test_invalid_sender_returns_e004(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REFXX",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-6",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
            "auth_token": "tok-ref",
        },
        "id": 6,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E004"


def test_unsupported_game_type_returns_e002(player_client: TestClient):
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-test-7",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "not_supported",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
            "auth_token": "tok-ref",
        },
        "id": 7,
    }
    resp = player_client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E002"
