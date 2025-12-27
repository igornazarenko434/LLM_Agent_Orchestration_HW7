import re

import pytest
from agents.base.agent_base import BaseAgent


@pytest.mark.unit
def test_base_agent_defaults():
    agent = BaseAgent(agent_id="TEST", agent_type="player", host="127.0.0.1", port=5555)
    assert agent.sender == "player:TEST"
    assert agent.host == "127.0.0.1"
    assert agent.port == 5555


@pytest.mark.unit
def test_base_agent_timestamp_and_conversation_id():
    agent = BaseAgent(agent_id="TEST", agent_type="player")
    ts = agent._utc_timestamp()
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts)
    conv_id = agent._conversation_id()
    assert conv_id.startswith("conv-")
