"""
Unit tests for Referee server (Mission 7.5, 7.8).

Tests referee initialization, configuration loading, and server setup.
"""

import pytest
from fastapi.testclient import TestClient
from league_sdk.repositories import MatchRepository

from agents.referee_REF01.server import RefereeAgent


class TestRefereeAgent:
    """Test suite for Referee agent server."""

    @pytest.fixture
    def referee(self):
        """Create referee agent instance."""
        return RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")

    def test_referee_initialization(self, referee):
        """Test referee initializes with correct config."""
        assert referee.agent_id == "REF01"
        assert referee.agent_type == "referee"
        assert referee.league_id == "league_2025_even_odd"
        assert referee.state == "INIT"
        assert referee.auth_token is None
        assert referee.match_conductor is None

    def test_referee_loads_config(self, referee):
        """Test referee loads configuration from agents_config.json."""
        assert referee.agents_config is not None
        assert referee.system_config is not None
        assert referee.agent_record is not None
        assert referee.agent_record.get("agent_id") == "REF01"
        assert referee.agent_record.get("agent_type") == "referee"

    def test_referee_port_from_config(self, referee):
        """Test referee gets port from config."""
        # Should get port 8001 from agents_config.json
        assert referee.port == 8001

    def test_referee_capabilities_from_config(self, referee):
        """Test referee capabilities loaded from config."""
        capabilities = referee.agent_record.get("capabilities", [])
        expected_capabilities = [
            "conduct_match",
            "enforce_timeouts",
            "determine_winner",
            "report_results",
            "get_match_state",
        ]
        assert set(expected_capabilities).issubset(set(capabilities))

    def test_referee_game_types_from_config(self, referee):
        """Test referee game types loaded from config."""
        game_types = referee.agent_record.get("game_types", [])
        assert "even_odd" in game_types

    def test_referee_max_concurrent_matches_from_config(self, referee):
        """Test max concurrent matches loaded from config."""
        max_concurrent = referee.agent_record.get("max_concurrent_matches")
        assert max_concurrent == 10

    def test_referee_active_matches_tracking(self, referee):
        """Test referee tracks active matches."""
        assert isinstance(referee.active_matches, dict)
        assert len(referee.active_matches) == 0

    def test_referee_transition_state(self, referee):
        """Test referee state transitions."""
        assert referee.state == "INIT"

        referee._transition("REGISTERED")
        assert referee.state == "REGISTERED"

        referee._transition("ACTIVE")
        assert referee.state == "ACTIVE"

    def test_referee_timestamp_format(self, referee):
        """Test referee timestamp is ISO 8601 UTC with Z suffix."""
        timestamp = referee._timestamp()
        assert timestamp.endswith("Z")
        assert "T" in timestamp
        # Should be parseable as ISO format
        from datetime import datetime

        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed is not None

    def test_referee_mcp_route_registered(self, referee):
        """Test /mcp route is registered in FastAPI app."""
        routes = [route.path for route in referee.app.routes]
        assert "/mcp" in routes

    def test_referee_health_endpoint(self, referee):
        """Test /health endpoint exists."""
        routes = [route.path for route in referee.app.routes]
        assert "/health" in routes


def test_get_match_state_returns_match(tmp_path):
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    referee.match_repo = MatchRepository(data_root=tmp_path)
    referee.match_repo.save(
        "R1M1",
        {
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "game_type": "even_odd",
            "status": "FINISHED",
        },
    )
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "get_match_state",
        "params": {
            "protocol": "league.v2",
            "sender": "player:P01",
            "auth_token": "tok-player",
            "match_id": "R1M1",
        },
        "id": 55,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["match"]["match_id"] == "R1M1"


def test_start_match_requires_registration():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "conv-start-1",
            "match_id": "R1M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
        },
        "id": 77,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E004"


def test_start_match_missing_required_field_returns_e002():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    referee.match_conductor = object()
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "conv-start-2",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
        },
        "id": 78,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E002"


def test_referee_protocol_mismatch_returns_e011():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "protocol": "league.v1",
            "sender": "league_manager:LM01",
            "conversation_id": "conv-proto",
            "match_id": "R1M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
        },
        "id": 79,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E011"


def test_referee_missing_sender_returns_e002():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "protocol": "league.v2",
            "conversation_id": "conv-missing-sender",
            "match_id": "R1M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
        },
        "id": 80,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E002"


def test_referee_unknown_method_returns_404():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "UNKNOWN_METHOD",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "conv-unknown",
        },
        "id": 81,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 404


def test_referee_get_registration_status():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "get_registration_status",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "reg-status-1",
        },
        "id": 82,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["message_type"] == "get_registration_status"


@pytest.mark.asyncio
async def test_referee_manual_register_uses_register_with_retry(monkeypatch):
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")

    async def fake_register_with_retry(max_attempts):
        referee._transition("REGISTERED")
        return {"status": "ACCEPTED", "attempts": max_attempts}

    monkeypatch.setattr(referee, "register_with_retry", fake_register_with_retry)
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "manual_register",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "manual-reg-2",
            "max_attempts": 2,
        },
        "id": 83,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"]["registration_result"]["status"] == "ACCEPTED"


def test_player_response_unknown_conversation_returns_404():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_JOIN_ACK",
        "params": {
            "protocol": "league.v2",
            "sender": "player:P01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-missing",
            "auth_token": "tok-player",
            "match_id": "R1M1",
            "player_id": "P01",
            "arrival_timestamp": "2025-01-01T00:00:01Z",
            "accept": True,
        },
        "id": 84,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E005"


def test_referee_unsupported_game_type_returns_e002():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "protocol": "league.v2",
            "sender": "league_manager:LM01",
            "conversation_id": "conv-unsupported-game",
            "match_id": "R1M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
            "game_type": "unknown_game",
        },
        "id": 85,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E002"


def test_player_response_missing_auth_returns_401():
    referee = RefereeAgent(agent_id="REF01", league_id="league_2025_even_odd")
    client = TestClient(referee.app)
    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_JOIN_ACK",
        "params": {
            "protocol": "league.v2",
            "sender": "player:P01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-missing-auth",
            "match_id": "R1M1",
            "player_id": "P01",
            "arrival_timestamp": "2025-01-01T00:00:01Z",
            "accept": True,
        },
        "id": 86,
    }
    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E012"


class TestRefereeRegistration:
    """Test suite for referee registration with League Manager."""

    @pytest.fixture
    def referee(self):
        """Create referee agent instance."""
        return RefereeAgent(agent_id="REF01")

    def test_registration_timeout_from_config(self, referee):
        """Test registration timeout loaded from system config."""
        timeout = referee.system_config.timeouts.registration_sec
        assert timeout == 10  # From system.json

    def test_registration_builds_metadata(self, referee):
        """Test registration builds correct metadata from config."""
        # Would need to mock League Manager to test actual registration
        # This tests the metadata structure
        assert referee.agent_record.get("display_name") is not None
        assert referee.agent_record.get("version") is not None
        assert referee.agent_record.get("game_types") is not None
        assert referee.agent_record.get("max_concurrent_matches") is not None
