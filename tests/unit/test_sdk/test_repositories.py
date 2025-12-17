"""
Unit tests for data repository layer (M2.3).

Tests file-based data access:
- StandingsRepository: Reading/writing standings
- RoundsRepository: Rounds history management
- MatchRepository: Creating and updating matches
- PlayerHistoryRepository: Tracking player stats
- Atomic file writes (temp file + rename)
"""

import json
from pathlib import Path

import pytest
from league_sdk.repositories import (
    MatchRepository,
    PlayerHistoryRepository,
    RoundsRepository,
    StandingsRepository,
    atomic_write,
    generate_timestamp,
)


@pytest.mark.unit
class TestAtomicWrite:
    """Test atomic file write operations."""

    def test_atomic_write_creates_file(self, tmp_path):
        """Test basic file creation."""
        target_file = tmp_path / "test.json"
        data = {"key": "value"}

        atomic_write(target_file, data)

        assert target_file.exists()
        with open(target_file, "r") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_atomic_write_creates_directories(self, tmp_path):
        """Test directory creation if missing."""
        target_file = tmp_path / "subdir" / "nested" / "test.json"

        atomic_write(target_file, {"a": 1})

        assert target_file.exists()

    def test_atomic_write_overwrites_existing(self, tmp_path):
        """Test overwriting existing file."""
        target_file = tmp_path / "test.json"
        atomic_write(target_file, {"version": 1})

        # Verify initial write
        with open(target_file, "r") as f:
            assert json.load(f)["version"] == 1

        # Overwrite
        atomic_write(target_file, {"version": 2})

        # Verify update
        with open(target_file, "r") as f:
            assert json.load(f)["version"] == 2


@pytest.mark.unit
class TestGenerateTimestamp:
    """Test timestamp generation helper."""

    def test_timestamp_format(self):
        """Test ISO 8601 UTC format with Z suffix."""
        ts = generate_timestamp()
        assert "T" in ts
        assert ts.endswith("Z")
        # Format: YYYY-MM-DDTHH:MM:SSZ (20 chars)
        assert len(ts) == 20


@pytest.mark.unit
class TestStandingsRepository:
    """Test StandingsRepository functionality."""

    def test_load_empty_standings(self, tmp_path):
        """Test loading when file doesn't exist."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        standings_data = repo.load()

        assert standings_data["schema_version"] == "1.0.0"
        assert standings_data["league_id"] == "test_league"
        assert standings_data["standings"] == []

    def test_save_standings(self, tmp_path):
        """Test saving standings data."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        standings_data = {
            "schema_version": "1.0.0",
            "league_id": "test_league",
            "standings": [{"player_id": "P01", "points": 3}],
        }
        repo.save(standings_data)

        loaded = repo.load()
        assert loaded["standings"] == [{"player_id": "P01", "points": 3}]

    def test_update_player_new(self, tmp_path):
        """Test updating a player not yet in standings."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        repo.update_player("P01", "WIN", 3)

        standings_data = repo.load()
        assert len(standings_data["standings"]) == 1
        p1 = standings_data["standings"][0]
        assert p1["player_id"] == "P01"
        assert p1["points"] == 3
        assert p1["wins"] == 1
        assert p1["losses"] == 0

    def test_update_player_existing(self, tmp_path):
        """Test updating an existing player."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        # First match: win
        repo.update_player("P01", "WIN", 3)
        # Second match: draw
        repo.update_player("P01", "DRAW", 1)

        standings_data = repo.load()
        p1 = standings_data["standings"][0]
        assert p1["points"] == 4  # 3 + 1
        assert p1["wins"] == 1
        assert p1["draws"] == 1
        assert p1["matches_played"] == 2

    def test_standings_sorted_by_points(self, tmp_path):
        """Test that standings are sorted by points descending."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        repo.update_player("P01", "DRAW", 1)
        repo.update_player("P02", "WIN", 3)

        standings_data = repo.load()
        standings = standings_data["standings"]

        # Should be sorted: P02 (3 pts) before P01 (1 pt)
        assert standings[0]["player_id"] == "P02"
        assert standings[0]["points"] == 3
        assert standings[1]["player_id"] == "P01"
        assert standings[1]["points"] == 1

    def test_get_player_standing(self, tmp_path):
        """Test retrieving specific player stats."""
        repo = StandingsRepository("test_league", data_root=tmp_path)

        repo.update_player("P01", "WIN", 3)

        stats = repo.get_player_standing("P01")
        assert stats["points"] == 3
        assert stats["wins"] == 1

        assert repo.get_player_standing("P99") is None


@pytest.mark.unit
class TestRoundsRepository:
    """Test RoundsRepository (schedule management)."""

    def test_load_empty_rounds(self, tmp_path):
        """Test loading when no rounds exist."""
        repo = RoundsRepository("test_league", data_root=tmp_path)

        rounds_data = repo.load()

        assert rounds_data["schema_version"] == "1.0.0"
        assert rounds_data["league_id"] == "test_league"
        assert rounds_data["rounds"] == []

    def test_add_new_round(self, tmp_path):
        """Test adding a new round."""
        repo = RoundsRepository("test_league", data_root=tmp_path)

        matches = [{"match_id": "M1", "players": ["P1", "P2"]}]
        repo.add_round(1, matches)

        rounds_data = repo.load()
        rounds = rounds_data["rounds"]
        assert len(rounds) == 1
        assert rounds[0]["round_id"] == 1
        assert rounds[0]["status"] == "PENDING"
        assert rounds[0]["matches"] == matches

    def test_update_existing_round(self, tmp_path):
        """Test updating an existing round's matches."""
        repo = RoundsRepository("test_league", data_root=tmp_path)

        repo.add_round(1, [{"match_id": "M1"}])
        repo.add_round(1, [{"match_id": "M2"}])  # Update with new matches

        round_data = repo.get_round(1)
        assert len(round_data["matches"]) == 1
        assert round_data["matches"][0]["match_id"] == "M2"

    def test_update_round_status(self, tmp_path):
        """Test updating round status."""
        repo = RoundsRepository("test_league", data_root=tmp_path)

        repo.add_round(1, [])
        repo.update_round_status(1, "IN_PROGRESS")

        round_data = repo.get_round(1)
        assert round_data["status"] == "IN_PROGRESS"

    def test_get_round(self, tmp_path):
        """Test retrieving specific round data."""
        repo = RoundsRepository("test_league", data_root=tmp_path)

        repo.add_round(1, [])

        assert repo.get_round(1) is not None
        assert repo.get_round(99) is None


@pytest.mark.unit
class TestMatchRepository:
    """Test MatchRepository functionality."""

    def test_load_nonexistent_match(self, tmp_path):
        """Test loading a match that doesn't exist."""
        repo = MatchRepository(data_root=tmp_path)

        assert repo.load("M99") is None

    def test_create_match(self, tmp_path):
        """Test creating a new match."""
        repo = MatchRepository(data_root=tmp_path)

        match_data = repo.create_match(
            match_id="M1",
            league_id="league_1",
            round_id=1,
            game_type="even_odd",
            player_a_id="P01",
            player_b_id="P02",
            referee_id="REF01",
        )

        assert match_data["match_id"] == "M1"
        assert match_data["status"] == "PENDING"
        assert match_data["players"]["player_a"] == "P01"
        assert match_data["players"]["player_b"] == "P02"

    def test_save_and_load_match(self, tmp_path):
        """Test saving and loading match data."""
        repo = MatchRepository(data_root=tmp_path)

        data = {"match_id": "test", "status": "PENDING"}
        repo.save("test", data)

        loaded = repo.load("test")
        assert loaded["match_id"] == "test"
        assert loaded["status"] == "PENDING"

    def test_update_match_status(self, tmp_path):
        """Test updating match status."""
        repo = MatchRepository(data_root=tmp_path)

        repo.create_match("M1", "league_1", 1, "even_odd", "P01", "P02", "REF01")
        repo.update_status("M1", "IN_PROGRESS")

        match_data = repo.load("M1")
        assert match_data["status"] == "IN_PROGRESS"

    def test_add_transcript_entry(self, tmp_path):
        """Test adding entries to match transcript."""
        repo = MatchRepository(data_root=tmp_path)

        repo.create_match("M1", "league_1", 1, "even_odd", "P01", "P02", "REF01")

        entry = {"timestamp": "2025-01-01T12:00:00Z", "event": "GAME_START"}
        repo.add_transcript_entry("M1", entry)

        match_data = repo.load("M1")
        assert len(match_data["transcript"]) == 1
        assert match_data["transcript"][0] == entry

    def test_set_result(self, tmp_path):
        """Test setting final match result."""
        repo = MatchRepository(data_root=tmp_path)

        repo.create_match("M1", "league_1", 1, "even_odd", "P01", "P02", "REF01")

        result = {"winner": "P01", "score": {"P01": 3, "P02": 0}}
        repo.set_result("M1", result)

        match_data = repo.load("M1")
        assert match_data["result"] == result
        assert match_data["status"] == "COMPLETED"  # Note: COMPLETED not FINISHED

    def test_list_matches(self, tmp_path):
        """Test listing all matches."""
        repo = MatchRepository(data_root=tmp_path)

        repo.create_match("M1", "league_1", 1, "even_odd", "P01", "P02", "REF01")
        repo.create_match("M2", "league_1", 1, "even_odd", "P03", "P04", "REF01")

        matches = repo.list_matches()
        assert len(matches) == 2
        assert "M1" in matches
        assert "M2" in matches

    def test_list_matches_filtered_by_league(self, tmp_path):
        """Test listing matches filtered by league."""
        repo = MatchRepository(data_root=tmp_path)

        repo.create_match("M1", "league_1", 1, "even_odd", "P01", "P02", "REF01")
        repo.create_match("M2", "league_2", 1, "even_odd", "P03", "P04", "REF01")

        matches = repo.list_matches(league_id="league_1")
        assert len(matches) == 1
        assert "M1" in matches


@pytest.mark.unit
class TestPlayerHistoryRepository:
    """Test PlayerHistoryRepository."""

    def test_load_empty_history(self, tmp_path):
        """Test loading when no history exists."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        history = repo.load()

        assert history["schema_version"] == "1.0.0"
        assert history["player_id"] == "P01"
        assert history["matches"] == []
        assert history["stats"]["total_matches"] == 0
        assert history["stats"]["wins"] == 0
        assert history["stats"]["draws"] == 0
        assert history["stats"]["losses"] == 0
        assert history["stats"]["total_points"] == 0

    def test_add_match_to_history(self, tmp_path):
        """Test adding a match to player history."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match(
            match_id="M1", league_id="league_1", round_id=1, opponent_id="P02", result="WIN", points=3
        )

        history = repo.load()
        assert len(history["matches"]) == 1
        assert history["matches"][0]["match_id"] == "M1"
        assert history["matches"][0]["result"] == "WIN"

    def test_stats_auto_update_on_win(self, tmp_path):
        """Test stats update automatically on win."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match("M1", "league_1", 1, "P02", "WIN", 3)

        stats = repo.get_stats()
        assert stats["wins"] == 1
        assert stats["total_matches"] == 1
        assert stats["total_points"] == 3

    def test_stats_auto_update_on_draw(self, tmp_path):
        """Test stats update automatically on draw."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match("M1", "league_1", 1, "P02", "DRAW", 1)

        stats = repo.get_stats()
        assert stats["draws"] == 1
        assert stats["total_points"] == 1

    def test_stats_auto_update_on_loss(self, tmp_path):
        """Test stats update automatically on loss."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match("M1", "league_1", 1, "P02", "LOSS", 0)

        stats = repo.get_stats()
        assert stats["losses"] == 1
        assert stats["total_points"] == 0

    def test_stats_cumulative(self, tmp_path):
        """Test that stats accumulate across multiple matches."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match("M1", "league_1", 1, "P02", "WIN", 3)
        repo.add_match("M2", "league_1", 1, "P03", "LOSS", 0)
        repo.add_match("M3", "league_1", 2, "P04", "DRAW", 1)

        stats = repo.get_stats()
        assert stats["total_matches"] == 3
        assert stats["wins"] == 1
        assert stats["losses"] == 1
        assert stats["draws"] == 1
        assert stats["total_points"] == 4

    def test_add_match_with_details(self, tmp_path):
        """Test adding match with optional details."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        details = {"game_type": "even_odd", "duration_sec": 45}
        repo.add_match("M1", "league_1", 1, "P02", "WIN", 3, details=details)

        history = repo.load()
        match = history["matches"][0]
        assert match["details"] == details

    def test_get_recent_matches(self, tmp_path):
        """Test getting recent matches."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        for i in range(5):
            repo.add_match(f"M{i}", "league_1", 1, "P02", "WIN", 3)

        recent = repo.get_recent_matches(3)
        assert len(recent) == 3
        # Should return last 3 matches
        assert recent[0]["match_id"] == "M2"
        assert recent[1]["match_id"] == "M3"
        assert recent[2]["match_id"] == "M4"

    def test_get_recent_matches_less_than_count(self, tmp_path):
        """Test getting recent matches when fewer exist."""
        repo = PlayerHistoryRepository("P01", data_root=tmp_path)

        repo.add_match("M1", "league_1", 1, "P02", "WIN", 3)

        recent = repo.get_recent_matches(5)
        assert len(recent) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
