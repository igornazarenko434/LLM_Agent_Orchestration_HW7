"""
Unit tests for SequentialQueueProcessor (thread safety for standings updates).

Tests the queue-based pattern that eliminates race conditions when
multiple concurrent tasks update shared resources.
"""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from league_sdk.queue_processor import SequentialQueueProcessor


@pytest.mark.unit
class TestSequentialQueueProcessor:
    """Test sequential queue processor for thread-safe operations."""

    @pytest.mark.asyncio
    async def test_processor_starts_and_stops(self):
        """Test processor lifecycle."""
        process_func = Mock()
        processor = SequentialQueueProcessor(process_func)

        assert not processor.is_running()

        await processor.start()
        assert processor.is_running()

        await processor.stop()
        assert not processor.is_running()

    @pytest.mark.asyncio
    async def test_processes_single_item(self):
        """Test processing a single item."""
        items_processed = []

        async def process_item(item):
            items_processed.append(item)

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        await processor.enqueue("test_item")
        await asyncio.sleep(0.1)  # Allow processing

        await processor.stop()

        assert items_processed == ["test_item"]

    @pytest.mark.asyncio
    async def test_processes_items_sequentially(self):
        """Test items are processed in order."""
        items_processed = []

        async def process_item(item):
            items_processed.append(item)
            await asyncio.sleep(0.05)  # Simulate processing time

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        # Enqueue multiple items
        for i in range(5):
            await processor.enqueue(i)

        await asyncio.sleep(0.5)  # Allow all processing
        await processor.stop()

        assert items_processed == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_concurrent_enqueue_safe(self):
        """Test multiple concurrent enqueues are processed correctly."""
        items_processed = []

        async def process_item(item):
            items_processed.append(item)

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        # Simulate multiple concurrent producers
        await asyncio.gather(
            processor.enqueue("A"),
            processor.enqueue("B"),
            processor.enqueue("C"),
            processor.enqueue("D"),
        )

        await asyncio.sleep(0.2)
        await processor.stop()

        assert len(items_processed) == 4
        assert set(items_processed) == {"A", "B", "C", "D"}

    @pytest.mark.asyncio
    async def test_handles_processing_errors(self):
        """Test processor continues after errors."""
        items_processed = []

        async def process_item(item):
            if item == "error":
                raise ValueError("Test error")
            items_processed.append(item)

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        await processor.enqueue("item1")
        await processor.enqueue("error")
        await processor.enqueue("item2")

        await asyncio.sleep(0.2)
        await processor.stop()

        # Should process item1 and item2, skip error
        assert items_processed == ["item1", "item2"]

    @pytest.mark.asyncio
    async def test_sync_process_function(self):
        """Test processor works with synchronous functions."""
        items_processed = []

        def process_item(item):  # Synchronous function
            items_processed.append(item)

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        await processor.enqueue("sync_item")
        await asyncio.sleep(0.1)

        await processor.stop()

        assert items_processed == ["sync_item"]

    @pytest.mark.asyncio
    async def test_queue_size_tracking(self):
        """Test queue size is tracked correctly."""
        slow_process = asyncio.Event()

        async def process_item(item):
            await slow_process.wait()

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        # Enqueue items (won't be processed until event is set)
        await processor.enqueue("item1")
        await processor.enqueue("item2")
        await processor.enqueue("item3")

        assert processor.get_queue_size() == 3

        # Allow processing
        slow_process.set()
        await asyncio.sleep(0.2)

        await processor.stop()

        assert processor.get_queue_size() == 0

    @pytest.mark.asyncio
    async def test_graceful_shutdown_waits_for_queue(self):
        """Test graceful shutdown waits for queue to drain."""
        items_processed = []

        async def process_item(item):
            await asyncio.sleep(0.01)
            items_processed.append(item)

        processor = SequentialQueueProcessor(process_item)
        await processor.start()

        # Enqueue items
        for i in range(3):
            await processor.enqueue(i)

        # Give queue time to start processing
        await asyncio.sleep(0.05)

        # Stop should wait for queue to drain
        await processor.stop(timeout=2.0)

        assert len(items_processed) == 3

    @pytest.mark.asyncio
    async def test_cannot_enqueue_when_stopped(self):
        """Test enqueue raises error when processor is stopped."""
        processor = SequentialQueueProcessor(Mock())

        with pytest.raises(RuntimeError, match="not started"):
            await processor.enqueue("item")


@pytest.mark.unit
class TestQueueProcessorStandingsUseCase:
    """Test queue processor for standings update use case."""

    @pytest.mark.asyncio
    async def test_eliminates_race_condition(self):
        """Test that queue eliminates race condition in standings updates."""
        # Simulate standings file
        standings = {"player1": 0, "player2": 0, "player3": 0}
        read_count = {"count": 0}

        async def update_standings(match_result):
            """Simulates read-modify-write operation on standings."""
            # Read (race condition point without queue)
            read_count["count"] += 1
            current = standings.copy()

            # Modify
            winner = match_result["winner"]
            current[winner] = current.get(winner, 0) + 3

            # Simulate processing delay (makes race condition more likely)
            await asyncio.sleep(0.01)

            # Write
            standings[winner] = current[winner]

        processor = SequentialQueueProcessor(update_standings)
        await processor.start()

        # Simulate 10 concurrent match results
        match_results = [
            {"winner": "player1"},
            {"winner": "player2"},
            {"winner": "player1"},
            {"winner": "player3"},
            {"winner": "player1"},
            {"winner": "player2"},
            {"winner": "player1"},
            {"winner": "player3"},
            {"winner": "player1"},
            {"winner": "player2"},
        ]

        # Process concurrently (would cause race condition without queue)
        await asyncio.gather(*[processor.enqueue(result) for result in match_results])

        await asyncio.sleep(0.5)  # Allow all processing
        await processor.stop()

        # Verify correct final standings (no lost updates)
        assert standings["player1"] == 15  # 5 wins × 3 points
        assert standings["player2"] == 9  # 3 wins × 3 points
        assert standings["player3"] == 6  # 2 wins × 3 points

        # Verify all reads happened (no missed updates)
        assert read_count["count"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
