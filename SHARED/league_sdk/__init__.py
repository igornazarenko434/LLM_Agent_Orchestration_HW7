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

# Import core protocol models
from .protocol import (
    MessageEnvelope,
    ErrorCode,
    # Registration Messages
    RefereeRegisterRequest,
    RefereeRegisterResponse,
    LeagueRegisterRequest,
    LeagueRegisterResponse,
    # League Orchestration
    RoundAnnouncement,
    RoundCompleted,
    LeagueCompleted,
    LeagueStandingsUpdate,
    # Match Flow
    GameInvitation,
    GameJoinAck,
    ChooseParityCall,
    ChooseParityResponse,
    GameOver,
    MatchResultReport,
    # Query Messages
    LeagueQuery,
    LeagueQueryResponse,
    # Error Messages
    LeagueError,
    GameError,
    # JSON-RPC 2.0 Wrapper
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    wrap_message,
    unwrap_message,
    # Helper functions
    validate_message_envelope,
    get_message_class,
)

# Import logging infrastructure
from .logger import (
    JsonLogger,
    setup_logger,
    JSONFormatter,
    log_message_sent,
    log_message_received,
    log_error,
)

# Import retry infrastructure
from .retry import (
    retry_with_backoff,
    RetryableError,
    NonRetryableError,
    MaxRetriesExceededError,
    CircuitBreaker,
    RetryConfig,
    call_with_retry,
    get_retry_config,
    is_error_retryable,
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
