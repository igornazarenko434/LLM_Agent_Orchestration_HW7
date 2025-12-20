#!/usr/bin/env python3
"""
Manual data retention cleanup script.

This script provides manual execution of data retention cleanup policies.
Use this for manual cleanup, testing, or when automated cleanup isn't available.

Usage:
    # Dry run (preview what would be deleted)
    python SHARED/scripts/cleanup_data.py --dry-run

    # Execute cleanup
    python SHARED/scripts/cleanup_data.py --execute

    # Cleanup specific data type
    python SHARED/scripts/cleanup_data.py --execute --type logs
    python SHARED/scripts/cleanup_data.py --execute --type matches

    # Custom retention period
    python SHARED/scripts/cleanup_data.py --execute --type logs --retention-days 60

    # Verbose output
    python SHARED/scripts/cleanup_data.py --execute --verbose

See: doc/data_retention_policy.md for full policy details
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from league_sdk.cleanup import (  # noqa: E402
    archive_old_matches,
    cleanup_old_logs,
    get_retention_config,
    prune_league_rounds,
    prune_player_histories,
    run_full_cleanup,
)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup console logging for the script."""
    logger = logging.getLogger("cleanup_script")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def print_banner():
    """Print script banner."""
    print("=" * 70)
    print("Data Retention Cleanup Script".center(70))
    print("Even/Odd League Multi-Agent System".center(70))
    print("=" * 70)
    print()


def print_config(config: dict):
    """Print current retention configuration."""
    print("Current Retention Configuration:")
    print("-" * 70)
    print(f"  Enabled: {config.get('enabled', False)}")
    print(f"  Logs Retention: {config.get('logs_retention_days', 30)} days")
    print(f"  Match Data Retention: {config.get('match_data_retention_days', 365)} days")
    print(f"  Player History Retention: {config.get('player_history_retention_days', 365)} days")
    print(f"  Rounds Retention: {config.get('rounds_retention_days', 365)} days")
    print(f"  Archive Enabled: {config.get('archive_enabled', True)}")
    print(f"  Archive Path: {config.get('archive_path', 'SHARED/archive/')}")
    print()


def print_stats(stats_dict: dict):
    """Print cleanup statistics."""
    print("\nCleanup Results:")
    print("=" * 70)

    total_deleted = 0
    total_archived = 0
    total_mb = 0.0

    for data_type, stats in stats_dict.items():
        if hasattr(stats, "to_dict"):
            stats_data = stats.to_dict()
        else:
            stats_data = stats

        print(f"\n{data_type.upper().replace('_', ' ')}:")
        print(f"  Files Scanned: {stats_data.get('files_scanned', 0)}")
        print(f"  Files Deleted: {stats_data.get('files_deleted', 0)}")
        print(f"  Files Archived: {stats_data.get('files_archived', 0)}")
        print(f"  Space Freed: {stats_data.get('mb_freed', 0):.2f} MB")

        if stats_data.get("errors_count", 0) > 0:
            print(f"  Errors: {stats_data.get('errors_count', 0)}")
            for error in stats_data.get("errors", [])[:5]:
                print(f"    - {error}")

        total_deleted += stats_data.get("files_deleted", 0)
        total_archived += stats_data.get("files_archived", 0)
        total_mb += stats_data.get("mb_freed", 0)

    print("\n" + "=" * 70)
    print("TOTALS:")
    print(f"  Total Files Deleted: {total_deleted}")
    print(f"  Total Files Archived: {total_archived}")
    print(f"  Total Space Freed: {total_mb:.2f} MB")
    print("=" * 70)


async def run_cleanup(args, logger):
    """Execute cleanup based on arguments."""
    config = get_retention_config()

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be deleted\n")
        # TODO: Implement dry-run mode (would need to modify cleanup functions)
        print("Note: Dry-run mode not fully implemented yet.")
        print("Run without --dry-run to execute cleanup.\n")
        return

    results = {}

    if args.type == "all" or args.type is None:
        # Run full cleanup
        logger.info("Running full cleanup (all data types)...")
        results = await run_full_cleanup(logger=logger)

    elif args.type == "logs":
        logger.info("Running log cleanup...")
        retention_days = args.retention_days or config.get("logs_retention_days", 30)
        results["logs"] = await cleanup_old_logs(retention_days=retention_days, logger=logger)

    elif args.type == "matches":
        logger.info("Running match data cleanup...")
        retention_days = args.retention_days or config.get("match_data_retention_days", 365)
        results["matches"] = await archive_old_matches(retention_days=retention_days, logger=logger)

    elif args.type == "player_history":
        logger.info("Running player history cleanup...")
        retention_days = args.retention_days or config.get("player_history_retention_days", 365)
        results["player_history"] = await prune_player_histories(
            retention_days=retention_days, logger=logger
        )

    elif args.type == "rounds":
        logger.info("Running rounds history cleanup...")
        retention_days = args.retention_days or config.get("rounds_retention_days", 365)
        results["rounds"] = await prune_league_rounds(retention_days=retention_days, logger=logger)

    return results


def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(
        description="Manual data retention cleanup script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview)
  python SHARED/scripts/cleanup_data.py --dry-run

  # Execute full cleanup
  python SHARED/scripts/cleanup_data.py --execute

  # Cleanup only logs
  python SHARED/scripts/cleanup_data.py --execute --type logs

  # Custom retention period for logs
  python SHARED/scripts/cleanup_data.py --execute --type logs --retention-days 60

  # Verbose output
  python SHARED/scripts/cleanup_data.py --execute --verbose
        """,
    )

    parser.add_argument(
        "--execute", action="store_true", help="Execute cleanup (without this, it's a dry run)"
    )

    parser.add_argument("--dry-run", action="store_true", help="Preview what would be deleted")

    parser.add_argument(
        "--type",
        choices=["all", "logs", "matches", "player_history", "rounds"],
        default="all",
        help="Type of data to clean up (default: all)",
    )

    parser.add_argument(
        "--retention-days",
        type=int,
        help="Custom retention period in days (overrides config)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output (show DEBUG logs)")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=args.verbose)

    # Print banner
    print_banner()

    # Load and print config
    config = get_retention_config()
    print_config(config)

    # Check if cleanup is enabled
    if not config.get("enabled", True):
        print("⚠️  WARNING: Data retention cleanup is DISABLED in system.json")
        print("Set 'data_retention.enabled' to true to enable cleanup.\n")
        sys.exit(1)

    # Validation
    if not args.execute and not args.dry_run:
        print("❌ ERROR: Must specify either --execute or --dry-run\n")
        parser.print_help()
        sys.exit(1)

    if args.execute and args.dry_run:
        print("❌ ERROR: Cannot specify both --execute and --dry-run\n")
        sys.exit(1)

    # Run cleanup
    try:
        start_time = datetime.now(timezone.utc)

        results = asyncio.run(run_cleanup(args, logger))

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Print results
        if results:
            print_stats(results)
            print(f"\nCleanup completed in {duration:.2f} seconds")
            print(f"Timestamp: {end_time.isoformat()}")
        else:
            print("\nNo cleanup performed (dry-run mode)")

    except KeyboardInterrupt:
        print("\n\n⚠️  Cleanup interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        print(f"\n❌ ERROR: Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
