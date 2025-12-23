"""
Even/Odd game logic implementation (Mission 7.7).

Implements winner determination based on drawn number parity using game config.
Complies with doc/game_rules/even_odd.md and SHARED/config/games/games_registry.json.
"""

import secrets
from enum import Enum
from typing import Any, Dict, Literal, Tuple

from league_sdk.config_loader import load_json_file

GAMES_REGISTRY_PATH = "SHARED/config/games/games_registry.json"


class GameResult(str, Enum):
    """Game result outcomes."""

    WIN = "WIN"
    DRAW = "DRAW"
    LOSS = "LOSS"
    TECHNICAL_LOSS = "TECHNICAL_LOSS"


class EvenOddGameLogic:
    """Even/Odd game logic with config-driven rules."""

    def __init__(self):
        """Initialize game logic from games registry configuration."""
        self.game_config = self._load_game_config()
        self.min_number = self.game_config["random_range_min"]
        self.max_number = self.game_config["random_range_max"]
        self.valid_choices = set(self.game_config["valid_choices"])
        self.even_numbers = set(self.game_config["rules"]["parity_definition"]["even"])
        self.odd_numbers = set(self.game_config["rules"]["parity_definition"]["odd"])

    def _load_game_config(self) -> Dict[str, Any]:
        """
        Load Even/Odd game configuration from games registry.

        Returns:
            Game-specific configuration dict

        Raises:
            ValueError: If even_odd game not found in registry
        """
        registry = load_json_file(GAMES_REGISTRY_PATH)
        for game in registry.get("games", []):
            if game.get("game_type") == "even_odd":
                return game.get("game_specific_config", {})
        raise ValueError("even_odd game not found in games registry")

    def draw_random_number(self) -> int:
        """
        Draw cryptographically random number from configured range.

        Uses secrets.randbelow() for cryptographic randomness (§7 of game rules).

        Returns:
            Random integer in range [min_number, max_number] inclusive
        """
        range_size = self.max_number - self.min_number + 1
        return secrets.randbelow(range_size) + self.min_number

    def check_parity(self, number: int) -> Literal["even", "odd"]:
        """
        Determine parity of a number using config-defined sets.

        Args:
            number: Integer to check

        Returns:
            "even" if number is in even set, "odd" if in odd set

        Raises:
            ValueError: If number not in either parity set
        """
        if number in self.even_numbers:
            return "even"
        elif number in self.odd_numbers:
            return "odd"
        else:
            raise ValueError(f"Number {number} not in parity definition sets")

    def validate_choice(self, choice: str) -> bool:
        """
        Validate player's parity choice against config.

        Args:
            choice: Player's parity choice

        Returns:
            True if valid, False otherwise
        """
        return choice in self.valid_choices

    def determine_winner(
        self,
        player_a_id: str,
        player_b_id: str,
        player_a_choice: Literal["even", "odd"],
        player_b_choice: Literal["even", "odd"],
        drawn_number: int,
    ) -> Tuple[str, str, str]:
        """
        Determine match winner based on Even/Odd game rules (§3 of game rules).

        Rules:
        - If both players choose same parity: DRAW (§3.1 Scenario 5-6)
        - Otherwise: Player whose choice matches drawn number parity wins (§3.1 Scenario 1-4)

        Args:
            player_a_id: Player A identifier
            player_b_id: Player B identifier
            player_a_choice: Player A parity choice ("even" or "odd")
            player_b_choice: Player B parity choice ("even" or "odd")
            drawn_number: Randomly drawn number from configured range

        Returns:
            Tuple of (winner_id, player_a_status, player_b_status)
            - winner_id: ID of winning player, or "DRAW" if draw
            - player_a_status: "WIN", "DRAW", or "LOSS"
            - player_b_status: "WIN", "DRAW", or "LOSS"
        """
        # §3.1 Scenario 5-6: Check for draw (both choose same parity)
        if player_a_choice == player_b_choice:
            return ("DRAW", GameResult.DRAW.value, GameResult.DRAW.value)

        # Determine parity of drawn number
        number_parity = self.check_parity(drawn_number)

        # §3.1 Scenario 1-4: Check which player's choice matches the drawn number parity
        if player_a_choice == number_parity:
            return (player_a_id, GameResult.WIN.value, GameResult.LOSS.value)
        else:
            return (player_b_id, GameResult.LOSS.value, GameResult.WIN.value)

    def award_technical_loss(self, offending_player_id: str, opponent_id: str) -> Tuple[str, str, str]:
        """
        Award technical loss per §5 of game rules.

        Args:
            offending_player_id: ID of player who violated rules/timeout
            opponent_id: ID of opponent (receives automatic win)

        Returns:
            Tuple of (winner_id, offender_status, opponent_status)
            - winner_id: opponent_id (automatic win)
            - offender_status: "TECHNICAL_LOSS"
            - opponent_status: "WIN"
        """
        return (opponent_id, GameResult.TECHNICAL_LOSS.value, GameResult.WIN.value)

    def get_points(self, result: str) -> int:
        """
        Get points for a game result per §4 scoring system.

        Args:
            result: Game result ("WIN", "DRAW", "LOSS", or "TECHNICAL_LOSS")

        Returns:
            Points: WIN=3, DRAW=1, LOSS/TECHNICAL_LOSS=0
        """
        if result == GameResult.WIN.value:
            return 3
        elif result == GameResult.DRAW.value:
            return 1
        else:  # LOSS or TECHNICAL_LOSS
            return 0
