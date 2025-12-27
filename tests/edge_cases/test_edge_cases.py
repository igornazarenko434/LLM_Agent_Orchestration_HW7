import asyncio
import logging

import pytest
from fastapi.testclient import TestClient
from league_sdk.protocol import GameJoinAck, JSONRPCRequest, MessageEnvelope
from league_sdk.utils import generate_conversation_id, generate_timestamp
from pydantic import ValidationError

from agents.player_P01.server import PlayerAgent
from agents.referee_REF01.game_logic import EvenOddGameLogic
from agents.referee_REF01.match_conductor import MatchConductor
from agents.referee_REF01.timeout_enforcement import TimeoutEnforcer


@pytest.mark.edge
def test_protocol_mismatch_rejected():
    with pytest.raises((ValueError, ValidationError)):
        MessageEnvelope(
            protocol="league.v1",
            message_type="LEAGUE_REGISTER_REQUEST",
            sender="player:P01",
            timestamp=generate_timestamp(),
            conversation_id=generate_conversation_id(),
        )


@pytest.mark.edge
def test_missing_auth_token_rejected():
    agent = PlayerAgent(agent_id="P99")
    client = TestClient(agent.app)

    payload = {
        "jsonrpc": "2.0",
        "method": "GAME_INVITATION",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "2025-01-01T00:00:00Z",
            "conversation_id": "conv-edge-auth",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "role_in_match": "PLAYER_A",
            "opponent_id": "P02",
        },
        "id": 1,
    }

    resp = client.post("/mcp", json=payload)
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["data"]["error_code"] == "E012"


@pytest.mark.edge
def test_invalid_parity_choice_rejected():
    logic = EvenOddGameLogic()
    assert logic.validate_choice("blue") is False


@pytest.mark.edge
def test_invalid_parity_number_raises():
    logic = EvenOddGameLogic()
    invalid_number = logic.max_number + 1
    with pytest.raises(ValueError):
        logic.check_parity(invalid_number)


@pytest.mark.edge
@pytest.mark.asyncio
async def test_timeout_enforcer_returns_none_after_retries(monkeypatch):
    logger = logging.getLogger("test-timeout")
    enforcer = TimeoutEnforcer(
        referee_id="REF01",
        auth_token="tok-ref",
        std_logger=logger,
        timeout_join_ack=0.01,
        timeout_parity_choice=0.01,
        max_retries=0,
        initial_delay=0.01,
        max_delay=0.01,
        game_error_timeout=0.01,
    )

    send_calls = []

    async def fake_send_game_error(**kwargs):
        send_calls.append(kwargs)

    monkeypatch.setattr(enforcer, "_send_game_error", fake_send_game_error)

    async def slow_response():
        await asyncio.sleep(0.05)
        return {"message_type": "GAME_JOIN_ACK"}

    result = await enforcer.wait_for_join_ack(
        player_id="P01",
        match_id="R1M1",
        conversation_id="conv-timeout",
        response_getter=slow_response,
        player_endpoint="http://localhost:9999/mcp",
    )

    assert result is None
    assert len(send_calls) == 0


@pytest.mark.edge
@pytest.mark.asyncio
async def test_conversation_id_mismatch_ignored(monkeypatch):
    logger = logging.getLogger("test-conversation")
    conductor = MatchConductor(
        referee_id="REF01",
        auth_token="tok-ref",
        league_id="league_2025_even_odd",
        std_logger=logger,
    )

    async def passthrough_wait(_player_id, _match_id, _conv_id, response_getter, _endpoint):
        return await response_getter()

    monkeypatch.setattr(conductor.timeout_enforcer, "wait_for_join_ack", passthrough_wait)

    message_queue: asyncio.Queue = asyncio.Queue()
    conversation_id = "conv-ok"

    def _ack(sender: str, conv_id: str) -> JSONRPCRequest:
        params = GameJoinAck(
            sender=sender,
            timestamp=generate_timestamp(),
            conversation_id=conv_id,
            auth_token="tok-ref",
            match_id="R1M1",
            player_id=sender.split(":")[1],
            arrival_timestamp=generate_timestamp(),
            accept=True,
        ).model_dump()
        return JSONRPCRequest(jsonrpc="2.0", method="GAME_JOIN_ACK", params=params, id="ack")

    await message_queue.put(_ack("player:P01", "conv-wrong"))
    await message_queue.put(_ack("player:P01", conversation_id))
    await message_queue.put(_ack("player:P02", conversation_id))

    results = await conductor._wait_for_join_acks(
        match_id="R1M1",
        player_a_id="P01",
        player_b_id="P02",
        conversation_id=conversation_id,
        transcript=[],
        message_queue=message_queue,
    )

    assert results["P01"].conversation_id == conversation_id
    assert results["P02"].conversation_id == conversation_id
