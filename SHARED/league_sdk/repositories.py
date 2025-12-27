"""
Data persistence layer using file-based JSON storage.

This module provides repository classes for dynamic data (not static configuration):
- StandingsRepository: League standings data (standings.json)
- RoundsRepository: Rounds history (rounds.json)
- MatchRepository: Individual match records (<match_id>.json)
- PlayerHistoryRepository: Player match history (history.json)

All repositories use atomic write pattern (temp file + rename) to ensure data integrity.
Each repository handles read, update, and save for a specific data type.

Data Structure:
- SHARED/data/leagues/<league_id>/standings.json
- SHARED/data/leagues/<league_id>/rounds.json
- SHARED/data/matches/<match_id>.json
- SHARED/data/players/<player_id>/history.json
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "StandingsRepository",
    "RoundsRepository",
    "MatchRepository",
    "PlayerHistoryRepository",
    "atomic_write",
]

# Default data root directory
DATA_ROOT = Path("SHARED/data")


def atomic_write(file_path: str | Path, data: dict) -> None:
    """
    Atomically write JSON data to file using temp file + rename pattern.

    This ensures data integrity even if the write is interrupted.

    Args:
        file_path: Target file path
        data: Data to write as JSON

    Raises:
        IOError: If write fails
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file in same directory
    fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Atomic rename (replaces existing file)
        os.replace(temp_path, path)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def generate_timestamp() -> str:
    """Generate ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================================
# STANDINGS REPOSITORY
# ============================================================================


class StandingsRepository:
    """
    Repository for league standings data.

    Manages league standings table with player rankings, points, wins, losses, etc.
    File location: SHARED/data/leagues/<league_id>/standings.json
    """

    def __init__(self, league_id: str, data_root: Path = DATA_ROOT):
        """
        Initialize standings repository for a specific league.

        Args:
            league_id: Unique league identifier
            data_root: Root directory for data storage (default: SHARED/data)
        """
        self.league_id = league_id
        self.path = data_root / "leagues" / league_id / "standings.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """
        Load standings from JSON file.

        Returns:
            Dictionary with schema_version, standings list, and metadata
        """
        if not self.path.exists():
            return {
                "schema_version": "1.0.0",
                "league_id": self.league_id,
                "standings": [],
                "last_updated": generate_timestamp(),
            }

        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, standings: Dict[str, Any]) -> None:
        """
        Save standings to JSON file with automatic timestamp update.

        Args:
            standings: Standings dictionary to save
        """
        standings["last_updated"] = generate_timestamp()
        standings["schema_version"] = standings.get("schema_version", "1.0.0")
        standings["league_id"] = self.league_id
        atomic_write(self.path, standings)

    def update_player(self, player_id: str, result: str, points: int) -> None:
        """
        Update a player's standings after a match.

        Args:
            player_id: Player identifier
            result: Match result ("WIN", "DRAW", "LOSS")
            points: Points to add (3 for win, 1 for draw, 0 for loss)
        """
        standings_data = self.load()
        standings_list = standings_data.get("standings", [])

        # Find player in standings
        player_entry = None
        for entry in standings_list:
            if entry.get("player_id") == player_id:
                player_entry = entry
                break

        # Create new entry if player not found
        if player_entry is None:
            player_entry = {
                "player_id": player_id,
                "points": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "matches_played": 0,
            }
            standings_list.append(player_entry)

        # Update stats
        player_entry["matches_played"] = player_entry.get("matches_played", 0) + 1
        player_entry["points"] = player_entry.get("points", 0) + points

        if result == "WIN":
            player_entry["wins"] = player_entry.get("wins", 0) + 1
        elif result == "DRAW":
            player_entry["draws"] = player_entry.get("draws", 0) + 1
        elif result == "LOSS":
            player_entry["losses"] = player_entry.get("losses", 0) + 1

        # Sort standings by points (descending) then wins (descending)
        standings_list.sort(key=lambda x: (x.get("points", 0), x.get("wins", 0)), reverse=True)

        standings_data["standings"] = standings_list
        self.save(standings_data)

    def get_player_standing(self, player_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific player's standing.

        Args:
            player_id: Player identifier

        Returns:
            Player standing dictionary or None if not found
        """
        standings_data = self.load()
        for entry in standings_data.get("standings", []):
            if entry.get("player_id") == player_id:
                return entry
        return None


# ============================================================================
# ROUNDS REPOSITORY
# ============================================================================


class RoundsRepository:
    """
    Repository for rounds history.

    Manages round-by-round history of matches and results.
    File location: SHARED/data/leagues/<league_id>/rounds.json
    """

    def __init__(self, league_id: str, data_root: Path = DATA_ROOT):
        """
        Initialize rounds repository for a specific league.

        Args:
            league_id: Unique league identifier
            data_root: Root directory for data storage (default: SHARED/data)
        """
        self.league_id = league_id
        self.path = data_root / "leagues" / league_id / "rounds.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """
        Load rounds history from JSON file.

        Returns:
            Dictionary with schema_version, rounds list, and metadata
        """
        if not self.path.exists():
            return {
                "schema_version": "1.0.0",
                "league_id": self.league_id,
                "rounds": [],
                "last_updated": generate_timestamp(),
            }

        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, rounds_data: Dict[str, Any]) -> None:
        """
        Save rounds data to JSON file with automatic timestamp update.

        Args:
            rounds_data: Rounds dictionary to save
        """
        rounds_data["last_updated"] = generate_timestamp()
        rounds_data["schema_version"] = rounds_data.get("schema_version", "1.0.0")
        rounds_data["league_id"] = self.league_id
        atomic_write(self.path, rounds_data)

    def add_round(self, round_id: int, matches: List[Dict[str, Any]]) -> None:
        """
        Add a new round to the history.

        Args:
            round_id: Round number
            matches: List of match dictionaries for this round
        """
        rounds_data = self.load()
        rounds_list = rounds_data.get("rounds", [])

        # Check if round already exists
        existing_round = None
        for round_entry in rounds_list:
            if round_entry.get("round_id") == round_id:
                existing_round = round_entry
                break

        if existing_round:
            # Update existing round
            existing_round["matches"] = matches
            existing_round["updated_at"] = generate_timestamp()
        else:
            # Add new round
            rounds_list.append(
                {
                    "round_id": round_id,
                    "matches": matches,
                    "status": "PENDING",
                    "created_at": generate_timestamp(),
                }
            )

        rounds_data["rounds"] = rounds_list
        self.save(rounds_data)

    def update_round_status(self, round_id: int, status: str) -> None:
        """
        Update the status of a round.

        Args:
            round_id: Round number
            status: New status ("PENDING", "IN_PROGRESS", "COMPLETED")
        """
        rounds_data = self.load()
        rounds_list = rounds_data.get("rounds", [])

        for round_entry in rounds_list:
            if round_entry.get("round_id") == round_id:
                round_entry["status"] = status
                round_entry["updated_at"] = generate_timestamp()
                break

        rounds_data["rounds"] = rounds_list
        self.save(rounds_data)

    def get_round(self, round_id: int) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific round.

        Args:
            round_id: Round number

        Returns:
            Round dictionary or None if not found
        """
        rounds_data = self.load()
        for round_entry in rounds_data.get("rounds", []):
            if round_entry.get("round_id") == round_id:
                return round_entry
        return None


# ============================================================================
# MATCH REPOSITORY
# ============================================================================


class MatchRepository:
    """
    Repository for individual match data.

    Manages detailed match records including players, moves, and results.
    File location: SHARED/data/matches/<match_id>.json
    """

    def __init__(self, data_root: Path = DATA_ROOT):
        """
        Initialize match repository.

        Args:
            data_root: Root directory for data storage (default: SHARED/data)
        """
        self.base_path = data_root / "matches"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def load(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        Load match data from JSON file.

        Args:
            match_id: Match identifier

        Returns:
            Match data dictionary or None if not found
        """
        file_path = self.base_path / f"{match_id}.json"
        if not file_path.exists():
            return None

        return json.loads(file_path.read_text(encoding="utf-8"))

    def save(self, match_id: str, match_data: Dict[str, Any]) -> None:
        """
        Save match data to JSON file with automatic timestamp update.

        Args:
            match_id: Match identifier
            match_data: Match data dictionary to save
        """
        match_data["last_updated"] = generate_timestamp()
        match_data["schema_version"] = match_data.get("schema_version", "1.0.0")
        match_data["match_id"] = match_id

        file_path = self.base_path / f"{match_id}.json"
        atomic_write(file_path, match_data)

    def create_match(
        self,
        match_id: str,
        league_id: str,
        round_id: int,
        game_type: str,
        player_a_id: str,
        player_b_id: str,
        referee_id: str,
    ) -> Dict[str, Any]:
        """
        Create a new match record.

        Args:
            match_id: Match identifier
            league_id: League identifier
            round_id: Round number
            game_type: Game type
            player_a_id: Player A identifier
            player_b_id: Player B identifier
            referee_id: Referee identifier

        Returns:
            Created match data dictionary
        """
        match_data = {
            "schema_version": "1.0.0",
            "match_id": match_id,
            "league_id": league_id,
            "round_id": round_id,
            "game_type": game_type,
            "players": {"player_a": player_a_id, "player_b": player_b_id},
            "referee_id": referee_id,
            "status": "PENDING",
            "result": None,
            "transcript": [],
            "created_at": generate_timestamp(),
            "last_updated": generate_timestamp(),
        }

        self.save(match_id, match_data)
        return match_data

    def update_status(self, match_id: str, status: str) -> None:
        """
        Update match status.

        Args:
            match_id: Match identifier
            status: New status ("PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED")
        """
        match_data = self.load(match_id)
        if match_data:
            match_data["status"] = status
            self.save(match_id, match_data)

    def add_transcript_entry(self, match_id: str, entry: Dict[str, Any]) -> None:
        """
        Add an entry to the match transcript.

        Args:
            match_id: Match identifier
            entry: Transcript entry (message or event)
        """
        match_data = self.load(match_id)
        if match_data:
            transcript = match_data.get("transcript", [])
            transcript.append(entry)
            match_data["transcript"] = transcript
            self.save(match_id, match_data)

    def set_result(self, match_id: str, result: Dict[str, Any]) -> None:
        """
        Set the final result of a match.

        Args:
            match_id: Match identifier
            result: Result dictionary with winner, score, etc.
        """
        match_data = self.load(match_id)
        if match_data:
            match_data["result"] = result
            match_data["status"] = "COMPLETED"
            self.save(match_id, match_data)

    def list_matches(
        self, league_id: Optional[str] = None, round_id: Optional[int] = None
    ) -> List[str]:
        """
        List all match IDs, optionally filtered by league and round.

        Args:
            league_id: Optional league ID filter
            round_id: Optional round ID filter

        Returns:
            List of match IDs
        """
        match_files = list(self.base_path.glob("*.json"))
        match_ids = []

        for file in match_files:
            match_id = file.stem

            # Apply filters if specified
            if league_id or round_id:
                match_data = self.load(match_id)
                if not match_data:
                    continue

                if league_id and match_data.get("league_id") != league_id:
                    continue

                if round_id is not None and match_data.get("round_id") != round_id:
                    continue

            match_ids.append(match_id)

        return sorted(match_ids)


# ============================================================================
# PLAYER HISTORY REPOSITORY
# ============================================================================


class PlayerHistoryRepository:
    """
    Repository for player match history.

    Manages comprehensive player statistics and match history.
    File location: SHARED/data/players/<player_id>/history.json
    """

    def __init__(self, player_id: str, data_root: Path = DATA_ROOT):
        """
        Initialize player history repository for a specific player.

        Args:
            player_id: Player identifier
            data_root: Root directory for data storage (default: SHARED/data)
        """
        self.player_id = player_id
        self.path = data_root / "players" / player_id / "history.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """
        Load player history from JSON file.

        Returns:
            Dictionary with schema_version, matches, stats, and metadata
        """
        if not self.path.exists():
            return {
                "schema_version": "1.0.0",
                "player_id": self.player_id,
                "matches": [],
                "stats": {"total_matches": 0, "wins": 0, "draws": 0, "losses": 0, "total_points": 0},
                "last_updated": generate_timestamp(),
            }

        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, history_data: Dict[str, Any]) -> None:
        """
        Save player history to JSON file with automatic timestamp update.

        Args:
            history_data: History dictionary to save
        """
        history_data["last_updated"] = generate_timestamp()
        history_data["schema_version"] = history_data.get("schema_version", "1.0.0")
        history_data["player_id"] = self.player_id
        atomic_write(self.path, history_data)

    def add_match(
        self,
        match_id: str,
        league_id: str,
        round_id: int,
        opponent_id: str,
        result: str,
        points: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a match to player's history and update stats.

        Args:
            match_id: Match identifier
            league_id: League identifier
            round_id: Round number
            opponent_id: Opponent player ID
            result: Match result ("WIN", "DRAW", "LOSS")
            points: Points earned
            details: Optional additional match details
        """
        history_data = self.load()

        # Add match record
        match_record = {
            "match_id": match_id,
            "league_id": league_id,
            "round_id": round_id,
            "opponent_id": opponent_id,
            "result": result,
            "points": points,
            "timestamp": generate_timestamp(),
        }

        if details:
            match_record["details"] = details

        history_data["matches"].append(match_record)

        # Update stats
        stats = history_data.get(
            "stats", {"total_matches": 0, "wins": 0, "draws": 0, "losses": 0, "total_points": 0}
        )

        stats["total_matches"] = stats.get("total_matches", 0) + 1
        stats["total_points"] = stats.get("total_points", 0) + points

        if result == "WIN":
            stats["wins"] = stats.get("wins", 0) + 1
        elif result == "DRAW":
            stats["draws"] = stats.get("draws", 0) + 1
        elif result == "LOSS":
            stats["losses"] = stats.get("losses", 0) + 1

        history_data["stats"] = stats
        self.save(history_data)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get player statistics.

        Returns:
            Statistics dictionary
        """
        history_data = self.load()
        return history_data.get("stats", {})

    def get_recent_matches(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get player's most recent matches.

        Args:
            count: Number of recent matches to return

        Returns:
            List of recent match records
        """
        history_data = self.load()
        matches = history_data.get("matches", [])
        return matches[-count:] if len(matches) > count else matches
