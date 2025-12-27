"""
Unit tests for League Manager registration (M7.9).

Tests:
- Referee registration
- Player registration
- Auth token generation
- Duplicate detection
- ID generation
- Error handling
"""

import pytest
from agents.league_manager.server import LeagueManager

from league_sdk.protocol import JSONRPCRequest


class TestLeagueManagerRegistration:
    """Test suite for League Manager registration handlers."""

    @pytest.fixture
    def lm(self):
        """Create League Manager instance."""
        return LeagueManager(agent_id="LM01", league_id="league_2025_even_odd")

    def test_lm_initialization(self, lm):
        """Test League Manager initializes correctly."""
        assert lm.agent_id == "LM01"
        assert lm.agent_type == "league_manager"
        assert lm.league_id == "league_2025_even_odd"
        assert lm.port == 8000  # From config
        assert len(lm.registered_referees) == 0
        assert len(lm.registered_players) == 0

    def test_lm_loads_config(self, lm):
        """Test League Manager loads configuration."""
        assert lm.agents_config is not None
        assert lm.system_config is not None
        assert lm.lm_config is not None
        assert lm.lm_config.get("agent_id") == "LM01"

    @pytest.mark.asyncio
    async def test_referee_registration_success(self, lm):
        """Test successful referee registration."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="REFEREE_REGISTER_REQUEST",
            params={
                "sender": "referee:REFTEST",
                "timestamp": "2025-01-15T12:00:00Z",
                "conversation_id": "reg-test-001",
                "referee_meta": {
                    "display_name": "Test Referee",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": "http://localhost:9001/mcp",
                    "max_concurrent_matches": 10,
                },
            },
            id=1,
        )

        response = await lm._handle_referee_registration(request)

        assert response.status_code == 200
        content = response.body.decode()
        assert "ACCEPTED" in content
        assert "REFTEST" in content  # Sender-derived referee ID
        assert len(lm.registered_referees) == 1

        # Verify stored data
        ref = lm.registered_referees["REFTEST"]
        assert ref["referee_id"] == "REFTEST"
        assert ref["contact_endpoint"] == "http://localhost:9001/mcp"
        assert ref["display_name"] == "Test Referee"
        assert len(ref["auth_token"]) == 32  # 32 hex chars

    @pytest.mark.asyncio
    async def test_player_registration_success(self, lm):
        """Test successful player registration."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="LEAGUE_REGISTER_REQUEST",
            params={
                "sender": "player:PTEST",
                "timestamp": "2025-01-15T12:00:00Z",
                "conversation_id": "reg-player-001",
                "player_meta": {
                    "display_name": "Test Player",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "strategy": "random",
                },
            },
            id=1,
        )

        response = await lm._handle_player_registration(request)

        assert response.status_code == 200
        content = response.body.decode()
        assert "ACCEPTED" in content
        assert "PTEST" in content  # Sender-derived player ID
        assert len(lm.registered_players) == 1

        # Verify stored data
        player = lm.registered_players["PTEST"]
        assert player["player_id"] == "PTEST"
        assert player["sender"] == "player:PTEST"
        assert player["display_name"] == "Test Player"
        assert len(player["auth_token"]) == 32

    @pytest.mark.asyncio
    async def test_duplicate_referee_registration(self, lm):
        """Test duplicate referee registration is rejected."""
        # Register first referee
        request1 = JSONRPCRequest(
            jsonrpc="2.0",
            method="REFEREE_REGISTER_REQUEST",
            params={
                "sender": "referee:REFA",
                "timestamp": "2025-01-15T12:00:00Z",
                "conversation_id": "reg-ref-1",
                "referee_meta": {
                    "display_name": "Referee A",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": "http://localhost:9001/mcp",
                    "max_concurrent_matches": 10,
                },
            },
            id=1,
        )
        await lm._handle_referee_registration(request1)
        assert len(lm.registered_referees) == 1

        # Try to register with same endpoint (duplicate)
        request2 = JSONRPCRequest(
            jsonrpc="2.0",
            method="REFEREE_REGISTER_REQUEST",
            params={
                "sender": "referee:REFB",
                "timestamp": "2025-01-15T12:01:00Z",
                "conversation_id": "reg-ref-2",
                "referee_meta": {
                    "display_name": "Referee B",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": "http://localhost:9001/mcp",  # Same endpoint!
                    "max_concurrent_matches": 10,
                },
            },
            id=2,
        )

        response = await lm._handle_referee_registration(request2)

        assert response.status_code == 409  # Conflict
        content = response.body.decode()
        assert "already registered" in content.lower()
        assert len(lm.registered_referees) == 1  # Still only 1

    @pytest.mark.asyncio
    async def test_duplicate_player_registration(self, lm):
        """Test duplicate player registration is rejected."""
        # Register first player
        request1 = JSONRPCRequest(
            jsonrpc="2.0",
            method="LEAGUE_REGISTER_REQUEST",
            params={
                "sender": "player:PLAYER_X",
                "timestamp": "2025-01-15T12:00:00Z",
                "conversation_id": "reg-p-1",
                "player_meta": {
                    "display_name": "Player X",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "strategy": "random",
                },
            },
            id=1,
        )
        await lm._handle_player_registration(request1)
        assert len(lm.registered_players) == 1

        # Try to register with same sender (duplicate)
        request2 = JSONRPCRequest(
            jsonrpc="2.0",
            method="LEAGUE_REGISTER_REQUEST",
            params={
                "sender": "player:PLAYER_X",  # Same sender!
                "timestamp": "2025-01-15T12:01:00Z",
                "conversation_id": "reg-p-2",
                "player_meta": {
                    "display_name": "Player X Again",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "strategy": "history_based",
                },
            },
            id=2,
        )

        response = await lm._handle_player_registration(request2)

        assert response.status_code == 409  # Conflict
        content = response.body.decode()
        assert "already registered" in content.lower()
        assert len(lm.registered_players) == 1

    def test_generate_referee_ids(self, lm):
        """Test referee ID generation is sequential."""
        assert lm._generate_referee_id() == "REF01"
        assert lm._generate_referee_id() == "REF02"
        assert lm._generate_referee_id() == "REF03"

    def test_generate_player_ids(self, lm):
        """Test player ID generation is sequential."""
        assert lm._generate_player_id() == "P01"
        assert lm._generate_player_id() == "P02"
        assert lm._generate_player_id() == "P03"

    def test_generate_auth_token(self, lm):
        """Test auth token generation."""
        token1 = lm._generate_auth_token()
        token2 = lm._generate_auth_token()

        # Should be 32 hex characters (16 bytes * 2)
        assert len(token1) == 32
        assert len(token2) == 32

        # Should be unique
        assert token1 != token2

        # Should be hexadecimal
        assert all(c in "0123456789abcdef" for c in token1)
        assert all(c in "0123456789abcdef" for c in token2)

    @pytest.mark.asyncio
    async def test_missing_required_field_referee(self, lm):
        """Test referee registration with missing field."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="REFEREE_REGISTER_REQUEST",
            params={
                "sender": "referee:REFTEST",
                # Missing timestamp!
                "conversation_id": "reg-test-001",
                "referee_meta": {
                    "display_name": "Test Referee",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": "http://localhost:9001/mcp",
                },
            },
            id=1,
        )

        response = await lm._handle_referee_registration(request)

        assert response.status_code == 400
        content = response.body.decode()
        assert "missing" in content.lower()

    @pytest.mark.asyncio
    async def test_missing_required_field_player(self, lm):
        """Test player registration with missing field."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="LEAGUE_REGISTER_REQUEST",
            params={
                "sender": "player:PTEST",
                "timestamp": "2025-01-15T12:00:00Z",
                # Missing conversation_id!
                "player_meta": {
                    "display_name": "Test Player",
                    "version": "1.0.0",
                },
            },
            id=1,
        )

        response = await lm._handle_player_registration(request)

        assert response.status_code == 400
        content = response.body.decode()
        assert "missing" in content.lower()

    @pytest.mark.asyncio
    async def test_multiple_referee_registrations(self, lm):
        """Test multiple referee registrations work correctly."""
        for i in range(3):
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="REFEREE_REGISTER_REQUEST",
                params={
                    "sender": f"referee:REF{i+1:02d}",
                    "timestamp": "2025-01-15T12:00:00Z",
                    "conversation_id": f"reg-ref-{i}",
                    "referee_meta": {
                        "display_name": f"Referee {i}",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": f"http://localhost:{9001+i}/mcp",
                        "max_concurrent_matches": 10,
                    },
                },
                id=i,
            )
            response = await lm._handle_referee_registration(request)
            assert response.status_code == 200

        assert len(lm.registered_referees) == 3
        assert "REF01" in lm.registered_referees
        assert "REF02" in lm.registered_referees
        assert "REF03" in lm.registered_referees

    @pytest.mark.asyncio
    async def test_multiple_player_registrations(self, lm):
        """Test multiple player registrations work correctly."""
        for i in range(5):
            request = JSONRPCRequest(
                jsonrpc="2.0",
                method="LEAGUE_REGISTER_REQUEST",
                params={
                    "sender": f"player:P{i+1:02d}",
                    "timestamp": "2025-01-15T12:00:00Z",
                    "conversation_id": f"reg-p-{i}",
                    "player_meta": {
                        "display_name": f"Player {i}",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "strategy": "random",
                    },
                },
                id=i,
            )
            response = await lm._handle_player_registration(request)
            assert response.status_code == 200

        assert len(lm.registered_players) == 5
        assert "P01" in lm.registered_players
        assert "P05" in lm.registered_players
