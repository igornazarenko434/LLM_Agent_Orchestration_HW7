"""
Entry point for Player Agent P03.

Starts the MCP server on the configured host/port.
"""

from __future__ import annotations

import asyncio
import os
import signal
from pathlib import Path

from league_sdk.config_loader import load_agents_config, load_json_file, load_system_config

from agents.player_P01.server import PlayerAgent


def _default_league_id() -> str | None:
    leagues_path = Path("SHARED/config/leagues")
    if not leagues_path.exists():
        return None
    league_files = sorted(p.stem for p in leagues_path.glob("*.json"))
    if len(league_files) == 1:
        return league_files[0]
    return None


def _auto_register_enabled(player_record: dict, defaults: dict) -> bool:
    record_meta = player_record.get("metadata", {}) if player_record else {}
    default_meta = defaults.get("metadata", {})
    return bool(record_meta.get("auto_register", default_meta.get("auto_register", False)))


async def deregister_on_shutdown(agent) -> None:
    """
    Gracefully de-register from League Manager on shutdown (P1 fix).

    Ensures League Manager knows agent is unavailable.
    """
    if agent.state in ("REGISTERED", "ACTIVE"):
        try:
            print(f"De-registering {agent.agent_id} from League Manager...")
            result = await asyncio.wait_for(agent.send_deregistration_request(), timeout=5.0)
            if result.get("status") != "FAILED":
                print(f"✅ De-registered {agent.agent_id}")
            else:
                print(f"⚠️  De-registration failed: {result.get('reason')}")
        except asyncio.TimeoutError:
            print("⚠️  De-registration timeout (League Manager not responding)")
        except Exception as e:
            print(f"⚠️  De-registration error: {e}")


async def register_with_retry_background(agent, player_record, defaults) -> None:
    """
    Background task for non-blocking registration with retry (P0 fix).

    Attempts registration without blocking agent startup. Agent remains
    operational even if registration fails.
    """
    if not _auto_register_enabled(player_record, defaults):
        print(f"ℹ️  Auto-registration disabled for {agent.agent_id}")
        print("   Use manual_register MCP tool to register when ready")
        return

    print(f"Starting registration for {agent.agent_id}...")

    try:
        result = await agent.register_with_retry()

        if result.get("status") == "ACCEPTED":
            print(f"✅ Successfully registered as {agent.agent_id}")
            print(f"   Correlation ID: {result.get('correlation_id')}")
            print(f"   Attempts: {result.get('attempts', 1)}")
        elif result.get("status") == "ALREADY_REGISTERED":
            print(f"ℹ️  {agent.agent_id} already registered (skipping)")
        else:
            print(f"⚠️  Registration failed after {result.get('attempts')} attempts")
            print(f"   Reason: {result.get('reason')}")
            print(f"   Correlation ID: {result.get('correlation_id')}")
            print("   Agent is running but UNREGISTERED")
            print("   Use manual_register MCP tool to retry when League Manager is ready")

    except Exception as e:
        print(f"❌ Registration error: {e}")
        print("   Agent is running but UNREGISTERED")
        print("   Use manual_register MCP tool to retry")


async def main() -> None:
    system_config = load_system_config("SHARED/config/system.json")
    agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
    defaults = load_json_file("SHARED/config/defaults/player.json")

    player_record: dict = next(
        (p for p in agents_config.get("players", []) if p.get("agent_id") == "P03"),
        {},
    )

    default_league_id = _default_league_id()

    agent_id = os.getenv("AGENT_ID") or player_record.get("agent_id")
    league_id = os.getenv("LEAGUE_ID") or default_league_id
    host = os.getenv("BASE_HOST") or system_config.network.host
    port_env = os.getenv("PLAYER_PORT")
    port = (
        int(port_env)
        if port_env
        else player_record.get("port", system_config.network.player_port_start)
    )

    if not agent_id:
        raise SystemExit(
            "Missing agent_id. Provide AGENT_ID or configure players in agents_config.json."
        )
    if not league_id:
        raise SystemExit("Missing league_id. Provide LEAGUE_ID or add a league config file.")

    agent = PlayerAgent(agent_id=agent_id, league_id=league_id, host=host, port=port)
    agent.start(run_in_thread=True)

    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # P0 FIX: Non-blocking registration in background task
    # Agent starts immediately and remains operational even if registration fails
    registration_task = asyncio.create_task(
        register_with_retry_background(agent, player_record, defaults)
    )

    print(f"Player {agent_id} running on {host}:{port}")
    print(f"Health endpoint: http://{host}:{port}/health")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    print("Press Ctrl+C to stop the player agent")

    await shutdown_event.wait()

    # P1 FIX: De-register on shutdown
    await deregister_on_shutdown(agent)

    # Wait for registration task to complete (if still running)
    if not registration_task.done():
        registration_task.cancel()
        try:
            await registration_task
        except asyncio.CancelledError:
            pass

    agent.stop()
    print(f"Player {agent_id} stopped")


if __name__ == "__main__":
    asyncio.run(main())
