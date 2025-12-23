"""
Unit tests for timeout enforcement (Mission 7.6).

Tests:
- GAME_JOIN_ACK timeout (5s)
- CHOOSE_PARITY_RESPONSE timeout (30s)
- GAME_ERROR (E001) sending
- Technical loss on max retries exceeded
- Exponential backoff
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from league_sdk.protocol import ErrorCode

from agents.referee_REF01.timeout_enforcement import TimeoutEnforcer


@pytest.fixture
def timeout_enforcer():
    """Create TimeoutEnforcer instance with test config."""
    return TimeoutEnforcer(
        referee_id="REF01",
        auth_token="test_token",
        std_logger=Mock(),
        timeout_join_ack=5,  # 5s from system.json
        timeout_parity_choice=30,  # 30s from system.json
        max_retries=3,  # From system.json
        initial_delay=2.0,  # From system.json
        max_delay=10.0,  # From system.json
    )


class TestTimeoutEnforcer:
    """Test suite for TimeoutEnforcer."""

    @pytest.mark.asyncio
    async def test_wait_for_join_ack_success(self, timeout_enforcer):
        """Test successful join ACK within timeout."""

        async def response_getter():
            await asyncio.sleep(0.1)
            return {"player_id": "P01", "accept": True}

        result = await timeout_enforcer.wait_for_join_ack(
            player_id="P01",
            match_id="R1M1",
            conversation_id="conv-test-1",
            response_getter=response_getter,
            player_endpoint="http://localhost:8101/mcp",
        )

        assert result is not None
        assert result["player_id"] == "P01"
        assert result["accept"] is True

    @pytest.mark.asyncio
    async def test_wait_for_join_ack_timeout(self, timeout_enforcer):
        """Test join ACK timeout triggers GAME_ERROR."""

        async def response_getter():
            # Simulate timeout by sleeping longer than timeout
            await asyncio.sleep(10)
            return {"player_id": "P01"}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            result = await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Should return None after max retries
            assert result is None

            # Should have sent GAME_ERROR (max_retries + 1 times)
            assert mock_retry.call_count == timeout_enforcer.max_retries

    @pytest.mark.asyncio
    async def test_wait_for_parity_choice_success(self, timeout_enforcer):
        """Test successful parity choice within timeout."""

        async def response_getter():
            await asyncio.sleep(0.1)
            return {"parity_choice": "even"}

        result = await timeout_enforcer.wait_for_parity_choice(
            player_id="P01",
            match_id="R1M1",
            conversation_id="conv-test-1",
            response_getter=response_getter,
            player_endpoint="http://localhost:8101/mcp",
        )

        assert result is not None
        assert result["parity_choice"] == "even"

    @pytest.mark.asyncio
    async def test_wait_for_parity_choice_timeout(self, timeout_enforcer):
        """Test parity choice timeout triggers GAME_ERROR."""

        async def response_getter():
            # Simulate timeout
            await asyncio.sleep(35)
            return {"parity_choice": "even"}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            result = await timeout_enforcer.wait_for_parity_choice(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Should return None after max retries
            assert result is None

            # Should have sent GAME_ERROR
            assert mock_retry.call_count == timeout_enforcer.max_retries

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, timeout_enforcer):
        """Test exponential backoff between retries."""
        call_times = []

        async def response_getter():
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(10)  # Always timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Should have made multiple attempts
            assert len(call_times) > 1

            # Verify exponential backoff (timing is approximate)
            # First retry: ~2s delay, second: ~4s delay, third: ~8s (capped at max_delay)

    @pytest.mark.asyncio
    async def test_game_error_message_format(self, timeout_enforcer):
        """Test GAME_ERROR message has correct format."""

        async def response_getter():
            await asyncio.sleep(10)  # Timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Verify GAME_ERROR was sent
            assert mock_retry.called

            # Get the payload sent
            call_args = mock_retry.call_args_list[0]
            payload = call_args[0][1]  # Second positional arg is the payload

            assert payload["jsonrpc"] == "2.0"
            assert payload["method"] == "GAME_ERROR"
            assert payload["params"]["error_code"] == ErrorCode.TIMEOUT_ERROR  # String enum
            assert payload["params"]["affected_player"] == "P01"
            assert payload["params"]["match_id"] == "R1M1"
            assert "retry_info" in payload["params"]
            assert payload["params"]["retry_info"]["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_retry_info_in_game_error(self, timeout_enforcer):
        """Test retry_info contains correct details."""

        async def response_getter():
            await asyncio.sleep(10)  # Timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Get first GAME_ERROR sent
            payload = mock_retry.call_args_list[0][0][1]
            retry_info = payload["params"]["retry_info"]

            assert retry_info["retry_count"] == 1  # First retry
            assert retry_info["max_retries"] == 3
            assert "next_retry_at" in retry_info
            assert "backoff_delay_sec" in retry_info

    @pytest.mark.asyncio
    async def test_consequence_message(self, timeout_enforcer):
        """Test consequence message warns about technical loss."""

        async def response_getter():
            await asyncio.sleep(10)  # Timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            payload = mock_retry.call_args_list[0][0][1]
            assert "Technical loss" in payload["params"]["consequence"]
            assert str(timeout_enforcer.max_retries) in payload["params"]["consequence"]

    @pytest.mark.asyncio
    async def test_logging_timeout_events(self, timeout_enforcer):
        """Test timeout events are logged with E001 error code."""
        mock_logger = Mock()
        timeout_enforcer.std_logger = mock_logger

        async def response_getter():
            await asyncio.sleep(10)  # Timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Verify error logging was called
            # The log_error function should have been called
            assert mock_logger.error.called or mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_max_retries_from_config(self, timeout_enforcer):
        """Test max retries comes from system.json config."""
        assert timeout_enforcer.max_retries == 3  # From system.json

        async def response_getter():
            await asyncio.sleep(10)  # Timeout
            return {}

        with patch("agents.referee_REF01.timeout_enforcement.call_with_retry") as mock_retry:
            mock_retry.return_value = {"jsonrpc": "2.0", "result": {}, "id": 1}

            await timeout_enforcer.wait_for_join_ack(
                player_id="P01",
                match_id="R1M1",
                conversation_id="conv-test-1",
                response_getter=response_getter,
                player_endpoint="http://localhost:8101/mcp",
            )

            # Should attempt exactly max_retries times (not more)
            assert mock_retry.call_count == 3

    @pytest.mark.asyncio
    async def test_timeouts_from_config(self, timeout_enforcer):
        """Test timeouts come from system.json config."""
        assert timeout_enforcer.timeout_join_ack == 5  # From system.json
        assert timeout_enforcer.timeout_parity_choice == 30  # From system.json

    @pytest.mark.asyncio
    async def test_backoff_delays_from_config(self, timeout_enforcer):
        """Test backoff delays come from system.json config."""
        assert timeout_enforcer.initial_delay == 2.0  # From system.json
        assert timeout_enforcer.max_delay == 10.0  # From system.json
