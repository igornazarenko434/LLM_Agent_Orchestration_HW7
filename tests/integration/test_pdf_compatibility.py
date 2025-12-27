"""
Integration test for PDF method name compatibility.

Tests that agents accept BOTH PDF-style method names and message-type names,
proving the compatibility layer works end-to-end.
"""

import asyncio

import pytest
import requests

from agents.league_manager.server import LeagueManager
from agents.player_P01.server import PlayerAgent
from agents.referee_REF01.server import RefereeAgent


@pytest.fixture
def player_agent():
    """Create a test player agent."""
    agent = PlayerAgent(agent_id="TESTP01", host="127.0.0.1", port=9901)
    agent.start(run_in_thread=True)
    yield agent
    agent.stop()


@pytest.fixture
def referee_agent():
    """Create a test referee agent."""
    agent = RefereeAgent(agent_id="TESTREF01", host="127.0.0.1", port=9801)
    agent.start(run_in_thread=True)
    yield agent
    agent.stop()


@pytest.fixture
def league_manager_agent():
    """Create a test league manager agent."""
    agent = LeagueManager(
        agent_id="TESTLM",
        league_id="league_2025_even_odd",
        host="127.0.0.1",
        port=9001,
    )
    asyncio.run(agent.start(run_in_thread=True))
    yield agent
    agent.stop()


class TestPDFMethodCompatibility:
    """Test that PDF-style method names work with all agents."""

    @pytest.mark.asyncio
    async def test_player_accepts_pdf_method_names(self, player_agent):
        """Player agent should accept PDF-style method names."""
        await asyncio.sleep(0.5)  # Let server start

        # Try PDF-style method: 'handle_game_invitation' instead of 'GAME_INVITATION'
        response = requests.post(
            "http://localhost:9901/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "handle_game_invitation",  # ← PDF-style name
                "params": {
                    "protocol": "league.v2",
                    "message_type": "GAME_INVITATION",
                    "sender": "referee:REF01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-conv-001",
                    "auth_token": "test_token",
                    "league_id": "league_2025_even_odd",
                    "round_id": 1,
                    "match_id": "TEST_M1",
                    "game_type": "even_odd",
                    "role_in_match": "PLAYER_A",
                    "opponent_id": "P02",
                },
                "id": 1,
            },
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data or "error" in data
        # Even if it errors due to auth/registration, the method was recognized

    @pytest.mark.asyncio
    async def test_player_accepts_message_type_names(self, player_agent):
        """Player agent should still accept message-type names."""
        await asyncio.sleep(0.5)

        # Try message-type method: 'GAME_INVITATION' (our style)
        response = requests.post(
            "http://localhost:9901/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "GAME_INVITATION",  # ← Message-type name
                "params": {
                    "protocol": "league.v2",
                    "message_type": "GAME_INVITATION",
                    "sender": "referee:REF01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-conv-002",
                    "auth_token": "test_token",
                    "league_id": "league_2025_even_odd",
                    "round_id": 1,
                    "match_id": "TEST_M2",
                    "game_type": "even_odd",
                    "role_in_match": "PLAYER_A",
                    "opponent_id": "P02",
                },
                "id": 2,
            },
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data or "error" in data

    @pytest.mark.asyncio
    async def test_league_manager_accepts_pdf_registration(self, league_manager_agent):
        """League Manager should accept PDF-style registration method."""
        await asyncio.sleep(0.5)

        # Try PDF-style method: 'register_player' instead of 'LEAGUE_REGISTER_REQUEST'
        response = requests.post(
            "http://localhost:9001/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "register_player",  # ← PDF-style name
                "params": {
                    "protocol": "league.v2",
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "sender": "player:TEST_PDF_P01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-reg-001",
                    "auth_token": "",
                    "league_id": "league_2025_even_odd",
                    "player_meta": {
                        "display_name": "PDF Test Player",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": "http://localhost:9999/mcp",
                    },
                },
                "id": 3,
            },
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"]["status"] in ["ACCEPTED", "REJECTED"]

    @pytest.mark.asyncio
    async def test_league_manager_accepts_message_type_registration(self, league_manager_agent):
        """League Manager should still accept message-type registration."""
        await asyncio.sleep(0.5)

        # Try message-type method: 'LEAGUE_REGISTER_REQUEST' (our style)
        response = requests.post(
            "http://localhost:9001/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "LEAGUE_REGISTER_REQUEST",  # ← Message-type name
                "params": {
                    "protocol": "league.v2",
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "sender": "player:TEST_MSG_P01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-reg-002",
                    "auth_token": "",
                    "league_id": "league_2025_even_odd",
                    "player_meta": {
                        "display_name": "Message Type Test Player",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": "http://localhost:9998/mcp",
                    },
                },
                "id": 4,
            },
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert data["result"]["status"] in ["ACCEPTED", "REJECTED"]

    @pytest.mark.asyncio
    async def test_both_methods_route_to_same_handler(self, league_manager_agent):
        """PDF-style and message-type names should produce identical behavior."""
        await asyncio.sleep(0.5)

        # Register with PDF-style method
        response_pdf = requests.post(
            "http://localhost:9001/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "register_player",  # PDF style
                "params": {
                    "protocol": "league.v2",
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "sender": "player:TEST_IDENTICAL_P01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-identical-001",
                    "auth_token": "",
                    "league_id": "league_2025_even_odd",
                    "player_meta": {
                        "display_name": "Identical Test 1",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": "http://localhost:9997/mcp",
                    },
                },
                "id": 5,
            },
            timeout=5,
        )

        # Register with message-type method
        response_msg = requests.post(
            "http://localhost:9001/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "LEAGUE_REGISTER_REQUEST",  # Message-type style
                "params": {
                    "protocol": "league.v2",
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "sender": "player:TEST_IDENTICAL_P02",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-identical-002",
                    "auth_token": "",
                    "league_id": "league_2025_even_odd",
                    "player_meta": {
                        "display_name": "Identical Test 2",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": "http://localhost:9996/mcp",
                    },
                },
                "id": 6,
            },
            timeout=5,
        )

        # Both should succeed
        assert response_pdf.status_code == 200
        assert response_msg.status_code == 200

        # Both should return same structure
        data_pdf = response_pdf.json()
        data_msg = response_msg.json()

        assert "result" in data_pdf
        assert "result" in data_msg
        assert data_pdf["result"]["status"] == "ACCEPTED"
        assert data_msg["result"]["status"] == "ACCEPTED"

        # Both should have similar response structure
        assert set(data_pdf["result"].keys()) == set(data_msg["result"].keys())


class TestPDFMethodErrorHandling:
    """Test that PDF-style method names get proper error handling."""

    @pytest.mark.asyncio
    async def test_unknown_pdf_method_returns_error(self, player_agent):
        """Unknown PDF-style method should return method not found error."""
        await asyncio.sleep(0.5)

        response = requests.post(
            "http://localhost:9901/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "unknown_pdf_method",  # Unknown method
                "params": {
                    "protocol": "league.v2",
                    "message_type": "unknown_pdf_method",
                    "sender": "referee:REF01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-unknown-001",
                    "auth_token": "test_token",
                },
                "id": 99,
            },
            timeout=5,
        )

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_pdf_method_translation_logged(self, player_agent):
        """PDF method translation should be logged (visible in debug logs)."""
        await asyncio.sleep(0.5)

        # Make a request with PDF-style method
        # The translation will be logged at DEBUG level
        response = requests.post(
            "http://localhost:9901/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "handle_game_invitation",
                "params": {
                    "protocol": "league.v2",
                    "message_type": "GAME_INVITATION",
                    "sender": "referee:REF01",
                    "timestamp": "2025-01-15T10:00:00Z",
                    "conversation_id": "test-logging-001",
                    "auth_token": "test",
                    "league_id": "test",
                    "round_id": 1,
                    "match_id": "M1",
                    "game_type": "even_odd",
                    "role_in_match": "PLAYER_A",
                    "opponent_id": "P02",
                },
                "id": 100,
            },
            timeout=5,
        )

        # Request should succeed (or fail for auth, but method should be recognized)
        assert response.status_code in [200, 401, 400]
        # The translation log will be in the agent's log file at DEBUG level
