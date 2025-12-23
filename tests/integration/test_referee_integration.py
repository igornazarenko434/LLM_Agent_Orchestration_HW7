"""
Integration tests for Referee agent (improve coverage before League Manager).

These tests exercise the match_conductor and server paths that aren't covered
by unit tests.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.referee_REF01.server import RefereeAgent


class TestRefereeIntegration:
    """Integration tests for referee agent."""

    @pytest.fixture
    def referee(self):
        """Create referee instance."""
        return RefereeAgent(agent_id="REF01")

    @pytest.mark.asyncio
    async def test_start_match_handler_without_registration(self, referee):
        """Test START_MATCH handler rejects when not registered."""
        from league_sdk.protocol import JSONRPCRequest

        # Build START_MATCH request
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="START_MATCH",
            params={
                "match_id": "M001",
                "round_id": 1,
                "player_a_id": "P01",
                "player_b_id": "P02",
                "conversation_id": "conv-001",
            },
            id=1,
        )

        # Call handler
        response = await referee._handle_start_match(request)

        # Should return error (not registered)
        assert response.status_code == 403
        content = response.body.decode()
        assert "not registered" in content.lower()

    @pytest.mark.asyncio
    async def test_registration_builds_correct_metadata(self, referee):
        """Test registration builds correct metadata from config."""
        # Mock the League Manager endpoint
        with patch("league_sdk.retry.call_with_retry") as mock_retry:
            # Mock successful registration response
            mock_retry.return_value = {
                "result": {
                    "status": "ACCEPTED",
                    "referee_id": "REF01",
                    "auth_token": "test_token_123",
                }
            }

            # Attempt registration
            success = await referee.register_with_league_manager()

            # Verify registration was called with correct metadata
            assert mock_retry.called
            call_args = mock_retry.call_args
            payload = call_args[0][1]  # Second argument is payload

            assert payload["method"] == "REFEREE_REGISTER_REQUEST"
            params = payload["params"]
            meta = params["referee_meta"]

            # Verify metadata from config
            assert meta["display_name"] == "Referee 01"
            assert meta["version"] == "1.0.0"
            assert "even_odd" in meta["game_types"]
            assert meta["max_concurrent_matches"] == 10
            assert meta["contact_endpoint"] == "http://localhost:8001/mcp"

    @pytest.mark.asyncio
    async def test_registration_success_initializes_match_conductor(self, referee):
        """Test successful registration initializes MatchConductor."""
        assert referee.match_conductor is None

        with patch("league_sdk.retry.call_with_retry") as mock_retry:
            mock_retry.return_value = {
                "result": {
                    "status": "ACCEPTED",
                    "referee_id": "REF01",
                    "auth_token": "test_token_123",
                }
            }

            success = await referee.register_with_league_manager()

            assert success is True
            assert referee.referee_id == "REF01"
            assert referee.auth_token == "test_token_123"
            assert referee.match_conductor is not None
            assert referee.state == "REGISTERED"

    @pytest.mark.asyncio
    async def test_registration_rejection_handled(self, referee):
        """Test registration rejection is handled gracefully."""
        with patch("league_sdk.retry.call_with_retry") as mock_retry:
            mock_retry.return_value = {
                "result": {"status": "REJECTED", "reason": "Invalid credentials"}
            }

            success = await referee.register_with_league_manager()

            assert success is False
            assert referee.match_conductor is None
            assert referee.state == "INIT"

    @pytest.mark.asyncio
    async def test_registration_error_handled(self, referee):
        """Test registration error is handled gracefully."""
        with patch("league_sdk.retry.call_with_retry") as mock_retry:
            mock_retry.return_value = {"error": {"code": -32000, "message": "Internal error"}}

            success = await referee.register_with_league_manager()

            assert success is False
            assert referee.match_conductor is None
