"""
Entry point for Player Agent P01.

Starts the MCP server on the configured host/port with enhanced CLI argument support.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import sys
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


def parse_args():
    """
    Parse command-line arguments for Player P01.

    Priority Order:
        1. CLI arguments (highest priority)
        2. Environment variables
        3. Config file values
        4. Hardcoded defaults (lowest priority)
    """
    # Load configs for defaults
    try:
        system_config = load_system_config("SHARED/config/system.json")
        agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
    except Exception:
        # If configs fail to load, use minimal defaults for help text
        system_config = None
        agents_config = {"players": []}

    default_league_id = _default_league_id()

    player_record = next(
        (p for p in agents_config.get("players", []) if p.get("agent_id") == "P01"),
        {},
    )

    parser = argparse.ArgumentParser(
        prog="player_P01",
        description="Player Agent P01 for Even/Odd League Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with defaults from config
  python -m agents.player_P01.main

  # Override player ID and port
  python -m agents.player_P01.main --player-id P05 --port 8105

  # Enable debug logging
  python -m agents.player_P01.main --log-level DEBUG

  # Plain output for screen readers (no emojis)
  python -m agents.player_P01.main --plain

  # Verbose mode for troubleshooting
  python -m agents.player_P01.main --verbose

  # JSON output for automation/CI
  python -m agents.player_P01.main --json

Environment Variables:
  AGENT_ID        Override player ID (CLI takes precedence)
  LEAGUE_ID       Override league ID
  BASE_HOST       Override bind host
  PLAYER_PORT     Override bind port
  LOG_LEVEL       Override log level (DEBUG|INFO|WARNING|ERROR)

Exit Codes:
  0   Success - agent running
  1   Configuration error (E002, E008, E011)
  2   Network error (E016, E018)
  3   Registration error (E004, E012, E017)
  4   Runtime error (E015)

Error Codes:
  E001-E018 - See doc/error_codes_reference.md
  Retryable: E001, E005, E006, E009, E014, E015, E016
  Non-retryable: E002, E003, E004, E007, E008, E010, E011, E012, E013, E017, E018

Documentation:
  README: README.md
  API Reference: doc/api_reference.md
  Troubleshooting: doc/troubleshooting.md
  Error Codes: doc/error_codes_reference.md (to be created in Phase 1.5)
  System Integration: doc/system_integration_verification_plan.md
        """,
    )

    # Required arguments (with fallbacks)
    default_host = system_config.network.host if system_config else "0.0.0.0"
    default_port = (
        player_record.get("port", system_config.network.player_port_start if system_config else 8101)
        if player_record
        else 8101
    )
    default_log_level = system_config.logging.get("level", "INFO") if system_config else "INFO"

    parser.add_argument(
        "--player-id",
        type=str,
        default=os.getenv("AGENT_ID") or player_record.get("agent_id", "P01"),
        metavar="ID",
        help="Player ID (default: P01 from config or env AGENT_ID)",
    )

    parser.add_argument(
        "--league-id",
        type=str,
        default=os.getenv("LEAGUE_ID") or default_league_id,
        required=default_league_id is None and not os.getenv("LEAGUE_ID"),
        metavar="ID",
        help="League ID (default: auto-detected from SHARED/config/leagues/)",
    )

    # Network arguments
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("BASE_HOST") or default_host,
        metavar="HOST",
        help=f"Host to bind to (default: {default_host} from config or env BASE_HOST)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PLAYER_PORT", default_port)),
        metavar="PORT",
        help=f"Port to bind to (default: {default_port} from config or env PLAYER_PORT)",
    )

    # Logging arguments
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL") or default_log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        metavar="LEVEL",
        help=f"Log level (default: {default_log_level} from config or env LOG_LEVEL)",
    )

    # Output control arguments (NEW - Phase 1.5)
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output (show all registration attempts, debug details)",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Minimal output (errors only, for CI/CD pipelines)",
    )

    parser.add_argument(
        "--plain",
        action="store_true",
        help="Plain text output (no emojis, for screen readers and accessibility)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output status as JSON (for automation and programmatic parsing)",
    )

    # Config override (NEW - Phase 1.5)
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to custom config directory (default: SHARED/config)",
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="Player Agent P01 1.0.0 (league.v2 protocol)",
    )

    args = parser.parse_args()

    # Validation
    if args.verbose and args.quiet:
        parser.error("--verbose and --quiet are mutually exclusive")

    if args.json and (args.verbose or args.plain):
        parser.error("--json cannot be combined with --verbose or --plain")

    if not (1024 <= args.port <= 65535):
        parser.error(f"Port must be between 1024-65535, got: {args.port}")

    return args


def format_output(msg: str, plain: bool = False, msg_type: str = "info") -> str:
    """Format output based on plain mode setting."""
    if plain:
        prefixes = {
            "info": "[INFO]",
            "success": "[SUCCESS]",
            "warning": "[WARNING]",
            "error": "[ERROR]",
        }
        return f"{prefixes.get(msg_type, '[INFO]')} {msg}"
    else:
        emojis = {
            "info": "ℹ️ ",
            "success": "✅",
            "warning": "⚠️ ",
            "error": "❌",
        }
        return f"{emojis.get(msg_type, 'ℹ️ ')} {msg}"


async def deregister_on_shutdown(agent, plain: bool = False) -> None:
    """
    Gracefully de-register from League Manager on shutdown (P1 fix).

    Ensures League Manager knows agent is unavailable.
    """
    if agent.state in ("REGISTERED", "ACTIVE"):
        try:
            print(
                format_output(f"De-registering {agent.agent_id} from League Manager...", plain, "info")
            )
            result = await asyncio.wait_for(agent.send_deregistration_request(), timeout=5.0)
            if result.get("status") != "FAILED":
                print(format_output(f"De-registered {agent.agent_id}", plain, "success"))
            else:
                print(
                    format_output(f"De-registration failed: {result.get('reason')}", plain, "warning")
                )
        except asyncio.TimeoutError:
            print(
                format_output(
                    "De-registration timeout (League Manager not responding)", plain, "warning"
                )
            )
        except Exception as e:
            print(format_output(f"De-registration error: {e}", plain, "warning"))


async def register_with_retry_background(
    agent, player_record, defaults, plain: bool = False, verbose: bool = False, quiet: bool = False
) -> None:
    """
    Background task for non-blocking registration with retry (P0 fix).

    Attempts registration without blocking agent startup. Agent remains
    operational even if registration fails.
    """
    if not _auto_register_enabled(player_record, defaults):
        if not quiet:
            print(format_output(f"Auto-registration disabled for {agent.agent_id}", plain, "info"))
            print("   Use manual_register MCP tool to register when ready")
        return

    if not quiet:
        print(format_output(f"Starting registration for {agent.agent_id}...", plain, "info"))

    try:
        result = await agent.register_with_retry()

        if result.get("status") == "ACCEPTED":
            if not quiet:
                print(format_output(f"Successfully registered as {agent.agent_id}", plain, "success"))
                if verbose:
                    print(f"   Correlation ID: {result.get('correlation_id')}")
                    print(f"   Attempts: {result.get('attempts', 1)}")
        elif result.get("status") == "ALREADY_REGISTERED":
            if verbose and not quiet:
                print(format_output(f"{agent.agent_id} already registered (skipping)", plain, "info"))
        else:
            if not quiet:
                print(
                    format_output(
                        f"Registration failed after {result.get('attempts')} attempts",
                        plain,
                        "warning",
                    )
                )
                print(f"   Reason: {result.get('reason')}")
                if verbose:
                    print(f"   Correlation ID: {result.get('correlation_id')}")
                print("   Agent is running but UNREGISTERED")
                print("   Use manual_register MCP tool to retry when League Manager is ready")

    except Exception as e:
        print(format_output(f"Registration error: {e}", plain, "error"))
        if not quiet:
            print("   Agent is running but UNREGISTERED")
            print("   Use manual_register MCP tool to retry")


async def main() -> None:
    """Main entry point with enhanced CLI support."""
    args = parse_args()

    # Set up logging level based on args
    if args.verbose:
        log_level = "DEBUG"
    elif args.quiet:
        log_level = "ERROR"
    else:
        log_level = args.log_level

    # Load configs (with custom config path if provided)
    config_base = args.config if args.config else "SHARED/config"

    try:
        system_config = load_system_config(f"{config_base}/system.json")
        agents_config = load_agents_config(f"{config_base}/agents/agents_config.json")
        defaults = load_json_file(f"{config_base}/defaults/player.json")
    except Exception as e:
        print(format_output(f"Failed to load configuration: {e}", args.plain, "error"), file=sys.stderr)
        print("", file=sys.stderr)
        print("Suggested actions:", file=sys.stderr)
        print(f"  1. Check if config directory exists: ls -ld {config_base}", file=sys.stderr)
        print(
            f"  2. Validate JSON files: python3 -m json.tool {config_base}/system.json", file=sys.stderr
        )
        print("  3. See doc/error_codes_reference.md#e002-invalid_message_format", file=sys.stderr)
        sys.exit(1)

    player_record: dict = next(
        (p for p in agents_config.get("players", []) if p.get("agent_id") == args.player_id),
        {},
    )

    # Use args values (CLI takes priority over everything)
    agent_id = args.player_id
    league_id = args.league_id
    host = args.host
    port = args.port

    if not agent_id:
        print(format_output("Missing agent_id", args.plain, "error"), file=sys.stderr)
        print("", file=sys.stderr)
        print("Suggested actions:", file=sys.stderr)
        print("  1. Provide --player-id argument", file=sys.stderr)
        print("  2. Set AGENT_ID environment variable", file=sys.stderr)
        print("  3. Configure player in SHARED/config/agents/agents_config.json", file=sys.stderr)
        sys.exit(1)

    if not league_id:
        print(format_output("Missing league_id", args.plain, "error"), file=sys.stderr)
        print("", file=sys.stderr)
        print("Suggested actions:", file=sys.stderr)
        print("  1. Provide --league-id argument", file=sys.stderr)
        print("  2. Set LEAGUE_ID environment variable", file=sys.stderr)
        print("  3. Add league config to SHARED/config/leagues/", file=sys.stderr)
        sys.exit(1)

    # Create agent
    agent = PlayerAgent(agent_id=agent_id, league_id=league_id, host=host, port=port)

    # Start agent
    agent.start(run_in_thread=True)

    # Setup graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        if not args.quiet:
            print(f"\nReceived signal {sig}, shutting down gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # P0 FIX: Non-blocking registration in background task
    registration_task = asyncio.create_task(
        register_with_retry_background(
            agent, player_record, defaults, args.plain, args.verbose, args.quiet
        )
    )

    # Output based on mode
    if args.json:
        output = {
            "status": "running",
            "agent_id": agent_id,
            "league_id": league_id,
            "host": host,
            "port": port,
            "endpoints": {
                "health": f"http://{host}:{port}/health",
                "mcp": f"http://{host}:{port}/mcp",
            },
        }
        print(json.dumps(output))
    elif not args.quiet:
        if args.plain:
            print(f"[INFO] Player {agent_id} running on {host}:{port}")
            print(f"[INFO] Health endpoint: http://{host}:{port}/health")
            print(f"[INFO] MCP endpoint: http://{host}:{port}/mcp")
            print("[INFO] Press Ctrl+C to stop")
        else:
            print(f"🎮 Player {agent_id} running on {host}:{port}")
            print(f"   Health: http://{host}:{port}/health")
            print(f"   MCP: http://{host}:{port}/mcp")
            print("Press Ctrl+C to stop")

    await shutdown_event.wait()

    # P1 FIX: De-register on shutdown
    await deregister_on_shutdown(agent, args.plain)

    # Wait for registration task to complete (if still running)
    if not registration_task.done():
        registration_task.cancel()
        try:
            await registration_task
        except asyncio.CancelledError:
            pass

    agent.stop()
    if not args.quiet:
        print(format_output(f"Player {agent_id} stopped", args.plain, "success"))


if __name__ == "__main__":
    asyncio.run(main())
