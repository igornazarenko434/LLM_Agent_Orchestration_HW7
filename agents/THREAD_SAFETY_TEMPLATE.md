# Thread Safety Implementation Template for Mission 7 Agents

This template shows how to implement Referee and League Manager agents following thread safety best practices established in Mission 2.6.

## Referee Agent Template (M7.5-M7.8)

```python
"""
Referee Agent - Thread-Safe Match Conductor

Thread Safety Features:
- Async/await for all HTTP calls (non-blocking)
- asyncio.gather() for concurrent player communication
- Unique conversation_id per match (isolation)
- Can handle 50+ concurrent matches
"""

import asyncio
from typing import Dict, Any
from league_sdk import call_with_retry, CircuitBreaker
from agents.base import BaseAgent


class RefereeAgent(BaseAgent):
    def __init__(self, referee_id: str):
        super().__init__(agent_id=referee_id, agent_type="referee")
        # Circuit breaker already has asyncio.Lock (thread-safe)

    async def conduct_match(self, match_id: str, player_a: str, player_b: str):
        """
        Conduct match asynchronously (non-blocking).

        Thread Safety:
        - Async function (doesn't block event loop)
        - Uses asyncio.gather() for concurrent operations
        - Isolated by match_id/conversation_id
        """
        conversation_id = self._conversation_id()

        # ✅ Step 1-2: Send invitations concurrently
        try:
            invitations = await asyncio.gather(
                self.send_invitation(player_a, match_id, conversation_id),
                self.send_invitation(player_b, match_id, conversation_id),
                return_exceptions=True  # Don't fail if one invitation fails
            )
        except Exception as e:
            self.logger.error(f"Match {match_id} invitation failed: {e}")
            return

        # ✅ Step 3-4: Collect parity choices concurrently (with timeout)
        try:
            choices = await asyncio.gather(
                self.request_parity_choice(player_a, match_id, timeout=30),
                self.request_parity_choice(player_b, match_id, timeout=30),
                return_exceptions=True
            )
        except Exception as e:
            self.logger.error(f"Match {match_id} parity collection failed: {e}")
            return

        # ✅ Step 5: Determine winner
        result = self.determine_winner(choices)

        # ✅ Step 6: Send GAME_OVER concurrently
        await asyncio.gather(
            self.send_game_over(player_a, match_id, result),
            self.send_game_over(player_b, match_id, result),
            return_exceptions=True
        )

        # ✅ Post-match: Report to League Manager (async)
        await call_with_retry(
            endpoint=self.league_manager_endpoint(),
            method="MATCH_RESULT_REPORT",
            params=result,
            timeout=self.config.network.request_timeout_sec,
            logger=self.std_logger,
            circuit_breaker=self.circuit_breaker
        )

    async def send_invitation(self, player_id: str, match_id: str, conversation_id: str):
        """Send GAME_INVITATION to player (async)."""
        invitation = {
            "message_type": "GAME_INVITATION",
            "match_id": match_id,
            "conversation_id": conversation_id,
            "player_id": player_id,
            # ... other fields
        }

        # ✅ CRITICAL: Use await (non-blocking)
        response = await call_with_retry(
            endpoint=self.get_player_endpoint(player_id),
            method="GAME_INVITATION",
            params=invitation,
            timeout=5,  # 5s timeout per spec
            logger=self.std_logger,
            circuit_breaker=self.circuit_breaker
        )

        return response

    async def request_parity_choice(self, player_id: str, match_id: str, timeout: int):
        """Request parity choice from player (async with timeout)."""
        call_params = {
            "message_type": "CHOOSE_PARITY_CALL",
            "match_id": match_id,
            "player_id": player_id,
            # ... other fields
        }

        # ✅ CRITICAL: Use await with timeout
        try:
            response = await asyncio.wait_for(
                call_with_retry(
                    endpoint=self.get_player_endpoint(player_id),
                    method="CHOOSE_PARITY_CALL",
                    params=call_params,
                    timeout=timeout,
                    logger=self.std_logger,
                    circuit_breaker=self.circuit_breaker
                ),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"Player {player_id} parity choice timeout")
            # Award technical loss
            return self.create_technical_loss(player_id)
```

## League Manager Template (M7.9-M7.13)

```python
"""
League Manager - Thread-Safe Registration & Standings

Thread Safety Features:
- Async MCP endpoint
- In-memory dicts for registrations (no file I/O races)
- SequentialQueueProcessor for standings (eliminates race conditions)
- Concurrent broadcasts with asyncio.gather()
"""

import asyncio
from typing import Dict, Any
from league_sdk import SequentialQueueProcessor, call_with_retry
from league_sdk.repositories import StandingsRepository
from agents.base import BaseAgent


class LeagueManager(BaseAgent):
    def __init__(self, league_id: str):
        super().__init__(agent_id="LM01", agent_type="league_manager")
        self.league_id = league_id

        # ✅ In-memory storage (thread-safe for async operations)
        self.registered_players = {}
        self.registered_referees = {}

        # ✅ Standings repository
        self.standings_repo = StandingsRepository(league_id)

        # ✅ CRITICAL: Queue processor for thread-safe standings updates
        self.standings_processor = SequentialQueueProcessor(
            process_func=self._update_standings_file,
            max_queue_size=100,
            logger=self.std_logger
        )

    async def start(self):
        """Start agent and queue processor."""
        super().start(run_in_thread=True)

        # ✅ Start standings queue processor
        await self.standings_processor.start()
        self.logger.info("League Manager started with queue processor")

    async def stop(self):
        """Graceful shutdown - wait for queue to drain."""
        # ✅ Wait for queue to finish processing
        await self.standings_processor.stop(timeout=10.0)
        super().stop()
        self.logger.info("League Manager stopped")

    async def register_player(self, params: Dict[str, Any]):
        """
        Handle player registration (async, concurrent-safe).

        Thread Safety:
        - Stores in memory (dict operations are atomic in async)
        - No file I/O during registration
        """
        player_id = self.generate_player_id()
        auth_token = self.generate_auth_token()

        # ✅ Store in memory (no race condition)
        self.registered_players[player_id] = {
            "metadata": params["player_meta"],
            "auth_token": auth_token,
            "endpoint": params["player_meta"]["contact_endpoint"]
        }

        return {
            "status": "ACCEPTED",
            "player_id": player_id,
            "auth_token": auth_token
        }

    async def report_match_result(self, params: Dict[str, Any]):
        """
        Handle MATCH_RESULT_REPORT from referee (async).

        Thread Safety:
        - Enqueues result for sequential processing
        - Returns immediately (non-blocking)
        - Multiple concurrent referees safe
        """
        # Validate auth_token
        if not self.is_valid_referee_token(params["auth_token"]):
            return {"error": {"error_code": "E012"}}

        # ✅ CRITICAL: Enqueue for sequential processing (prevents race condition)
        await self.standings_processor.enqueue(params["result"])

        # Return immediately
        return {"status": "ack", "message": "Result queued for processing"}

    async def _update_standings_file(self, match_result: Dict[str, Any]):
        """
        Update standings file (called sequentially by queue).

        Thread Safety:
        - Called sequentially by queue processor
        - No race condition (only one call at a time)
        - No lost updates
        """
        try:
            # Read current standings
            standings = self.standings_repo.load()

            # Update standings
            winner = match_result["winner"]
            standings.update_player_stats(
                player_id=winner,
                wins=1,
                points=3,
                games_played=1
            )

            # Write atomically
            self.standings_repo.save(standings)

            self.logger.info(f"Standings updated for {winner}")

            # ✅ Broadcast update to all players (concurrent)
            await self.broadcast_standings_update(standings)

        except Exception as e:
            self.logger.error(f"Failed to update standings: {e}")

    async def broadcast_standings_update(self, standings: Dict[str, Any]):
        """
        Broadcast LEAGUE_STANDINGS_UPDATE to all players (concurrent).

        Thread Safety:
        - Uses asyncio.gather() for concurrent broadcasts
        - Non-blocking
        - Handles failures gracefully
        """
        update_message = {
            "message_type": "LEAGUE_STANDINGS_UPDATE",
            "standings": standings,
            "timestamp": self._utc_timestamp()
        }

        # ✅ Broadcast concurrently to all players
        tasks = [
            call_with_retry(
                endpoint=player["endpoint"],
                method="LEAGUE_STANDINGS_UPDATE",
                params=update_message,
                timeout=self.config.network.request_timeout_sec,
                logger=self.std_logger,
                circuit_breaker=self.circuit_breaker
            )
            for player in self.registered_players.values()
        ]

        # ✅ Execute concurrently, catch exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Broadcast failed for player {i}: {result}")
```

## Key Patterns Summary

### ✅ DO:
- Use `async def` for all functions that do I/O
- Use `await call_with_retry()` for HTTP calls
- Use `await asyncio.sleep()` for delays
- Use `asyncio.gather()` for concurrent operations
- Use `SequentialQueueProcessor` for shared file updates
- Use `return_exceptions=True` in gather() for error handling
- Each match has unique conversation_id

### ❌ DON'T:
- Use `requests.post()` (blocking)
- Use `time.sleep()` (blocking)
- Update shared files directly from multiple handlers
- Forget to await async functions
- Block the event loop

## References

- **Thread Safety Documentation**: `doc/architecture/thread_safety.md`
- **Queue Processor Guide**: `doc/guides/queue_processor_guide.md`
- **Player Agent Example**: `agents/player_P01/server.py` (already async)
- **BaseAgent Pattern**: `agents/base/agent_base.py` (async register)
