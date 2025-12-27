"""
Method name compatibility layer for PDF-style method names.

This module provides translation between PDF-style tool method names
(e.g., 'handle_game_invitation', 'register_referee') and our message-type-based
method names (e.g., 'GAME_INVITATION', 'REFEREE_REGISTER_REQUEST').

This enables the system to accept BOTH naming conventions while maintaining
our type-safe, protocol-driven architecture internally.
"""

from typing import Dict

# PDF-style method names → Internal message types
# Based on HW7_Instructions PDF examples
METHOD_ALIASES: Dict[str, str] = {
    # Registration methods
    "register_referee": "REFEREE_REGISTER_REQUEST",
    "register_player": "LEAGUE_REGISTER_REQUEST",
    # Player-facing methods (PDF requires these exact names)
    "handle_game_invitation": "GAME_INVITATION",
    "choose_parity": "CHOOSE_PARITY_CALL",
    "notify_match_result": "GAME_OVER",
    # Match flow methods
    "game_join_ack": "GAME_JOIN_ACK",
    "choose_parity_response": "CHOOSE_PARITY_RESPONSE",
    # Referee/LM notification methods
    "notify_round": "ROUND_ANNOUNCEMENT",
    "update_standings": "LEAGUE_STANDINGS_UPDATE",
    "notify_round_completed": "ROUND_COMPLETED",
    "notify_league_completed": "LEAGUE_COMPLETED",
    "notify_game_error": "GAME_ERROR",
    # Match result reporting
    "report_match_result": "MATCH_RESULT_REPORT",
    # Query methods
    "league_query": "LEAGUE_QUERY",
    # Generic MCP wrapper (PDF suggests this)
    "mcp_message": "MCP_MESSAGE",  # Generic authenticated dispatch
    # Ping/health (PDF example)
    "ping": "PING",
    # Note: Debug tools (get_standings, get_player_state, etc.) keep their names
    # as they're already in tool-style format
}

# Reverse mapping for completeness (message type → PDF method name)
MESSAGE_TYPE_TO_PDF_METHOD: Dict[str, str] = {v: k for k, v in METHOD_ALIASES.items()}


def translate_pdf_method_to_message_type(method: str) -> str:
    """
    Translate PDF-style method name to internal message type.

    Args:
        method: Method name from JSON-RPC request (could be PDF-style or message-type)

    Returns:
        Internal message type (e.g., 'GAME_INVITATION')

    Examples:
        >>> translate_pdf_method_to_message_type('handle_game_invitation')
        'GAME_INVITATION'

        >>> translate_pdf_method_to_message_type('GAME_INVITATION')
        'GAME_INVITATION'  # Pass-through if already message type

        >>> translate_pdf_method_to_message_type('choose_parity')
        'CHOOSE_PARITY_CALL'
    """
    return METHOD_ALIASES.get(method, method)


def is_pdf_method(method: str) -> bool:
    """
    Check if method name is PDF-style (lowercase_snake_case tool name).

    Args:
        method: Method name to check

    Returns:
        True if method is a PDF-style alias, False otherwise

    Examples:
        >>> is_pdf_method('handle_game_invitation')
        True

        >>> is_pdf_method('GAME_INVITATION')
        False
    """
    return method in METHOD_ALIASES


__all__ = [
    "METHOD_ALIASES",
    "MESSAGE_TYPE_TO_PDF_METHOD",
    "translate_pdf_method_to_message_type",
    "is_pdf_method",
]
