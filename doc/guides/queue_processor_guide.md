# SequentialQueueProcessor - Quick Reference for Mission 7

## Purpose
Eliminates race conditions when multiple concurrent tasks update shared resources (standings, rankings).

## When to Use
- **League Manager (M7.11-M7.12)**: Processing match results from multiple concurrent referees
- **Any time**: Multiple producers need to update a single shared resource

## Pattern: Without Queue (Race Condition)
```python
# ⚠️ PROBLEM: Multiple referees update standings concurrently
async def handle_match_result(result):
    # Read standings file
    standings = load_standings_json()  # ← Race condition here!

    # Update
    standings[winner] += 3

    # Write back
    save_standings_json(standings)     # ← Lost updates possible!

# Multiple concurrent calls create race condition:
await asyncio.gather(
    handle_match_result(result1),  # Both read same initial state
    handle_match_result(result2),  # One update gets lost!
)
```

## Pattern: With Queue (Thread-Safe)
```python
from league_sdk import SequentialQueueProcessor

# ✅ SOLUTION: Sequential processing via queue
async def update_standings_file(result):
    """Process one result at a time (no race condition)."""
    standings = load_standings_json()
    standings[result["winner"]] += 3
    save_standings_json(standings)

# Create processor (in LeagueManager.__init__)
self.standings_processor = SequentialQueueProcessor(update_standings_file)

# Start processor (in LeagueManager.start)
await self.standings_processor.start()

# Enqueue results from multiple referees
async def handle_match_result(result):
    await self.standings_processor.enqueue(result)

# Multiple concurrent calls are now safe:
await asyncio.gather(
    handle_match_result(result1),  # Enqueued
    handle_match_result(result2),  # Enqueued
    handle_match_result(result3),  # Enqueued
)
# All processed sequentially - zero lost updates!

# Graceful shutdown (in LeagueManager.stop)
await self.standings_processor.stop()
```

## Complete League Manager Example

```python
from league_sdk import SequentialQueueProcessor
from league_sdk.repositories import StandingsRepository

class LeagueManager(BaseAgent):
    def __init__(self, league_id: str):
        super().__init__(agent_id="LM01", agent_type="league_manager")
        self.standings_repo = StandingsRepository(league_id)

        # Create queue processor for thread-safe standings updates
        self.standings_processor = SequentialQueueProcessor(
            process_func=self._update_standings,
            max_queue_size=100,  # Optional limit
            logger=self.std_logger
        )

    async def start(self):
        """Start agent and queue processor."""
        super().start(run_in_thread=True)
        await self.standings_processor.start()
        self.logger.info("League Manager started with queue processor")

    async def stop(self):
        """Graceful shutdown."""
        await self.standings_processor.stop(timeout=10.0)
        super().stop()
        self.logger.info("League Manager stopped")

    async def _update_standings(self, match_result: Dict[str, Any]) -> None:
        """
        Process one match result (called sequentially by queue).

        Thread-safe: Only one call at a time, no race conditions.
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

        except Exception as e:
            self.logger.error(f"Failed to update standings: {e}")
            # Queue processor continues processing other items

    async def handle_match_result_report(self, params: Dict[str, Any]):
        """
        Handle MATCH_RESULT_REPORT from referee (async MCP handler).

        Multiple referees can call this concurrently - safe via queue.
        """
        match_result = params["result"]

        # Enqueue for sequential processing (non-blocking)
        await self.standings_processor.enqueue(match_result)

        return {"status": "ack", "message": "Result queued for processing"}
```

## Benefits

1. **Zero Race Conditions**: Sequential processing eliminates read-modify-write races
2. **Non-Blocking**: Enqueue is fast, processing happens asynchronously
3. **Resilient**: Errors in one item don't stop queue processing
4. **Observable**: Check queue size, monitor processing rate
5. **Graceful Shutdown**: Waits for queue to drain before stopping

## Monitoring

```python
# Check queue status
queue_size = self.standings_processor.get_queue_size()
is_running = self.standings_processor.is_running()

self.logger.info(f"Standings queue: {queue_size} pending items")
```

## Testing

```python
@pytest.mark.asyncio
async def test_concurrent_match_results():
    """Test multiple concurrent results are processed correctly."""
    processor = SequentialQueueProcessor(update_standings)
    await processor.start()

    # Simulate 10 concurrent referees reporting
    results = [create_match_result(i) for i in range(10)]
    await asyncio.gather(*[processor.enqueue(r) for r in results])

    await asyncio.sleep(1.0)  # Allow processing
    await processor.stop()

    # Verify no lost updates
    assert all_results_processed()
```

## See Also

- `tests/unit/test_sdk/test_queue_processor.py` - Comprehensive tests
- `doc/architecture/thread_safety.md` - Full thread safety documentation
