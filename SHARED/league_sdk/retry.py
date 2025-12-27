"""
Retry policy implementation with exponential backoff and circuit breaker.

This module provides:
- retry_with_backoff(): Decorator for automatic retries
- CircuitBreaker: Circuit breaker pattern for resilience
- call_with_retry(): HTTP request wrapper with retry logic
- Configurable retry behavior from system.json
- Integration with league.v2 protocol error codes
"""

import asyncio
import functools
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

__all__ = [
    "retry_with_backoff",
    "RetryableError",
    "NonRetryableError",
    "CircuitBreaker",
    "RetryConfig",
    "call_with_retry",
    "get_retry_config",
    "is_error_retryable",
]

T = TypeVar("T")


# ============================================================================
# EXCEPTION CLASSES
# ============================================================================


class RetryableError(Exception):
    """Base class for errors that should be retried."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class NonRetryableError(Exception):
    """Base class for errors that should not be retried."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class MaxRetriesExceededError(Exception):
    """Raised when maximum retry attempts are exceeded."""

    def __init__(self, message: str, retry_count: int, last_error: Exception):
        super().__init__(message)
        self.retry_count = retry_count
        self.last_error = last_error


# ============================================================================
# RETRY CONFIGURATION
# ============================================================================


class RetryConfig:
    """
    Retry policy configuration.

    Loads from system.json or uses defaults.
    Per assignment: max_retries=3, backoff: 2, 4, 8 seconds
    """

    # Default values per assignment specification
    MAX_RETRIES = 3
    BACKOFF_STRATEGY = "exponential"
    INITIAL_DELAY_SEC = 2.0
    MAX_DELAY_SEC = 10.0
    BACKOFF_MULTIPLIER = 2.0

    # Retryable error codes per protocol
    # E001 (TIMEOUT_ERROR) and E009 added per user requirements
    RETRYABLE_ERRORS = [
        "E001",  # TIMEOUT_ERROR (retryable per requirements)
        "E005",  # INVALID_GAME_STATE
        "E006",  # PLAYER_NOT_AVAILABLE
        "E009",  # ROUND_NOT_ACTIVE (connection error)
        "E014",  # RATE_LIMIT_EXCEEDED
        "E015",  # INTERNAL_SERVER_ERROR
        "E016",  # SERVICE_UNAVAILABLE
    ]

    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load retry configuration from system.json.

        Args:
            config_path: Path to system.json (default: SHARED/config/system.json)

        Returns:
            Dictionary with retry configuration
        """
        if config_path is None:
            config_path = Path("SHARED/config/system.json")

        try:
            import json

            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("retry_policy", {})
        except (FileNotFoundError, json.JSONDecodeError):
            # Return defaults if config file not found
            return {
                "max_retries": cls.MAX_RETRIES,
                "backoff_strategy": cls.BACKOFF_STRATEGY,
                "initial_delay_sec": cls.INITIAL_DELAY_SEC,
                "max_delay_sec": cls.MAX_DELAY_SEC,
                "retryable_errors": cls.RETRYABLE_ERRORS,
            }


def get_retry_config() -> Dict[str, Any]:
    """Get retry configuration from system.json."""
    return RetryConfig.load_from_file()


def is_error_retryable(error_code: str) -> bool:
    """
    Determine if an error code represents a retryable error.

    Per protocol specification:
    - Retryable: E001, E005, E006, E009, E014, E015, E016
    - Non-retryable: E002, E003, E004, E007, E008, E010, E011, E012, E013, E017, E018

    Args:
        error_code: Error code string (e.g., "E001")

    Returns:
        True if error is retryable, False otherwise
    """
    config = get_retry_config()
    retryable_errors = config.get("retryable_errors", RetryConfig.RETRYABLE_ERRORS)
    return error_code in retryable_errors


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================


class CircuitBreaker:
    """
    Circuit breaker pattern for resilience with async/await support.

    Prevents repeated calls to a failing service by opening the circuit
    after a threshold of failures. After a timeout, allows one test call
    (half-open state) to check if service has recovered.

    Thread-safe for async concurrent operations using asyncio.Lock.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered, one request allowed

    Per specification:
    - failure_threshold: 5 failures trigger OPEN state
    - reset_timeout: 60 seconds before testing recovery
    """

    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 5)
            reset_timeout: Seconds before attempting recovery test (default: 60)
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = asyncio.Lock()  # Async lock for thread safety

    async def can_execute(self) -> bool:
        """
        Check if request can be executed (async with lock for thread safety).

        Returns:
            True if request allowed, False if circuit is open
        """
        async with self._lock:
            if self.state == "CLOSED":
                return True

            if self.state == "OPEN":
                # Check if timeout expired, transition to HALF_OPEN
                if self.last_failure_time and datetime.now(
                    timezone.utc
                ) - self.last_failure_time > timedelta(seconds=self.reset_timeout):
                    self.state = "HALF_OPEN"
                    return True
                return False

            # HALF_OPEN state: allow one test request
            return True

    async def record_success(self) -> None:
        """Record successful request, reset circuit to CLOSED (async with lock)."""
        async with self._lock:
            self.failures = 0
            self.state = "CLOSED"
            self.last_failure_time = None

    async def record_failure(self) -> None:
        """Record failed request, potentially open circuit (async with lock)."""
        async with self._lock:
            self.failures += 1
            self.last_failure_time = datetime.now(timezone.utc)

            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
            elif self.state == "HALF_OPEN":
                # Test request failed, back to OPEN
                self.state = "OPEN"

    def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state.

        Returns:
            Dictionary with state information
        """
        return {
            "state": self.state,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "reset_timeout_sec": self.reset_timeout,
        }


# ============================================================================
# RETRY DECORATOR WITH EXPONENTIAL BACKOFF
# ============================================================================


def retry_with_backoff(
    max_retries: Optional[int] = None,
    retryable_exceptions: Tuple = (ConnectionError, TimeoutError, RetryableError),
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    logger: Optional[logging.Logger] = None,
    track_retry_info: bool = False,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Per assignment specification:
    - Max retries: 3 (configurable via system.json)
    - Backoff delays: 2, 4, 8 seconds (exponential)
    - Retryable errors: E001, E005, E006, E009, E014, E015, E016
    - After max retries: Raise MaxRetriesExceededError (TECHNICAL_LOSS)

    Args:
        max_retries: Maximum retry attempts (default: from config or 3)
        retryable_exceptions: Exceptions to retry (default: Connection/Timeout errors)
        initial_delay: Initial delay in seconds (default: from config or 2.0)
        max_delay: Maximum delay in seconds (default: from config or 10.0)
        logger: Optional logger for retry attempts
        track_retry_info: If True, return retry info in exceptions

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_backoff(max_retries=3, logger=my_logger)
        async def send_message(endpoint: str, message: dict):
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=message, timeout=10)
                response.raise_for_status()
                return response.json()
    """
    # Load config
    config = get_retry_config()
    max_retries = max_retries or config.get("max_retries", RetryConfig.MAX_RETRIES)
    initial_delay = initial_delay or config.get("initial_delay_sec", RetryConfig.INITIAL_DELAY_SEC)
    max_delay = max_delay or config.get("max_delay_sec", RetryConfig.MAX_DELAY_SEC)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            retry_attempts = []

            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)

                    # Log success after retry
                    if attempt > 0 and logger:
                        logger.info(
                            f"Retry successful for {func.__name__} on attempt {attempt + 1}",
                            extra={
                                "event_type": "RETRY_SUCCESS",
                                "attempt": attempt + 1,
                                "total_retries": attempt,
                            },
                        )

                    return result

                except retryable_exceptions as e:
                    last_exception = e

                    # Calculate next retry time
                    if attempt < max_retries - 1:
                        # Exponential backoff: 2^attempt * initial_delay
                        delay = min(
                            initial_delay * (RetryConfig.BACKOFF_MULTIPLIER**attempt), max_delay
                        )
                        next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)

                        retry_attempts.append(
                            {
                                "attempt": attempt + 1,
                                "error": str(e),
                                "delay_seconds": delay,
                                "next_retry_at": next_retry_at.isoformat(),
                            }
                        )

                        if logger:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s",
                                extra={
                                    "event_type": "RETRY_ATTEMPT",
                                    "attempt": attempt + 1,
                                    "max_retries": max_retries,
                                    "delay_seconds": delay,
                                    "next_retry_at": next_retry_at.isoformat(),
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )

                        time.sleep(delay)
                    else:
                        # Max retries exceeded
                        if logger:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded for {func.__name__}",
                                extra={
                                    "event_type": "RETRY_EXHAUSTED",
                                    "max_retries": max_retries,
                                    "total_attempts": attempt + 1,
                                    "error": str(e),
                                },
                            )

                        # Raise MaxRetriesExceededError with context
                        error_msg = f"Max retries ({max_retries}) exceeded: {str(e)}"
                        max_retries_error = MaxRetriesExceededError(
                            error_msg, retry_count=attempt + 1, last_error=e
                        )

                        if track_retry_info:
                            max_retries_error.retry_info = {
                                "retry_count": attempt + 1,
                                "max_retries": max_retries,
                                "attempts": retry_attempts,
                            }

                        raise max_retries_error

                except Exception as e:
                    # Non-retryable exception, fail fast
                    if logger:
                        logger.error(
                            f"Non-retryable error in {func.__name__}: {e}",
                            extra={
                                "event_type": "NON_RETRYABLE_ERROR",
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )
                    raise

            # This should never be reached due to the raise in the loop
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


# ============================================================================
# HTTP REQUEST RETRY WRAPPER
# ============================================================================


async def call_with_retry(
    endpoint: str,
    method: str,
    params: Dict[str, Any],
    timeout: int = 30,
    logger: Optional[logging.Logger] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
) -> Dict[str, Any]:
    """
    Send JSON-RPC 2.0 request with retry logic (async with httpx).

    THREAD SAFETY: Uses async httpx client for non-blocking I/O.
    Critical for Mission 7: Enables concurrent match handling without blocking event loop.

    Per specification:
    - Max 3 retries with exponential backoff (2, 4, 8 seconds)
    - Retries on Connection/Timeout errors
    - Returns error dict after max retries exceeded
    - Integrates with circuit breaker pattern

    Args:
        endpoint: HTTP endpoint URL
        method: JSON-RPC method name
        params: Method parameters (protocol message)
        timeout: Request timeout in seconds (default: 30)
        logger: Optional logger for retry events
        circuit_breaker: Optional circuit breaker instance

    Returns:
        JSON-RPC response dictionary

    Example:
        response = await call_with_retry(
            endpoint="http://localhost:8101/mcp",
            method="handle_game_invitation",
            params=invitation_message,
            timeout=30
        )
    """
    import httpx

    # Check circuit breaker (async)
    if circuit_breaker and not await circuit_breaker.can_execute():
        return {
            "error": {
                "error_code": "E016",
                "error_name": "SERVICE_UNAVAILABLE",
                "error_description": f"Circuit breaker OPEN for {endpoint}",
                "circuit_breaker_state": circuit_breaker.get_state(),
            }
        }

    config = get_retry_config()
    max_retries = config.get("max_retries", RetryConfig.MAX_RETRIES)
    initial_delay = config.get("initial_delay_sec", RetryConfig.INITIAL_DELAY_SEC)

    last_error = None

    for attempt in range(max_retries):
        try:
            # Use async httpx client (non-blocking I/O)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                    timeout=timeout,
                )

                # For 2xx responses, return success
                if 200 <= response.status_code < 300:
                    # Record success in circuit breaker (async)
                    if circuit_breaker:
                        await circuit_breaker.record_success()
                    return response.json()

                # For 4xx and 5xx responses, return the error response (don't raise exception)
                # This allows callers to handle specific error codes (e.g., 409 DUPLICATE_REGISTRATION)
                return response.json()

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e

            # Record failure in circuit breaker (async)
            if circuit_breaker:
                await circuit_breaker.record_failure()

            if attempt < max_retries - 1:
                # Calculate delay: 2, 4, 8 seconds
                delay = initial_delay * (RetryConfig.BACKOFF_MULTIPLIER**attempt)

                if logger:
                    logger.warning(
                        f"Request failed, retry {attempt + 1}/{max_retries} after {delay}s",
                        extra={
                            "event_type": "HTTP_RETRY",
                            "endpoint": endpoint,
                            "method": method,
                            "attempt": attempt + 1,
                            "delay_seconds": delay,
                            "error": str(e),
                        },
                    )

                # Use async sleep (non-blocking)
                await asyncio.sleep(delay)

    # Max retries exceeded, return error response
    if logger:
        logger.error(
            f"Max retries exceeded for {endpoint}",
            extra={
                "event_type": "HTTP_RETRY_EXHAUSTED",
                "endpoint": endpoint,
                "method": method,
                "max_retries": max_retries,
                "last_error": str(last_error),
            },
        )

    return {
        "error": {
            "error_code": "E015",
            "error_name": "INTERNAL_SERVER_ERROR",
            "error_description": f"Max retries ({max_retries}) exceeded: {str(last_error)}",
            "retry_info": {
                "retry_count": max_retries,
                "max_retries": max_retries,
                "last_error": str(last_error),
            },
        }
    }
