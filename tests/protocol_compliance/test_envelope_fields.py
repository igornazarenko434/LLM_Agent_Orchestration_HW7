"""
Protocol compliance tests for message envelope mandatory fields.

Tests that all messages have the required envelope fields:
- protocol
- message_type
- sender
- timestamp
- conversation_id
"""

import pytest
from league_sdk.protocol import MessageEnvelope
from league_sdk.utils import generate_conversation_id, generate_timestamp

LEAGUE_REGISTER_REQUEST = "LEAGUE_REGISTER_REQUEST"


@pytest.mark.protocol
class TestEnvelopeFields:
    """Test mandatory envelope fields for protocol messages."""

    def test_envelope_has_conversation_id(self):
        """Test that message envelope requires conversation_id field."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        assert hasattr(envelope, "conversation_id")
        assert envelope.conversation_id.startswith("conv-")

    def test_envelope_has_message_type(self):
        """Test that message envelope requires message_type field."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        assert hasattr(envelope, "message_type")
        assert envelope.message_type == LEAGUE_REGISTER_REQUEST

    def test_envelope_has_sender(self):
        """Test that message envelope requires sender field."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        assert hasattr(envelope, "sender")
        assert envelope.sender == "player:P01"

    def test_envelope_has_timestamp(self):
        """Test that message envelope requires timestamp field."""
        timestamp = generate_timestamp()
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=timestamp,
        )

        assert hasattr(envelope, "timestamp")
        assert envelope.timestamp == timestamp

    def test_envelope_has_protocol(self):
        """Test that message envelope requires protocol field."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        assert hasattr(envelope, "protocol")
        assert envelope.protocol == "league.v2"

    def test_envelope_missing_conversation_id_fails(self):
        """Test that envelope without conversation_id fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=None,  # Missing required field
                message_type=LEAGUE_REGISTER_REQUEST,
                sender="player:P01",
                timestamp=generate_timestamp(),
            )

    def test_envelope_missing_message_type_fails(self):
        """Test that envelope without message_type fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=generate_conversation_id(),
                message_type=None,  # Missing required field
                sender="player:P01",
                timestamp=generate_timestamp(),
            )

    def test_envelope_missing_sender_fails(self):
        """Test that envelope without sender fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=generate_conversation_id(),
                message_type=LEAGUE_REGISTER_REQUEST,
                sender=None,  # Missing required field
                timestamp=generate_timestamp(),
            )

    def test_envelope_missing_timestamp_fails(self):
        """Test that envelope without timestamp fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=generate_conversation_id(),
                message_type=LEAGUE_REGISTER_REQUEST,
                sender="player:P01",
                timestamp=None,  # Missing required field
            )

    def test_envelope_all_required_fields_present(self):
        """Test that a valid envelope has all required fields."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        required_fields = ["protocol", "conversation_id", "message_type", "sender", "timestamp"]

        for field in required_fields:
            assert hasattr(envelope, field), f"Envelope missing required field: {field}"

    def test_envelope_serialization_includes_all_fields(self):
        """Test that serialized envelope includes all mandatory fields."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        # Convert to dict (assuming model_dump or dict method exists)
        if hasattr(envelope, "model_dump"):
            envelope_dict = envelope.model_dump()
        elif hasattr(envelope, "dict"):
            envelope_dict = envelope.dict()
        else:
            envelope_dict = vars(envelope)

        required_fields = ["protocol", "conversation_id", "message_type", "sender", "timestamp"]

        for field in required_fields:
            assert field in envelope_dict, f"Serialized envelope missing: {field}"

    def test_envelope_field_types(self):
        """Test that envelope fields have correct types."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
        )

        assert isinstance(envelope.conversation_id, str)
        assert isinstance(envelope.message_type, str)
        assert isinstance(envelope.sender, str)
        assert isinstance(envelope.timestamp, str)
        assert isinstance(envelope.protocol, str)

    def test_envelope_optional_context_fields(self):
        """Test that optional context fields are allowed."""
        envelope = MessageEnvelope(
            conversation_id=generate_conversation_id(),
            message_type=LEAGUE_REGISTER_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            auth_token="tok-123",
            league_id="league_2025_even_odd",
            round_id=1,
            match_id="R1M1",
        )

        assert envelope.auth_token == "tok-123"
        assert envelope.league_id == "league_2025_even_odd"
        assert envelope.round_id == 1
        assert envelope.match_id == "R1M1"
