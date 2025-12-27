"""
League Manager entry point (Missions 7.9-7.12).

Enhanced with comprehensive CLI argument parsing, accessibility support,
and proper error handling (Mission M6.1 & M6.2).
"""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

# Add SHARED to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "SHARED"))

from agents.league_manager.server import LeagueManager  # noqa: E402

from league_sdk.config_loader import load_agents_config, load_system_config  # noqa: E402


def _default_league_id() -> str | None:
    leagues_path = Path("SHARED/config/leagues")
    if not leagues_path.exists():
        return None
    league_files = sorted(p.stem for p in leagues_path.glob("*.json"))
    if len(league_files) == 1:
        return league_files[0]
    return None


def format_output(message: str, mode: str = "normal") -> str:
    """
    Format output for different accessibility modes.

    Args:
        message: The message to format
        mode: Output mode - "normal", "plain", "json", "quiet"

    Returns:
        Formatted message string
    """
    if mode == "plain":
        # Remove emojis and special characters for screen readers
        import re

        return re.sub(r"[^\w\s\-:.,/()\[\]]", "", message)
    elif mode == "quiet":
        # Only show errors/warnings
        return ""
    return message


def parse_args():
    """
    Parse command-line arguments for League Manager.

    Priority Order:
        1. CLI arguments (highest priority)
        2. Environment variables
        3. Config file values
        4. Hardcoded defaults (lowest priority)

    Exit Codes (aligned with doc/reference/error_codes_reference.md):
        0 - Success
        1 - Configuration error
        2 - Network/connection error
        3 - Authentication error
        4 - Runtime error
    """
    system_config = load_system_config("SHARED/config/system.json")
    agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
    lm_config = agents_config.get("league_manager", {})
    default_league_id = _default_league_id()

    parser = argparse.ArgumentParser(
        prog="league_manager",
        description="League Manager for Even/Odd League Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show help
  python -m agents.league_manager.main --help

  # Start with custom league ID and port
  python -m agents.league_manager.main --league-id league_2025_custom --port 8000

  # Start in screen reader mode (accessibility)
  python -m agents.league_manager.main --plain

  # Start with verbose logging
  python -m agents.league_manager.main --verbose --log-level DEBUG

  # Start with custom host
  python -m agents.league_manager.main --host 0.0.0.0 --port 8000

Environment Variables:
  LEAGUE_ID          Override default league ID
  LM_PORT            Override default port
  LOG_LEVEL          Override default log level

Configuration Priority:
  CLI args > Environment variables > Config files > Defaults

Exit Codes:
  0 - Success
  1 - Configuration error (invalid arguments, missing config)
  2 - Network error (port unavailable, connection failed)
  3 - Authentication error (registration rejected)
  4 - Runtime error (unexpected failure)

For more information, see:
  - doc/reference/error_codes_reference.md
  - SHARED/config/agents/agents_config.json

Responsibilities:
  - Accept referee and player registrations
  - Maintain league standings and schedule
  - Coordinate match lifecycle
  - Provide centralized state management
""",
    )

    # Core arguments
    parser.add_argument(
        "--league-id",
        type=str,
        default=os.getenv("LEAGUE_ID", default_league_id),
        required=default_league_id is None and "LEAGUE_ID" not in os.environ,
        help="League ID (default: %(default)s, env: LEAGUE_ID)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=system_config.network.host,
        help="Host to bind to (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(
            os.getenv(
                "LM_PORT",
                lm_config.get("port", system_config.network.league_manager_port),
            )
        ),
        help="Port to bind to (default: %(default)s, env: LM_PORT)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", system_config.logging.get("level", "INFO")),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: %(default)s, env: LOG_LEVEL)",
    )

    # Output control
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (detailed logging and progress)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (only show errors)",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Plain text output (no emojis, WCAG 2.1 compliant for screen readers)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON output format (machine-readable)",
    )

    # Config file
    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom config file (overrides defaults)",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="League Manager 1.0.0 (league.v2 protocol)",
    )

    args = parser.parse_args()

    # Validate mutually exclusive flags
    if args.verbose and args.quiet:
        parser.error("--verbose and --quiet are mutually exclusive")
    if args.json and args.plain:
        parser.error("--json and --plain are mutually exclusive")

    # Validate port range
    if not (1024 <= args.port <= 65535):
        parser.error(
            f"Port must be between 1024-65535, got: {args.port}\n"
            f"  Suggested fix: Use --port <valid_port> (e.g., --port 8000)"
        )

    return args


async def main():
    """Run the League Manager entry point."""
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
