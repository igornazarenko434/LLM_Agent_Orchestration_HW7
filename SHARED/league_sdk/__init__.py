"""
League SDK - Shared utilities for Even/Odd League Multi-Agent System.

This package provides common functionality for all agents in the league system:
- Protocol models and message validation (18 message types)
- Configuration loading and management
- Data persistence layer (repositories)
- Structured logging infrastructure
- Retry policies for resilient communication
- Utility functions (timestamps, auth tokens, etc.)

Version: 1.0.0
Protocol: league.v2
"""

__version__ = "1.0.0"
__protocol__ = "league.v2"

# Import logging infrastructure
from .logger import (
    JSONFormatter,
    JsonLogger,
    log_error,
    log_message_received,
    log_message_sent,
    setup_logger,
)

# Import core protocol models
from .protocol import (  # Registration Messages; League Orchestration; Match Flow; Query Messages; Error Messages; JSON-RPC 2.0 Wrapper; Helper functions
    ChooseParityCall,
    ChooseParityResponse,
    ErrorCode,
    GameError,
    GameInvitation,
    GameJoinAck,
    GameOver,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    LeagueCompleted,
    LeagueError,
    LeagueQuery,
    LeagueQueryResponse,
    LeagueRegisterRequest,
    LeagueRegisterResponse,
    LeagueStandingsUpdate,
    MatchResultReport,
    MessageEnvelope,
    RefereeRegisterRequest,
    RefereeRegisterResponse,
    RoundAnnouncement,
    RoundCompleted,
    get_message_class,
    unwrap_message,
    validate_message_envelope,
    wrap_message,
)

# Import retry infrastructure
from .retry import (
    CircuitBreaker,
    MaxRetriesExceededError,
    NonRetryableError,
    RetryableError,
    RetryConfig,
    call_with_retry,
    get_retry_config,
    is_error_retryable,
    retry_with_backoff,
)

__all__ = [
    "__version__",
    "__protocol__",
    # Protocol Models
    "MessageEnvelope",
    "ErrorCode",
    # Registration
    "RefereeRegisterRequest",
    "RefereeRegisterResponse",
    "LeagueRegisterRequest",
    "LeagueRegisterResponse",
    # League Orchestration
    "RoundAnnouncement",
    "RoundCompleted",
    "LeagueCompleted",
    "LeagueStandingsUpdate",
    # Match Flow
    "GameInvitation",
    "GameJoinAck",
    "ChooseParityCall",
    "ChooseParityResponse",
    "GameOver",
    "MatchResultReport",
    # Query
    "LeagueQuery",
    "LeagueQueryResponse",
    # Errors
    "LeagueError",
    "GameError",
    # JSON-RPC 2.0
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "wrap_message",
    "unwrap_message",
    # Helper Functions
    "validate_message_envelope",
    "get_message_class",
    # Logging
    "JsonLogger",
    "setup_logger",
    "JSONFormatter",
    "log_message_sent",
    "log_message_received",
    "log_error",
    # Retry & Resilience
    "retry_with_backoff",
    "RetryableError",
    "NonRetryableError",
    "MaxRetriesExceededError",
    "CircuitBreaker",
    "RetryConfig",
    "call_with_retry",
    "get_retry_config",
    "is_error_retryable",
]
