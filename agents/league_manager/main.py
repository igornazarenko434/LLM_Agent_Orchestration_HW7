"""
League Manager entry point (Missions 7.9-7.12).
"""

import argparse
import asyncio
import signal
import sys
from pathlib import Path

# Add SHARED to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "SHARED"))

from league_sdk.config_loader import load_agents_config, load_system_config  # noqa: E402

from agents.league_manager.server import LeagueManager  # noqa: E402


def _default_league_id() -> str | None:
    leagues_path = Path("SHARED/config/leagues")
    if not leagues_path.exists():
        return None
    league_files = sorted(p.stem for p in leagues_path.glob("*.json"))
    if len(league_files) == 1:
        return league_files[0]
    return None


def parse_args():
    """Parse command-line arguments."""
    system_config = load_system_config("SHARED/config/system.json")
    agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
    lm_config = agents_config.get("league_manager", {})
    default_league_id = _default_league_id()

    parser = argparse.ArgumentParser(description="League Manager for Even/Odd League")
    parser.add_argument(
        "--league-id",
        type=str,
        default=default_league_id,
        required=default_league_id is None,
        help="League ID (default: from config)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=system_config.network.host,
        help="Host to bind to (default: from config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=lm_config.get("port", system_config.network.league_manager_port),
        help="Port to bind to (default: from config)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=system_config.logging.get("level", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="League Manager 1.0.0",
    )
    return parser.parse_args()


async def main():
    """Main entry point for League Manager."""
    args = parse_args()

    # Create League Manager
    lm = LeagueManager(
        agent_id="LM01",
        league_id=args.league_id,
        host=args.host,
        port=args.port,
    )

    # Setup graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        print(f"\nReceived signal {sig}, shutting down gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start HTTP server in background thread
        await lm.start(run_in_thread=True)
        print(f"League Manager started on {args.host}:{lm.port}")
        print(f"League: {args.league_id}")
        print("Ready to accept registrations (REFEREE_REGISTER_REQUEST, LEAGUE_REGISTER_REQUEST)")
        print("Press Ctrl+C to stop the League Manager")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    finally:
        # Stop server
        lm.stop()
        print("League Manager stopped")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
