"""
Unit tests for League Manager data retention initialization (M7.9.5).

Tests:
- Retention config loading on startup
- Archive directory creation
- Logging of retention policy status
- Handling of disabled retention
- Error handling for missing configs
"""

import json
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add SHARED to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "SHARED"))

from agents.league_manager.server import LeagueManager  # noqa: E402


class TestDataRetentionInitialization:
    """Test data retention initialization in League Manager (M7.9.5)."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create temporary config directory structure."""
        config_dir = tmp_path / "SHARED" / "config"
        config_dir.mkdir(parents=True)

        # Create system.json with data retention config
        system_config = {
            "schema_version": "1.0.0",
            "protocol_version": "league.v2",
            "data_retention": {
                "enabled": True,
                "logs_retention_days": 30,
                "match_data_retention_days": 365,
                "player_history_retention_days": 365,
                "rounds_retention_days": 365,
                "standings_retention": "permanent",
                "cleanup_schedule_cron": "0 2 * * *",
                "archive_enabled": True,
                "archive_path": str(tmp_path / "SHARED" / "archive"),
                "archive_compression": "gzip",
            },
            "timeouts": {
                "registration_sec": 10,
                "game_join_ack_sec": 5,
                "parity_choice_sec": 30,
            },
            "retry_policy": {
                "max_retries": 3,
                "initial_delay_sec": 2.0,
            },
            "circuit_breaker": {
                "failure_threshold": 5,
                "reset_timeout_sec": 60,
            },
            "network": {
                "host": "localhost",
                "league_manager_port": 8000,
            },
            "logging": {
                "level": "INFO",
                "format": "json",
            },
        }

        with open(config_dir / "system.json", "w") as f:
            json.dump(system_config, f)

        # Create agents_config.json
        agents_config = {
            "league_manager": {
                "agent_id": "LM01",
                "port": 8000,
                "display_name": "League Manager Test",
            }
        }

        agents_dir = config_dir / "agents"
        agents_dir.mkdir()
        with open(agents_dir / "agents_config.json", "w") as f:
            json.dump(agents_config, f)

        return tmp_path

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger to capture log calls."""
        return MagicMock(spec=logging.Logger)

    def test_retention_initialization_creates_archive_directories(self, temp_config_dir):
        """Test that archive directories are created on initialization."""
        archive_path = temp_config_dir / "SHARED" / "archive"

        # Archive path should not exist yet
        assert not archive_path.exists()

        # Mock BaseAgent to avoid server startup
        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        # Load actual config
                        with open(temp_config_dir / "SHARED" / "config" / "system.json") as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"

                        # Create mock logger and set it BEFORE calling _init_data_retention
                        mock_logger = MagicMock(spec=logging.Logger)
                        lm.std_logger = mock_logger

                        # Load configs manually (since BaseAgent.__init__ is mocked)
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value

                        # Initialize retention manually
                        lm._init_data_retention()

        # Verify archive directories created
        assert (archive_path / "logs").exists()
        assert (archive_path / "matches").exists()
        assert (archive_path / "players").exists()
        assert (archive_path / "leagues").exists()

    def test_retention_config_loaded_correctly(self, temp_config_dir):
        """Test that retention configuration is loaded from system.json."""
        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        # Load actual config
                        with open(temp_config_dir / "SHARED" / "config" / "system.json") as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        lm.std_logger = MagicMock()
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value
                        lm._init_data_retention()

        # Verify retention config loaded
        assert hasattr(lm, "retention_config")
        assert lm.retention_config["enabled"] is True
        assert lm.retention_config["logs_retention_days"] == 30
        assert lm.retention_config["match_data_retention_days"] == 365
        assert lm.retention_config["archive_enabled"] is True

    def test_retention_disabled_logs_warning(self, temp_config_dir, caplog):
        """Test that disabled retention logs a warning."""
        # Modify config to disable retention
        config_path = temp_config_dir / "SHARED" / "config" / "system.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        config["data_retention"]["enabled"] = False
        with open(config_path, "w") as f:
            json.dump(config, f)

        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        with open(config_path) as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        mock_logger = MagicMock(spec=logging.Logger)
                        lm.std_logger = mock_logger
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value
                        lm._init_data_retention()

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "DISABLED" in call_args[0][0]

    def test_retention_initialization_logs_policy_details(self, temp_config_dir):
        """Test that retention policy details are logged on initialization."""
        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        # Load actual config
                        with open(temp_config_dir / "SHARED" / "config" / "system.json") as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        mock_logger = MagicMock(spec=logging.Logger)
                        lm.std_logger = mock_logger
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value
                        lm._init_data_retention()

        # Verify info log was called with retention details
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "Data retention initialized" in call_args[0][0]

        # Check extra fields
        extra = call_args[1]["extra"]
        assert extra["event_type"] == "RETENTION_INITIALIZED"
        assert extra["retention_enabled"] is True
        assert extra["logs_retention_days"] == 30
        assert extra["match_data_retention_days"] == 365
        assert extra["archive_enabled"] is True
        assert "archive_path" in extra

    def test_existing_archive_directories_not_recreated(self, temp_config_dir):
        """Test that existing archive directories are not recreated (idempotent)."""
        archive_path = temp_config_dir / "SHARED" / "archive"

        # Pre-create directories
        (archive_path / "logs").mkdir(parents=True)
        (archive_path / "matches").mkdir(parents=True)

        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        with open(temp_config_dir / "SHARED" / "config" / "system.json") as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        mock_logger = MagicMock()
                        lm.std_logger = mock_logger
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value
                        lm._init_data_retention()

        # Verify directories still exist and new ones created
        assert (archive_path / "logs").exists()
        assert (archive_path / "matches").exists()
        assert (archive_path / "players").exists()  # Newly created
        assert (archive_path / "leagues").exists()  # Newly created

        # Verify log shows only newly created directories
        extra = mock_logger.info.call_args[1]["extra"]
        directories_created = extra["directories_created"]
        assert isinstance(directories_created, list)
        assert len(directories_created) == 2  # Only players and leagues

    def test_retention_initialization_handles_default_config(self, temp_config_dir):
        """Test retention uses defaults when config values missing."""
        # Modify config to have minimal data_retention section
        config_path = temp_config_dir / "SHARED" / "config" / "system.json"
        with open(config_path, "r") as f:
            config = json.load(f)
        config["data_retention"] = {"enabled": True}  # Minimal config
        with open(config_path, "w") as f:
            json.dump(config, f)

        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_load_system:
                with patch("agents.league_manager.server.load_agents_config") as mock_load_agents:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        with open(config_path) as f:
                            system_config = json.load(f)
                            mock_load_system.return_value = system_config
                            mock_get_retention.return_value = system_config["data_retention"]
                        with open(
                            temp_config_dir / "SHARED" / "config" / "agents" / "agents_config.json"
                        ) as f:
                            mock_load_agents.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        mock_logger = MagicMock()
                        lm.std_logger = mock_logger
                        lm.system_config = system_config
                        lm.agents_config = mock_load_agents.return_value
                        lm._init_data_retention()

        # Verify defaults used
        extra = mock_logger.info.call_args[1]["extra"]
        assert extra["logs_retention_days"] == 30  # Default
        assert extra["archive_enabled"] is True  # Default
        assert "SHARED/archive" in extra["archive_path"]  # Default path


class TestRetentionIntegration:
    """Integration tests for retention initialization with full League Manager."""

    def test_league_manager_initializes_retention_on_startup(self, tmp_path):
        """Test that League Manager initializes retention during normal startup."""
        # This is a smoke test to ensure retention init doesn't break startup
        # More detailed tests above

        # Create minimal config
        config_dir = tmp_path / "SHARED" / "config"
        config_dir.mkdir(parents=True)

        system_config = {
            "data_retention": {
                "enabled": True,
                "archive_path": str(tmp_path / "SHARED" / "archive"),
            },
            "timeouts": {"registration_sec": 10},
            "retry_policy": {"max_retries": 3},
            "circuit_breaker": {"failure_threshold": 5},
            "network": {"league_manager_port": 8000},
            "logging": {"level": "INFO"},
        }

        with open(config_dir / "system.json", "w") as f:
            json.dump(system_config, f)

        agents_dir = config_dir / "agents"
        agents_dir.mkdir()
        with open(agents_dir / "agents_config.json", "w") as f:
            json.dump({"league_manager": {"agent_id": "LM01", "port": 8000}}, f)

        # Mock BaseAgent to avoid server startup
        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_sys:
                with patch("agents.league_manager.server.load_agents_config") as mock_ag:
                    with patch(
                        "agents.league_manager.server.get_retention_config"
                    ) as mock_get_retention:
                        with open(config_dir / "system.json") as f:
                            sys_config = json.load(f)
                            mock_sys.return_value = sys_config
                            mock_get_retention.return_value = sys_config["data_retention"]
                        with open(agents_dir / "agents_config.json") as f:
                            mock_ag.return_value = json.load(f)

                        # Create League Manager (without base init)
                        lm = object.__new__(LeagueManager)
                        lm.agent_id = "LM01"
                        lm.league_id = "test_league"
                        lm.std_logger = MagicMock()
                        lm.system_config = sys_config
                        lm.agents_config = mock_ag.return_value
                        lm._init_data_retention()

        # Verify retention initialized
        assert hasattr(lm, "retention_config")
        assert (tmp_path / "SHARED" / "archive" / "logs").exists()
