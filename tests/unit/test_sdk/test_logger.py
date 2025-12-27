"""
Unit tests for structured logging (M2.4).

Tests the JsonLogger implementation:
- JSON formatting
- Log levels
- Output to file
- Convenience methods (info, error, etc.)
- Legacy helper function compatibility
"""

import json
import logging
from pathlib import Path

import pytest

from league_sdk.logger import (
    JSONFormatter,
    JsonLogger,
    log_error,
    log_message_received,
    log_message_sent,
    setup_logger,
)


@pytest.mark.unit
class TestJsonLoggerInitialization:
    """Test JsonLogger initialization and setup."""

    def test_agent_logger_creates_agents_directory(self, tmp_path):
        """Test that agent logger creates agents/ directory."""
        logger = JsonLogger(component="player:P01", agent_id="P01", log_root=tmp_path)

        # Check directory was created
        assert (tmp_path / "agents").exists()
        assert logger.log_file == tmp_path / "agents" / "P01.log.jsonl"

    def test_league_logger_creates_league_directory(self, tmp_path):
        """Test that league logger creates league/<id>/ directory."""
        logger = JsonLogger(
            component="league_manager", league_id="league_2025_even_odd", log_root=tmp_path
        )

        assert (tmp_path / "league" / "league_2025_even_odd").exists()
        assert (
            logger.log_file == tmp_path / "league" / "league_2025_even_odd" / "league_manager.log.jsonl"
        )

    def test_system_logger_creates_system_directory(self, tmp_path):
        """Test that system logger creates system/ directory."""
        logger = JsonLogger(component="orchestrator", log_root=tmp_path)

        assert (tmp_path / "system").exists()
        assert logger.log_file == tmp_path / "system" / "orchestrator.log.jsonl"

    def test_default_agent_id_uses_component(self, tmp_path):
        """Test that agent_id defaults to component."""
        logger = JsonLogger(component="test_component", log_root=tmp_path)
        assert logger.agent_id == "test_component"


@pytest.mark.unit
class TestJsonLoggerLevels:
    """Test log level filtering."""

    def test_default_min_level_is_info(self, tmp_path):
        """Test that default min_level is INFO."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.debug("Debug message")
        logger.info("Info message")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        # DEBUG should be filtered out (default min_level=INFO)
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["message"] == "Info message"
        assert data["level"] == "INFO"

    def test_debug_level_logs_all(self, tmp_path):
        """Test that min_level=DEBUG logs all messages."""
        logger = JsonLogger(component="test", min_level="DEBUG", log_root=tmp_path)

        logger.debug("Debug message")
        logger.info("Info message")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "Debug message" in lines[0]
        assert "Info message" in lines[1]

    def test_info_level_filters_debug(self, tmp_path):
        """Test that min_level=INFO filters DEBUG."""
        logger = JsonLogger(component="test", min_level="INFO", log_root=tmp_path)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "Debug message" not in "".join(lines)
        assert "Info message" in lines[0]
        assert "Warning message" in lines[1]

    def test_warning_level_filters_debug_and_info(self, tmp_path):
        """Test that min_level=WARNING filters DEBUG and INFO."""
        logger = JsonLogger(component="test", min_level="WARNING", log_root=tmp_path)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 2
        assert "Warning message" in lines[0]
        assert "Error message" in lines[1]

    def test_error_level_only_logs_errors(self, tmp_path):
        """Test that min_level=ERROR only logs ERROR."""
        logger = JsonLogger(component="test", min_level="ERROR", log_root=tmp_path)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["message"] == "Error message"
        assert data["level"] == "ERROR"


@pytest.mark.unit
class TestJsonLoggerFormat:
    """Test JSON format and field presence."""

    def test_log_creates_valid_json(self, tmp_path):
        """Test that log entries are valid JSON."""
        logger = JsonLogger(component="test", agent_id="TEST01", log_root=tmp_path)

        logger.info("Test message")

        with logger.log_file.open("r") as f:
            line = f.readline()

        # Should parse without error
        data = json.loads(line)
        assert isinstance(data, dict)

    def test_mandatory_fields_present(self, tmp_path):
        """Test that all mandatory fields are present."""
        logger = JsonLogger(component="test", agent_id="TEST01", log_root=tmp_path)

        logger.info("Test message")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        # Mandatory fields
        assert "timestamp" in data
        assert "level" in data
        assert "agent_id" in data
        assert "component" in data
        assert "message" in data

        assert data["agent_id"] == "TEST01"
        assert data["component"] == "test"
        assert data["message"] == "Test message"
        assert data["level"] == "INFO"

    def test_timestamp_format(self, tmp_path):
        """Test ISO 8601 UTC timestamp format."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.info("Test message")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        # Should be ISO 8601 format ending with Z
        assert data["timestamp"].endswith("Z")
        assert "T" in data["timestamp"]

    def test_optional_fields_included_when_provided(self, tmp_path):
        """Test that optional fields are included when provided."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.log(
            "INFO",
            "Test message",
            event_type="TEST_EVENT",
            message_type="GAME_INVITATION",
            conversation_id="R1M1",
        )

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "TEST_EVENT"
        assert data["message_type"] == "GAME_INVITATION"
        assert data["conversation_id"] == "R1M1"

    def test_extra_fields_included(self, tmp_path):
        """Test that extra kwargs are included in log."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.info("Test message", custom_field="custom_value", match_id="R1M1", player_count=4)

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["custom_field"] == "custom_value"
        assert data["match_id"] == "R1M1"
        assert data["player_count"] == 4


@pytest.mark.unit
class TestJsonLoggerConvenienceMethods:
    """Test convenience methods."""

    def test_debug_method(self, tmp_path):
        """Test debug() convenience method."""
        logger = JsonLogger(component="test", min_level="DEBUG", log_root=tmp_path)

        logger.debug("Debug message", event_type="DEBUG_EVENT")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["level"] == "DEBUG"
        assert data["message"] == "Debug message"
        assert data["event_type"] == "DEBUG_EVENT"

    def test_info_method(self, tmp_path):
        """Test info() convenience method."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.info("Info message", event_type="INFO_EVENT")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["level"] == "INFO"
        assert data["message"] == "Info message"

    def test_warning_method(self, tmp_path):
        """Test warning() convenience method."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.warning("Warning message", event_type="WARNING_EVENT")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["level"] == "WARNING"
        assert data["message"] == "Warning message"

    def test_error_method(self, tmp_path):
        """Test error() convenience method."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.error("Error message", event_type="ERROR_EVENT")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["level"] == "ERROR"
        assert data["message"] == "Error message"


@pytest.mark.unit
class TestJsonLoggerMessageLogging:
    """Test message logging helper methods."""

    def test_log_message_sent(self, tmp_path):
        """Test log_message_sent() method."""
        logger = JsonLogger(
            component="player:P01", agent_id="P01", min_level="DEBUG", log_root=tmp_path
        )

        logger.log_message_sent("GAME_INVITATION", "P02", conversation_id="R1M1")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "MESSAGE_SENT"
        assert data["message_type"] == "GAME_INVITATION"
        assert data["recipient"] == "P02"
        assert data["conversation_id"] == "R1M1"

    def test_log_message_received(self, tmp_path):
        """Test log_message_received() method."""
        logger = JsonLogger(
            component="player:P01", agent_id="P01", min_level="DEBUG", log_root=tmp_path
        )

        logger.log_message_received("CHOOSE_PARITY_CALL", "REF01", conversation_id="R1M1")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "MESSAGE_RECEIVED"
        assert data["message_type"] == "CHOOSE_PARITY_CALL"
        assert data["sender"] == "REF01"
        assert data["conversation_id"] == "R1M1"

    def test_log_error_event(self, tmp_path):
        """Test log_error_event() method."""
        logger = JsonLogger(component="referee:REF01", agent_id="REF01", log_root=tmp_path)

        logger.log_error_event("E001", "Timeout error", player_id="P01", match_id="R1M1")

        with logger.log_file.open("r") as f:
            data = json.loads(f.readline())

        assert data["level"] == "ERROR"
        assert data["event_type"] == "ERROR_OCCURRED"
        assert data["error_code"] == "E001"
        assert "E001" in data["message"]
        assert "Timeout error" in data["message"]


@pytest.mark.unit
class TestLegacyLoggerAPI:
    """Test legacy setup_logger() and helper functions."""

    def test_setup_logger_creates_rotating_handler(self, tmp_path):
        """Test that setup_logger creates logger with JSONFormatter."""
        log_file = tmp_path / "test.log.jsonl"

        logger = setup_logger("test_component", log_file)

        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_legacy_log_message_sent(self, tmp_path):
        """Test log_message_sent() helper function."""
        log_file = tmp_path / "test.log.jsonl"
        logger = setup_logger("test", log_file)

        message = {"message_type": "GAME_INVITATION", "sender": "REF01", "conversation_id": "R1M1"}

        log_message_sent(logger, message)

        with open(log_file, "r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "MESSAGE_SENT"
        assert data["message_type"] == "GAME_INVITATION"

    def test_legacy_log_message_received(self, tmp_path):
        """Test log_message_received() helper function."""
        log_file = tmp_path / "test.log.jsonl"
        logger = setup_logger("test", log_file)

        message = {"message_type": "CHOOSE_PARITY_CALL", "sender": "REF01", "conversation_id": "R1M1"}

        log_message_received(logger, message)

        with open(log_file, "r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "MESSAGE_RECEIVED"
        assert data["message_type"] == "CHOOSE_PARITY_CALL"

    def test_legacy_log_error(self, tmp_path):
        """Test log_error() helper function."""
        log_file = tmp_path / "test.log.jsonl"
        logger = setup_logger("test", log_file)

        log_error(logger, "E001", {"message": "Timeout occurred", "player_id": "P01"})

        with open(log_file, "r") as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "ERROR_OCCURRED"
        assert data["error_code"] == "E001"
        assert "E001" in data["message"]
        assert "Timeout occurred" in data["message"]

    def test_jsonformatter_outputs_valid_json(self, tmp_path):
        """Test that JSONFormatter produces valid JSON."""
        log_file = tmp_path / "test.log.jsonl"
        logger = setup_logger("test", log_file)

        logger.info("Test message", extra={"custom_field": "value"})

        with open(log_file, "r") as f:
            data = json.loads(f.readline())

        assert "timestamp" in data
        assert "component" in data
        assert "level" in data
        assert "message" in data
        assert data["custom_field"] == "value"


@pytest.mark.unit
class TestAppendOnlyBehavior:
    """Test append-only log behavior."""

    def test_multiple_logs_append(self, tmp_path):
        """Test that multiple log calls append to file."""
        logger = JsonLogger(component="test", log_root=tmp_path)

        logger.info("Message 1")
        logger.info("Message 2")
        logger.info("Message 3")

        with logger.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 3
        assert "Message 1" in lines[0]
        assert "Message 2" in lines[1]
        assert "Message 3" in lines[2]

    def test_multiple_logger_instances_append(self, tmp_path):
        """Test that multiple logger instances append to same file."""
        logger1 = JsonLogger(component="test", agent_id="P01", log_root=tmp_path)
        logger2 = JsonLogger(component="test", agent_id="P01", log_root=tmp_path)

        logger1.info("From logger 1")
        logger2.info("From logger 2")

        with logger1.log_file.open("r") as f:
            lines = f.readlines()

        assert len(lines) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
