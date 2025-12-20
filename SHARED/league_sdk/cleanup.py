"""
Data retention and cleanup utilities for the Even/Odd League system.

This module provides functions to enforce data retention policies:
- cleanup_old_logs(): Delete logs older than retention period
- archive_old_matches(): Archive and delete old match data
- prune_player_histories(): Remove old matches from player history
- prune_league_rounds(): Remove old rounds from league history
- get_retention_config(): Load retention settings from system.json

All cleanup operations:
1. Archive data before deletion (if enabled)
2. Log all operations for audit trail
3. Handle errors gracefully (continue on failure)
4. Return statistics (files deleted, space freed, etc.)

Thread Safety:
- All functions are async (non-blocking)
- Safe for concurrent execution (no shared state)
- Use atomic file operations via repositories

See: doc/data_retention_policy.md for full policy details
"""

import asyncio
import gzip
import json
import logging
import shutil
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from league_sdk.repositories import (
    MatchRepository,
    PlayerHistoryRepository,
    RoundsRepository,
    StandingsRepository,
)

__all__ = [
    "cleanup_old_logs",
    "archive_old_matches",
    "prune_player_histories",
    "prune_league_rounds",
    "get_retention_config",
    "CleanupStats",
    "run_full_cleanup",
]


# ============================================================================
# CONFIGURATION
# ============================================================================


def get_retention_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load data retention configuration from system.json.

    Args:
        config_path: Path to system.json (default: SHARED/config/system.json)

    Returns:
        Dictionary with data_retention configuration

    Example:
        >>> config = get_retention_config()
        >>> config["logs_retention_days"]
        30
    """
    if config_path is None:
        config_path = Path("SHARED/config/system.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            system_config = json.load(f)
            return system_config.get("data_retention", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Return defaults if config not found
        logging.warning(f"Could not load retention config: {e}, using defaults")
        return {
            "enabled": True,
            "logs_retention_days": 30,
            "match_data_retention_days": 365,
            "player_history_retention_days": 365,
            "rounds_retention_days": 365,
            "archive_enabled": True,
            "archive_path": "SHARED/archive/",
        }


# ============================================================================
# CLEANUP STATISTICS
# ============================================================================


class CleanupStats:
    """Statistics from cleanup operations."""

    def __init__(self):
        self.files_scanned = 0
        self.files_deleted = 0
        self.files_archived = 0
        self.bytes_freed = 0
        self.errors = []

    def add_deleted(self, file_path: Path) -> None:
        """Record a deleted file."""
        try:
            size = file_path.stat().st_size if file_path.exists() else 0
            self.bytes_freed += size
            self.files_deleted += 1
        except Exception as e:
            self.errors.append(f"Could not get size of {file_path}: {e}")

    def add_archived(self, file_path: Path) -> None:
        """Record an archived file."""
        self.files_archived += 1

    def add_error(self, error: str) -> None:
        """Record an error."""
        self.errors.append(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "files_scanned": self.files_scanned,
            "files_deleted": self.files_deleted,
            "files_archived": self.files_archived,
            "bytes_freed": self.bytes_freed,
            "mb_freed": round(self.bytes_freed / (1024 * 1024), 2),
            "errors_count": len(self.errors),
            "errors": self.errors[:10],  # Limit to first 10 errors
        }


# ============================================================================
# LOG CLEANUP
# ============================================================================


async def cleanup_old_logs(
    retention_days: Optional[int] = None,
    log_dir: Optional[Path] = None,
    archive_enabled: Optional[bool] = None,
    logger: Optional[logging.Logger] = None,
) -> CleanupStats:
    """
    Clean up log files older than retention period.

    Deletes rotated log files (*.log.jsonl.1, *.log.jsonl.2, etc.) that are
    older than the retention period. Active log files (*.log.jsonl) are never deleted.

    Args:
        retention_days: Days to retain logs (default: from config or 30)
        log_dir: Root log directory (default: SHARED/logs)
        archive_enabled: Whether to archive before deleting (default: from config)
        logger: Optional logger for operation logs

    Returns:
        CleanupStats with files deleted, space freed, etc.

    Example:
        >>> stats = await cleanup_old_logs(retention_days=30)
        >>> print(f"Deleted {stats.files_deleted} files, freed {stats.mb_freed} MB")
    """
    config = get_retention_config()
    retention_days = retention_days or config.get("logs_retention_days", 30)
    log_dir = log_dir or Path("SHARED/logs")
    archive_enabled = archive_enabled or config.get("archive_enabled", True)
    archive_path = Path(config.get("archive_path", "SHARED/archive")) / "logs"

    if logger is None:
        logger = logging.getLogger(__name__)

    stats = CleanupStats()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info(
        f"Starting log cleanup: retention={retention_days} days, cutoff={cutoff_date.isoformat()}"
    )

    # Find all rotated log files
    rotated_logs: list[Path] = []
    for pattern in ["**/*.log.jsonl.*", "**/*.log.*"]:
        rotated_logs.extend(log_dir.rglob(pattern))

    stats.files_scanned = len(rotated_logs)

    for log_file in rotated_logs:
        try:
            # Check if file is a rotated log (not active .log.jsonl)
            # Active logs end with .log.jsonl
            # Rotated logs have numbers: .log.jsonl.1, .log.jsonl.2, etc.
            if log_file.name.endswith(".log.jsonl"):
                # Skip active log files
                continue

            # Check modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)

            if mtime < cutoff_date:
                # Archive before deletion
                if archive_enabled:
                    await _archive_log_file(log_file, archive_path, mtime, logger)
                    stats.add_archived(log_file)

                # Delete the file
                stats.add_deleted(log_file)
                log_file.unlink()

                logger.debug(
                    f"Deleted old log: {log_file}",
                    extra={"file_age_days": (datetime.now(timezone.utc) - mtime).days},
                )

        except Exception as e:
            error_msg = f"Failed to cleanup {log_file}: {e}"
            stats.add_error(error_msg)
            logger.error(error_msg, exc_info=True)

    logger.info("Log cleanup completed", extra=stats.to_dict())
    return stats


async def _archive_log_file(
    log_file: Path, archive_path: Path, mtime: datetime, logger: logging.Logger
) -> None:
    """Archive a log file by compressing and moving to archive directory."""
    # Create archive directory structure: archive/logs/YYYY/MM/
    year_month_dir = archive_path / str(mtime.year) / f"{mtime.month:02d}"
    year_month_dir.mkdir(parents=True, exist_ok=True)

    # Compress file
    archive_file = year_month_dir / f"{log_file.name}.gz"

    # Compress in a thread pool to avoid blocking
    await asyncio.to_thread(_compress_file, log_file, archive_file)

    logger.debug(f"Archived log to {archive_file}")


def _compress_file(source: Path, destination: Path) -> None:
    """Compress a file using gzip (blocking operation)."""
    with open(source, "rb") as f_in:
        with gzip.open(destination, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)


# ============================================================================
# MATCH DATA CLEANUP
# ============================================================================


async def archive_old_matches(
    retention_days: Optional[int] = None,
    archive_enabled: Optional[bool] = None,
    logger: Optional[logging.Logger] = None,
) -> CleanupStats:
    """
    Archive and delete completed matches older than retention period.

    Groups matches by league and year, creates compressed archives, then deletes
    the original match files.

    Args:
        retention_days: Days to retain match data (default: from config or 365)
        archive_enabled: Whether to archive before deleting (default: from config)
        logger: Optional logger for operation logs

    Returns:
        CleanupStats with files archived/deleted, space freed, etc.

    Example:
        >>> stats = await archive_old_matches(retention_days=365)
        >>> print(f"Archived {stats.files_archived} matches")
    """
    config = get_retention_config()
    retention_days = retention_days or config.get("match_data_retention_days", 365)
    archive_enabled = archive_enabled or config.get("archive_enabled", True)
    archive_path = Path(config.get("archive_path", "SHARED/archive")) / "matches"

    if logger is None:
        logger = logging.getLogger(__name__)

    stats = CleanupStats()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info(
        f"Starting match data cleanup: retention={retention_days} days, "
        f"cutoff={cutoff_date.isoformat()}"
    )

    # Load all matches
    match_repo = MatchRepository()
    match_ids = match_repo.list_matches()
    stats.files_scanned = len(match_ids)

    # Group old matches by league and year
    matches_to_archive: Dict[str, List[Dict[str, Any]]] = {}

    for match_id in match_ids:
        try:
            match_data = match_repo.load(match_id)
            if not match_data:
                continue

            # Only cleanup COMPLETED matches
            if match_data.get("status") != "COMPLETED":
                continue

            # Check age
            created_at_str = match_data.get("created_at")
            if not created_at_str:
                continue

            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

            if created_at < cutoff_date:
                # Group by league/year for archiving
                league_id = match_data.get("league_id", "unknown")
                year = created_at.year
                archive_key = f"{league_id}/{year}"

                if archive_key not in matches_to_archive:
                    matches_to_archive[archive_key] = []

                matches_to_archive[archive_key].append(
                    {
                        "match_id": match_id,
                        "match_data": match_data,
                        "file_path": match_repo.base_path / f"{match_id}.json",
                    }
                )

        except Exception as e:
            error_msg = f"Failed to process match {match_id}: {e}"
            stats.add_error(error_msg)
            logger.error(error_msg, exc_info=True)

    # Archive and delete
    for archive_key, matches in matches_to_archive.items():
        try:
            if archive_enabled:
                await _archive_matches_tarball(matches, archive_key, archive_path, logger)

            # Delete original files
            for match_info in matches:
                file_path = match_info["file_path"]
                stats.add_deleted(file_path)
                file_path.unlink()
                stats.add_archived(file_path)

        except Exception as e:
            error_msg = f"Failed to archive matches for {archive_key}: {e}"
            stats.add_error(error_msg)
            logger.error(error_msg, exc_info=True)

    logger.info("Match cleanup completed", extra=stats.to_dict())
    return stats


async def _archive_matches_tarball(
    matches: List[Dict[str, Any]], archive_key: str, archive_path: Path, logger: logging.Logger
) -> None:
    """Create a tar.gz archive of match files."""
    # Create archive directory
    league_id, year = archive_key.split("/")
    archive_dir = archive_path / league_id
    archive_dir.mkdir(parents=True, exist_ok=True)

    archive_file = archive_dir / f"{year}.tar.gz"

    # Create tarball in thread pool (blocking operation)
    await asyncio.to_thread(_create_tarball, matches, archive_file)

    logger.info(f"Created match archive: {archive_file} ({len(matches)} matches)")


def _create_tarball(matches: List[Dict[str, Any]], archive_file: Path) -> None:
    """Create a tar.gz archive (blocking operation)."""
    with tarfile.open(archive_file, "w:gz") as tar:
        for match_info in matches:
            file_path = match_info["file_path"]
            if file_path.exists():
                tar.add(file_path, arcname=file_path.name)


# ============================================================================
# PLAYER HISTORY CLEANUP
# ============================================================================


async def prune_player_histories(
    retention_days: Optional[int] = None,
    data_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> CleanupStats:
    """
    Remove old match records from player history files while preserving stats.

    Removes individual match records older than retention period from the
    "matches" array, but keeps aggregate statistics intact.

    Args:
        retention_days: Days to retain player history (default: from config or 365)
        data_dir: Root data directory (default: SHARED/data)
        logger: Optional logger for operation logs

    Returns:
        CleanupStats with players pruned, matches removed, etc.

    Example:
        >>> stats = await prune_player_histories(retention_days=365)
        >>> print(f"Pruned {stats.files_deleted} old match records")
    """
    config = get_retention_config()
    retention_days = retention_days or config.get("player_history_retention_days", 365)

    if logger is None:
        logger = logging.getLogger(__name__)

    stats = CleanupStats()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info(
        f"Starting player history cleanup: retention={retention_days} days, "
        f"cutoff={cutoff_date.isoformat()}"
    )

    # Find all player history files
    data_root = data_dir or Path("SHARED")
    player_data_dir = data_root / "data" / "players"
    if not player_data_dir.exists():
        return stats

    history_files = list(player_data_dir.rglob("history.json"))
    stats.files_scanned = len(history_files)

    for history_file in history_files:
        try:
            # Load history
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)

            matches = history_data.get("matches", [])
            original_count = len(matches)

            # Filter old matches
            recent_matches = []
            for match in matches:
                timestamp_str = match.get("timestamp")
                if not timestamp_str:
                    continue

                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp >= cutoff_date:
                    recent_matches.append(match)

            # Update history if matches were removed
            if len(recent_matches) < original_count:
                history_data["matches"] = recent_matches
                history_data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                # Write updated history (atomic) - Repository expects data_root to be SHARED/data
                PlayerHistoryRepository(history_data["player_id"], data_root=data_root / "data").save(
                    history_data
                )

                removed_count = original_count - len(recent_matches)
                stats.files_deleted += removed_count  # Count of match records removed

                logger.debug(
                    f"Pruned player history: {history_file.parent.name}",
                    extra={"matches_removed": removed_count, "matches_remaining": len(recent_matches)},
                )

        except Exception as e:
            error_msg = f"Failed to prune {history_file}: {e}"
            stats.add_error(error_msg)
            logger.error(error_msg, exc_info=True)

    logger.info("Player history cleanup completed", extra=stats.to_dict())
    return stats


# ============================================================================
# LEAGUE ROUNDS CLEANUP
# ============================================================================


async def prune_league_rounds(
    retention_days: Optional[int] = None,
    data_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> CleanupStats:
    """
    Remove old rounds from league rounds history files.

    Removes round records older than retention period from the "rounds" array.

    Args:
        retention_days: Days to retain rounds history (default: from config or 365)
        data_dir: Optional data directory (default: SHARED)
        logger: Optional logger for operation logs

    Returns:
        CleanupStats with leagues pruned, rounds removed, etc.

    Example:
        >>> stats = await prune_league_rounds(retention_days=365)
        >>> print(f"Pruned {stats.files_deleted} old rounds")
    """
    config = get_retention_config()
    retention_days = retention_days or config.get("rounds_retention_days", 365)

    if logger is None:
        logger = logging.getLogger(__name__)

    stats = CleanupStats()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info(
        f"Starting rounds cleanup: retention={retention_days} days, cutoff={cutoff_date.isoformat()}"
    )

    # Find all league rounds files
    data_root = data_dir or Path("SHARED")
    leagues_dir = data_root / "data" / "leagues"
    if not leagues_dir.exists():
        return stats

    rounds_files = list(leagues_dir.rglob("rounds.json"))
    stats.files_scanned = len(rounds_files)

    for rounds_file in rounds_files:
        try:
            # Load rounds
            with open(rounds_file, "r", encoding="utf-8") as f:
                rounds_data = json.load(f)

            rounds = rounds_data.get("rounds", [])
            original_count = len(rounds)

            # Filter old rounds
            recent_rounds = []
            for round_entry in rounds:
                created_at_str = round_entry.get("created_at")
                if not created_at_str:
                    continue

                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                if created_at >= cutoff_date:
                    recent_rounds.append(round_entry)

            # Update rounds if any were removed
            if len(recent_rounds) < original_count:
                rounds_data["rounds"] = recent_rounds
                rounds_data["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                # Add metadata about archived rounds
                if "archived_rounds" not in rounds_data:
                    rounds_data["archived_rounds"] = 0
                rounds_data["archived_rounds"] += original_count - len(recent_rounds)

                # Write updated rounds (atomic) - Repository expects data_root to be SHARED/data
                league_id = rounds_data.get("league_id", rounds_file.parent.name)
                RoundsRepository(league_id, data_root=data_root / "data").save(rounds_data)

                removed_count = original_count - len(recent_rounds)
                stats.files_deleted += removed_count  # Count of round records removed

                logger.debug(
                    f"Pruned league rounds: {league_id}",
                    extra={"rounds_removed": removed_count, "rounds_remaining": len(recent_rounds)},
                )

        except Exception as e:
            error_msg = f"Failed to prune {rounds_file}: {e}"
            stats.add_error(error_msg)
            logger.error(error_msg, exc_info=True)

    logger.info("Rounds cleanup completed", extra=stats.to_dict())
    return stats


# ============================================================================
# FULL CLEANUP
# ============================================================================


async def run_full_cleanup(logger: Optional[logging.Logger] = None) -> Dict[str, CleanupStats]:
    """
    Run complete data retention cleanup: logs → matches → history → rounds.

    This is the main entry point for automated cleanup (called by League Manager).

    Args:
        logger: Optional logger for operation logs

    Returns:
        Dictionary with cleanup stats for each data type

    Example:
        >>> results = await run_full_cleanup()
        >>> total_mb = sum(r.bytes_freed / (1024**2) for r in results.values())
        >>> print(f"Total space freed: {total_mb:.2f} MB")
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    config = get_retention_config()

    if not config.get("enabled", True):
        logger.info("Data retention cleanup is disabled in config")
        return {}

    logger.info("Starting full data retention cleanup")
    start_time = datetime.now(timezone.utc)

    results = {}

    try:
        # Run all cleanup operations in sequence
        results["logs"] = await cleanup_old_logs(logger=logger)
        results["matches"] = await archive_old_matches(logger=logger)
        results["player_history"] = await prune_player_histories(logger=logger)
        results["league_rounds"] = await prune_league_rounds(logger=logger)

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Calculate totals
        total_deleted = sum(r.files_deleted for r in results.values())
        total_archived = sum(r.files_archived for r in results.values())
        total_mb = sum(r.bytes_freed for r in results.values()) / (1024 * 1024)

        logger.info(
            "Full cleanup completed",
            extra={
                "duration_sec": duration,
                "total_files_deleted": total_deleted,
                "total_files_archived": total_archived,
                "total_mb_freed": round(total_mb, 2),
                "results": {k: v.to_dict() for k, v in results.items()},
            },
        )

    except Exception as e:
        logger.error(f"Full cleanup failed: {e}", exc_info=True)
        raise

    return results
