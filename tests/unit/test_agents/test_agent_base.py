import types

import pytest

from agents.base.agent_base import BaseAgent
from league_sdk.config_models import SystemConfig


class DummyServer:
    def __init__(self, config=None):
        self.config = config
        self.should_exit = False
        self.run_called = False

    def run(self):
        self.run_called = True


def test_base_agent_loads_config_defaults():
    agent = BaseAgent(agent_id="P01", agent_type="player")
    assert isinstance(agent.config, SystemConfig)
    assert agent.host == agent.config.network.host
    assert agent.port == agent.config.network.player_port_start
    assert agent.app is not None
    assert agent.logger is not None


def test_start_and_stop(monkeypatch):
    created = {}

    def fake_config(app, host, port, log_level, timeout_keep_alive):
        created["config"] = {
            "app": app,
            "host": host,
            "port": port,
            "log_level": log_level,
            "timeout_keep_alive": timeout_keep_alive,
        }
        return types.SimpleNamespace()

    dummy_server = DummyServer()

    def fake_server(config):
        created["server_cfg"] = config
        dummy_server.config = config
        return dummy_server

    monkeypatch.setattr("agents.base.agent_base.uvicorn.Config", fake_config)
    monkeypatch.setattr("agents.base.agent_base.uvicorn.Server", fake_server)

    agent = BaseAgent(agent_id="P01", agent_type="player", port=8105)
    agent.start(run_in_thread=False)

    assert dummy_server.run_called is True
    assert created["config"]["host"] == agent.host
    assert created["config"]["port"] == agent.port

    agent.stop()
    assert dummy_server.should_exit is True


@pytest.mark.asyncio
async def test_register_invokes_call_with_retry(monkeypatch):
    captured = {}

    async def fake_call(endpoint, method, params, timeout, logger, circuit_breaker=None):
        captured.update(
            {
                "endpoint": endpoint,
                "method": method,
                "params": params,
                "timeout": timeout,
                "logger": logger,
                "circuit_breaker": circuit_breaker,
            }
        )
        return {"ok": True}

    monkeypatch.setattr("agents.base.agent_base.call_with_retry", fake_call)

    agent = BaseAgent(agent_id="P01", agent_type="player", port=8101)
    meta = {
        "display_name": "Agent Alpha",
        "version": "1.0.0",
        "game_types": ["even_odd"],
        "contact_endpoint": "http://localhost:8101/mcp",
    }
    response = await agent.register(metadata=meta)

    assert response == {"ok": True}
    assert captured["method"] == "LEAGUE_REGISTER_REQUEST"
    assert captured["params"]["message_type"] == "LEAGUE_REGISTER_REQUEST"
    assert captured["params"]["sender"] == "player:P01"
    assert "conversation_id" in captured["params"]
    assert captured["endpoint"].endswith(":8000/mcp")
    assert captured["timeout"] == agent.config.network.request_timeout_sec
