"""
Structured logging infrastructure using JSON Lines format.

This module provides two logger classes:
1. JsonLogger: Modern JSONL logger with automatic directory management
2. setup_logger(): Legacy logging.Logger configuration for backward compatibility

JsonLogger is the recommended approach for all agents.
"""

import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "JsonLogger",
    "setup_logger",
    "JSONFormatter",
    "log_message_sent",
    "log_message_received",
    "log_error",
]

# Default log root directory
LOG_ROOT = Path("SHARED/logs")


class JsonLogger:
    """
    Modern JSON Lines logger with automatic directory management.

    This logger writes structured logs in JSONL format with proper directory
    organization based on component type (league, agents, system).

    Usage:
        # Agent logger
        logger = JsonLogger(component="player:P01", agent_id="P01")
        logger.info("GAME_INVITATION_RECEIVED", match_id="R1M1", opponent="P02")

        # League logger
        logger = JsonLogger(component="league_manager", league_id="league_2025_even_odd")
        logger.info("ROUND_ANNOUNCEMENT_SENT", round_id=1, matches_count=2)

        # System logger
        logger = JsonLogger(component="orchestrator")
        logger.info("SYSTEM_STARTUP", version="1.0.0")
    """

    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

    def __init__(
        self,
        component: str,
        agent_id: Optional[str] = None,
        league_id: Optional[str] = None,
        min_level: str = "INFO",
        log_root: Optional[Path] = None,
    ):
        """
        Initialize JsonLogger.

        Args:
            component: Component name (e.g., "player:P01", "league_manager")
            agent_id: Agent ID for agent logs (e.g., "P01", "REF01")
            league_id: League ID for league logs (e.g., "league_2025_even_odd")
            min_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
            log_root: Custom log root directory (default: SHARED/logs)
        """
        self.component = component
        self.agent_id = agent_id or component
        self.min_level = self.LEVELS.index(min_level)

        # Determine log directory based on context
        root = log_root or LOG_ROOT

        if league_id:
            # League-specific logs: logs/league/<league_id>/
            subdir = root / "league" / league_id
            log_filename = f"{component}.log.jsonl"
        elif agent_id:
            # Agent logs: logs/agents/
            subdir = root / "agents"
            log_filename = f"{agent_id}.log.jsonl"
        else:
            # System logs: logs/system/
            subdir = root / "system"
            log_filename = f"{component}.log.jsonl"

        # Create directory if it doesn't exist
        subdir.mkdir(parents=True, exist_ok=True)
        self.log_file = subdir / log_filename

    def log(
        self,
        level: str,
        message: str,
        event_type: Optional[str] = None,
        message_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **extra_fields,
    ) -> None:
        """
        Write a log entry.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Human-readable message
            event_type: Event type for categorization
            message_type: Protocol message type (e.g., "GAME_INVITATION")
            conversation_id: Conversation/match ID for tracing
            data: Additional structured data
            **extra_fields: Any additional fields to include in log
        """
        # Check minimum level
        if self.LEVELS.index(level) < self.min_level:
            return

        # Build log entry with mandatory fields
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level,
            "agent_id": self.agent_id,
            "component": self.component,
            "message": message,
        }

        # Add optional fields
        if event_type:
            log_entry["event_type"] = event_type
        if message_type:
            log_entry["message_type"] = message_type
        if conversation_id:
            log_entry["conversation_id"] = conversation_id
        if data:
            log_entry["data"] = data

        # Add any extra fields
        log_entry.update(extra_fields)

        # Write to file (append-only)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def debug(self, message: str, event_type: Optional[str] = None, **kwargs) -> None:
        """Log DEBUG level message."""
        self.log("DEBUG", message, event_type=event_type, **kwargs)

    def info(self, message: str, event_type: Optional[str] = None, **kwargs) -> None:
        """Log INFO level message."""
        self.log("INFO", message, event_type=event_type, **kwargs)

    def warning(self, message: str, event_type: Optional[str] = None, **kwargs) -> None:
        """Log WARNING level message."""
        self.log("WARNING", message, event_type=event_type, **kwargs)

    def error(self, message: str, event_type: Optional[str] = None, **kwargs) -> None:
        """Log ERROR level message."""
        self.log("ERROR", message, event_type=event_type, **kwargs)

    def log_message_sent(
        self, message_type: str, recipient: str, conversation_id: Optional[str] = None, **details
    ) -> None:
        """
        Log a sent message.

        Args:
            message_type: Protocol message type
            recipient: Recipient agent ID
            conversation_id: Conversation ID for tracing
            **details: Additional message details
        """
        self.debug(
            f"Sent {message_type} to {recipient}",
            event_type="MESSAGE_SENT",
            message_type=message_type,
            recipient=recipient,
            conversation_id=conversation_id,
            **details,
        )

    def log_message_received(
        self, message_type: str, sender: str, conversation_id: Optional[str] = None, **details
    ) -> None:
        """
        Log a received message.

        Args:
            message_type: Protocol message type
            sender: Sender agent ID
            conversation_id: Conversation ID for tracing
            **details: Additional message details
        """
        self.debug(
            f"Received {message_type} from {sender}",
            event_type="MESSAGE_RECEIVED",
            message_type=message_type,
            sender=sender,
            conversation_id=conversation_id,
            **details,
        )

    def log_error_event(self, error_code: str, error_message: str, **details) -> None:
        """
        Log an error event with error code.

        Args:
            error_code: Error code (e.g., "E001")
            error_message: Error description
            **details: Additional error details
        """
        self.error(
            f"Error {error_code}: {error_message}",
            event_type="ERROR_OCCURRED",
            error_code=error_code,
            **details,
        )


# ============================================================================
# Legacy Logger API (for backward compatibility)
# ============================================================================


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON Lines."""

    # Standard LogRecord attributes to skip (not part of extra fields)
    STANDARD_ATTRIBUTES = {
        "name",
        "msg",
        "args",
        "created",
        "msecs",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "process",
        "processName",
        "thread",
        "threadName",
        "taskName",
        "relativeCreated",
        "getMessage",
        "message",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string representation of log entry
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "component": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        # Add all extra fields (any attribute not in standard LogRecord)
        for key, value in record.__dict__.items():
            if key not in self.STANDARD_ATTRIBUTES and not key.startswith("_"):
                log_data[key] = value

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    component: str,
    log_file: str | Path,
    level: int = logging.INFO,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Set up structured JSON logger with rotation (legacy API).

    Args:
        component: Component name (e.g., "player:P01", "referee:REF01")
        log_file: Path to log file (should end in .log.jsonl)
        level: Logging level (default: INFO)
        max_bytes: Maximum log file size before rotation (default: 100MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(component)
    logger.setLevel(level)
    logger.propagate = False

    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    handler.setLevel(level)

    # Set JSON formatter
    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger


def log_message_sent(logger: logging.Logger, message: dict) -> None:
    """
    Log a sent message with structured fields (legacy API).

    Args:
        logger: Logger instance
        message: Message dictionary (should include message_type, conversation_id)
    """
    payload = message.get("result") if isinstance(message.get("result"), dict) else message
    message_type = payload.get("message_type") or payload.get("method")
    conversation_id = payload.get("conversation_id")
    if conversation_id is None and isinstance(payload.get("params"), dict):
        conversation_id = payload["params"].get("conversation_id")
    sender = payload.get("sender")
    if sender is None and isinstance(payload.get("params"), dict):
        sender = payload["params"].get("sender")
    logger.info(
        f"Sent {message_type or 'UNKNOWN'}",
        extra={
            "event_type": "MESSAGE_SENT",
            "message_type": message_type,
            "conversation_id": conversation_id,
            "sender": sender,
        },
    )


def log_message_received(logger: logging.Logger, message: dict) -> None:
    """
    Log a received message with structured fields (legacy API).

    Args:
        logger: Logger instance
        message: Message dictionary
    """
    payload = message.get("result") if isinstance(message.get("result"), dict) else message
    message_type = payload.get("message_type") or payload.get("method")
    conversation_id = payload.get("conversation_id")
    if conversation_id is None and isinstance(payload.get("params"), dict):
        conversation_id = payload["params"].get("conversation_id")
    sender = payload.get("sender")
    if sender is None and isinstance(payload.get("params"), dict):
        sender = payload["params"].get("sender")
    logger.info(
        f"Received {message_type or 'UNKNOWN'}",
        extra={
            "event_type": "MESSAGE_RECEIVED",
            "message_type": message_type,
            "conversation_id": conversation_id,
            "sender": sender,
        },
    )


def log_error(logger: logging.Logger, error_code: str, details: dict) -> None:
    """
    Log an error with error code and details (legacy API).

    Args:
        logger: Logger instance
        error_code: Error code (e.g., "E001")
        details: Error details dictionary
    """
    # Extract message from details to avoid overwriting LogRecord.message
    error_message = details.get("message", "Unknown error")
    extra_details = {k: v for k, v in details.items() if k != "message"}

    logger.error(
        f"Error {error_code}: {error_message}",
        extra={"event_type": "ERROR_OCCURRED", "error_code": error_code, **extra_details},
    )
