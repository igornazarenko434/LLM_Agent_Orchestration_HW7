"""
Unit tests for data retention and cleanup utilities.

Tests the league_sdk.cleanup module functions:
- cleanup_old_logs(): Log file cleanup
- archive_old_matches(): Match data archival
- prune_player_histories(): Player history pruning
- prune_league_rounds(): Rounds history pruning
- get_retention_config(): Config loading
- run_full_cleanup(): Full cleanup orchestration

Coverage:
- Normal cleanup scenarios
- Edge cases (empty directories, missing files)
- Error handling (permissions, invalid data)
- Archive functionality
- Configuration loading
"""

import asyncio
import gzip
import json
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from league_sdk.cleanup import (
    CleanupStats,
    archive_old_matches,
    cleanup_old_logs,
    get_retention_config,
    prune_league_rounds,
    prune_player_histories,
    run_full_cleanup,
)
from league_sdk.repositories import MatchRepository, PlayerHistoryRepository, RoundsRepository

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory structure."""
    data_dir = tmp_path / "SHARED" / "data"
    logs_dir = tmp_path / "SHARED" / "logs"
    archive_dir = tmp_path / "SHARED" / "archive"

    # Create directories
    (data_dir / "matches").mkdir(parents=True)
    (data_dir / "players" / "P01").mkdir(parents=True)
    (data_dir / "leagues" / "test_league").mkdir(parents=True)
    (logs_dir / "agents").mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    return tmp_path / "SHARED"


@pytest.fixture
def mock_config():
    """Mock retention configuration."""
    return {
        "enabled": True,
        "logs_retention_days": 30,
        "match_data_retention_days": 365,
        "player_history_retention_days": 365,
        "rounds_retention_days": 365,
        "archive_enabled": True,
        "archive_path": "SHARED/archive/",
    }


@pytest.fixture
def sample_match_data():
    """Sample match data for testing."""
    return {
        "schema_version": "1.0.0",
        "match_id": "R1M1",
        "league_id": "test_league",
        "round_id": 1,
        "game_type": "even_odd",
        "players": {"player_a": "P01", "player_b": "P02"},
        "referee_id": "REF01",
        "status": "COMPLETED",
        "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}},
        "transcript": [],
        "created_at": "2024-01-15T10:00:00Z",
        "last_updated": "2024-01-15T10:05:00Z",
    }


# ============================================================================
# TEST: CleanupStats
# ============================================================================


def test_cleanup_stats_initialization():
    """Test CleanupStats initializes with zero values."""
    stats = CleanupStats()
    assert stats.files_scanned == 0
    assert stats.files_deleted == 0
    assert stats.files_archived == 0
    assert stats.bytes_freed == 0
    assert stats.errors == []


def test_cleanup_stats_add_deleted(tmp_path):
    """Test recording deleted files."""
    stats = CleanupStats()
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    stats.add_deleted(test_file)
    assert stats.files_deleted == 1
    assert stats.bytes_freed > 0


def test_cleanup_stats_to_dict():
    """Test converting stats to dictionary."""
    stats = CleanupStats()
    stats.files_scanned = 10
    stats.files_deleted = 5
    stats.files_archived = 3
    stats.bytes_freed = 1024 * 1024 * 50  # 50 MB
    stats.errors = ["Error 1", "Error 2"]

    result = stats.to_dict()
    assert result["files_scanned"] == 10
    assert result["files_deleted"] == 5
    assert result["files_archived"] == 3
    assert result["mb_freed"] == 50.0
    assert result["errors_count"] == 2


# ============================================================================
# TEST: Configuration Loading
# ============================================================================


def test_get_retention_config_loads_from_file(tmp_path):
    """Test loading retention config from system.json."""
    config_file = tmp_path / "system.json"
    config_data = {
        "data_retention": {
            "enabled": True,
            "logs_retention_days": 60,
            "match_data_retention_days": 730,
        }
    }
    config_file.write_text(json.dumps(config_data))

    config = get_retention_config(config_path=config_file)
    assert config["enabled"] is True
    assert config["logs_retention_days"] == 60
    assert config["match_data_retention_days"] == 730


def test_get_retention_config_returns_defaults_on_error(tmp_path):
    """Test default config returned when file doesn't exist."""
    config = get_retention_config(config_path=tmp_path / "nonexistent.json")

    assert config["enabled"] is True
    assert config["logs_retention_days"] == 30
    assert config["match_data_retention_days"] == 365


# ============================================================================
# TEST: Log Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup_old_logs_deletes_old_files(temp_data_dir):
    """Test cleanup deletes log files older than retention period."""
    logs_dir = temp_data_dir / "logs" / "agents"

    # Create old log file (60 days old)
    old_log = logs_dir / "P01.log.jsonl.1"
    old_log.write_text("old log content")
    old_time = datetime.now(timezone.utc) - timedelta(days=60)
    old_log.touch()
    import os

    os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))

    # Create recent log file (10 days old)
    recent_log = logs_dir / "P01.log.jsonl.2"
    recent_log.write_text("recent log content")

    # Run cleanup with 30-day retention
    stats = await cleanup_old_logs(
        retention_days=30, log_dir=temp_data_dir / "logs", archive_enabled=False
    )

    # Old file should be deleted, recent file should remain
    assert not old_log.exists()
    assert recent_log.exists()
    assert stats.files_deleted >= 1


@pytest.mark.asyncio
async def test_cleanup_old_logs_preserves_active_logs(temp_data_dir):
    """Test cleanup never deletes active log files (*.log.jsonl)."""
    logs_dir = temp_data_dir / "logs" / "agents"

    # Create active log file
    active_log = logs_dir / "P01.log.jsonl"
    active_log.write_text("active log content")

    # Make it old
    old_time = datetime.now(timezone.utc) - timedelta(days=365)
    import os

    os.utime(active_log, (old_time.timestamp(), old_time.timestamp()))

    # Run cleanup
    stats = await cleanup_old_logs(
        retention_days=30, log_dir=temp_data_dir / "logs", archive_enabled=False
    )

    # Active log should NOT be deleted
    assert active_log.exists()


@pytest.mark.asyncio
async def test_cleanup_old_logs_archives_before_delete(temp_data_dir):
    """Test cleanup archives files before deleting."""
    logs_dir = temp_data_dir / "logs" / "agents"
    archive_dir = temp_data_dir / "archive" / "logs"

    # Create old log file
    old_log = logs_dir / "P01.log.jsonl.1"
    old_log.write_text("log content to archive")
    old_time = datetime.now(timezone.utc) - timedelta(days=60)
    import os

    os.utime(old_log, (old_time.timestamp(), old_time.timestamp()))

    # Run cleanup with archiving enabled
    stats = await cleanup_old_logs(
        retention_days=30, log_dir=temp_data_dir / "logs", archive_enabled=True
    )

    # File should be deleted
    assert not old_log.exists()

    # Archive should exist
    assert stats.files_archived >= 1


# ============================================================================
# TEST: Match Data Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_archive_old_matches_deletes_old_completed_matches(temp_data_dir, sample_match_data):
    """Test cleanup archives and deletes old completed matches."""
    matches_dir = temp_data_dir / "data" / "matches"

    # Create old match (2 years old)
    old_match = matches_dir / "R1M1.json"
    sample_match_data["created_at"] = (datetime.now(timezone.utc) - timedelta(days=730)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    old_match.write_text(json.dumps(sample_match_data))

    # Patch repository to use temp directory
    with patch("league_sdk.cleanup.MatchRepository") as MockRepo:
        mock_repo = Mock()
        mock_repo.base_path = matches_dir
        mock_repo.list_matches.return_value = ["R1M1"]
        mock_repo.load.return_value = sample_match_data
        MockRepo.return_value = mock_repo

        stats = await archive_old_matches(retention_days=365, archive_enabled=False)

        assert stats.files_scanned >= 1


@pytest.mark.asyncio
async def test_archive_old_matches_preserves_in_progress_matches(temp_data_dir, sample_match_data):
    """Test cleanup does NOT delete in-progress matches."""
    matches_dir = temp_data_dir / "data" / "matches"

    # Create old in-progress match
    in_progress_match = matches_dir / "R1M1.json"
    sample_match_data["status"] = "IN_PROGRESS"
    sample_match_data["created_at"] = (datetime.now(timezone.utc) - timedelta(days=730)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    in_progress_match.write_text(json.dumps(sample_match_data))

    # Patch repository
    with patch("league_sdk.cleanup.MatchRepository") as MockRepo:
        mock_repo = Mock()
        mock_repo.base_path = matches_dir
        mock_repo.list_matches.return_value = ["R1M1"]
        mock_repo.load.return_value = sample_match_data
        MockRepo.return_value = mock_repo

        stats = await archive_old_matches(retention_days=365, archive_enabled=False)

        # In-progress match should NOT be deleted
        assert stats.files_deleted == 0


# ============================================================================
# TEST: Player History Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_prune_player_histories_removes_old_matches(temp_data_dir):
    """Test pruning removes old matches from player history."""
    player_history_file = temp_data_dir / "data" / "players" / "P01" / "history.json"

    # Create history with old and recent matches
    history_data = {
        "schema_version": "1.0.0",
        "player_id": "P01",
        "matches": [
            {
                "match_id": "R1M1",
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=730)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "result": "WIN",
                "points": 3,
            },
            {
                "match_id": "R2M1",
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "result": "WIN",
                "points": 3,
            },
        ],
        "stats": {"total_matches": 2, "wins": 2, "total_points": 6},
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    player_history_file.write_text(json.dumps(history_data))

    # Run cleanup
    stats = await prune_player_histories(retention_days=365, data_dir=temp_data_dir)

    # Reload history
    with open(player_history_file, "r") as f:
        updated_history = json.load(f)

    # Old match should be removed, recent match should remain
    assert len(updated_history["matches"]) == 1
    assert updated_history["matches"][0]["match_id"] == "R2M1"

    # Stats should remain unchanged
    assert updated_history["stats"]["total_matches"] == 2
    assert updated_history["stats"]["wins"] == 2


@pytest.mark.asyncio
async def test_prune_player_histories_preserves_stats(temp_data_dir):
    """Test pruning preserves aggregate statistics."""
    player_history_file = temp_data_dir / "data" / "players" / "P01" / "history.json"

    history_data = {
        "player_id": "P01",
        "matches": [
            {
                "match_id": "R1M1",
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=730)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        ],
        "stats": {"total_matches": 100, "wins": 75, "total_points": 225},
    }
    player_history_file.write_text(json.dumps(history_data))

    await prune_player_histories(retention_days=365, data_dir=temp_data_dir)

    with open(player_history_file, "r") as f:
        updated_history = json.load(f)

    # Stats should be unchanged
    assert updated_history["stats"]["total_matches"] == 100
    assert updated_history["stats"]["wins"] == 75


# ============================================================================
# TEST: League Rounds Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_prune_league_rounds_removes_old_rounds(temp_data_dir):
    """Test pruning removes old rounds from league history."""
    rounds_file = temp_data_dir / "data" / "leagues" / "test_league" / "rounds.json"

    rounds_data = {
        "schema_version": "1.0.0",
        "league_id": "test_league",
        "rounds": [
            {
                "round_id": 1,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=730)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "status": "COMPLETED",
            },
            {
                "round_id": 2,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "status": "COMPLETED",
            },
        ],
    }
    rounds_file.write_text(json.dumps(rounds_data))

    await prune_league_rounds(retention_days=365, data_dir=temp_data_dir)

    with open(rounds_file, "r") as f:
        updated_rounds = json.load(f)

    # Old round should be removed, recent round should remain
    assert len(updated_rounds["rounds"]) == 1
    assert updated_rounds["rounds"][0]["round_id"] == 2

    # Archived rounds count should be updated
    assert updated_rounds.get("archived_rounds", 0) == 1


# ============================================================================
# TEST: Full Cleanup
# ============================================================================


@pytest.mark.asyncio
async def test_run_full_cleanup_executes_all_cleanups(mock_config):
    """Test full cleanup runs all cleanup operations."""
    with patch("league_sdk.cleanup.get_retention_config", return_value=mock_config):
        with patch("league_sdk.cleanup.cleanup_old_logs") as mock_logs:
            with patch("league_sdk.cleanup.archive_old_matches") as mock_matches:
                with patch("league_sdk.cleanup.prune_player_histories") as mock_history:
                    with patch("league_sdk.cleanup.prune_league_rounds") as mock_rounds:
                        # Setup mocks to return stats
                        mock_logs.return_value = CleanupStats()
                        mock_matches.return_value = CleanupStats()
                        mock_history.return_value = CleanupStats()
                        mock_rounds.return_value = CleanupStats()

                        results = await run_full_cleanup()

                        # All cleanup functions should be called
                        assert mock_logs.called
                        assert mock_matches.called
                        assert mock_history.called
                        assert mock_rounds.called

                        # Results should contain all cleanup types
                        assert "logs" in results
                        assert "matches" in results
                        assert "player_history" in results
                        assert "league_rounds" in results


@pytest.mark.asyncio
async def test_run_full_cleanup_respects_disabled_config():
    """Test full cleanup does nothing when disabled in config."""
    disabled_config = {"enabled": False}

    with patch("league_sdk.cleanup.get_retention_config", return_value=disabled_config):
        results = await run_full_cleanup()

        # No cleanup should be performed
        assert results == {}


# ============================================================================
# TEST: Error Handling
# ============================================================================


@pytest.mark.asyncio
async def test_cleanup_handles_missing_directories(temp_data_dir):
    """Test cleanup gracefully handles missing directories."""
    # Try to cleanup non-existent log directory
    stats = await cleanup_old_logs(
        retention_days=30,
        log_dir=temp_data_dir / "nonexistent",
        archive_enabled=False,
    )

    # Should complete without errors
    assert stats.files_scanned == 0
    assert stats.files_deleted == 0


@pytest.mark.asyncio
async def test_cleanup_continues_on_file_errors(temp_data_dir):
    """Test cleanup continues when individual file operations fail."""
    logs_dir = temp_data_dir / "logs" / "agents"

    # Create multiple old log files
    for i in range(3):
        log_file = logs_dir / f"P0{i}.log.jsonl.1"
        log_file.write_text("log content")
        old_time = datetime.now(timezone.utc) - timedelta(days=60)
        import os

        os.utime(log_file, (old_time.timestamp(), old_time.timestamp()))

    # Make one file read-only to cause error
    (logs_dir / "P01.log.jsonl.1").chmod(0o000)

    try:
        stats = await cleanup_old_logs(
            retention_days=30, log_dir=temp_data_dir / "logs", archive_enabled=False
        )

        # Should have some errors but continue processing
        assert len(stats.errors) > 0 or stats.files_deleted >= 2

    finally:
        # Restore permissions for cleanup
        try:
            (logs_dir / "P01.log.jsonl.1").chmod(0o644)
        except Exception:
            pass
