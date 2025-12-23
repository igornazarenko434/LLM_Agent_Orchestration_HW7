"""
Timeout enforcement for referee agent (Mission 7.6).

Implements timeout handling with retry logic and GAME_ERROR sending.
All timeouts and retry policy loaded from system.json (no hardcoding).
"""

import asyncio
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Any, Callable, Dict, Optional

from league_sdk.logger import log_error, log_message_sent
from league_sdk.protocol import ErrorCode, GameError
from league_sdk.retry import call_with_retry


class TimeoutEnforcer:
    """
    Enforces timeouts for player responses with retry logic.

    Per §6 game rules and M7.6 requirements:
    - GAME_JOIN_ACK: 5s timeout, retry 3 times with backoff
    - CHOOSE_PARITY_RESPONSE: 30s timeout, retry 3 times with backoff
    - Awards technical loss on max retries exceeded
    - Sends GAME_ERROR (E001) to offending player with retry info
    """

    def __init__(
        self,
        referee_id: str,
        auth_token: str,
        std_logger: Logger,
        timeout_join_ack: int,
        timeout_parity_choice: int,
        max_retries: int,
        initial_delay: float,
        max_delay: float,
    ):
        """
        Initialize timeout enforcer.

        Args:
            referee_id: Referee agent ID
            auth_token: Referee's auth token
            std_logger: Logger instance
            timeout_join_ack: Timeout for join ACK (from system.json)
            timeout_parity_choice: Timeout for parity choice (from system.json)
            max_retries: Max retry attempts (from system.json)
            initial_delay: Initial backoff delay (from system.json)
            max_delay: Max backoff delay (from system.json)
        """
        self.referee_id = referee_id
        self.auth_token = auth_token
        self.std_logger = std_logger
        self.timeout_join_ack = timeout_join_ack
        self.timeout_parity_choice = timeout_parity_choice
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay

    async def wait_for_join_ack(
        self,
        player_id: str,
        match_id: str,
        conversation_id: str,
        response_getter: Callable[[], Any],
        player_endpoint: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for GAME_JOIN_ACK with 5s timeout and retry logic.

        Per M7.6 requirements:
        - 5s timeout (from system.json)
        - Retry 3 times with exponential backoff
        - Send GAME_ERROR (E001) on each timeout
        - Return None on max retries exceeded (triggers technical loss)

        Args:
            player_id: Player identifier
            match_id: Match identifier
            conversation_id: Conversation ID
            response_getter: Async function to get player response
            player_endpoint: Player endpoint for GAME_ERROR sending

        Returns:
            Player's join ACK response dict, or None if timeout
        """
        return await self._wait_with_retry(
            player_id=player_id,
            match_id=match_id,
            conversation_id=conversation_id,
            response_getter=response_getter,
            player_endpoint=player_endpoint,
            timeout=self.timeout_join_ack,
            action_required="GAME_JOIN_ACK",
            error_description="Player failed to acknowledge game invitation within 5s",
        )

    async def wait_for_parity_choice(
        self,
        player_id: str,
        match_id: str,
        conversation_id: str,
        response_getter: Callable[[], Any],
        player_endpoint: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for CHOOSE_PARITY_RESPONSE with 30s timeout and retry logic.

        Per M7.6 requirements:
        - 30s timeout (from system.json)
        - Retry 3 times with exponential backoff
        - Send GAME_ERROR (E001) on each timeout
        - Return None on max retries exceeded (triggers technical loss)

        Args:
            player_id: Player identifier
            match_id: Match identifier
            conversation_id: Conversation ID
            response_getter: Async function to get player response
            player_endpoint: Player endpoint for GAME_ERROR sending

        Returns:
            Player's parity choice response dict, or None if timeout
        """
        return await self._wait_with_retry(
            player_id=player_id,
            match_id=match_id,
            conversation_id=conversation_id,
            response_getter=response_getter,
            player_endpoint=player_endpoint,
            timeout=self.timeout_parity_choice,
            action_required="CHOOSE_PARITY_RESPONSE",
            error_description="Player failed to submit parity choice within 30s",
        )

    async def _wait_with_retry(
        self,
        player_id: str,
        match_id: str,
        conversation_id: str,
        response_getter: Callable[[], Any],
        player_endpoint: str,
        timeout: int,
        action_required: str,
        error_description: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generic wait with retry and GAME_ERROR sending.

        Implements exponential backoff per system.json retry_policy.

        Args:
            player_id: Player identifier
            match_id: Match identifier
            conversation_id: Conversation ID
            response_getter: Async function to get player response
            player_endpoint: Player endpoint for GAME_ERROR
            timeout: Timeout in seconds
            action_required: Action name for GAME_ERROR
            error_description: Error description for GAME_ERROR

        Returns:
            Response dict or None on max retries exceeded
        """
        retry_count = 0
        backoff_delay = self.initial_delay

        while retry_count <= self.max_retries:
            try:
                # Try to get response with timeout
                response = await asyncio.wait_for(
                    response_getter(),
                    timeout=timeout,
                )

                # Success - log and return
                self.std_logger.info(
                    f"Received {action_required} from {player_id}",
                    extra={
                        "player_id": player_id,
                        "match_id": match_id,
                        "action": action_required,
                        "retry_count": retry_count,
                    },
                )
                return response

            except (asyncio.TimeoutError, TimeoutError) as exc:
                retry_count += 1

                # Log timeout event with error code E001
                timeout_details = {
                    "player_id": player_id,
                    "match_id": match_id,
                    "conversation_id": conversation_id,
                    "action_required": action_required,
                    "timeout_seconds": timeout,
                    "retry_count": retry_count,
                    "max_retries": self.max_retries,
                }
                log_error(self.std_logger, ErrorCode.TIMEOUT_ERROR, timeout_details)

                # Check if max retries exceeded
                if retry_count > self.max_retries:
                    self.std_logger.error(
                        f"Max retries exceeded for {player_id} on {action_required}",
                        extra=timeout_details,
                    )
                    return None  # Triggers technical loss

                # Send GAME_ERROR (E001) to player
                await self._send_game_error(
                    player_id=player_id,
                    player_endpoint=player_endpoint,
                    match_id=match_id,
                    conversation_id=conversation_id,
                    action_required=action_required,
                    error_description=error_description,
                    retry_count=retry_count,
                )

                # Wait before retry with exponential backoff
                self.std_logger.info(
                    f"Retrying {action_required} for {player_id} after {backoff_delay}s",
                    extra={"backoff_delay": backoff_delay, "retry_count": retry_count},
                )
                await asyncio.sleep(backoff_delay)

                # Increase backoff delay exponentially
                backoff_delay = min(backoff_delay * 2, self.max_delay)

        return None  # Should not reach here, but safety fallback

    async def _send_game_error(
        self,
        player_id: str,
        player_endpoint: str,
        match_id: str,
        conversation_id: str,
        action_required: str,
        error_description: str,
        retry_count: int,
    ) -> None:
        """
        Send GAME_ERROR (E001) to player who timed out.

        Per protocol: Informs player of timeout and provides retry info.

        Args:
            player_id: Player who timed out
            player_endpoint: Player's endpoint
            match_id: Match identifier
            conversation_id: Conversation ID
            action_required: Required action that timed out
            error_description: Error description
            retry_count: Current retry count
        """
        # Generate ISO 8601 UTC timestamp without microseconds (protocol requirement)
        now = datetime.now(timezone.utc)
        timestamp = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        # Calculate next retry time
        next_retry_delay = min(self.initial_delay * (2 ** (retry_count - 1)), self.max_delay)
        next_retry_time = now + timedelta(seconds=next_retry_delay)
        next_retry_at = next_retry_time.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        # Build GAME_ERROR message per protocol
        game_error = GameError(
            sender=f"referee:{self.referee_id}",
            timestamp=timestamp,
            conversation_id=conversation_id,
            auth_token=self.auth_token,
            match_id=match_id,
            error_code=ErrorCode.TIMEOUT_ERROR,  # ErrorCode is already string enum
            error_description=error_description,
            affected_player=player_id,
            action_required=action_required,
            retry_info={
                "retry_count": retry_count,
                "max_retries": self.max_retries,
                "next_retry_at": next_retry_at,
                "backoff_delay_sec": next_retry_delay,
            },
            consequence=(f"Technical loss if max retries ({self.max_retries}) exceeded"),
        )

        # Send GAME_ERROR to player
        payload = {
            "jsonrpc": "2.0",
            "method": "GAME_ERROR",
            "params": game_error.model_dump(),
            "id": 1,
        }

        try:
            # Use call_with_retry but with max_retries=1 (don't retry GAME_ERROR sending)
            await call_with_retry(
                player_endpoint,
                payload,
                logger=self.std_logger,
                max_retries=1,
                timeout=5,  # Short timeout for error notification
            )

            log_message_sent(self.std_logger, game_error.model_dump())

            self.std_logger.info(
                f"Sent GAME_ERROR (E001) to {player_id}",
                extra={
                    "player_id": player_id,
                    "match_id": match_id,
                    "error_code": ErrorCode.TIMEOUT_ERROR.value,
                    "retry_count": retry_count,
                },
            )
        except Exception as exc:
            # Log error but don't fail the match
            self.std_logger.warning(
                f"Failed to send GAME_ERROR to {player_id}: {exc}",
                extra={"player_id": player_id, "error": str(exc)},
            )
