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

# Import data retention and cleanup utilities
from .cleanup import (
    CleanupStats,
    archive_old_matches,
    cleanup_old_logs,
    get_retention_config,
    prune_league_rounds,
    prune_player_histories,
    run_full_cleanup,
)

# Import logging infrastructure
from .logger import (
    JSONFormatter,
    JsonLogger,
    log_error,
    log_message_received,
    log_message_sent,
    setup_logger,
)

# Import method name compatibility layer
from .method_aliases import (
    MESSAGE_TYPE_TO_PDF_METHOD,
    METHOD_ALIASES,
    is_pdf_method,
    translate_pdf_method_to_message_type,
)

# Import core protocol models
from .protocol import (  # Registration, Orchestration, Match Flow, Query, Errors, JSON-RPC, Helpers
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

# Import queue processor for thread-safe sequential processing
from .queue_processor import SequentialQueueProcessor

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
    # Queue Processor
    "SequentialQueueProcessor",
    # Data Retention & Cleanup
    "CleanupStats",
    "cleanup_old_logs",
    "archive_old_matches",
    "prune_player_histories",
    "prune_league_rounds",
    "get_retention_config",
    "run_full_cleanup",
    # Method Name Compatibility
    "METHOD_ALIASES",
    "MESSAGE_TYPE_TO_PDF_METHOD",
    "translate_pdf_method_to_message_type",
    "is_pdf_method",
]
