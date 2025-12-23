"""
Unit tests for Even/Odd game logic (Mission 7.7).

Tests winner determination, randomness, parity checking, and technical losses.
"""

import pytest

from agents.referee_REF01.game_logic import EvenOddGameLogic, GameResult


class TestEvenOddGameLogic:
    """Test suite for Even/Odd game logic."""

    @pytest.fixture
    def game_logic(self):
        """Create game logic instance."""
        return EvenOddGameLogic()

    def test_load_game_config(self, game_logic):
        """Test game configuration loads from registry."""
        assert game_logic.min_number == 1
        assert game_logic.max_number == 10
        assert game_logic.valid_choices == {"even", "odd"}
        assert game_logic.even_numbers == {2, 4, 6, 8, 10}
        assert game_logic.odd_numbers == {1, 3, 5, 7, 9}

    def test_draw_random_number_in_range(self, game_logic):
        """Test random number is within configured range."""
        for _ in range(100):
            number = game_logic.draw_random_number()
            assert 1 <= number <= 10

    def test_draw_random_number_distribution(self, game_logic):
        """Test random number distribution is roughly uniform."""
        numbers = [game_logic.draw_random_number() for _ in range(1000)]
        unique_numbers = set(numbers)

        # Should cover all numbers 1-10
        assert unique_numbers == set(range(1, 11))

        # Each number should appear roughly 100 times (±50 tolerance)
        for num in range(1, 11):
            count = numbers.count(num)
            assert 50 <= count <= 150, f"Number {num} appeared {count} times (expected ~100)"

    def test_check_parity_even_numbers(self, game_logic):
        """Test parity check for even numbers."""
        for num in [2, 4, 6, 8, 10]:
            assert game_logic.check_parity(num) == "even"

    def test_check_parity_odd_numbers(self, game_logic):
        """Test parity check for odd numbers."""
        for num in [1, 3, 5, 7, 9]:
            assert game_logic.check_parity(num) == "odd"

    def test_check_parity_invalid_number(self, game_logic):
        """Test parity check raises error for invalid number."""
        with pytest.raises(ValueError, match="not in parity definition sets"):
            game_logic.check_parity(11)

    def test_validate_choice_valid(self, game_logic):
        """Test valid choice validation."""
        assert game_logic.validate_choice("even") is True
        assert game_logic.validate_choice("odd") is True

    def test_validate_choice_invalid(self, game_logic):
        """Test invalid choice validation."""
        assert game_logic.validate_choice("EVEN") is False
        assert game_logic.validate_choice("ODD") is False
        assert game_logic.validate_choice("maybe") is False
        assert game_logic.validate_choice("") is False

    def test_determine_winner_both_choose_even_draw(self, game_logic):
        """Test draw when both players choose even (§3.1 Scenario 5)."""
        winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "even", "even", 2)
        assert winner == "DRAW"
        assert status_a == GameResult.DRAW.value
        assert status_b == GameResult.DRAW.value

    def test_determine_winner_both_choose_odd_draw(self, game_logic):
        """Test draw when both players choose odd (§3.1 Scenario 6)."""
        winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "odd", "odd", 7)
        assert winner == "DRAW"
        assert status_a == GameResult.DRAW.value
        assert status_b == GameResult.DRAW.value

    def test_determine_winner_player_a_wins_even_match(self, game_logic):
        """Test Player A wins when choosing even and number is even (§3.1 Scenario 1)."""
        winner, status_a, status_b = game_logic.determine_winner(
            "P01", "P02", "even", "odd", 8  # even number
        )
        assert winner == "P01"
        assert status_a == GameResult.WIN.value
        assert status_b == GameResult.LOSS.value

    def test_determine_winner_player_b_wins_even_match(self, game_logic):
        """Test Player B wins when choosing even and number is even (§3.1 Scenario 3)."""
        winner, status_a, status_b = game_logic.determine_winner(
            "P01", "P02", "odd", "even", 4  # even number
        )
        assert winner == "P02"
        assert status_a == GameResult.LOSS.value
        assert status_b == GameResult.WIN.value

    def test_determine_winner_player_a_wins_odd_match(self, game_logic):
        """Test Player A wins when choosing odd and number is odd (§3.1 Scenario 4)."""
        winner, status_a, status_b = game_logic.determine_winner(
            "P01", "P02", "odd", "even", 7  # odd number
        )
        assert winner == "P01"
        assert status_a == GameResult.WIN.value
        assert status_b == GameResult.LOSS.value

    def test_determine_winner_player_b_wins_odd_match(self, game_logic):
        """Test Player B wins when choosing odd and number is odd (§3.1 Scenario 2)."""
        winner, status_a, status_b = game_logic.determine_winner(
            "P01", "P02", "even", "odd", 3  # odd number
        )
        assert winner == "P02"
        assert status_a == GameResult.LOSS.value
        assert status_b == GameResult.WIN.value

    def test_determine_winner_all_even_numbers(self, game_logic):
        """Test winner determination for all even numbers."""
        for num in [2, 4, 6, 8, 10]:
            # Player A chooses even → wins
            winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "even", "odd", num)
            assert winner == "P01"
            assert status_a == GameResult.WIN.value

            # Player B chooses even → wins
            winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "odd", "even", num)
            assert winner == "P02"
            assert status_b == GameResult.WIN.value

    def test_determine_winner_all_odd_numbers(self, game_logic):
        """Test winner determination for all odd numbers."""
        for num in [1, 3, 5, 7, 9]:
            # Player A chooses odd → wins
            winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "odd", "even", num)
            assert winner == "P01"
            assert status_a == GameResult.WIN.value

            # Player B chooses odd → wins
            winner, status_a, status_b = game_logic.determine_winner("P01", "P02", "even", "odd", num)
            assert winner == "P02"
            assert status_b == GameResult.WIN.value

    def test_award_technical_loss(self, game_logic):
        """Test technical loss award (§5 of game rules)."""
        winner, offender_status, opponent_status = game_logic.award_technical_loss("P01", "P02")
        assert winner == "P02"  # Opponent wins
        assert offender_status == GameResult.TECHNICAL_LOSS.value
        assert opponent_status == GameResult.WIN.value

    def test_get_points_win(self, game_logic):
        """Test points for WIN (§4 scoring: 3 points)."""
        assert game_logic.get_points(GameResult.WIN.value) == 3

    def test_get_points_draw(self, game_logic):
        """Test points for DRAW (§4 scoring: 1 point)."""
        assert game_logic.get_points(GameResult.DRAW.value) == 1

    def test_get_points_loss(self, game_logic):
        """Test points for LOSS (§4 scoring: 0 points)."""
        assert game_logic.get_points(GameResult.LOSS.value) == 0

    def test_get_points_technical_loss(self, game_logic):
        """Test points for TECHNICAL_LOSS (§4 scoring: 0 points)."""
        assert game_logic.get_points(GameResult.TECHNICAL_LOSS.value) == 0

    @pytest.mark.parametrize("iterations", [100])
    def test_game_outcomes_statistical(self, game_logic, iterations):
        """
        Test game outcomes over multiple iterations (M7.7 requirement).

        Validates:
        - Draws occur when both choose same parity
        - Winners determined correctly based on number parity
        - Roughly 50% even/odd distribution
        """
        draws = 0
        wins_a = 0
        wins_b = 0
        even_numbers = 0
        odd_numbers = 0

        for _ in range(iterations):
            drawn_number = game_logic.draw_random_number()
            if drawn_number in game_logic.even_numbers:
                even_numbers += 1
            else:
                odd_numbers += 1

            # Test different choice combinations
            winner, status_a, status_b = game_logic.determine_winner(
                "P01", "P02", "even", "odd", drawn_number
            )
            if winner == "DRAW":
                draws += 1
            elif winner == "P01":
                wins_a += 1
            else:
                wins_b += 1

        # With different choices, should never draw
        assert draws == 0

        # Roughly even distribution of even/odd numbers (±20 tolerance)
        assert 30 <= even_numbers <= 70
        assert 30 <= odd_numbers <= 70

        # Winners should correlate with number parity
        assert wins_a + wins_b == iterations
