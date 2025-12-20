"""
Sequential queue processor for thread-safe operations.

Provides a queue-based pattern for processing concurrent requests sequentially,
eliminating race conditions in shared resource updates (e.g., standings, rankings).

Usage in League Manager (M7.11-M7.12):
    processor = SequentialQueueProcessor(process_func=update_standings_file)
    await processor.start()

    # From multiple concurrent match result handlers:
    await processor.enqueue(match_result_data)

    # Graceful shutdown:
    await processor.stop()
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Optional


class SequentialQueueProcessor:
    """
    Processes items from a queue sequentially, ensuring thread-safe operations.

    This pattern eliminates race conditions when multiple concurrent tasks
    need to update a shared resource (like standings JSON file).

    Thread Safety:
    - Multiple concurrent producers can safely enqueue items
    - Single consumer processes items sequentially (no race conditions)
    - Queue operations are atomic (asyncio.Queue is thread-safe for async)

    Example:
        async def update_standings(result: Dict[str, Any]) -> None:
            # Read current standings
            standings = load_standings()
            # Update standings
            standings.update_from_result(result)
            # Write atomically
            save_standings(standings)

        processor = SequentialQueueProcessor(update_standings)
        await processor.start()

        # Multiple referees report results concurrently:
        await asyncio.gather(
            processor.enqueue(result1),
            processor.enqueue(result2),
            processor.enqueue(result3),
        )
        # All processed sequentially, no race conditions
    """

    def __init__(
        self,
        process_func: Callable[[Any], Any],
        max_queue_size: int = 0,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize sequential queue processor.

        Args:
            process_func: Async or sync function to process each item
            max_queue_size: Maximum queue size (0 = unlimited)
            logger: Optional logger for processing events
        """
        self.process_func = process_func
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.logger = logger or logging.getLogger(__name__)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the queue processor worker."""
        if self._running:
            self.logger.warning("Queue processor already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())
        self.logger.info("Sequential queue processor started")

    async def stop(self, timeout: float = 5.0) -> None:
        """
        Stop the queue processor gracefully.

        Args:
            timeout: Maximum time to wait for queue to drain (seconds)
        """
        if not self._running:
            return

        self._running = False

        # Wait for queue to drain (with timeout)
        try:
            await asyncio.wait_for(self.queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"Queue did not drain within {timeout}s, forcing shutdown")

        # Cancel worker task
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Sequential queue processor stopped")

    async def enqueue(self, item: Any) -> None:
        """
        Add item to processing queue.

        Thread-safe: Can be called concurrently from multiple tasks.

        Args:
            item: Item to process
        """
        if not self._running:
            raise RuntimeError("Queue processor not started")

        await self.queue.put(item)
        self.logger.debug(f"Item enqueued, queue size: {self.queue.qsize()}")

    async def _process_queue(self) -> None:
        """Worker task that processes items sequentially."""
        while self._running:
            try:
                # Wait for next item (with timeout to check _running flag)
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue  # Check _running flag

                # Process item sequentially
                try:
                    if inspect.iscoroutinefunction(self.process_func):
                        await self.process_func(item)
                    else:
                        self.process_func(item)

                    self.logger.debug("Item processed successfully")

                except Exception as e:
                    self.logger.error(f"Error processing item: {e}", exc_info=True)

                finally:
                    # Mark item as done
                    self.queue.task_done()

            except Exception as e:
                self.logger.error(f"Unexpected error in queue worker: {e}", exc_info=True)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    def is_running(self) -> bool:
        """Check if processor is running."""
        return self._running
