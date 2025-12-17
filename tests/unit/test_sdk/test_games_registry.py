"""
Unit tests for games_registry.json (M3.3).

Tests game registry configuration:
- Loading games registry
- Validating game definitions
- Ensuring Even/Odd game is correctly defined
- Checking protocol consistency
"""

import pytest
import json
from pathlib import Path
from league_sdk.config_loader import load_json_file, validate_config
from league_sdk.config_models import GameConfig

@pytest.mark.unit
class TestGamesRegistry:
    """Test games_registry.json content and validation."""

    @pytest.fixture
    def registry_data(self):
        """Load the actual games_registry.json file."""
        config_path = Path("SHARED/config/games/games_registry.json")
        if not config_path.exists():
            pytest.skip("games_registry.json not found")
        return load_json_file(config_path)

    def test_load_actual_games_registry(self, registry_data):
        """Test that the registry file loads and has expected structure."""
        assert "schema_version" in registry_data
        assert "games" in registry_data
        assert isinstance(registry_data["games"], list)
        assert len(registry_data["games"]) >= 1

    def test_even_odd_game_definition(self, registry_data):
        """Test that the Even/Odd game is correctly defined."""
        games = registry_data["games"]
        even_odd = next((g for g in games if g["game_type"] == "even_odd"), None)
        
        assert even_odd is not None, "Even/Odd game definition missing"
        assert even_odd["display_name"] == "Even/Odd"
        assert even_odd["rules_module"] == "agents.referee.games.even_odd"
        assert even_odd["supports_draw"] is True
        assert even_odd["min_players"] == 2
        assert even_odd["max_players"] == 2

    def test_even_odd_game_specific_config(self, registry_data):
        """Test game-specific configuration for Even/Odd."""
        games = registry_data["games"]
        even_odd = next((g for g in games if g["game_type"] == "even_odd"), None)
        
        config = even_odd.get("game_specific_config", {{}})
        assert "random_range_min" in config
        assert "random_range_max" in config
        assert config["random_range_min"] == 1
        assert config["random_range_max"] == 10
        assert "valid_choices" in config
        assert "even" in config["valid_choices"]
        assert "odd" in config["valid_choices"]

    def test_even_odd_rules_definition(self, registry_data):
        """Test that rules are defined in configuration."""
        games = registry_data["games"]
        even_odd = next((g for g in games if g["game_type"] == "even_odd"), None)
        
        config = even_odd.get("game_specific_config", {{}})
        assert "rules" in config
        rules = config["rules"]
        assert "win_condition" in rules
        assert "draw_condition" in rules
        assert "parity_definition" in rules

    def test_games_registry_json_validity(self, registry_data):
        """Test that all games in registry match the Pydantic model."""
        for game_data in registry_data["games"]:
            # This will raise ValidationError if invalid
            game_config = validate_config(game_data, GameConfig)
            assert isinstance(game_config, GameConfig)

    def test_all_games_have_required_fields(self, registry_data):
        """Manually verify required fields for all games."""
        required_fields = [
            "game_type", "display_name", "rules_module", 
            "supports_draw", "max_round_time_sec"
        ]
        for game in registry_data["games"]:
            for field in required_fields:
                assert field in game, f"Missing field {field} in game {game.get('game_type')}"

@pytest.mark.unit
class TestGamesRegistryProtocolConsistency:
    """Test consistency between Game Registry and Protocol/System requirements."""

    def test_max_round_time_matches_protocol(self):
        """Verify max_round_time_sec is reasonable for protocol timeouts."""
        config_path = Path("SHARED/config/games/games_registry.json")
        if not config_path.exists():
            pytest.skip("games_registry.json not found")
            
        data = load_json_file(config_path)
        for game in data["games"]:
            # Protocol has specific timeouts (e.g. 30s for move)
            # Round time should be at least move timeout
            assert game["max_round_time_sec"] >= 30

    def test_game_types_match_league_config(self):
        """Verify defined games match what is used in league config."""
        games_path = Path("SHARED/config/games/games_registry.json")
        league_path = Path("SHARED/config/leagues/league_2025_even_odd.json")
        
        if not games_path.exists() or not league_path.exists():
            pytest.skip("Config files missing")

        games_data = load_json_file(games_path)
        league_data = load_json_file(league_path)

        defined_games = {g["game_type"] for g in games_data["games"]}
        league_game = league_data["game_type"]

        assert league_game in defined_games, \
            f"League uses game type '{league_game}' which is not defined in registry"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])