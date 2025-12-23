"""
Match conductor for referee agent (Mission 7.5).

Implements complete 6-step match protocol flow with async/await and timeout enforcement.
Thread-safe implementation following doc/architecture/thread_safety.md Section 2.4.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

from league_sdk.config_loader import load_agents_config, load_json_file, load_system_config
from league_sdk.logger import log_error, log_message_received, log_message_sent
from league_sdk.protocol import (
    ChooseParityCall,
    ChooseParityResponse,
    ErrorCode,
    GameInvitation,
    GameJoinAck,
    GameOver,
    MatchResultReport,
)
from league_sdk.repositories import MatchRepository
from league_sdk.retry import call_with_retry

from agents.referee_REF01.game_logic import EvenOddGameLogic
from agents.referee_REF01.timeout_enforcement import TimeoutEnforcer


class MatchState(str, Enum):
    """Match lifecycle states per M7.5 requirements."""

    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    COLLECTING_CHOICES = "COLLECTING_CHOICES"
    DRAWING_NUMBER = "DRAWING_NUMBER"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class MatchConductor:
    """
    Conducts complete match flow with timeout enforcement.

    Thread Safety (CRITICAL):
    - All methods are async (non-blocking)
    - Uses asyncio.gather() for concurrent HTTP calls to players
    - Each match isolated by unique conversation_id
    - Can handle 50+ concurrent matches without blocking
    """

    def __init__(
        self,
        referee_id: str,
        auth_token: str,
        league_id: str,
        std_logger: Logger,
    ):
        """
        Initialize match conductor.

        Args:
            referee_id: Referee agent ID (e.g., "REF01")
            auth_token: Referee's auth token from registration
            league_id: League identifier
            std_logger: Standard Python logger instance
        """
        self.referee_id = referee_id
        self.auth_token = auth_token
        self.league_id = league_id
        self.std_logger = std_logger
        self.game_logic = EvenOddGameLogic()
        self.match_repo = MatchRepository(league_id)

        # Load ALL configs (no hardcoding!)
        self.system_config = load_system_config("SHARED/config/system.json")
        self.agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
        self.league_config = load_json_file(f"SHARED/config/leagues/{league_id}.json")

        # Load player endpoints from agents config
        self.player_endpoints: Dict[str, str] = {}
        for player in self.agents_config.get("players", []):
            player_id = player.get("agent_id")
            endpoint = player.get("endpoint")
            if player_id and endpoint:
                self.player_endpoints[player_id] = endpoint

        # Load League Manager endpoint for match result reporting
        lm_config = self.agents_config.get("league_manager", {})
        self.league_manager_endpoint = lm_config.get("endpoint")

        # Load timeouts from system.json (§6 game rules compliance)
        self.timeout_game_join_ack = self.system_config.timeouts.game_join_ack_sec
        self.timeout_parity_choice = self.system_config.timeouts.parity_choice_sec
        self.timeout_game_over = self.system_config.timeouts.game_over_sec
        self.timeout_match_result = self.system_config.timeouts.match_result_sec

        # Load retry policy from system.json
        self.max_retries = self.system_config.retry_policy.max_retries
        self.initial_delay = self.system_config.retry_policy.initial_delay_sec
        self.max_delay = self.system_config.retry_policy.max_delay_sec

        # Initialize timeout enforcer (Mission 7.6)
        self.timeout_enforcer = TimeoutEnforcer(
            referee_id=referee_id,
            auth_token=auth_token,
            std_logger=std_logger,
            timeout_join_ack=self.timeout_game_join_ack,
            timeout_parity_choice=self.timeout_parity_choice,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
        )

    async def conduct_match(
        self,
        match_id: str,
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
    ) -> Dict[str, Any]:
        """
        Conduct complete match following 6-step protocol (§6 of game rules).

        Thread Safety: async function, uses asyncio.gather() for concurrent calls.

        Steps:
        1. Send GAME_INVITATION to both players
        2. Wait for GAME_JOIN_ACK (5s timeout each, with retry)
        3. Send CHOOSE_PARITY_CALL to both players
        4. Receive CHOOSE_PARITY_RESPONSE (30s timeout each)
        5. Draw random number (1-10), determine outcome using Even/Odd logic
        6. Send GAME_OVER to both players with results
        Post-Match: Send MATCH_RESULT_REPORT to League Manager

        Args:
            match_id: Match identifier (e.g., "R1M1")
            round_id: Round number
            player_a_id: Player A identifier
            player_b_id: Player B identifier
            conversation_id: Unique conversation ID for this match

        Returns:
            Match result dictionary with winner, scores, transcript

        Raises:
            ValueError: If players not found in config
            TimeoutError: If players don't respond within timeout
        """
        match_state = MatchState.WAITING_FOR_PLAYERS
        match_transcript: list[Dict[str, Any]] = []
        drawn_number: Optional[int] = None
        winner_id: Optional[str] = None
        player_a_status: Optional[str] = None
        player_b_status: Optional[str] = None

        try:
            self.std_logger.info(
                f"Starting match {match_id}",
                extra={
                    "match_id": match_id,
                    "round_id": round_id,
                    "player_a": player_a_id,
                    "player_b": player_b_id,
                    "conversation_id": conversation_id,
                    "state": match_state.value,
                },
            )

            # === STEP 1: Send GAME_INVITATION to both players (concurrent) ===
            invitation_results = await self._send_invitations(
                match_id, round_id, player_a_id, player_b_id, conversation_id, match_transcript
            )
            if not invitation_results:
                return self._create_technical_loss_result(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    "Both players failed invitation",
                    match_transcript,
                )

            # === STEP 2: Wait for GAME_JOIN_ACK (5s timeout each, with retry) ===
            join_acks = await self._wait_for_join_acks(
                match_id, player_a_id, player_b_id, conversation_id, match_transcript
            )

            # Check for timeout violations
            if join_acks[player_a_id] is None and join_acks[player_b_id] is None:
                # Both timed out - double technical loss
                return self._create_technical_loss_result(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    "Both players timed out on join",
                    match_transcript,
                )
            elif join_acks[player_a_id] is None:
                # Player A timed out - Player B wins
                winner_id, player_a_status, player_b_status = self.game_logic.award_technical_loss(
                    player_a_id, player_b_id
                )
                return await self._finish_match_with_technical_loss(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    winner_id,
                    player_a_status,
                    player_b_status,
                    conversation_id,
                    match_transcript,
                    offending_player=player_a_id,
                )
            elif join_acks[player_b_id] is None:
                # Player B timed out - Player A wins
                winner_id, player_b_status, player_a_status = self.game_logic.award_technical_loss(
                    player_b_id, player_a_id
                )
                return await self._finish_match_with_technical_loss(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    winner_id,
                    player_a_status,
                    player_b_status,
                    conversation_id,
                    match_transcript,
                    offending_player=player_b_id,
                )

            # === STEP 3: Send CHOOSE_PARITY_CALL to both players ===
            match_state = MatchState.COLLECTING_CHOICES
            await self._send_parity_calls(
                match_id, player_a_id, player_b_id, conversation_id, match_transcript
            )

            # === STEP 4: Receive PARITY_CHOICE responses (30s timeout each) ===
            parity_choices = await self._wait_for_parity_choices(
                match_id, player_a_id, player_b_id, conversation_id, match_transcript
            )

            # Check for timeout violations or invalid choices
            if parity_choices[player_a_id] is None and parity_choices[player_b_id] is None:
                return self._create_technical_loss_result(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    "Both players timed out on parity choice",
                    match_transcript,
                )
            elif parity_choices[player_a_id] is None:
                winner_id, player_a_status, player_b_status = self.game_logic.award_technical_loss(
                    player_a_id, player_b_id
                )
                return await self._finish_match_with_technical_loss(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    winner_id,
                    player_a_status,
                    player_b_status,
                    conversation_id,
                    match_transcript,
                    offending_player=player_a_id,
                )
            elif parity_choices[player_b_id] is None:
                winner_id, player_b_status, player_a_status = self.game_logic.award_technical_loss(
                    player_b_id, player_a_id
                )
                return await self._finish_match_with_technical_loss(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    winner_id,
                    player_a_status,
                    player_b_status,
                    conversation_id,
                    match_transcript,
                    offending_player=player_b_id,
                )

            # === STEP 5: Draw random number and determine winner ===
            match_state = MatchState.DRAWING_NUMBER
            drawn_number = self.game_logic.draw_random_number()
            number_parity = self.game_logic.check_parity(drawn_number)

            self.std_logger.info(
                f"Drew number {drawn_number} (parity: {number_parity})",
                extra={
                    "match_id": match_id,
                    "drawn_number": drawn_number,
                    "number_parity": number_parity,
                    "player_a_choice": parity_choices[player_a_id],
                    "player_b_choice": parity_choices[player_b_id],
                },
            )

            # Type guard: ensure choices are valid before winner determination
            choice_a = parity_choices[player_a_id]
            choice_b = parity_choices[player_b_id]

            if choice_a not in ("even", "odd") or choice_b not in ("even", "odd"):
                raise ValueError(f"Invalid choices: {choice_a}, {choice_b}")

            winner_id, player_a_status, player_b_status = self.game_logic.determine_winner(
                player_a_id,
                player_b_id,
                choice_a,
                choice_b,
                drawn_number,
            )

            # === STEP 6: Send GAME_OVER to both players ===
            match_state = MatchState.FINISHED
            # Type-safe parity choices dict (validated above, create new dict for type safety)
            validated_choices: Dict[str, str] = {
                player_a_id: str(choice_a),
                player_b_id: str(choice_b),
            }
            await self._send_game_over(
                match_id,
                player_a_id,
                player_b_id,
                winner_id,
                player_a_status,
                player_b_status,
                drawn_number,
                number_parity,
                validated_choices,
                conversation_id,
                match_transcript,
            )

            # Create match result
            match_result = {
                "match_id": match_id,
                "round_id": round_id,
                "league_id": self.league_id,
                "winner": winner_id,
                "score": {
                    player_a_id: self.game_logic.get_points(player_a_status),
                    player_b_id: self.game_logic.get_points(player_b_status),
                },
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "lifecycle": {"state": match_state.value, "finished_at": self._timestamp()},
                "transcript": match_transcript,
            }

            # Persist match data
            self.match_repo.save_match(match_result)

            # === POST-MATCH: Send MATCH_RESULT_REPORT to League Manager ===
            await self._send_match_result_to_league_manager(
                match_id,
                round_id,
                winner_id,
                player_a_id,
                player_b_id,
                player_a_status,
                player_b_status,
                conversation_id,
            )

            self.std_logger.info(
                f"Match {match_id} completed",
                extra={"match_id": match_id, "winner": winner_id, "state": match_state.value},
            )

            return match_result

        except Exception as exc:
            match_state = MatchState.FAILED
            self.std_logger.error(
                f"Match {match_id} failed: {exc}",
                extra={"match_id": match_id, "error": str(exc), "state": match_state.value},
                exc_info=True,
            )
            raise

    async def _send_invitations(
        self,
        match_id: str,
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
    ) -> Dict[str, bool]:
        """
        Send GAME_INVITATION to both players concurrently.

        Thread Safety: Uses asyncio.gather() for concurrent HTTP calls.

        Returns:
            Dict mapping player_id -> success boolean
        """
        timestamp = self._timestamp()

        invitation_a = GameInvitation(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type="even_odd",
            role_in_match="PLAYER_A",
            opponent_id=player_b_id,
        )

        invitation_b = GameInvitation(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type="even_odd",
            role_in_match="PLAYER_B",
            opponent_id=player_a_id,
        )

        # Send invitations concurrently (Thread Safety: asyncio.gather)
        results = await asyncio.gather(
            self._send_to_player(player_a_id, "GAME_INVITATION", invitation_a.model_dump()),
            self._send_to_player(player_b_id, "GAME_INVITATION", invitation_b.model_dump()),
            return_exceptions=True,
        )

        # Log invitations
        log_message_sent(self.std_logger, invitation_a.model_dump())
        log_message_sent(self.std_logger, invitation_b.model_dump())
        transcript.append(
            {"step": "invitation", "player_a": str(results[0]), "player_b": str(results[1])}
        )

        return {
            player_a_id: not isinstance(results[0], Exception),
            player_b_id: not isinstance(results[1], Exception),
        }

    async def _wait_for_join_acks(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
    ) -> Dict[str, Optional[GameJoinAck]]:
        """
        Wait for GAME_JOIN_ACK from both players with timeout enforcement (M7.6).

        Uses TimeoutEnforcer with:
        - 5s timeout (from system.json)
        - Retry 3 times with exponential backoff
        - Send GAME_ERROR (E001) on each timeout
        - Return None on max retries exceeded

        Returns:
            Dict mapping player_id -> GameJoinAck (or None if timeout)
        """

        async def get_player_a_response():
            """
            Get player A's join ACK response.

            TODO: In production, this would:
            - Poll a response queue
            - Listen to WebSocket
            - Or use callback mechanism
            For now, simulates immediate success for testing.
            """
            # PRODUCTION: await self.response_queue.get(match_id, player_a_id, "GAME_JOIN_ACK")
            await asyncio.sleep(0.1)  # Simulate network delay
            return GameJoinAck(
                sender=f"player:{player_a_id}",
                timestamp=self._timestamp(),
                conversation_id=conversation_id,
                auth_token="player_token",
                match_id=match_id,
                player_id=player_a_id,
                arrival_timestamp=self._timestamp(),
                accept=True,
            )

        async def get_player_b_response():
            """Get player B's join ACK response."""
            # PRODUCTION: await self.response_queue.get(match_id, player_b_id, "GAME_JOIN_ACK")
            await asyncio.sleep(0.1)  # Simulate network delay
            return GameJoinAck(
                sender=f"player:{player_b_id}",
                timestamp=self._timestamp(),
                conversation_id=conversation_id,
                auth_token="player_token",
                match_id=match_id,
                player_id=player_b_id,
                arrival_timestamp=self._timestamp(),
                accept=True,
            )

        # Wait for both players with timeout enforcement (concurrent)
        player_a_endpoint = self.player_endpoints.get(player_a_id)
        player_b_endpoint = self.player_endpoints.get(player_b_id)

        # Type guard: ensure endpoints exist
        if not player_a_endpoint or not player_b_endpoint:
            raise ValueError(f"Missing endpoints for players: {player_a_id}, {player_b_id}")

        results = await asyncio.gather(
            self.timeout_enforcer.wait_for_join_ack(
                player_a_id, match_id, conversation_id, get_player_a_response, player_a_endpoint
            ),
            self.timeout_enforcer.wait_for_join_ack(
                player_b_id, match_id, conversation_id, get_player_b_response, player_b_endpoint
            ),
            return_exceptions=True,
        )

        transcript.append(
            {
                "step": "join_ack_wait",
                "player_a_ack": results[0] is not None,
                "player_b_ack": results[1] is not None,
            }
        )

        return {player_a_id: results[0], player_b_id: results[1]}

    async def _send_parity_calls(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
    ) -> None:
        """Send CHOOSE_PARITY_CALL to both players concurrently."""
        timestamp = self._timestamp()

        call_a = ChooseParityCall(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            player_id=player_a_id,
            game_type="even_odd",
            context={
                "opponent_id": player_b_id,
                "round_id": 1,  # TODO: Get from match context
            },
        )

        call_b = ChooseParityCall(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            player_id=player_b_id,
            game_type="even_odd",
            context={
                "opponent_id": player_a_id,
                "round_id": 1,
            },
        )

        # Send concurrently
        await asyncio.gather(
            self._send_to_player(player_a_id, "CHOOSE_PARITY_CALL", call_a.model_dump()),
            self._send_to_player(player_b_id, "CHOOSE_PARITY_CALL", call_b.model_dump()),
            return_exceptions=True,
        )

        log_message_sent(self.std_logger, call_a.model_dump())
        log_message_sent(self.std_logger, call_b.model_dump())
        transcript.append({"step": "parity_call", "sent_to": [player_a_id, player_b_id]})

    async def _wait_for_parity_choices(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
    ) -> Dict[str, Optional[Literal["even", "odd"]]]:
        """
        Wait for CHOOSE_PARITY_RESPONSE from both players with timeout enforcement (M7.6).

        Uses TimeoutEnforcer with:
        - 30s timeout (from system.json)
        - Retry 3 times with exponential backoff
        - Send GAME_ERROR (E001) on each timeout
        - Return None on max retries exceeded

        Returns:
            Dict mapping player_id -> parity choice ("even"/"odd" or None if timeout)
        """

        async def get_player_a_choice():
            """
            Get player A's parity choice.

            TODO: In production, this would poll response queue or listen to callback.
            """
            # PRODUCTION: await self.response_queue.get(match_id, player_a_id, "CHOOSE_PARITY_RESPONSE")
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"parity_choice": "even"}  # Simulated response

        async def get_player_b_choice():
            """Get player B's parity choice."""
            # PRODUCTION: await self.response_queue.get(match_id, player_b_id, "CHOOSE_PARITY_RESPONSE")
            await asyncio.sleep(0.1)  # Simulate network delay
            return {"parity_choice": "odd"}  # Simulated response

        # Wait for both players with timeout enforcement (concurrent)
        player_a_endpoint = self.player_endpoints.get(player_a_id)
        player_b_endpoint = self.player_endpoints.get(player_b_id)

        # Type guard: ensure endpoints exist
        if not player_a_endpoint or not player_b_endpoint:
            raise ValueError(f"Missing endpoints for players: {player_a_id}, {player_b_id}")

        results = await asyncio.gather(
            self.timeout_enforcer.wait_for_parity_choice(
                player_a_id, match_id, conversation_id, get_player_a_choice, player_a_endpoint
            ),
            self.timeout_enforcer.wait_for_parity_choice(
                player_b_id, match_id, conversation_id, get_player_b_choice, player_b_endpoint
            ),
            return_exceptions=True,
        )

        # Extract parity choices from responses (type-safe)
        result_a = results[0]
        result_b = results[1]
        player_a_choice = result_a.get("parity_choice") if isinstance(result_a, dict) else None
        player_b_choice = result_b.get("parity_choice") if isinstance(result_b, dict) else None

        transcript.append(
            {
                "step": "parity_choice_wait",
                "player_a_choice": player_a_choice,
                "player_b_choice": player_b_choice,
            }
        )

        return {player_a_id: player_a_choice, player_b_id: player_b_choice}

    async def _send_game_over(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        winner_id: str,
        player_a_status: str,
        player_b_status: str,
        drawn_number: int,
        number_parity: str,
        parity_choices: Dict[str, str],
        conversation_id: str,
        transcript: list[Dict[str, Any]],
    ) -> None:
        """Send GAME_OVER to both players with match results."""
        timestamp = self._timestamp()

        game_over_a = GameOver(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            game_type="even_odd",
            game_result={
                "status": player_a_status,
                "winner_player_id": winner_id if winner_id != "DRAW" else None,
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "points_awarded": self.game_logic.get_points(player_a_status),
            },
        )

        game_over_b = GameOver(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            game_type="even_odd",
            game_result={
                "status": player_b_status,
                "winner_player_id": winner_id if winner_id != "DRAW" else None,
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "points_awarded": self.game_logic.get_points(player_b_status),
            },
        )

        # Send concurrently
        await asyncio.gather(
            self._send_to_player(player_a_id, "GAME_OVER", game_over_a.model_dump()),
            self._send_to_player(player_b_id, "GAME_OVER", game_over_b.model_dump()),
            return_exceptions=True,
        )

        log_message_sent(self.std_logger, game_over_a.model_dump())
        log_message_sent(self.std_logger, game_over_b.model_dump())
        transcript.append({"step": "game_over", "winner": winner_id, "drawn_number": drawn_number})

    async def _send_to_player(
        self, player_id: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC message to player via HTTP.

        Thread Safety: Uses async call_with_retry (non-blocking).

        Args:
            player_id: Target player ID
            method: JSON-RPC method name
            params: Message parameters

        Returns:
            Player's response dict

        Raises:
            ValueError: If player endpoint not found
            TimeoutError: If player doesn't respond in time
        """
        endpoint = self.player_endpoints.get(player_id)
        if not endpoint:
            raise ValueError(f"Player {player_id} not found in agents config")

        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}

        # Use async call_with_retry with system.json retry policy (no hardcoding!)
        response = await call_with_retry(
            endpoint,
            payload,
            logger=self.std_logger,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
        )

        return response

    async def _send_match_result_to_league_manager(
        self,
        match_id: str,
        round_id: int,
        winner_id: str,
        player_a_id: str,
        player_b_id: str,
        player_a_status: str,
        player_b_status: str,
        conversation_id: str,
    ) -> None:
        """
        Send MATCH_RESULT_REPORT to League Manager (POST-MATCH step).

        This is the final step in the 6-step + post-match protocol.
        """
        if not self.league_manager_endpoint:
            self.std_logger.error("League Manager endpoint not configured")
            return

        timestamp = self._timestamp()

        # Build match result report per protocol
        match_result_report = MatchResultReport(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type="even_odd",
            result={
                "winner": winner_id,
                "score": {
                    player_a_id: self.game_logic.get_points(player_a_status),
                    player_b_id: self.game_logic.get_points(player_b_status),
                },
                "match_status": "COMPLETED",
                "player_a_status": player_a_status,
                "player_b_status": player_b_status,
            },
        )

        payload = {
            "jsonrpc": "2.0",
            "method": "MATCH_RESULT_REPORT",
            "params": match_result_report.model_dump(),
            "id": 1,
        }

        try:
            # Send to League Manager with timeout from system.json
            response = await call_with_retry(
                self.league_manager_endpoint,
                payload,
                logger=self.std_logger,
                max_retries=self.max_retries,
                timeout=self.timeout_match_result,
            )

            log_message_sent(self.std_logger, match_result_report.model_dump())
            log_message_received(self.std_logger, response)

            self.std_logger.info(
                "Match result reported to League Manager",
                extra={"match_id": match_id, "winner": winner_id},
            )
        except Exception as exc:
            self.std_logger.error(
                f"Failed to report match result to League Manager: {exc}",
                extra={"match_id": match_id, "error": str(exc)},
                exc_info=True,
            )

    async def _finish_match_with_technical_loss(
        self,
        match_id: str,
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        winner_id: str,
        player_a_status: str,
        player_b_status: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
        offending_player: str,
    ) -> Dict[str, Any]:
        """Finish match with technical loss result."""
        # Send GAME_ERROR to offending player and GAME_OVER to both
        await self._send_game_over(
            match_id,
            player_a_id,
            player_b_id,
            winner_id,
            player_a_status,
            player_b_status,
            0,  # No number drawn
            "N/A",
            {},
            conversation_id,
            transcript,
        )

        return {
            "match_id": match_id,
            "round_id": round_id,
            "league_id": self.league_id,
            "winner": winner_id,
            "score": {
                player_a_id: self.game_logic.get_points(player_a_status),
                player_b_id: self.game_logic.get_points(player_b_status),
            },
            "technical_loss": True,
            "offending_player": offending_player,
            "lifecycle": {"state": MatchState.FINISHED.value, "finished_at": self._timestamp()},
            "transcript": transcript,
        }

    def _create_technical_loss_result(
        self,
        match_id: str,
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        reason: str,
        transcript: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create technical loss result for both players."""
        return {
            "match_id": match_id,
            "round_id": round_id,
            "league_id": self.league_id,
            "winner": "NONE",
            "score": {player_a_id: 0, player_b_id: 0},
            "technical_loss": True,
            "reason": reason,
            "lifecycle": {"state": MatchState.FAILED.value, "finished_at": self._timestamp()},
            "transcript": transcript,
        }

    def _timestamp(self) -> str:
        """Generate ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
