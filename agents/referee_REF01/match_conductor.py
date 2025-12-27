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
    JSONRPCRequest,
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
        self.match_repo = MatchRepository()

        # Load ALL configs (no hardcoding!)
        self.system_config = load_system_config("SHARED/config/system.json")
        self.agents_config = load_agents_config("SHARED/config/agents/agents_config.json")
        self.league_config = load_json_file(f"SHARED/config/leagues/{league_id}.json")
        self.game_type = self.league_config.get("game_type")
        if not self.game_type:
            raise ValueError(f"Missing game_type in league config for {league_id}")
        self.scoring = self.league_config.get("scoring", {})

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
        self.timeout_game_error = self.system_config.network.request_timeout_sec

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
            game_error_timeout=self.timeout_game_error,
        )

    async def conduct_match(
        self,
        match_id: str,
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        message_queue: Optional[asyncio.Queue] = None,
    ) -> Dict[str, Any]:
        """
        Conduct complete match following 6-step protocol (§6 of game rules).

        Thread Safety: async function, uses asyncio.gather() for concurrent calls.

        Args:
            match_id: Match identifier (e.g., "R1M1")
            round_id: Round number
            player_a_id: Player A identifier
            player_b_id: Player B identifier
            conversation_id: Unique conversation ID for this match
            message_queue: Queue for receiving player responses (GAME_JOIN_ACK, CHOOSE_PARITY_RESPONSE)

        ...
        """
        if message_queue is None:
            # For testing or backward compatibility
            message_queue = asyncio.Queue()

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

            # Create initial match record
            self.match_repo.create_match(
                match_id=match_id,
                league_id=self.league_id,
                round_id=round_id,
                game_type=self.game_type,
                player_a_id=player_a_id,
                player_b_id=player_b_id,
                referee_id=self.referee_id,
            )

            # === STEP 1: Send GAME_INVITATION to both players (concurrent) ===
            invitation_results = await self._send_invitations(
                match_id,
                round_id,
                player_a_id,
                player_b_id,
                conversation_id,
                match_transcript,
                message_queue,
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
                match_id, player_a_id, player_b_id, conversation_id, match_transcript, message_queue
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
                match_id,
                round_id,
                player_a_id,
                player_b_id,
                conversation_id,
                match_transcript,
                message_queue,
            )

            # === STEP 4: Receive PARITY_CHOICE responses (30s timeout each) ===
            parity_choices = await self._wait_for_parity_choices(
                match_id, player_a_id, player_b_id, conversation_id, match_transcript, message_queue
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

            # Validate player A choice (E010 INVALID_MOVE)
            if choice_a not in ("even", "odd"):
                log_error(
                    self.std_logger,
                    ErrorCode.INVALID_MOVE,
                    {
                        "match_id": match_id,
                        "round_id": round_id,
                        "player_id": player_a_id,
                        "invalid_choice": str(choice_a),
                        "valid_choices": ["even", "odd"],
                        "game_type": self.game_type,
                        "reason": f"Player {player_a_id} made invalid choice",
                    },
                )
                return self._create_technical_loss_result(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    f"Player {player_a_id} made invalid choice: {choice_a}",
                    match_transcript,
                    offending_player=player_a_id,
                )

            # Validate player B choice (E010 INVALID_MOVE)
            if choice_b not in ("even", "odd"):
                log_error(
                    self.std_logger,
                    ErrorCode.INVALID_MOVE,
                    {
                        "match_id": match_id,
                        "round_id": round_id,
                        "player_id": player_b_id,
                        "invalid_choice": str(choice_b),
                        "valid_choices": ["even", "odd"],
                        "game_type": self.game_type,
                        "reason": f"Player {player_b_id} made invalid choice",
                    },
                )
                return self._create_technical_loss_result(
                    match_id,
                    round_id,
                    player_a_id,
                    player_b_id,
                    f"Player {player_b_id} made invalid choice: {choice_b}",
                    match_transcript,
                    offending_player=player_b_id,
                )

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
                round_id,
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
                    player_a_id: self._points_for_status(player_a_status),
                    player_b_id: self._points_for_status(player_b_status),
                },
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "lifecycle": {"state": match_state.value, "finished_at": self._timestamp()},
                "transcript": match_transcript,
            }

            # Persist match data
            self.match_repo.save(match_id, match_result)

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
        message_queue: asyncio.Queue,
    ) -> Dict[str, bool]:
        """
        Send GAME_INVITATION to both players concurrently.

        Thread Safety: Uses asyncio.gather() for concurrent HTTP calls.

        Returns:
            Dict mapping player_id -> success boolean
        """
        timestamp = self._timestamp()

        # DEBUG: Log auth_token value
        auth_len = len(self.auth_token) if self.auth_token else 0
        self.std_logger.info(
            f"Creating GAME_INVITATION with auth_token length: {auth_len}",
            extra={
                "auth_token_preview": (
                    self.auth_token[:8] + "..."
                    if self.auth_token and len(self.auth_token) >= 8
                    else "EMPTY"
                )
            },
        )

        invitation_a = GameInvitation(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type=self.game_type,
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
            game_type=self.game_type,
            role_in_match="PLAYER_B",
            opponent_id=player_a_id,
        )

        # DEBUG: Log actual invitation data
        dumped = invitation_a.model_dump()
        self.std_logger.info(
            "GAME_INVITATION dumped data",
            extra={
                "has_auth_token": bool(dumped.get("auth_token")),
                "auth_token_length": (
                    len(dumped.get("auth_token", "")) if dumped.get("auth_token") else 0
                ),
            },
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
        # If players responded inline, enqueue their ACKs for timeout logic to consume.
        for player_id, response in zip([player_a_id, player_b_id], results):
            if isinstance(response, Exception):
                continue
            if not isinstance(response, dict):
                continue
            payload = response.get("result", response)
            if isinstance(payload, dict) and payload.get("message_type") == "GAME_JOIN_ACK":
                await message_queue.put(
                    JSONRPCRequest(
                        jsonrpc="2.0",
                        method="GAME_JOIN_ACK",
                        params=payload,
                        id=f"ack-{player_id}",
                    )
                )

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
        message_queue: asyncio.Queue,
    ) -> Dict[str, Optional[GameJoinAck]]:
        """
        Wait for GAME_JOIN_ACK from both players with timeout enforcement (M7.6).
        """

        # We need to demultiplex messages from the single queue to specific players
        # Create futures for each player's response
        player_a_future: asyncio.Future[Optional[GameJoinAck]] = asyncio.Future()
        player_b_future: asyncio.Future[Optional[GameJoinAck]] = asyncio.Future()

        # Start a background task to read from queue and fulfill futures
        async def message_dispatcher():
            try:
                while not (player_a_future.done() and player_b_future.done()):
                    # Wait for next message or until we don't need to wait anymore
                    try:
                        # Use a small timeout to allow checking if futures are done/cancelled
                        msg_request = await asyncio.wait_for(message_queue.get(), timeout=0.1)
                        sender = msg_request.params.get("sender", "")
                        response_conv_id = msg_request.params.get("conversation_id")

                        # E013 CONVERSATION_ID_MISMATCH - Validate conversation thread
                        if response_conv_id != conversation_id:
                            log_error(
                                self.std_logger,
                                ErrorCode.CONVERSATION_ID_MISMATCH,
                                {
                                    "match_id": match_id,
                                    "expected_conversation_id": conversation_id,
                                    "received_conversation_id": response_conv_id,
                                    "sender": sender,
                                    "message_type": msg_request.method,
                                    "reason": "Response from different conversation thread",
                                },
                            )
                            # Ignore mismatched responses, continue waiting
                            continue

                        if sender == f"player:{player_a_id}" and msg_request.method == "GAME_JOIN_ACK":
                            if not player_a_future.done():
                                try:
                                    ack = GameJoinAck(**msg_request.params)
                                    player_a_future.set_result(ack)
                                except Exception as e:
                                    self.std_logger.error(f"Invalid ACK from A: {e}")

                        elif (
                            sender == f"player:{player_b_id}" and msg_request.method == "GAME_JOIN_ACK"
                        ):
                            if not player_b_future.done():
                                try:
                                    ack = GameJoinAck(**msg_request.params)
                                    player_b_future.set_result(ack)
                                except Exception as e:
                                    self.std_logger.error(f"Invalid ACK from B: {e}")

                    except (asyncio.TimeoutError, asyncio.QueueEmpty):
                        continue
            except asyncio.CancelledError:
                pass

        dispatcher_task = asyncio.create_task(message_dispatcher())

        async def get_player_a_response():
            return await player_a_future

        async def get_player_b_response():
            return await player_b_future

        # Wait for both players with timeout enforcement (concurrent)
        player_a_endpoint = self.player_endpoints.get(player_a_id)
        player_b_endpoint = self.player_endpoints.get(player_b_id)

        # Type guard: ensure endpoints exist
        if not player_a_endpoint or not player_b_endpoint:
            dispatcher_task.cancel()
            raise ValueError(f"Missing endpoints for players: {player_a_id}, {player_b_id}")

        try:
            results = await asyncio.gather(
                self.timeout_enforcer.wait_for_join_ack(
                    player_a_id, match_id, conversation_id, get_player_a_response, player_a_endpoint
                ),
                self.timeout_enforcer.wait_for_join_ack(
                    player_b_id, match_id, conversation_id, get_player_b_response, player_b_endpoint
                ),
                return_exceptions=True,
            )
        finally:
            dispatcher_task.cancel()
            try:
                await dispatcher_task
            except asyncio.CancelledError:
                pass

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
        round_id: int,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
        message_queue: asyncio.Queue,
    ) -> None:
        """Send CHOOSE_PARITY_CALL to both players concurrently."""
        timestamp = self._timestamp()

        # Calculate deadline (timestamp + timeout)
        from datetime import datetime, timedelta, timezone

        current_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        deadline_time = current_time + timedelta(seconds=self.timeout_parity_choice)
        deadline = deadline_time.isoformat().replace("+00:00", "Z")

        call_a = ChooseParityCall(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            player_id=player_a_id,
            game_type=self.game_type,
            context={
                "opponent_id": player_b_id,
                "round_id": round_id,
            },
            deadline=deadline,
        )

        call_b = ChooseParityCall(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            player_id=player_b_id,
            game_type=self.game_type,
            context={
                "opponent_id": player_a_id,
                "round_id": round_id,
            },
            deadline=deadline,
        )

        # Send concurrently
        results = await asyncio.gather(
            self._send_to_player(player_a_id, "CHOOSE_PARITY_CALL", call_a.model_dump()),
            self._send_to_player(player_b_id, "CHOOSE_PARITY_CALL", call_b.model_dump()),
            return_exceptions=True,
        )

        log_message_sent(self.std_logger, call_a.model_dump())
        log_message_sent(self.std_logger, call_b.model_dump())
        # If players responded inline, enqueue their parity responses for timeout logic.
        for player_id, response in zip([player_a_id, player_b_id], results):
            if isinstance(response, Exception):
                continue
            if not isinstance(response, dict):
                continue
            payload = response.get("result", response)
            if isinstance(payload, dict) and payload.get("message_type") == "CHOOSE_PARITY_RESPONSE":
                await message_queue.put(
                    JSONRPCRequest(
                        jsonrpc="2.0",
                        method="CHOOSE_PARITY_RESPONSE",
                        params=payload,
                        id=f"parity-{player_id}",
                    )
                )
        transcript.append({"step": "parity_call", "sent_to": [player_a_id, player_b_id]})

    async def _wait_for_parity_choices(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        conversation_id: str,
        transcript: list[Dict[str, Any]],
        message_queue: asyncio.Queue,
    ) -> Dict[str, Optional[Literal["even", "odd"]]]:
        """
        Wait for CHOOSE_PARITY_RESPONSE from both players with timeout enforcement (M7.6).
        """

        # We need to demultiplex messages from the single queue to specific players
        # Create futures for each player's response
        player_a_future: asyncio.Future[Optional[Literal["even", "odd"]]] = asyncio.Future()
        player_b_future: asyncio.Future[Optional[Literal["even", "odd"]]] = asyncio.Future()

        # Start a background task to read from queue and fulfill futures
        async def message_dispatcher():
            try:
                while not (player_a_future.done() and player_b_future.done()):
                    # Wait for next message or until we don't need to wait anymore
                    try:
                        # Use a small timeout to allow checking if futures are done/cancelled
                        msg_request = await asyncio.wait_for(message_queue.get(), timeout=0.1)
                        sender = msg_request.params.get("sender", "")
                        response_conv_id = msg_request.params.get("conversation_id")

                        # E013 CONVERSATION_ID_MISMATCH - Validate conversation thread
                        if response_conv_id != conversation_id:
                            log_error(
                                self.std_logger,
                                ErrorCode.CONVERSATION_ID_MISMATCH,
                                {
                                    "match_id": match_id,
                                    "expected_conversation_id": conversation_id,
                                    "received_conversation_id": response_conv_id,
                                    "sender": sender,
                                    "message_type": msg_request.method,
                                    "reason": "Response from different conversation thread",
                                },
                            )
                            # Ignore mismatched responses, continue waiting
                            continue

                        if (
                            sender == f"player:{player_a_id}"
                            and msg_request.method == "CHOOSE_PARITY_RESPONSE"
                        ):
                            if not player_a_future.done():
                                try:
                                    resp = ChooseParityResponse(**msg_request.params)
                                    player_a_future.set_result(resp)
                                except Exception as e:
                                    self.std_logger.error(f"Invalid Parity Response from A: {e}")

                        elif (
                            sender == f"player:{player_b_id}"
                            and msg_request.method == "CHOOSE_PARITY_RESPONSE"
                        ):
                            if not player_b_future.done():
                                try:
                                    resp = ChooseParityResponse(**msg_request.params)
                                    player_b_future.set_result(resp)
                                except Exception as e:
                                    self.std_logger.error(f"Invalid Parity Response from B: {e}")

                    except (asyncio.TimeoutError, asyncio.QueueEmpty):
                        continue
            except asyncio.CancelledError:
                pass

        dispatcher_task = asyncio.create_task(message_dispatcher())

        async def get_player_a_choice():
            resp = await player_a_future
            return {"parity_choice": resp.parity_choice}

        async def get_player_b_choice():
            resp = await player_b_future
            return {"parity_choice": resp.parity_choice}

        # Wait for both players with timeout enforcement (concurrent)
        player_a_endpoint = self.player_endpoints.get(player_a_id)
        player_b_endpoint = self.player_endpoints.get(player_b_id)

        # Type guard: ensure endpoints exist
        if not player_a_endpoint or not player_b_endpoint:
            dispatcher_task.cancel()
            raise ValueError(f"Missing endpoints for players: {player_a_id}, {player_b_id}")

        try:
            results = await asyncio.gather(
                self.timeout_enforcer.wait_for_parity_choice(
                    player_a_id, match_id, conversation_id, get_player_a_choice, player_a_endpoint
                ),
                self.timeout_enforcer.wait_for_parity_choice(
                    player_b_id, match_id, conversation_id, get_player_b_choice, player_b_endpoint
                ),
                return_exceptions=True,
            )
        finally:
            dispatcher_task.cancel()
            try:
                await dispatcher_task
            except asyncio.CancelledError:
                pass

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
        round_id: int,
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
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type=self.game_type,
            game_result={
                "status": player_a_status,
                "winner_player_id": winner_id if winner_id != "DRAW" else None,
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "points_awarded": self._points_for_status(player_a_status),
            },
        )

        game_over_b = GameOver(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            league_id=self.league_id,
            round_id=round_id,
            match_id=match_id,
            game_type=self.game_type,
            game_result={
                "status": player_b_status,
                "winner_player_id": winner_id if winner_id != "DRAW" else None,
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "player_choices": parity_choices,
                "points_awarded": self._points_for_status(player_b_status),
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
            ValueError: If player endpoint not found (E018)
            Exception: If player unavailable after retries (E006)
        """
        endpoint = self.player_endpoints.get(player_id)
        if not endpoint:
            # E018 INVALID_ENDPOINT - Missing endpoint configuration
            log_error(
                self.std_logger,
                ErrorCode.INVALID_ENDPOINT,
                {
                    "player_id": player_id,
                    "reason": "Player endpoint not found in agents config",
                    "method": method,
                },
            )
            raise ValueError(f"Player {player_id} not found in agents config")

        try:
            # Use async call_with_retry with new signature (M7.9.1)
            # Retry config loaded from system.json by call_with_retry
            response = await call_with_retry(
                endpoint=endpoint,
                method=method,
                params=params,
                timeout=self.system_config.network.request_timeout_sec,
                logger=self.std_logger,
            )
            return response
        except Exception as e:
            # E006 PLAYER_NOT_AVAILABLE - Connection/network failure after retries
            # This happens when player is offline, unreachable, or timing out
            log_error(
                self.std_logger,
                ErrorCode.PLAYER_NOT_AVAILABLE,
                {
                    "player_id": player_id,
                    "endpoint": endpoint,
                    "method": method,
                    "error": str(e),
                    "reason": "Player unreachable after retries",
                },
            )
            raise

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
            game_type=self.game_type,
            result={
                "winner": winner_id,
                "score": {
                    player_a_id: self._points_for_status(player_a_status),
                    player_b_id: self._points_for_status(player_b_status),
                },
                "match_status": "COMPLETED",
                "player_a_status": player_a_status,
                "player_b_status": player_b_status,
            },
        )

        try:
            # Send to League Manager with timeout from system.json
            # Using async call_with_retry with new signature (M7.9.1)
            response = await call_with_retry(
                endpoint=self.league_manager_endpoint,
                method="MATCH_RESULT_REPORT",
                params=match_result_report.model_dump(),
                timeout=self.timeout_match_result,
                logger=self.std_logger,
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
            round_id,
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
                player_a_id: self._points_for_status(player_a_status),
                player_b_id: self._points_for_status(player_b_status),
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
        offending_player: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create technical loss result for both players."""
        result = {
            "match_id": match_id,
            "round_id": round_id,
            "league_id": self.league_id,
            "winner": "NONE",
            "score": {
                player_a_id: self._points_for_status("TECHNICAL_LOSS"),
                player_b_id: self._points_for_status("TECHNICAL_LOSS"),
            },
            "technical_loss": True,
            "reason": reason,
            "lifecycle": {"state": MatchState.FAILED.value, "finished_at": self._timestamp()},
            "transcript": transcript,
        }
        if offending_player:
            result["offending_player"] = offending_player
        return result

    def _points_for_status(self, status: str) -> int:
        """Map result status to points using league config scoring."""
        win_points = self.scoring.get("win_points", 3)
        draw_points = self.scoring.get("draw_points", 1)
        loss_points = self.scoring.get("loss_points", 0)

        if status == "WIN":
            return win_points
        if status == "DRAW":
            return draw_points
        return loss_points

    def _timestamp(self) -> str:
        """Generate ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
