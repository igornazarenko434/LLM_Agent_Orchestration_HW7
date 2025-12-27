"""
Configuration data models using Pydantic for schema validation.

This module defines typed models for all configuration files:
- SystemConfig: Global system settings (timeouts, retry policy, network)
- AgentConfig: Agent registry entries (endpoint, metadata)
- LeagueConfig: League-specific settings (scoring, participants)
- GameConfig: Game type definitions (rules, timeouts)

All models enforce PRD specifications and provide validation.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

__all__ = [
    "TimeoutConfig",
    "RetryPolicyConfig",
    "SecurityConfig",
    "NetworkConfig",
    "SystemConfig",
    "AgentConfig",
    "LeagueConfig",
    "ScoringConfig",
    "GameConfig",
]


# ============================================================================
# SYSTEM CONFIGURATION MODELS (PRD Section 6.4, 6.5)
# ============================================================================


class TimeoutConfig(BaseModel):
    """
    Timeout configurations for various operations.

    PRD Requirements:
    - registration: 10 seconds (REFEREE_REGISTER, LEAGUE_REGISTER)
    - game_join_ack: 5 seconds (GAME_JOIN_ACK)
    - parity_choice: 30 seconds (CHOOSE_PARITY)
    - game_over: 5 seconds (GAME_OVER)
    - match_result: 10 seconds (MATCH_RESULT_REPORT)
    - league_query: 10 seconds (LEAGUE_QUERY)
    - generic: 10 seconds (default for other operations)
    """

    registration_sec: int = Field(
        default=10, ge=1, le=60, description="Timeout for REFEREE_REGISTER and LEAGUE_REGISTER (10s)"
    )

    game_join_ack_sec: int = Field(
        default=5, ge=1, le=60, description="Timeout for GAME_JOIN_ACK response (5s)"
    )

    parity_choice_sec: int = Field(
        default=30, ge=1, le=120, description="Timeout for CHOOSE_PARITY response (30s)"
    )

    game_over_sec: int = Field(default=5, ge=1, le=60, description="Timeout for GAME_OVER message (5s)")

    match_result_sec: int = Field(
        default=10, ge=1, le=60, description="Timeout for MATCH_RESULT_REPORT (10s)"
    )

    league_query_sec: int = Field(default=10, ge=1, le=60, description="Timeout for LEAGUE_QUERY (10s)")

    generic_sec: int = Field(
        default=10, ge=1, le=60, description="Default timeout for other operations (10s)"
    )


class RetryPolicyConfig(BaseModel):
    """
    Retry policy configuration with exponential backoff.

    PRD Requirements (Section 6.4):
    - max_retries: 3
    - backoff_strategy: "exponential"
    - initial_delay_sec: 2
    - max_delay_sec: 10
    - retryable_errors: ["E005", "E006", "E009", "E014", "E015", "E016"]
    """

    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retry attempts (PRD: 3)"
    )

    backoff_strategy: Literal["exponential", "linear", "fixed"] = Field(
        default="exponential", description="Backoff strategy (PRD: exponential)"
    )

    initial_delay_sec: float = Field(
        default=2.0, ge=0.1, le=60.0, description="Initial retry delay in seconds (PRD: 2s)"
    )

    max_delay_sec: float = Field(
        default=10.0, ge=0.1, le=120.0, description="Maximum retry delay in seconds (PRD: 10s)"
    )

    retryable_errors: list[str] = Field(
        default=["E005", "E006", "E009", "E014", "E015", "E016"],
        description="List of retryable error codes (PRD Section 6.4)",
    )


class SecurityConfig(BaseModel):
    """
    Security configuration for authentication and authorization.

    Configuration for:
    - Auth token length and TTL
    - Authentication requirements
    - Allowed origins for CORS
    """

    auth_token_length: int = Field(
        default=32, ge=32, description="Minimum length for authentication tokens (32+ characters)"
    )

    token_ttl_minutes: int = Field(
        default=1440, ge=1, description="Token time-to-live in minutes (default: 24 hours)"
    )

    require_auth: bool = Field(
        default=True, description="Whether authentication is required for all requests"
    )

    allow_start_league_without_auth: bool = Field(
        default=False,
        description="Allow start_league tool without auth token (admin/operator usage)",
    )

    allowed_origins: list[str] = Field(
        default=["*"], description="Allowed origins for CORS (use ['*'] for development)"
    )


class NetworkConfig(BaseModel):
    """
    Network configuration for agent communication.

    PRD Requirements (Section 6.5):
    - League Manager: port 8000
    - Referees: ports 8001-8002
    - Players: ports 8101-8104 (minimum), scalable to 8101-9100
    """

    host: str = Field(
        default="localhost", description="Host for agent binding (localhost for local development)"
    )

    league_manager_port: int = Field(
        default=8000, ge=1024, le=65535, description="League Manager port (PRD: 8000)"
    )

    referee_port_start: int = Field(
        default=8001, ge=1024, le=65535, description="Starting port for referee agents (PRD: 8001)"
    )

    referee_port_end: int = Field(
        default=8002, ge=1024, le=65535, description="Ending port for referee agents (PRD: 8002)"
    )

    player_port_start: int = Field(
        default=8101, ge=1024, le=65535, description="Starting port for player agents (PRD: 8101)"
    )

    player_port_end: int = Field(
        default=9100,
        ge=1024,
        le=65535,
        description="Ending port for player agents (PRD: 9100 for 1000 players)",
    )

    max_connections: int = Field(
        default=100, ge=1, description="Maximum concurrent connections per agent"
    )

    request_timeout_sec: int = Field(
        default=30, ge=1, le=300, description="HTTP request timeout in seconds"
    )


class SystemConfig(BaseModel):
    """
    System-wide configuration settings.

    This is the root configuration model loaded from SHARED/config/system.json.
    Contains all global settings for timeouts, retry policies, networking, etc.
    """

    schema_version: str = Field(default="1.0.0", description="Configuration schema version")

    protocol_version: Literal["league.v2"] = Field(
        default="league.v2", description="Protocol version (must be 'league.v2')"
    )

    timeouts: TimeoutConfig = Field(
        default_factory=TimeoutConfig, description="Timeout configurations for various operations"
    )

    retry_policy: RetryPolicyConfig = Field(
        default_factory=RetryPolicyConfig, description="Retry policy with exponential backoff"
    )

    security: SecurityConfig = Field(
        default_factory=SecurityConfig, description="Security configuration (auth tokens, TTL, etc.)"
    )

    network: NetworkConfig = Field(
        default_factory=NetworkConfig, description="Network configuration for agent communication"
    )

    logging: dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "format": "json",
            "max_file_size_mb": 100,
            "backup_count": 5,
        },
        description="Logging configuration",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


# ============================================================================
# AGENT CONFIGURATION MODELS
# ============================================================================


class AgentConfig(BaseModel):
    """
    Agent registry configuration entry.

    Each agent (League Manager, Referee, Player) has an entry in
    SHARED/config/agents/agents_config.json with this structure.
    """

    agent_id: str = Field(
        ...,
        pattern=r"^[A-Z0-9]+$",
        description="Unique agent identifier (e.g., 'P01', 'REF01', 'LM01')",
    )

    agent_type: Literal["player", "referee", "league_manager"] = Field(..., description="Type of agent")

    display_name: str = Field(..., min_length=1, description="Human-readable agent name")

    endpoint: str = Field(
        ..., description="HTTP endpoint for MCP server (e.g., 'http://localhost:8101/mcp')"
    )

    port: int = Field(..., ge=1024, le=65535, description="Port number where agent listens")

    active: bool = Field(default=True, description="Whether agent is active and available")

    version: str = Field(default="1.0.0", description="Agent software version")

    game_types: list[str] = Field(
        default_factory=lambda: ["even_odd"], description="Supported game types"
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional agent-specific metadata"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


# ============================================================================
# LEAGUE CONFIGURATION MODELS
# ============================================================================


class ScoringConfig(BaseModel):
    """
    Scoring system configuration.

    PRD Requirements:
    - WIN: 3 points
    - DRAW: 1 point
    - LOSS: 0 points
    """

    model_config = ConfigDict(populate_by_name=True)

    points_for_win: int = Field(
        default=3,
        ge=0,
        alias="win_points",
        description="Points awarded for a win (PRD: 3)",
    )

    points_for_draw: int = Field(
        default=1,
        ge=0,
        alias="draw_points",
        description="Points awarded for a draw (PRD: 1)",
    )

    points_for_loss: int = Field(
        default=0,
        ge=0,
        alias="loss_points",
        description="Points awarded for a loss (PRD: 0)",
    )

    tiebreaker_order: list[str] = Field(
        default=["points", "wins", "head_to_head", "random"],
        description="Tiebreaker criteria in order of precedence",
    )


class ParticipantsConfig(BaseModel):
    """
    Configuration for league participants limits.
    """

    min_players: int = Field(default=2, ge=2, description="Minimum number of players required")

    max_players: int = Field(default=1000, ge=2, description="Maximum number of players allowed")


class LeagueConfig(BaseModel):
    """
    League-specific configuration.

    Loaded from SHARED/config/leagues/<league_id>.json
    Contains settings for a specific league instance.
    """

    schema_version: str = Field(default="1.0.0", description="Configuration schema version")

    league_id: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+$",
        description="Unique league identifier (e.g., 'league_2025_even_odd')",
    )

    display_name: str = Field(..., min_length=1, description="Human-readable league name")

    game_type: str = Field(..., description="Game type for this league (e.g., 'even_odd')")

    status: Literal["PENDING", "ACTIVE", "PAUSED", "COMPLETED"] = Field(
        default="PENDING", description="Current league status"
    )

    scoring: ScoringConfig = Field(
        default_factory=ScoringConfig, description="Scoring system configuration"
    )

    schedule_type: Literal["round_robin", "elimination", "swiss"] = Field(
        default="round_robin", description="Tournament scheduling algorithm (PRD: round_robin)"
    )

    participants: ParticipantsConfig = Field(
        default_factory=ParticipantsConfig, description="Participant limits configuration"
    )

    registration_deadline: Optional[str] = Field(
        default=None, description="ISO 8601 timestamp for registration cutoff"
    )

    start_time: Optional[str] = Field(default=None, description="ISO 8601 timestamp for league start")

    registered_players: list[str] = Field(
        default_factory=list, description="List of registered player IDs"
    )

    assigned_referees: list[str] = Field(
        default_factory=list, description="List of assigned referee IDs"
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional league-specific metadata"
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


# ============================================================================
# GAME CONFIGURATION MODELS
# ============================================================================


class GameConfig(BaseModel):
    """
    Game type configuration.

    Loaded from SHARED/config/games/games_registry.json
    Defines rules and settings for a specific game type.
    """

    game_type: str = Field(
        ..., pattern=r"^[a-z_]+$", description="Unique game type identifier (e.g., 'even_odd')"
    )

    display_name: str = Field(
        ..., min_length=1, description="Human-readable game name (e.g., 'Even/Odd')"
    )

    description: str = Field(default="", description="Game description and rules summary")

    rules_module: str = Field(
        ..., description="Python module path for game logic (e.g., 'agents.referee.games.even_odd')"
    )

    supports_draw: bool = Field(default=True, description="Whether this game can result in a draw")

    max_round_time_sec: int = Field(default=60, ge=1, description="Maximum time per round in seconds")

    min_players: int = Field(default=2, ge=1, description="Minimum players required for this game")

    max_players: int = Field(default=2, ge=1, description="Maximum players allowed in this game")

    game_specific_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Game-specific configuration (e.g., for even_odd: random_range)",
    )

    class Config:
        """Pydantic configuration."""

        extra = "allow"


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_port_in_range(port: int, agent_type: str, network_config: NetworkConfig) -> bool:
    """
    Validate that a port is in the correct range for the agent type.

    Args:
        port: Port number to validate
        agent_type: Type of agent ("player", "referee", "league_manager")
        network_config: Network configuration with port ranges

    Returns:
        True if port is valid for agent type

    Raises:
        ValueError: If port is not in valid range for agent type
    """
    if agent_type == "league_manager":
        if port != network_config.league_manager_port:
            raise ValueError(
                f"League Manager must use port {network_config.league_manager_port}, got {port}"
            )
    elif agent_type == "referee":
        if not (network_config.referee_port_start <= port <= network_config.referee_port_end):
            raise ValueError(
                f"Referee port {port} not in range "
                f"{network_config.referee_port_start}-{network_config.referee_port_end}"
            )
    elif agent_type == "player":
        if not (network_config.player_port_start <= port <= network_config.player_port_end):
            raise ValueError(
                f"Player port {port} not in range "
                f"{network_config.player_port_start}-{network_config.player_port_end}"
            )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    return True
