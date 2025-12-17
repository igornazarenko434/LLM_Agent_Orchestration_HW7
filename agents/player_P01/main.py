"""
Entry point for Player Agent P01.

Starts the MCP server on the configured host/port.
"""

from __future__ import annotations

import os

from agents.player_P01.server import PlayerAgent


def main() -> None:
    agent_id = os.getenv("AGENT_ID", "P01")
    league_id = os.getenv("LEAGUE_ID")
    host = os.getenv("BASE_HOST")
    port_env = os.getenv("PLAYER_PORT")
    port = int(port_env) if port_env else None

    agent = PlayerAgent(agent_id=agent_id, league_id=league_id, host=host, port=port)
    agent.start(run_in_thread=False)


if __name__ == "__main__":
    main()
