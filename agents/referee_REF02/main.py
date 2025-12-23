"""
Referee REF02 agent entry point.

Usage:
    python agents/referee_REF02/main.py [--referee-id REF02] [--port 8002]

Note: This referee imports the generic RefereeAgent implementation from referee_REF01.
All core logic (game_logic, timeout_enforcement, match_conductor) is shared.
"""

import argparse
import asyncio
import signal
import sys
from pathlib import Path

# Add SHARED to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "SHARED"))

from agents.referee_REF01.server import RefereeAgent  # noqa: E402


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Referee REF02 Agent for Even/Odd League")
    parser.add_argument(
        "--referee-id",
        type=str,
        default="REF02",
        help="Referee ID (default: REF02)",
    )
    parser.add_argument(
        "--league-id",
        type=str,
        default="league_2025_even_odd",
        help="League ID (default: league_2025_even_odd)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind to (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to (default: from config)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Referee REF02 Agent 1.0.0",
    )
    return parser.parse_args()


async def main():
    """Main entry point for referee REF02 agent."""
    args = parse_args()

    # Create referee agent (uses generic RefereeAgent class)
    referee = RefereeAgent(
        agent_id=args.referee_id,
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
        referee.start(run_in_thread=True)
        print(f"Referee {args.referee_id} started on {args.host}:{referee.port}")

        # Register with League Manager
        print("Registering with League Manager...")
        success = await referee.register_with_league_manager()
        if success:
            print(f"✅ Successfully registered as {referee.referee_id}")
            print(f"Ready to conduct matches for league: {args.league_id}")
        else:
            print("❌ Registration failed - check League Manager is running")
            sys.exit(1)

        # Wait for shutdown signal
        print("Press Ctrl+C to stop the referee agent")
        await shutdown_event.wait()

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    finally:
        # Stop server
        referee.stop()
        print(f"Referee {args.referee_id} stopped")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
