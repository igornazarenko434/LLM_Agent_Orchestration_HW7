"""
Unit tests for default configuration templates (M3.4).
"""

import pytest
import json
from pathlib import Path

@pytest.mark.unit
class TestDefaultConfigs:
    """Test default configuration templates."""

    def test_player_default_config_validity(self):
        """Test SHARED/config/defaults/player.json is valid and has required fields."""
        config_path = Path("SHARED/config/defaults/player.json")
        assert config_path.exists(), "player.json missing"

        with open(config_path, "r") as f:
            data = json.load(f)

        assert data["agent_type"] == "player"
        assert data["version"] == "1.0.0"
        assert "log_level" in data
        assert "game_types" in data
        assert "even_odd" in data["game_types"]
        assert "capabilities" in data
        assert "handle_game_invitation" in data["capabilities"]
        assert "metadata" in data
        assert data["metadata"]["strategy"] == "random"
        assert data["metadata"]["auto_register"] is True

    def test_referee_default_config_validity(self):
        """Test SHARED/config/defaults/referee.json is valid and has required fields."""
        config_path = Path("SHARED/config/defaults/referee.json")
        assert config_path.exists(), "referee.json missing"

        with open(config_path, "r") as f:
            data = json.load(f)

        assert data["agent_type"] == "referee"
        assert data["version"] == "1.0.0"
        assert "log_level" in data
        assert "game_types" in data
        assert "even_odd" in data["game_types"]
        assert "capabilities" in data
        assert "conduct_match" in data["capabilities"]
        assert "max_concurrent_matches" in data
        assert data["max_concurrent_matches"] >= 1
        assert "metadata" in data
        assert data["metadata"]["match_timeout_enforcement"] is True
        assert data["metadata"]["auto_register"] is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
