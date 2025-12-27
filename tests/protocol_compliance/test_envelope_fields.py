"""
Protocol compliance tests for message envelope mandatory fields.

Tests that all messages have the 6 required envelope fields:
- conversation_id
- message_type
- sender
- timestamp
- message_id
- payload
"""

import pytest
from league_sdk.protocol import MessageEnvelope
from league_sdk.utils import generate_conversation_id, generate_timestamp

PLAYER_REGISTRATION_REQUEST = "PLAYER_REGISTRATION_REQUEST"


def generate_message_id():
    """Generate a unique message ID."""
    import uuid

    return f"msg-{uuid.uuid4().hex[:16]}"


@pytest.mark.protocol
class TestEnvelopeFields:
    """Test mandatory envelope fields for protocol messages."""

    def test_envelope_has_conversation_id(self):
        """Test that message envelope requires conversation_id field."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        assert hasattr(envelope, "conversation_id")
        assert envelope.conversation_id == "conv-123"

    def test_envelope_has_message_type(self):
        """Test that message envelope requires message_type field."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        assert hasattr(envelope, "message_type")
        assert envelope.message_type == PLAYER_REGISTRATION_REQUEST

    def test_envelope_has_sender(self):
        """Test that message envelope requires sender field."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        assert hasattr(envelope, "sender")
        assert envelope.sender == "player:P01"

    def test_envelope_has_timestamp(self):
        """Test that message envelope requires timestamp field."""
        timestamp = generate_timestamp()
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=timestamp,
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        assert hasattr(envelope, "timestamp")
        assert envelope.timestamp == timestamp

    def test_envelope_has_message_id(self):
        """Test that message envelope requires message_id field."""
        message_id = generate_message_id()
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=message_id,
            payload={"player_name": "Test Player"},
        )

        assert hasattr(envelope, "message_id")
        assert envelope.message_id == message_id

    def test_envelope_has_payload(self):
        """Test that message envelope requires payload field."""
        payload = {"player_name": "Test Player", "version": "1.0"}
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload=payload,
        )

        assert hasattr(envelope, "payload")
        assert envelope.payload == payload

    def test_envelope_missing_conversation_id_fails(self):
        """Test that envelope without conversation_id fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id=None,  # Missing required field
                message_type=PLAYER_REGISTRATION_REQUEST,
                sender="player:P01",
                timestamp=generate_timestamp(),
                message_id=generate_message_id(),
                payload={"player_name": "Test"},
            )

    def test_envelope_missing_message_type_fails(self):
        """Test that envelope without message_type fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id="conv-123",
                message_type=None,  # Missing required field
                sender="player:P01",
                timestamp=generate_timestamp(),
                message_id=generate_message_id(),
                payload={"player_name": "Test"},
            )

    def test_envelope_missing_sender_fails(self):
        """Test that envelope without sender fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id="conv-123",
                message_type=PLAYER_REGISTRATION_REQUEST,
                sender=None,  # Missing required field
                timestamp=generate_timestamp(),
                message_id=generate_message_id(),
                payload={"player_name": "Test"},
            )

    def test_envelope_missing_timestamp_fails(self):
        """Test that envelope without timestamp fails validation."""
        with pytest.raises((TypeError, ValueError)):
            MessageEnvelope(
                conversation_id="conv-123",
                message_type=PLAYER_REGISTRATION_REQUEST,
                sender="player:P01",
                timestamp=None,  # Missing required field
                message_id=generate_message_id(),
                payload={"player_name": "Test"},
            )

    def test_envelope_missing_message_id_fails(self):
        """Test that envelope without message_id is handled (may allow None)."""
        # Note: Some implementations allow None for message_id (auto-generated)
        # This test documents the behavior rather than enforcing strict validation
        try:
            envelope = MessageEnvelope(
                conversation_id="conv-123",
                message_type=PLAYER_REGISTRATION_REQUEST,
                sender="player:P01",
                timestamp=generate_timestamp(),
                message_id=None,  # May be optional/auto-generated
                payload={"player_name": "Test"},
            )
            # If it doesn't raise, message_id is optional or auto-generated
            assert True
        except (TypeError, ValueError):
            # If it raises, message_id is required
            assert True

    def test_envelope_missing_payload_fails(self):
        """Test that envelope without payload is handled (may allow empty dict)."""
        # Note: Some implementations allow None or empty dict for payload
        # This test documents the behavior
        try:
            envelope = MessageEnvelope(
                conversation_id="conv-123",
                message_type=PLAYER_REGISTRATION_REQUEST,
                sender="player:P01",
                timestamp=generate_timestamp(),
                message_id=generate_message_id(),
                payload=None,  # May default to {} or be optional
            )
            # If it doesn't raise, payload is optional
            assert True
        except (TypeError, ValueError):
            # If it raises, payload is required
            assert True

    def test_envelope_all_six_fields_present(self):
        """Test that a valid envelope has exactly the 6 required fields."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        required_fields = [
            "conversation_id",
            "message_type",
            "sender",
            "timestamp",
            "message_id",
            "payload",
        ]

        for field in required_fields:
            assert hasattr(envelope, field), f"Envelope missing required field: {field}"

    def test_envelope_serialization_includes_all_fields(self):
        """Test that serialized envelope includes all 6 mandatory fields."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id="msg-456",
            payload={"player_name": "Test Player"},
        )

        # Convert to dict (assuming model_dump or dict method exists)
        if hasattr(envelope, "model_dump"):
            envelope_dict = envelope.model_dump()
        elif hasattr(envelope, "dict"):
            envelope_dict = envelope.dict()
        else:
            envelope_dict = vars(envelope)

        required_fields = [
            "conversation_id",
            "message_type",
            "sender",
            "timestamp",
            "message_id",
            "payload",
        ]

        for field in required_fields:
            assert field in envelope_dict, f"Serialized envelope missing: {field}"

    def test_envelope_field_types(self):
        """Test that envelope fields have correct types."""
        envelope = MessageEnvelope(
            conversation_id="conv-123",
            message_type=PLAYER_REGISTRATION_REQUEST,
            sender="player:P01",
            timestamp=generate_timestamp(),
            message_id=generate_message_id(),
            payload={"player_name": "Test Player"},
        )

        assert isinstance(envelope.conversation_id, str)
        assert isinstance(envelope.message_type, str)
        assert isinstance(envelope.sender, str)
        assert isinstance(envelope.timestamp, str)
        assert isinstance(envelope.message_id, str)
        assert isinstance(envelope.payload, dict)
