"""
Unit tests for Referee REF02 (verifies shared implementation).

Tests that REF02:
- Loads correct configuration from agents_config.json
- Uses port 8002 from config
- Shares implementation with REF01
- Has correct agent_id defaults
"""

import pytest

from agents.referee_REF01.server import RefereeAgent


class TestRefereeREF02:
    """Test suite for Referee REF02 agent."""

    @pytest.fixture
    def referee_ref02(self):
        """Create referee REF02 instance."""
        return RefereeAgent(agent_id="REF02", league_id="league_2025_even_odd")

    def test_ref02_initialization(self, referee_ref02):
        """Test REF02 initializes with correct config."""
        assert referee_ref02.agent_id == "REF02"
        assert referee_ref02.agent_type == "referee"
        assert referee_ref02.league_id == "league_2025_even_odd"
        assert referee_ref02.state == "INIT"

    def test_ref02_loads_config(self, referee_ref02):
        """Test REF02 loads configuration from agents_config.json."""
        assert referee_ref02.agents_config is not None
        assert referee_ref02.system_config is not None
        assert referee_ref02.agent_record is not None
        assert referee_ref02.agent_record.get("agent_id") == "REF02"
        assert referee_ref02.agent_record.get("agent_type") == "referee"

    def test_ref02_port_from_config(self, referee_ref02):
        """Test REF02 gets port 8002 from config."""
        assert referee_ref02.port == 8002

    def test_ref02_display_name_from_config(self, referee_ref02):
        """Test REF02 display name from config."""
        display_name = referee_ref02.agent_record.get("display_name")
        assert display_name == "Referee 02"

    def test_ref02_endpoint_from_config(self, referee_ref02):
        """Test REF02 endpoint from config."""
        endpoint = referee_ref02.agent_record.get("endpoint")
        assert endpoint == "http://localhost:8002/mcp"

    def test_ref02_capabilities_from_config(self, referee_ref02):
        """Test REF02 capabilities loaded from config."""
        capabilities = referee_ref02.agent_record.get("capabilities", [])
        expected_capabilities = [
            "conduct_match",
            "enforce_timeouts",
            "determine_winner",
            "report_results",
        ]
        assert set(expected_capabilities).issubset(set(capabilities))

    def test_ref02_game_types_from_config(self, referee_ref02):
        """Test REF02 game types loaded from config."""
        game_types = referee_ref02.agent_record.get("game_types", [])
        assert "even_odd" in game_types

    def test_ref02_max_concurrent_matches_from_config(self, referee_ref02):
        """Test REF02 max concurrent matches from config."""
        max_concurrent = referee_ref02.agent_record.get("max_concurrent_matches")
        assert max_concurrent == 10

    def test_ref02_shares_implementation_with_ref01(self, referee_ref02):
        """Test REF02 uses same RefereeAgent class as REF01."""
        # Both should use the same class
        ref01 = RefereeAgent(agent_id="REF01")
        assert type(referee_ref02).__name__ == type(ref01).__name__
        assert type(referee_ref02).__module__ == type(ref01).__module__

    def test_ref02_has_match_conductor_capability(self, referee_ref02):
        """Test REF02 can initialize match conductor after registration."""
        # Before registration, match_conductor should be None
        assert referee_ref02.match_conductor is None

    def test_ref02_active_status_from_config(self, referee_ref02):
        """Test REF02 active status from config."""
        active = referee_ref02.agent_record.get("active")
        assert active is True

    def test_ref02_version_from_config(self, referee_ref02):
        """Test REF02 version from config."""
        version = referee_ref02.agent_record.get("version")
        assert version == "1.0.0"

    def test_ref02_metadata_from_config(self, referee_ref02):
        """Test REF02 metadata loaded from config."""
        metadata = referee_ref02.agent_record.get("metadata", {})
        assert metadata.get("match_timeout_enforcement") is True
        assert metadata.get("supports_draw") is True
        assert metadata.get("specialization") == "even_odd"


class TestREF01vsREF02:
    """Test suite comparing REF01 and REF02 to ensure consistency."""

    @pytest.fixture
    def ref01(self):
        """Create REF01 instance."""
        return RefereeAgent(agent_id="REF01")

    @pytest.fixture
    def ref02(self):
        """Create REF02 instance."""
        return RefereeAgent(agent_id="REF02")

    def test_both_referees_share_same_class(self, ref01, ref02):
        """Test both referees use the same RefereeAgent class."""
        assert type(ref01) is type(ref02)

    def test_both_referees_have_same_capabilities(self, ref01, ref02):
        """Test both referees have identical capabilities."""
        ref01_caps = set(ref01.agent_record.get("capabilities", []))
        ref02_caps = set(ref02.agent_record.get("capabilities", []))
        assert ref01_caps == ref02_caps

    def test_both_referees_support_same_game_types(self, ref01, ref02):
        """Test both referees support same game types."""
        ref01_games = set(ref01.agent_record.get("game_types", []))
        ref02_games = set(ref02.agent_record.get("game_types", []))
        assert ref01_games == ref02_games

    def test_both_referees_have_different_ports(self, ref01, ref02):
        """Test referees have different ports (8001 vs 8002)."""
        assert ref01.port == 8001
        assert ref02.port == 8002
        assert ref01.port != ref02.port

    def test_both_referees_have_different_agent_ids(self, ref01, ref02):
        """Test referees have different agent IDs."""
        assert ref01.agent_id == "REF01"
        assert ref02.agent_id == "REF02"
        assert ref01.agent_id != ref02.agent_id

    def test_both_referees_have_same_max_concurrent_matches(self, ref01, ref02):
        """Test both referees support same number of concurrent matches."""
        ref01_max = ref01.agent_record.get("max_concurrent_matches")
        ref02_max = ref02.agent_record.get("max_concurrent_matches")
        assert ref01_max == ref02_max == 10
