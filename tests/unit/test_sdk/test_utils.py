import re

import pytest
from league_sdk import utils


@pytest.mark.unit
def test_generate_timestamp_format():
    ts = utils.generate_timestamp()
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", ts)


@pytest.mark.unit
def test_validate_timestamp():
    assert utils.validate_timestamp("2025-01-15T10:15:30Z") is True
    assert utils.validate_timestamp("2025-01-15 10:15:30") is False


@pytest.mark.unit
def test_parse_sender_valid():
    agent_type, agent_id = utils.parse_sender("player:P01")
    assert agent_type == "player"
    assert agent_id == "P01"


@pytest.mark.unit
def test_parse_sender_invalid():
    with pytest.raises(ValueError):
        utils.parse_sender("player:P_01")


@pytest.mark.unit
def test_generate_conversation_id_prefix():
    conv_id = utils.generate_conversation_id("match")
    assert conv_id.startswith("match-")
    assert len(conv_id.split("-")[-1]) == 6


@pytest.mark.unit
def test_generate_auth_token_length_and_min():
    token = utils.generate_auth_token(32)
    assert len(token) == 32
    with pytest.raises(ValueError):
        utils.generate_auth_token(16)
