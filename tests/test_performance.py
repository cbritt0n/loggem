"""Tests for performance optimization module"""

from datetime import datetime

import pytest

from loggem.core.models import LogEntry
from loggem.performance import (
    AdaptiveBatcher,
    AnalysisCache,
    AsyncBatchProcessor,
    BatchProcessor,
    MemoryEfficientProcessor,
    ProcessingStats,
    cached_analysis,
)


@pytest.fixture
def sample_entries():
    """Create sample log entries"""
    return [
        LogEntry(
            timestamp=datetime.now(),
            source="test",
            message=f"Sample message {i}",
            raw=f"Log entry {i}: Sample message with data",
            metadata={"index": i},
        )
        for i in range(100)
    ]


def test_batch_processor(sample_entries):
    """Test batch processing"""
    processor = BatchProcessor(batch_size=10, max_workers=2)

    def process_entry(entry):
        # Simple processing
        return entry.raw.upper()

    results = processor.process_entries(sample_entries, process_entry)

    assert len(results) == len(sample_entries)
    assert all(isinstance(r, str) for r in results)
    assert processor.stats.total_processed == len(sample_entries)

    processor.shutdown()


def test_processing_stats():
    """Test processing statistics"""
    stats = ProcessingStats()

    stats.update(100, 2.0)
    assert stats.total_processed == 100
    assert stats.total_time == 2.0
    assert stats.avg_time_per_entry == 0.02
    assert stats.throughput == 50.0


def test_memory_efficient_processor(sample_entries):
    """Test memory-efficient processing"""
    processor = MemoryEfficientProcessor(chunk_size=10)

    def process_entry(entry):
        return len(entry.raw)

    # Use generator
    def entry_generator():
        yield from sample_entries

    results = list(processor.process_stream(entry_generator(), process_entry))

    assert len(results) == len(sample_entries)
    assert all(isinstance(r, int) for r in results)


def test_analysis_cache():
    """Test analysis caching"""
    cache = AnalysisCache(maxsize=10)

    entry = LogEntry(
        timestamp=datetime.now(), source="test", message="Test", raw="Test log", metadata={}
    )

    # First access - cache miss
    result = cache.get(entry)
    assert result is None

    # Set cache
    cache.set(entry, {"score": 0.8})

    # Second access - cache hit
    result = cache.get(entry)
    assert result is not None
    assert result["score"] == 0.8

    # Check stats
    stats = cache.get_stats()
    assert stats["accesses"] == 2
    assert stats["hits"] == 1
    assert "50.00%" in stats["hit_rate"]


def test_cached_analysis_decorator():
    """Test cached analysis decorator"""
    cache = AnalysisCache(maxsize=10)

    call_count = [0]

    @cached_analysis(cache)
    def analyze_entry(entry):
        call_count[0] += 1
        return {"result": "analyzed"}

    entry = LogEntry(
        timestamp=datetime.now(), source="test", message="Test", raw="Test", metadata={}
    )

    # First call
    result1 = analyze_entry(entry)
    assert call_count[0] == 1

    # Second call - should use cache
    result2 = analyze_entry(entry)
    assert call_count[0] == 1  # No additional call
    assert result1 == result2


def test_cache_eviction():
    """Test cache eviction when full"""
    cache = AnalysisCache(maxsize=2)

    entries = [
        LogEntry(
            timestamp=datetime.now(), source="test", message="test", raw=f"Entry {i}", metadata={}
        )
        for i in range(3)
    ]

    # Fill cache
    cache.set(entries[0], "result0")
    cache.set(entries[1], "result1")

    # Verify both are cached
    stats = cache.get_stats()
    assert stats["size"] == 2

    # Add third - should evict oldest
    cache.set(entries[2], "result2")
    stats = cache.get_stats()
    assert stats["size"] == 2


def test_adaptive_batcher():
    """Test adaptive batch size adjustment"""
    batcher = AdaptiveBatcher(min_batch=10, max_batch=100, target_time=1.0)

    # Initial size
    assert batcher.get_batch_size() == 10

    # Fast processing - should increase
    batcher.adjust_batch_size(0.5)
    assert batcher.get_batch_size() > 10

    # Slow processing - should decrease
    batcher.adjust_batch_size(2.0)
    assert batcher.get_batch_size() < batcher.max_batch


def test_cache_clear():
    """Test cache clearing"""
    cache = AnalysisCache(maxsize=10)

    entry = LogEntry(
        timestamp=datetime.now(), source="test", message="test", raw="test", metadata={}
    )
    cache.set(entry, "result")

    assert cache.get_stats()["size"] == 1

    cache.clear()
    assert cache.get_stats()["size"] == 0
    assert cache.get_stats()["accesses"] == 0


@pytest.mark.asyncio
async def test_async_batch_processor(sample_entries):
    """Test async batch processor"""
    processor = AsyncBatchProcessor(batch_size=10, max_concurrent=5)

    async def async_process(entry: LogEntry) -> str:
        await asyncio.sleep(0.01)  # Simulate async work
        return entry.raw.upper()  # Use raw instead of content

    results = await processor.process_entries(sample_entries, async_process)

    assert len(results) == len(sample_entries)
    assert all(isinstance(r, str) for r in results)


# Import asyncio for async test
import asyncio
