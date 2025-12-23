"""
Unit tests for Referee server (Mission 7.5, 7.8).

Tests referee initialization, configuration loading, and server setup.
"""

import pytest

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
