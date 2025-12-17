"""
Utility functions for common operations.

This module provides helper functions for:
- Timestamp generation and validation
- Agent ID formatting and parsing
- Conversation ID generation
- Auth token generation
"""

import secrets
import string
from datetime import datetime, timezone
import re
from typing import Tuple

__all__ = [
    "generate_timestamp",
    "validate_timestamp",
    "format_sender",
    "parse_sender",
    "generate_conversation_id",
    "generate_auth_token"
]


def generate_timestamp() -> str:
    """
    Generate ISO 8601 UTC timestamp in league.v2 format.

    Returns:
        Timestamp string in format: YYYY-MM-DDTHH:MM:SSZ

    Example:
        >>> generate_timestamp()
        '2025-01-15T10:15:30Z'
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_timestamp(timestamp: str) -> bool:
    """
    Validate timestamp format against league.v2 specification.

    Args:
        timestamp: Timestamp string to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_timestamp("2025-01-15T10:15:30Z")
        True
        >>> validate_timestamp("2025-01-15 10:15:30")
        False
    """
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    if not re.match(pattern, timestamp):
        return False

    # Validate actual datetime
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def format_sender(agent_type: str, agent_id: str) -> str:
    """
    Format sender field according to league.v2 specification.

    Args:
        agent_type: Type of agent ("player", "referee", "league_manager")
        agent_id: Agent identifier (e.g., "P01", "REF01", "LM01")

    Returns:
        Formatted sender string: "{agent_type}:{agent_id}"

    Example:
        >>> format_sender("player", "P01")
        'player:P01'
        >>> format_sender("referee", "REF01")
        'referee:REF01'
    """
    return f"{agent_type}:{agent_id}"


def parse_sender(sender: str) -> Tuple[str, str]:
    """
    Parse sender field into agent_type and agent_id.

    Args:
        sender: Sender string in format "{agent_type}:{agent_id}"

    Returns:
        Tuple of (agent_type, agent_id)

    Raises:
        ValueError: If sender format is invalid

    Example:
        >>> parse_sender("player:P01")
        ('player', 'P01')
        >>> parse_sender("referee:REF01")
        ('referee', 'REF01')
    """
    pattern = r"^(player|referee|league_manager):([A-Z0-9]+)$"
    match = re.match(pattern, sender)

    if not match:
        raise ValueError(f"Invalid sender format: {sender}")

    return match.group(1), match.group(2)


def generate_conversation_id(prefix: str = "conv") -> str:
    """
    Generate unique conversation ID for message threading.

    Args:
        prefix: Optional prefix for conversation ID (default: "conv")

    Returns:
        Unique conversation ID string

    Example:
        >>> generate_conversation_id("match")
        'match-r1m1-a3f5e2'
        >>> generate_conversation_id()
        'conv-b8d9c1'
    """
    # Generate 6-character random suffix
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}-{suffix}"


def generate_auth_token(length: int = 32) -> str:
    """
    Generate cryptographically secure authentication token.

    Args:
        length: Token length in characters (default: 32, minimum required by PRD)

    Returns:
        Secure random token string

    Example:
        >>> token = generate_auth_token(32)
        >>> len(token) >= 32
        True
    """
    if length < 32:
        raise ValueError("Token length must be at least 32 characters")

    # Generate secure random token using alphanumeric characters
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
