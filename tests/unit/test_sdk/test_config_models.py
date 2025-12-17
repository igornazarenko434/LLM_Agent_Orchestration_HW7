"""
Unit tests for config_models.py.

Tests Pydantic models for configuration files:
- SystemConfig validation
- AgentConfig validation
- LeagueConfig validation
- GameConfig validation
"""

import pytest
from pydantic import ValidationError
from league_sdk.config_models import (
    SystemConfig,
    AgentConfig,
    LeagueConfig,
    GameConfig,
    TimeoutConfig,
    RetryPolicyConfig,
    SecurityConfig,
    NetworkConfig,
    ScoringConfig,
    validate_port_in_range
)

@pytest.mark.unit
class TestTimeoutConfig:
    """Test TimeoutConfig model."""

    def test_default_timeouts(self):
        """Test default values match PRD requirements."""
        config = TimeoutConfig()
        assert config.registration_sec == 10
        assert config.game_join_ack_sec == 5
        assert config.parity_choice_sec == 30
        assert config.game_over_sec == 5
        assert config.match_result_sec == 10
        assert config.league_query_sec == 10
        assert config.generic_sec == 10

    def test_custom_timeouts(self):
        """Test custom timeout values."""
        config = TimeoutConfig(
            registration_sec=20,
            game_join_ack_sec=10
        )
        assert config.registration_sec == 20
        assert config.game_join_ack_sec == 10
        # Check defaults are preserved for others
        assert config.parity_choice_sec == 30

    def test_timeout_validation(self):
        """Test validation constraints."""
        # Test lower bound (ge=1)
        with pytest.raises(ValidationError):
            TimeoutConfig(registration_sec=0)
        
        # Test upper bound (le=60 for registration)
        with pytest.raises(ValidationError):
            TimeoutConfig(registration_sec=61)

@pytest.mark.unit
class TestRetryPolicyConfig:
    """Test RetryPolicyConfig model."""

    def test_default_retry_policy(self):
        """Test default retry policy matches PRD."""
        config = RetryPolicyConfig()
        assert config.max_retries == 3
        assert config.backoff_strategy == "exponential"
        assert config.initial_delay_sec == 2.0
        assert config.max_delay_sec == 10.0
        assert "E005" in config.retryable_errors

    def test_custom_retry_policy(self):
        """Test custom retry policy."""
        config = RetryPolicyConfig(
            max_retries=5,
            backoff_strategy="linear"
        )
        assert config.max_retries == 5
        assert config.backoff_strategy == "linear"

    def test_backoff_strategy_validation(self):
        """Test validation of backoff strategy."""
        with pytest.raises(ValidationError):
            RetryPolicyConfig(backoff_strategy="random")  # Invalid strategy

@pytest.mark.unit
class TestSecurityConfig:
    """Test SecurityConfig model."""

    def test_default_security_config(self):
        """Test default security settings."""
        config = SecurityConfig()
        assert config.auth_token_length == 32
        assert config.token_ttl_minutes == 1440
        assert config.require_auth is True

    def test_custom_security_config(self):
        """Test custom security settings."""
        config = SecurityConfig(auth_token_length=64)
        assert config.auth_token_length == 64

    def test_auth_token_length_validation(self):
        """Test auth token length validation (ge=32)."""
        with pytest.raises(ValidationError):
            SecurityConfig(auth_token_length=16)

@pytest.mark.unit
class TestNetworkConfig:
    """Test NetworkConfig model."""

    def test_default_network_config(self):
        """Test default network settings match PRD."""
        config = NetworkConfig()
        assert config.host == "localhost"
        assert config.league_manager_port == 8000
        assert config.referee_port_start == 8001
        assert config.player_port_start == 8101

    def test_custom_network_config(self):
        """Test custom network settings."""
        config = NetworkConfig(host="0.0.0.0", league_manager_port=9000)
        assert config.host == "0.0.0.0"
        assert config.league_manager_port == 9000

@pytest.mark.unit
class TestSystemConfig:
    """Test SystemConfig model (root config)."""

    def test_default_system_config(self):
        """Test full default system config."""
        config = SystemConfig()
        assert config.schema_version == "1.0.0"
        assert config.protocol_version == "league.v2"
        # Check nested defaults
        assert config.timeouts.registration_sec == 10
        assert config.retry_policy.max_retries == 3

    def test_system_config_from_json(self):
        """Test creating SystemConfig from dict (simulating JSON load)."""
        data = {
            "schema_version": "1.0.0",
            "protocol_version": "league.v2",
            "timeouts": {"registration_sec": 15},
            "security": {"auth_token_length": 64}
        }
        config = SystemConfig(**data)
        assert config.timeouts.registration_sec == 15
        assert config.security.auth_token_length == 64
        # Defaults preserved
        assert config.timeouts.game_join_ack_sec == 5

    def test_protocol_version_validation(self):
        """Test protocol version must be 'league.v2'."""
        with pytest.raises(ValidationError):
            SystemConfig(protocol_version="league.v1")

@pytest.mark.unit
class TestAgentConfig:
    """Test AgentConfig model."""

    def test_valid_agent_config(self):
        """Test valid agent configuration."""
        config = AgentConfig(
            agent_id="P01",
            agent_type="player",
            display_name="Test Player",
            endpoint="http://localhost:8101/mcp",
            port=8101
        )
        assert config.agent_id == "P01"
        assert config.active is True  # Default

    def test_agent_id_pattern_validation(self):
        """Test agent ID regex pattern."""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="invalid-id",  # Contains hyphen
                agent_type="player",
                display_name="Test",
                endpoint="http://localhost",
                port=8000
            )

    def test_agent_type_validation(self):
        """Test agent type enum validation."""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="P01",
                agent_type="spectator",  # Invalid type
                display_name="Test",
                endpoint="http://localhost",
                port=8000
            )

@pytest.mark.unit
class TestScoringConfig:
    """Test ScoringConfig model."""

    def test_default_scoring_config(self):
        """Test default scoring rules (Win=3, Draw=1, Loss=0)."""
        config = ScoringConfig()
        assert config.points_for_win == 3
        assert config.points_for_draw == 1
        assert config.points_for_loss == 0

    def test_custom_scoring_config(self):
        """Test custom scoring rules."""
        config = ScoringConfig(points_for_win=5)
        assert config.points_for_win == 5

@pytest.mark.unit
class TestLeagueConfig:
    """Test LeagueConfig model."""

    def test_valid_league_config(self):
        """Test valid league configuration."""
        config = LeagueConfig(
            league_id="league_2025",
            display_name="Test League",
            game_type="even_odd"
        )
        assert config.status == "PENDING"  # Default
        assert config.scoring.points_for_win == 3  # Default

    def test_league_id_pattern_validation(self):
        """Test league ID regex pattern."""
        with pytest.raises(ValidationError):
            LeagueConfig(
                league_id="League 2025",  # Contains spaces/caps
                display_name="Test",
                game_type="even_odd"
            )

    def test_league_status_validation(self):
        """Test status enum validation."""
        with pytest.raises(ValidationError):
            LeagueConfig(
                league_id="test",
                display_name="Test",
                game_type="even_odd",
                status="ARCHIVED"  # Invalid status
            )

    def test_league_config_from_json(self):
        """Test creating LeagueConfig from dict."""
        data = {
            "league_id": "test_league",
            "display_name": "Test League",
            "game_type": "even_odd",
            "scoring": {"points_for_win": 5}
        }
        config = LeagueConfig(**data)
        assert config.scoring.points_for_win == 5

@pytest.mark.unit
class TestGameConfig:
    """Test GameConfig model."""

    def test_valid_game_config(self):
        """Test valid game configuration."""
        config = GameConfig(
            game_type="even_odd",
            display_name="Even/Odd",
            rules_module="games.even_odd"
        )
        assert config.supports_draw is True  # Default
        assert config.max_round_time_sec == 60  # Default

    def test_game_type_pattern_validation(self):
        """Test game type regex pattern."""
        with pytest.raises(ValidationError):
            GameConfig(
                game_type="Even-Odd",  # Invalid format
                display_name="Test",
                rules_module="test"
            )

    def test_game_config_from_json(self):
        """Test creating GameConfig from dict."""
        data = {
            "game_type": "even_odd",
            "display_name": "Even/Odd",
            "rules_module": "games.even_odd",
            "game_specific_config": {"range": [1, 10]}
        }
        config = GameConfig(**data)
        assert config.game_specific_config["range"] == [1, 10]

@pytest.mark.unit
class TestPortValidation:
    """Test validate_port_in_range helper."""

    def test_league_manager_port_validation(self):
        """Test League Manager port validation."""
        network_config = NetworkConfig()
        
        # Valid
        assert validate_port_in_range(8000, "league_manager", network_config) is True
        
        # Invalid
        with pytest.raises(ValueError):
            validate_port_in_range(8001, "league_manager", network_config)

    def test_referee_port_validation(self):
        """Test Referee port validation."""
        network_config = NetworkConfig()
        
        # Valid
        assert validate_port_in_range(8001, "referee", network_config) is True
        assert validate_port_in_range(8002, "referee", network_config) is True
        
        # Invalid
        with pytest.raises(ValueError):
            validate_port_in_range(8003, "referee", network_config)

    def test_player_port_validation(self):
        """Test Player port validation."""
        network_config = NetworkConfig()
        
        # Valid
        assert validate_port_in_range(8101, "player", network_config) is True
        
        # Invalid
        with pytest.raises(ValueError):
            validate_port_in_range(8000, "player", network_config)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])