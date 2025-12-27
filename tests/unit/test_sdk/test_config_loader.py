"""
Unit tests for config_loader.py (M2.2).

Tests configuration file loading and validation:
- Loading system config
- Loading league config
- Loading agents config
- Error handling for missing/invalid files
"""

import json
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from league_sdk.config_loader import (
    load_agents_config,
    load_json_file,
    load_league_config,
    load_system_config,
    validate_config,
)
from league_sdk.config_models import LeagueConfig, SystemConfig


@pytest.mark.unit
class TestLoadJSONFile:
    """Test JSON file loading."""

    def test_load_valid_json_file(self, tmp_path):
        """Test loading a valid JSON file."""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 123}
        test_file.write_text(json.dumps(test_data))

        loaded = load_json_file(test_file)
        assert loaded == test_data

    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/path/file.json")

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises JSONDecodeError."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_json_file(test_file)


@pytest.mark.unit
class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_valid_system_config(self):
        """Test validating valid system config data."""
        data = {
            "schema_version": "1.0.0",
            "protocol_version": "league.v2",
            "timeouts": {
                "registration_sec": 10,
                "game_join_ack_sec": 5,
                "parity_choice_sec": 30,
                "game_over_sec": 5,
                "match_result_sec": 10,
                "league_query_sec": 10,
                "generic_sec": 10,
            },
            "retry_policy": {
                "max_retries": 3,
                "backoff_strategy": "exponential",
                "initial_delay_sec": 2.0,
                "max_delay_sec": 10.0,
                "retryable_errors": ["E005", "E006"],
            },
            "security": {
                "auth_token_length": 32,
                "token_ttl_minutes": 1440,
                "require_auth": True,
                "allowed_origins": ["*"],
            },
            "network": {
                "host": "localhost",
                "league_manager_port": 8000,
                "referee_port_start": 8001,
                "referee_port_end": 8002,
                "player_port_start": 8101,
                "player_port_end": 9100,
            },
        }

        config = validate_config(data, SystemConfig)
        assert isinstance(config, SystemConfig)
        assert config.protocol_version == "league.v2"

    def test_validate_invalid_config(self):
        """Test validating invalid config raises ValidationError."""
        from pydantic import ValidationError as PydanticValidationError

        data = {
            "schema_version": "1.0.0",
            "protocol_version": "invalid_version",  # Should be "league.v2"
        }

        with pytest.raises(PydanticValidationError):
            validate_config(data, SystemConfig)


@pytest.mark.unit
class TestLoadSystemConfig:
    """Test loading system configuration."""

    def test_load_actual_system_config(self):
        """Test loading the actual system.json file."""
        config_path = Path("SHARED/config/system.json")

        if config_path.exists():
            config = load_system_config(config_path)

            assert isinstance(config, SystemConfig)
            assert config.schema_version == "1.0.0"
            assert config.system_id == "league_system_prod"
            assert config.protocol_version == "league.v2"
            assert config.timeouts.registration_sec == 10
            assert config.retry_policy.max_retries == 3
            assert config.security.auth_token_length == 32
            assert config.network.league_manager_port == 8000

    def test_load_system_config_with_custom_values(self, tmp_path):
        """Test loading system config with custom values."""
        config_file = tmp_path / "custom_system.json"
        config_data = {
            "schema_version": "1.0.0",
            "protocol_version": "league.v2",
            "timeouts": {
                "registration_sec": 15,
                "game_join_ack_sec": 10,
                "parity_choice_sec": 45,
                "game_over_sec": 8,
                "match_result_sec": 12,
                "league_query_sec": 15,
                "generic_sec": 15,
            },
            "retry_policy": {
                "max_retries": 5,
                "backoff_strategy": "linear",
                "initial_delay_sec": 1.0,
                "max_delay_sec": 5.0,
                "retryable_errors": ["E005"],
            },
            "security": {
                "auth_token_length": 64,
                "token_ttl_minutes": 720,
                "require_auth": False,
                "allowed_origins": ["http://localhost:3000"],
            },
            "network": {
                "host": "0.0.0.0",
                "league_manager_port": 9000,
                "referee_port_start": 9001,
                "referee_port_end": 9002,
                "player_port_start": 9101,
                "player_port_end": 10100,
            },
        }
        config_file.write_text(json.dumps(config_data))

        config = load_system_config(config_file)
        assert config.timeouts.registration_sec == 15
        assert config.retry_policy.max_retries == 5
        assert config.security.auth_token_length == 64
        assert config.network.league_manager_port == 9000

    def test_env_overrides_apply(self, monkeypatch):
        """Test that environment variables override JSON defaults."""
        config_path = Path("SHARED/config/system.json")
        if not config_path.exists():
            pytest.skip("system.json not found")

        monkeypatch.setenv("LEAGUE_MANAGER_PORT", "9001")
        monkeypatch.setenv("TIMEOUT_GAME_JOIN_ACK", "7")
        monkeypatch.setenv("RETRY_MAX_RETRIES", "4")
        monkeypatch.setenv("TIMEOUT_GAME_OVER", "6")
        monkeypatch.setenv("REQUEST_TIMEOUT_SEC", "25")
        config = load_system_config(config_path)

        assert config.network.league_manager_port == 9001
        assert config.timeouts.game_join_ack_sec == 7
        assert config.retry_policy.max_retries == 4
        assert config.timeouts.game_over_sec == 6
        assert config.network.request_timeout_sec == 25


@pytest.mark.unit
class TestLoadLeagueConfig:
    """Test loading league configuration."""

    def test_load_actual_league_config(self):
        """Test loading the actual league config file."""
        config_path = Path("SHARED/config/leagues/league_2025_even_odd.json")

        if config_path.exists():
            config = load_league_config(config_path)

            assert isinstance(config, LeagueConfig)
            assert config.league_id == "league_2025_even_odd"
            assert config.game_type == "even_odd"
            assert config.status == "ACTIVE"
            assert config.scoring.points_for_win == 3
            assert config.scoring.points_for_draw == 1
            assert config.scoring.points_for_loss == 0
            assert config.participants.max_players == 10000

    def test_load_league_config_with_custom_values(self, tmp_path):
        """Test loading league config with custom values."""
        config_file = tmp_path / "custom_league.json"
        config_data = {
            "schema_version": "1.0.0",
            "league_id": "test_league_2025",
            "display_name": "Test League 2025",
            "game_type": "even_odd",
            "status": "ACTIVE",
            "scoring": {"points_for_win": 5, "points_for_draw": 2, "points_for_loss": 0},
            "schedule_type": "round_robin",
            "participants": {"min_players": 4, "max_players": 100},
        }
        config_file.write_text(json.dumps(config_data))

        config = load_league_config(config_file)
        assert config.league_id == "test_league_2025"
        assert config.status == "ACTIVE"
        assert config.scoring.points_for_win == 5
        assert config.participants.min_players == 4


@pytest.mark.unit
class TestLoadAgentsConfig:
    """Test loading agents configuration."""

    def test_load_actual_agents_config(self):
        """Test loading the actual agents_config.json file."""
        config_path = Path("SHARED/config/agents/agents_config.json")

        if config_path.exists():
            config = load_agents_config(config_path)

            assert isinstance(config, dict)
            assert "schema_version" in config

            # Check league_manager (single object)
            assert "league_manager" in config
            lm = config["league_manager"]
            assert lm["agent_id"] == "LM01"
            assert lm["agent_type"] == "league_manager"
            assert lm["endpoint"] == "http://localhost:8000/mcp"
            assert lm["port"] == 8000
            assert "capabilities" in lm

            # Check referees (array)
            assert "referees" in config
            assert isinstance(config["referees"], list)
            assert len(config["referees"]) == 2
            assert config["referees"][0]["agent_id"] == "REF01"
            assert config["referees"][1]["agent_id"] == "REF02"

            # Check players (array)
            assert "players" in config
            assert isinstance(config["players"], list)
            assert len(config["players"]) == 4
            assert config["players"][0]["agent_id"] == "P01"
            assert config["players"][3]["agent_id"] == "P04"

    def test_load_agents_config_returns_dict(self, tmp_path):
        """Test that load_agents_config returns a dictionary."""
        config_file = tmp_path / "agents.json"
        config_data = {
            "schema_version": "1.0.0",
            "agents": [
                {
                    "agent_id": "TEST01",
                    "agent_type": "player",
                    "display_name": "Test Player",
                    "endpoint": "http://localhost:8101/mcp",
                    "port": 8101,
                    "active": True,
                }
            ],
        }
        config_file.write_text(json.dumps(config_data))

        config = load_agents_config(config_file)
        assert isinstance(config, dict)
        assert len(config["agents"]) == 1
        assert config["agents"][0]["agent_id"] == "TEST01"


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in configuration loading."""

    def test_load_system_config_missing_file(self):
        """Test loading system config from missing file."""
        with pytest.raises(FileNotFoundError):
            load_system_config("/nonexistent/system.json")

    def test_load_league_config_missing_file(self):
        """Test loading league config from missing file."""
        with pytest.raises(FileNotFoundError):
            load_league_config("/nonexistent/league.json")

    def test_load_agents_config_missing_file(self):
        """Test loading agents config from missing file."""
        with pytest.raises(FileNotFoundError):
            load_agents_config("/nonexistent/agents.json")

    def test_load_system_config_invalid_structure(self, tmp_path):
        """Test loading system config with invalid structure."""
        from pydantic import ValidationError as PydanticValidationError

        config_file = tmp_path / "invalid_system.json"
        # Invalid protocol_version will trigger ValidationError
        config_file.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "protocol_version": "invalid_version",  # Must be "league.v2"
                }
            )
        )

        with pytest.raises(PydanticValidationError):
            load_system_config(config_file)

    def test_load_league_config_invalid_structure(self, tmp_path):
        """Test loading league config with invalid structure."""
        from pydantic import ValidationError as PydanticValidationError

        config_file = tmp_path / "invalid_league.json"
        config_file.write_text(json.dumps({"invalid": "structure"}))

        with pytest.raises(PydanticValidationError):
            load_league_config(config_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
