"""
Unit tests for League Manager Round-Robin Scheduler (M7.10).

Tests:
- Round-robin schedule generation using Circle Method
- Match count validation: n*(n-1)/2 for n players
- Round distribution and balance
- Referee assignment (round-robin modulo)
- Match ID format: R{round}M{match}
- Odd player count handling (bye)
- Deterministic shuffle with league_id seed
- Persistence to rounds.json
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add SHARED to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "SHARED"))

from agents.league_manager.server import LeagueManager  # noqa: E402


class TestRoundRobinScheduler:
    """Test round-robin scheduling algorithm (M7.10)."""

    @pytest.fixture
    def temp_league_dir(self, tmp_path):
        """Create temporary league directory structure."""
        league_dir = tmp_path / "SHARED" / "data" / "leagues" / "test_league"
        league_dir.mkdir(parents=True)
        return league_dir

    @pytest.fixture
    def mock_league_manager(self, tmp_path):
        """Create League Manager with mocked dependencies."""
        # Create config structure
        config_dir = tmp_path / "SHARED" / "config"
        config_dir.mkdir(parents=True)

        # Create minimal system.json
        system_config = {
            "data_retention": {"enabled": True},
            "timeouts": {"registration_sec": 10},
            "retry_policy": {"max_retries": 3},
            "circuit_breaker": {"failure_threshold": 5},
            "network": {"league_manager_port": 8000},
            "logging": {"level": "INFO"},
        }
        with open(config_dir / "system.json", "w") as f:
            json.dump(system_config, f)

        # Create agents_config.json
        agents_dir = config_dir / "agents"
        agents_dir.mkdir()
        with open(agents_dir / "agents_config.json", "w") as f:
            json.dump({"league_manager": {"agent_id": "LM01", "port": 8000}}, f)

        # Create league config
        leagues_dir = config_dir / "leagues"
        leagues_dir.mkdir()
        league_config = {
            "schema_version": "1.0.0",
            "league_id": "test_league",
            "game_type": "even_odd",
            "status": "ACTIVE",
            "scoring": {"win_points": 3, "draw_points": 1},
            "schedule_type": "round_robin",
            "participants": {"min_players": 2, "max_players": 10000},
        }
        with open(leagues_dir / "test_league.json", "w") as f:
            json.dump(league_config, f)

        # Mock BaseAgent and create League Manager
        with patch("agents.league_manager.server.BaseAgent.__init__", return_value=None):
            with patch("agents.league_manager.server.load_system_config") as mock_sys:
                with patch("agents.league_manager.server.load_agents_config") as mock_ag:
                    with patch("agents.league_manager.server.load_league_config") as mock_league:
                        with patch(
                            "agents.league_manager.server.get_retention_config"
                        ) as mock_retention:
                            # Load actual configs
                            with open(config_dir / "system.json") as f:
                                mock_sys.return_value = json.load(f)
                            with open(agents_dir / "agents_config.json") as f:
                                mock_ag.return_value = json.load(f)
                            with open(leagues_dir / "test_league.json") as f:
                                league_cfg = json.load(f)
                                mock_league.return_value = type(
                                    "LeagueConfig",
                                    (),
                                    {
                                        "participants": league_cfg["participants"],
                                        "schedule_type": league_cfg["schedule_type"],
                                    },
                                )()
                            mock_retention.return_value = {"enabled": True}

                            # Create League Manager instance
                            lm = object.__new__(LeagueManager)
                            lm.agent_id = "LM01"
                            lm.league_id = "test_league"
                            lm.std_logger = MagicMock()
                            lm.system_config = mock_sys.return_value
                            lm.agents_config = mock_ag.return_value
                            lm.league_config = mock_league.return_value
                            lm.league_config.game_type = "even_odd"  # Add game_type
                            lm.registered_players = {}
                            lm.registered_referees = {}

                            # Mock RoundsRepository
                            mock_repo = MagicMock()
                            lm.rounds_repo = mock_repo

                            return lm

    def test_schedule_4_players_generates_6_matches(self, mock_league_manager):
        """Test: 4 players → 6 matches (n*(n-1)/2 = 4*3/2 = 6)."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01", "REF02"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        assert result["total_matches"] == 6, "4 players should generate 6 matches"
        assert result["players_count"] == 4
        assert result["referees_count"] == 2

    def test_schedule_6_players_generates_15_matches(self, mock_league_manager):
        """Test: 6 players → 15 matches (n*(n-1)/2 = 6*5/2 = 15)."""
        player_ids = [f"P{i:02d}" for i in range(1, 7)]  # P01-P06
        referee_ids = ["REF01", "REF02"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        assert result["total_matches"] == 15, "6 players should generate 15 matches"
        assert result["total_rounds"] == 5, "6 players should have 5 rounds"

    def test_schedule_8_players_generates_28_matches(self, mock_league_manager):
        """Test: 8 players → 28 matches (n*(n-1)/2 = 8*7/2 = 28)."""
        player_ids = [f"P{i:02d}" for i in range(1, 9)]  # P01-P08
        referee_ids = ["REF01", "REF02", "REF03"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        assert result["total_matches"] == 28, "8 players should generate 28 matches"
        assert result["total_rounds"] == 7, "8 players should have 7 rounds"

    def test_even_players_correct_rounds(self, mock_league_manager):
        """Test: Even number of players → n-1 rounds."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        assert result["total_rounds"] == 3, "4 players (even) should have 3 rounds"

    def test_odd_players_correct_rounds_with_bye(self, mock_league_manager):
        """Test: Odd number of players → n rounds (with bye)."""
        player_ids = ["P01", "P02", "P03"]  # 3 players
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # 3 players: 3*(3-1)/2 = 3 matches
        assert result["total_matches"] == 3, "3 players should generate 3 matches"
        # Odd count: treated as 4 (with bye) → 3 rounds
        assert result["total_rounds"] == 3, "3 players should have 3 rounds (with bye)"

    def test_match_ids_follow_format(self, mock_league_manager):
        """Test: Match IDs follow R{round}M{match} format."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # Check match ID format in first round
        round_1 = result["schedule"][0]
        assert round_1["matches"][0]["match_id"] == "R1M1"
        assert round_1["matches"][1]["match_id"] == "R1M2"

        # Check second round
        round_2 = result["schedule"][1]
        assert round_2["matches"][0]["match_id"] == "R2M1"

    def test_match_includes_league_id_and_game_type(self, mock_league_manager):
        """Test: Each match includes league_id and game_type."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # Check first match has all required fields
        first_match = result["schedule"][0]["matches"][0]
        assert "league_id" in first_match
        assert first_match["league_id"] == "test_league"
        assert "game_type" in first_match
        assert first_match["game_type"] == "even_odd"
        assert "round_id" in first_match
        assert first_match["round_id"] == 1

    def test_referee_assignment_round_robin(self, mock_league_manager):
        """Test: Referees assigned evenly using modulo distribution."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01", "REF02"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # Collect all referee assignments
        ref_assignments = []
        for round_data in result["schedule"]:
            for match in round_data["matches"]:
                ref_assignments.append(match["referee_id"])

        # 6 matches total: REF01, REF02, REF01, REF02, REF01, REF02
        assert ref_assignments[0] == "REF01"
        assert ref_assignments[1] == "REF02"
        assert ref_assignments[2] == "REF01"
        assert ref_assignments[3] == "REF02"
        assert ref_assignments[4] == "REF01"
        assert ref_assignments[5] == "REF02"

    def test_each_player_plays_once_per_round(self, mock_league_manager):
        """Test: Each player appears exactly once per round."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        for round_data in result["schedule"]:
            players_in_round = set()
            for match in round_data["matches"]:
                players_in_round.add(match["player_a_id"])
                players_in_round.add(match["player_b_id"])

            # Each player should appear exactly once
            assert len(players_in_round) == 4, "Each player should appear once per round"

    def test_all_unique_pairings(self, mock_league_manager):
        """Test: Each pair of players meets exactly once."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # Collect all pairings
        pairings = set()
        for round_data in result["schedule"]:
            for match in round_data["matches"]:
                pair = tuple(sorted([match["player_a_id"], match["player_b_id"]]))
                pairings.add(pair)

        # 4 players should have 6 unique pairings
        assert len(pairings) == 6, "Should have 6 unique pairings"

        # Verify all expected pairs exist
        expected_pairs = {
            ("P01", "P02"),
            ("P01", "P03"),
            ("P01", "P04"),
            ("P02", "P03"),
            ("P02", "P04"),
            ("P03", "P04"),
        }
        assert pairings == expected_pairs

    def test_deterministic_shuffle_reproducible(self, mock_league_manager):
        """Test: Deterministic shuffle produces same order with same league_id."""
        player_ids = ["P01", "P02", "P03", "P04"]

        # Shuffle twice with same league_id
        shuffled_1 = mock_league_manager._shuffle_players_deterministic(player_ids)
        shuffled_2 = mock_league_manager._shuffle_players_deterministic(player_ids)

        assert shuffled_1 == shuffled_2, "Shuffle should be deterministic"

    def test_schedule_persists_to_repository(self, mock_league_manager):
        """Test: Schedule is persisted to RoundsRepository."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        mock_league_manager.create_schedule(player_ids, referee_ids)

        # Verify repository was called
        assert mock_league_manager.rounds_repo.add_round.call_count == 3, "Should persist 3 rounds"

        # Check first round was saved correctly
        call_args = mock_league_manager.rounds_repo.add_round.call_args_list[0]
        assert call_args[1]["round_id"] == 1
        assert len(call_args[1]["matches"]) == 2  # 2 matches in first round

    def test_minimum_players_validation(self, mock_league_manager):
        """Test: Raises error if fewer than min_players."""
        player_ids = ["P01"]  # Only 1 player
        referee_ids = ["REF01"]

        with pytest.raises(ValueError, match="At least 2 players required"):
            mock_league_manager.create_schedule(player_ids, referee_ids)

    def test_no_referees_validation(self, mock_league_manager):
        """Test: Raises error if no referees available."""
        player_ids = ["P01", "P02"]
        referee_ids = []  # No referees

        with pytest.raises(ValueError, match="At least 1 referee required"):
            mock_league_manager.create_schedule(player_ids, referee_ids)

    def test_duplicate_player_ids_validation(self, mock_league_manager):
        """Test: Raises error if duplicate player IDs detected (E002)."""
        player_ids = ["P01", "P02", "P01", "P03"]  # P01 appears twice
        referee_ids = ["REF01"]

        with pytest.raises(ValueError, match="Duplicate player IDs not allowed"):
            mock_league_manager.create_schedule(player_ids, referee_ids)

    def test_capacity_warning_when_matches_exceed_referee_limit(self, mock_league_manager):
        """Test: Logs warning when matches per round exceed referee capacity."""
        # 6 players = 3 matches per round, but only 1 referee with capacity 1
        player_ids = [f"P{i:02d}" for i in range(1, 7)]  # P01-P06
        referee_ids = ["REF01"]
        mock_league_manager.registered_referees = {
            "REF01": {"max_concurrent_matches": 1}  # Low capacity
        }

        mock_league_manager.create_schedule(player_ids, referee_ids)

        # Check if warning was logged
        warning_calls = [
            call
            for call in mock_league_manager.std_logger.warning.call_args_list
            if "capacity" in str(call).lower()
        ]
        assert len(warning_calls) > 0, "Should log capacity warning"

    def test_per_match_logging_for_traceability(self, mock_league_manager):
        """Test: Each match assignment is logged with match_id, round_id, referee_id."""
        player_ids = ["P01", "P02", "P03", "P04"]
        referee_ids = ["REF01"]

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        # Should log 6 matches (4 players = 6 total matches)
        info_calls = mock_league_manager.std_logger.info.call_args_list
        match_assignment_logs = [
            call for call in info_calls if len(call.args) > 0 and "Match assigned" in str(call.args[0])
        ]

        assert len(match_assignment_logs) == 6, "Should log all 6 match assignments"

        # Verify first match log contains required fields
        first_log = match_assignment_logs[0]
        assert "extra" in first_log.kwargs
        extra_data = first_log.kwargs["extra"]
        assert "match_id" in extra_data
        assert "round_id" in extra_data
        assert "referee_id" in extra_data
        assert "league_id" in extra_data

    def test_schedule_uses_registered_players_by_default(self, mock_league_manager):
        """Test: Uses registered players if player_ids not provided."""
        # Register players
        mock_league_manager.registered_players = {
            "P01": {"display_name": "Player 1"},
            "P02": {"display_name": "Player 2"},
            "P03": {"display_name": "Player 3"},
            "P04": {"display_name": "Player 4"},
        }
        mock_league_manager.registered_referees = {"REF01": {"display_name": "Referee 1"}}

        result = mock_league_manager.create_schedule()  # No args

        assert result["players_count"] == 4
        assert result["referees_count"] == 1

    def test_large_league_100_players(self, mock_league_manager):
        """Test: Handles large league (100 players)."""
        player_ids = [f"P{i:03d}" for i in range(1, 101)]  # P001-P100
        referee_ids = [f"REF{i:02d}" for i in range(1, 11)]  # REF01-REF10

        result = mock_league_manager.create_schedule(player_ids, referee_ids)

        expected_matches = 100 * 99 // 2  # 4950 matches
        assert result["total_matches"] == expected_matches
        assert result["total_rounds"] == 99  # n-1 rounds for even count


class TestRoundRobinAlgorithm:
    """Test Circle Method algorithm implementation."""

    @pytest.fixture
    def mock_lm(self):
        """Create minimal League Manager for testing algorithm."""
        lm = object.__new__(LeagueManager)
        lm.league_id = "test_league"
        return lm

    def test_circle_method_4_players(self, mock_lm):
        """Test Circle Method with 4 players."""
        player_ids = ["P1", "P2", "P3", "P4"]
        rounds = mock_lm._generate_round_robin_rounds(player_ids)

        # 4 players (even) → 3 rounds
        assert len(rounds) == 3

        # Each round should have 2 matches (4 players / 2)
        for round_matches in rounds:
            assert len(round_matches) == 2

    def test_circle_method_3_players_odd(self, mock_lm):
        """Test Circle Method with 3 players (odd)."""
        player_ids = ["P1", "P2", "P3"]
        rounds = mock_lm._generate_round_robin_rounds(player_ids)

        # 3 players (odd, treated as 4 with bye) → 3 rounds
        assert len(rounds) == 3

        # Each round should have 1 match (one player has bye)
        for round_matches in rounds:
            assert len(round_matches) == 1

    def test_no_player_appears_twice_in_round(self, mock_lm):
        """Test: No player appears in two matches in same round."""
        player_ids = ["P1", "P2", "P3", "P4", "P5", "P6"]
        rounds = mock_lm._generate_round_robin_rounds(player_ids)

        for round_matches in rounds:
            players_in_round = []
            for p1, p2 in round_matches:
                players_in_round.extend([p1, p2])

            # No duplicates
            assert len(players_in_round) == len(set(players_in_round))


class TestRefereeAssignment:
    """Test referee assignment logic."""

    @pytest.fixture
    def mock_lm(self):
        """Create minimal League Manager."""
        lm = object.__new__(LeagueManager)
        lm.league_id = "test"
        lm.std_logger = MagicMock()  # Add logger for per-match logging
        return lm

    def test_single_referee_gets_all_matches(self, mock_lm):
        """Test: Single referee assigned to all matches."""
        rounds = [[("P1", "P2"), ("P3", "P4")]]
        referee_ids = ["REF01"]
        game_type = "even_odd"

        schedule = mock_lm._assign_referees_to_rounds(rounds, referee_ids, game_type)

        for round_data in schedule:
            for match in round_data["matches"]:
                assert match["referee_id"] == "REF01"

    def test_two_referees_alternate(self, mock_lm):
        """Test: Two referees alternate via modulo."""
        rounds = [[("P1", "P2"), ("P3", "P4"), ("P5", "P6")]]
        referee_ids = ["REF01", "REF02"]
        game_type = "even_odd"

        schedule = mock_lm._assign_referees_to_rounds(rounds, referee_ids, game_type)

        refs = [m["referee_id"] for m in schedule[0]["matches"]]
        assert refs == ["REF01", "REF02", "REF01"]


# Integration test
def test_full_schedule_integration():
    """Integration test: Full schedule generation workflow."""
    # This would require full League Manager setup
    # For now, covered by unit tests above
    pass
