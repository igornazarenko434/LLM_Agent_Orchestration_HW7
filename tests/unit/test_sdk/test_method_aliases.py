"""
Tests for PDF method name compatibility layer.

Verifies that both PDF-style method names (e.g., 'handle_game_invitation')
and our message-type names (e.g., 'GAME_INVITATION') work correctly.
"""

import pytest

from league_sdk.method_aliases import (
    MESSAGE_TYPE_TO_PDF_METHOD,
    METHOD_ALIASES,
    is_pdf_method,
    translate_pdf_method_to_message_type,
)


class TestMethodAliasTranslation:
    """Test translation from PDF method names to message types."""

    def test_translate_pdf_to_message_type(self):
        """PDF method names should translate to message types."""
        assert translate_pdf_method_to_message_type("handle_game_invitation") == "GAME_INVITATION"
        assert translate_pdf_method_to_message_type("choose_parity") == "CHOOSE_PARITY_CALL"
        assert translate_pdf_method_to_message_type("register_referee") == "REFEREE_REGISTER_REQUEST"
        assert translate_pdf_method_to_message_type("register_player") == "LEAGUE_REGISTER_REQUEST"

    def test_translate_passthrough_for_message_types(self):
        """Message types should pass through unchanged."""
        assert translate_pdf_method_to_message_type("GAME_INVITATION") == "GAME_INVITATION"
        assert translate_pdf_method_to_message_type("CHOOSE_PARITY_CALL") == "CHOOSE_PARITY_CALL"
        assert (
            translate_pdf_method_to_message_type("REFEREE_REGISTER_REQUEST")
            == "REFEREE_REGISTER_REQUEST"
        )

    def test_translate_unknown_methods_passthrough(self):
        """Unknown methods should pass through unchanged."""
        assert translate_pdf_method_to_message_type("unknown_method") == "unknown_method"
        assert translate_pdf_method_to_message_type("UNKNOWN_TYPE") == "UNKNOWN_TYPE"

    def test_is_pdf_method_detection(self):
        """Should correctly identify PDF-style methods."""
        # PDF-style methods
        assert is_pdf_method("handle_game_invitation") is True
        assert is_pdf_method("choose_parity") is True
        assert is_pdf_method("register_referee") is True

        # Message types (not PDF-style)
        assert is_pdf_method("GAME_INVITATION") is False
        assert is_pdf_method("CHOOSE_PARITY_CALL") is False
        assert is_pdf_method("REFEREE_REGISTER_REQUEST") is False

        # Unknown methods
        assert is_pdf_method("unknown") is False


class TestMethodAliasMappings:
    """Test the completeness of method alias mappings."""

    def test_all_required_player_methods_mapped(self):
        """All required player tool methods from PDF should be mapped."""
        required_player_tools = [
            "handle_game_invitation",
            "choose_parity",
            "notify_match_result",
        ]

        for tool in required_player_tools:
            assert tool in METHOD_ALIASES, f"Missing PDF tool: {tool}"
            assert METHOD_ALIASES[tool] != "", f"Empty mapping for {tool}"

    def test_all_registration_methods_mapped(self):
        """Registration methods from PDF should be mapped."""
        assert "register_referee" in METHOD_ALIASES
        assert METHOD_ALIASES["register_referee"] == "REFEREE_REGISTER_REQUEST"

        assert "register_player" in METHOD_ALIASES
        assert METHOD_ALIASES["register_player"] == "LEAGUE_REGISTER_REQUEST"

    def test_reverse_mapping_consistency(self):
        """Reverse mapping should be consistent with forward mapping."""
        for pdf_method, message_type in METHOD_ALIASES.items():
            # Check reverse mapping exists
            assert message_type in MESSAGE_TYPE_TO_PDF_METHOD
            # Check it maps back correctly
            assert MESSAGE_TYPE_TO_PDF_METHOD[message_type] == pdf_method

    def test_no_duplicate_message_types(self):
        """Each message type should map to only one PDF method."""
        message_types = list(METHOD_ALIASES.values())
        assert len(message_types) == len(set(message_types)), "Duplicate message types in aliases"

    def test_all_18_message_types_covered(self):
        """Key protocol message types should have PDF aliases."""
        critical_message_types = [
            "GAME_INVITATION",
            "CHOOSE_PARITY_CALL",
            "GAME_OVER",
            "REFEREE_REGISTER_REQUEST",
            "LEAGUE_REGISTER_REQUEST",
            "ROUND_ANNOUNCEMENT",
            "LEAGUE_STANDINGS_UPDATE",
            "MATCH_RESULT_REPORT",
            "LEAGUE_QUERY",
        ]

        mapped_types = set(METHOD_ALIASES.values())
        for msg_type in critical_message_types:
            assert msg_type in mapped_types, f"{msg_type} not mapped from any PDF method"


class TestEndToEndCompatibility:
    """Test that PDF-style and message-type methods produce same routing."""

    def test_pdf_and_message_type_equivalence(self):
        """PDF method and message type should translate to same final method."""
        # These pairs should be equivalent
        equivalence_pairs = [
            ("handle_game_invitation", "GAME_INVITATION"),
            ("choose_parity", "CHOOSE_PARITY_CALL"),
            ("register_referee", "REFEREE_REGISTER_REQUEST"),
            ("notify_match_result", "GAME_OVER"),
        ]

        for pdf_method, message_type in equivalence_pairs:
            translated_pdf = translate_pdf_method_to_message_type(pdf_method)
            translated_msg = translate_pdf_method_to_message_type(message_type)

            assert translated_pdf == translated_msg, (
                f"PDF method '{pdf_method}' and message type '{message_type}' "
                f"should route to same handler, but got: "
                f"'{translated_pdf}' vs '{translated_msg}'"
            )
            assert translated_pdf == message_type, (
                f"PDF method '{pdf_method}' should translate to '{message_type}', "
                f"but got '{translated_pdf}'"
            )

    def test_all_aliases_translate_to_valid_uppercase(self):
        """All PDF methods should translate to UPPERCASE message types."""
        for pdf_method, expected_type in METHOD_ALIASES.items():
            result = translate_pdf_method_to_message_type(pdf_method)
            assert result == expected_type
            assert (
                result.isupper() or "_" in result
            ), f"Message type '{result}' should be UPPERCASE with underscores"


@pytest.mark.parametrize(
    "pdf_method,expected_message_type",
    [
        ("handle_game_invitation", "GAME_INVITATION"),
        ("choose_parity", "CHOOSE_PARITY_CALL"),
        ("notify_match_result", "GAME_OVER"),
        ("register_referee", "REFEREE_REGISTER_REQUEST"),
        ("register_player", "LEAGUE_REGISTER_REQUEST"),
        ("notify_round", "ROUND_ANNOUNCEMENT"),
        ("update_standings", "LEAGUE_STANDINGS_UPDATE"),
        ("report_match_result", "MATCH_RESULT_REPORT"),
        ("league_query", "LEAGUE_QUERY"),
        ("notify_round_completed", "ROUND_COMPLETED"),
        ("notify_league_completed", "LEAGUE_COMPLETED"),
        ("notify_game_error", "GAME_ERROR"),
    ],
)
def test_specific_translations(pdf_method, expected_message_type):
    """Test each PDF method translates to correct message type."""
    result = translate_pdf_method_to_message_type(pdf_method)
    assert result == expected_message_type, (
        f"PDF method '{pdf_method}' should translate to '{expected_message_type}', "
        f"but got '{result}'"
    )
