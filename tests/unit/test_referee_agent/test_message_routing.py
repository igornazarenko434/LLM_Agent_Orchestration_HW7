import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents.referee_REF01.server import RefereeAgent
from fastapi import Request

from league_sdk.protocol import JSONRPCRequest


@pytest.fixture
def referee():
    return RefereeAgent(agent_id="REF01", league_id="test_league")


@pytest.mark.asyncio
async def test_route_player_response_success(referee):
    """Test that a player response is routed to the correct queue."""
    conversation_id = "conv-123"
    queue = asyncio.Queue()
    referee.message_queues[conversation_id] = queue

    # Create a dummy request
    request_data = {
        "jsonrpc": "2.0",
        "method": "GAME_JOIN_ACK",
        "params": {
            "conversation_id": conversation_id,
            "match_id": "match-1",
            "sender": "player:P01",
            "auth_token": "tok-player",
            "protocol": "league.v2",
        },
        "id": 1,
    }
    rpc_request = JSONRPCRequest(**request_data)

    # Route the response
    response = await referee._route_player_response(rpc_request)

    # Verify response status
    assert response.status_code == 200

    # Verify message was put in queue
    assert not queue.empty()
    queued_msg = await queue.get()
    assert queued_msg == rpc_request


@pytest.mark.asyncio
async def test_route_player_response_unknown_conversation(referee):
    """Test that a response with unknown conversation_id returns 404."""
    conversation_id = "unknown-conv"

    request_data = {
        "jsonrpc": "2.0",
        "method": "GAME_JOIN_ACK",
        "params": {
            "conversation_id": conversation_id,
            "match_id": "match-1",
            "sender": "player:P01",
            "auth_token": "tok-player",
            "protocol": "league.v2",
        },
        "id": 1,
    }
    rpc_request = JSONRPCRequest(**request_data)

    response = await referee._route_player_response(rpc_request)

    assert response.status_code == 404
    body = response.body.decode()
    assert "Match not active or conversation unknown" in body


@pytest.mark.asyncio
async def test_start_match_creates_queue(referee):
    """Test that START_MATCH creates a message queue for the conversation."""

    # Mock MatchConductor
    mock_conductor = AsyncMock()
    referee.match_conductor = mock_conductor
    referee.state = "REGISTERED"  # Simulate registered state

    conversation_id = "conv-start-match"
    request_data = {
        "jsonrpc": "2.0",
        "method": "START_MATCH",
        "params": {
            "match_id": "M1",
            "round_id": 1,
            "player_a_id": "P01",
            "player_b_id": "P02",
            "conversation_id": conversation_id,
            "sender": "league_manager:LM01",
            "protocol": "league.v2",
        },
        "id": 1,
    }
    rpc_request = JSONRPCRequest(**request_data)

    await referee._handle_start_match(rpc_request)

    # Verify queue was created
    assert conversation_id in referee.message_queues
    assert isinstance(referee.message_queues[conversation_id], asyncio.Queue)
    assert conversation_id in referee.active_matches

    # Clean up task
    referee.active_matches[conversation_id].cancel()
    try:
        await referee.active_matches[conversation_id]
    except asyncio.CancelledError:
        pass
