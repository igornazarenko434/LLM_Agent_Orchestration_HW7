"""
Referee agent entry point (Mission 7.5-7.8).

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

from agents.referee_REF01.server import RefereeAgent  # noqa: E402
from league_sdk.config_loader import (  # noqa: E402
    load_agents_config,
    load_json_file,
    load_system_config,
)


def _default_league_id() -> str | None:
    leagues_path = Path("SHARED/config/leagues")
    if not leagues_path.exists():
        return None
    league_files = sorted(p.stem for p in leagues_path.glob("*.json"))
    if len(league_files) == 1:
        return league_files[0]
    return None


def _default_referee_id(agents_config: dict, preferred_id: str) -> str | None:
    referees = agents_config.get("referees", [])
    for ref in referees:
        if ref.get("agent_id") == preferred_id:
            return ref.get("agent_id")
    if len(referees) == 1:
        return referees[0].get("agent_id")
    return None


def _auto_register_enabled(referee_record: dict, defaults: dict) -> bool:
    record_meta = referee_record.get("metadata", {}) if referee_record else {}
    default_meta = defaults.get("metadata", {})
    return bool(record_meta.get("auto_register", default_meta.get("auto_register", False)))


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
    Parse command-line arguments for Referee REF01.

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
    default_league_id = _default_league_id()
    default_referee_id = _default_referee_id(agents_config, "REF01")
    default_ref_record = next(
        (r for r in agents_config.get("referees", []) if r.get("agent_id") == default_referee_id),
        {},
    )

    parser = argparse.ArgumentParser(
        prog="referee_REF01",
        description="Referee Agent REF01 for Even/Odd League Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show help
  python -m agents.referee_REF01.main --help

  # Start with custom referee ID and port
  python -m agents.referee_REF01.main --referee-id REF05 --port 8005

  # Start in screen reader mode (accessibility)
  python -m agents.referee_REF01.main --plain

  # Start with verbose logging
  python -m agents.referee_REF01.main --verbose --log-level DEBUG

  # Start with custom league
  python -m agents.referee_REF01.main --league-id league_2025_custom

Environment Variables:
  REFEREE_ID       Override default referee ID
  LEAGUE_ID        Override default league ID
  REFEREE_PORT     Override default port
  LOG_LEVEL        Override default log level

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
  - SHARED/config/defaults/referee.json
""",
    )

    # Core arguments
    parser.add_argument(
        "--referee-id",
        type=str,
        default=os.getenv("REFEREE_ID", default_referee_id),
        required=default_referee_id is None and "REFEREE_ID" not in os.environ,
        help="Referee ID (default: %(default)s, env: REFEREE_ID)",
    )
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
                "REFEREE_PORT",
                default_ref_record.get("port", system_config.network.referee_port_start),
            )
        ),
        help="Port to bind to (default: %(default)s, env: REFEREE_PORT)",
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
        version="Referee Agent REF01 1.0.0 (league.v2 protocol)",
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
            f"  Suggested fix: Use --port <valid_port> (e.g., --port 8001)"
        )

    return args


async def deregister_on_shutdown(referee) -> None:
    """
    Gracefully de-register from League Manager on shutdown (P1 fix).

    Ensures League Manager knows referee is unavailable.
    """
    if referee.state in ("REGISTERED", "ACTIVE"):
        try:
            print(f"De-registering {referee.referee_id or referee.agent_id} from League Manager...")
            result = await asyncio.wait_for(referee.send_deregistration_request(), timeout=5.0)
            if result.get("status") != "FAILED":
                print(f"✅ De-registered {referee.referee_id or referee.agent_id}")
            else:
                print(f"⚠️  De-registration failed: {result.get('reason')}")
        except asyncio.TimeoutError:
            print("⚠️  De-registration timeout (League Manager not responding)")
        except Exception as e:
            print(f"⚠️  De-registration error: {e}")


async def register_with_retry_background(referee, referee_record, defaults) -> None:
    """
    Background task for non-blocking registration with retry (P0 fix).

    Attempts registration without blocking referee startup. Referee remains
    operational even if registration fails.
    """
    if not _auto_register_enabled(referee_record, defaults):
        print(f"ℹ️  Auto-registration disabled for {referee.agent_id}")
        print("   Use manual_register MCP tool to register when ready")
        return

    print(f"Starting registration for {referee.agent_id}...")

    try:
        result = await referee.register_with_retry()

        if result.get("status") == "ACCEPTED":
            print(f"✅ Successfully registered as {referee.referee_id}")
            print(f"   Correlation ID: {result.get('correlation_id')}")
            print(f"   Attempts: {result.get('attempts', 1)}")
            print(f"   Ready to conduct matches for league: {referee.league_id}")
        elif result.get("status") == "ALREADY_REGISTERED":
            print(f"ℹ️  {referee.agent_id} already registered (skipping)")
        else:
            print(f"⚠️  Registration failed after {result.get('attempts')} attempts")
            print(f"   Reason: {result.get('reason')}")
            print(f"   Correlation ID: {result.get('correlation_id')}")
            print("   Referee is running but UNREGISTERED")
            print("   Use manual_register MCP tool to retry when League Manager is ready")

    except Exception as e:
        print(f"❌ Registration error: {e}")
        print("   Referee is running but UNREGISTERED")
        print("   Use manual_register MCP tool to retry")


async def main():
    """Run the referee agent entry point."""
    args = parse_args()
    defaults = load_json_file("SHARED/config/defaults/referee.json")
    agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
    referee_record = next(
        (r for r in agents_config.get("referees", []) if r.get("agent_id") == args.referee_id),
        {},
    )

    # Create referee agent
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

        # P0 FIX: Non-blocking registration in background task
        # Referee starts immediately and remains operational even if registration fails
        registration_task = asyncio.create_task(
            register_with_retry_background(referee, referee_record, defaults)
        )

        print(f"Health endpoint: http://{args.host}:{referee.port}/health")
        print(f"MCP endpoint: http://{args.host}:{referee.port}/mcp")
        print("Press Ctrl+C to stop the referee agent")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    finally:
        # P1 FIX: De-register on shutdown
        await deregister_on_shutdown(referee)

        # Wait for registration task to complete (if still running)
        if "registration_task" in locals() and not registration_task.done():
            registration_task.cancel()
            try:
                await registration_task
            except asyncio.CancelledError:
                pass

        # Stop server
        referee.stop()
        print(f"Referee {args.referee_id} stopped")


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
