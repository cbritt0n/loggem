"""
Performance optimization utilities for LogGem.

Provides:
- Async log processing
- Batch processing optimization
- Memory-efficient streaming
- LRU caching for repeated analyses
- Connection pooling
"""

import asyncio
import hashlib
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional

from ..core.logging import get_logger
from ..core.models import LogEntry

logger = get_logger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for processing performance"""

    total_processed: int = 0
    total_time: float = 0.0
    avg_time_per_entry: float = 0.0
    throughput: float = 0.0  # entries per second

    def update(self, count: int, elapsed: float):
        """Update statistics"""
        self.total_processed += count
        self.total_time += elapsed
        self.avg_time_per_entry = (
            self.total_time / self.total_processed if self.total_processed > 0 else 0
        )
        self.throughput = self.total_processed / self.total_time if self.total_time > 0 else 0


class BatchProcessor:
    """Optimized batch processing for log entries"""

    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        """
        Initialize batch processor

        Args:
            batch_size: Number of entries to process in each batch
            max_workers: Maximum number of worker threads
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.stats = ProcessingStats()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        logger.info("batch_processor_initialized", batch_size=batch_size, max_workers=max_workers)

    def process_entries(
        self, entries: list[LogEntry], processor: Callable[[LogEntry], Any]
    ) -> list[Any]:
        """
        Process log entries in optimized batches

        Args:
            entries: List of log entries
            processor: Function to process each entry

        Returns:
            List of processing results
        """
        start_time = time.time()
        results = []

        # Process in batches
        for i in range(0, len(entries), self.batch_size):
            batch = entries[i : i + self.batch_size]

            # Parallel processing within batch
            batch_results = list(self._executor.map(processor, batch))
            results.extend(batch_results)

        elapsed = time.time() - start_time
        self.stats.update(len(entries), elapsed)

        logger.info(
            "batch_processed",
            count=len(entries),
            elapsed=f"{elapsed:.2f}s",
            throughput=f"{self.stats.throughput:.2f} entries/s",
        )

        return results

    def shutdown(self):
        """Shutdown executor"""
        self._executor.shutdown(wait=True)


class AsyncBatchProcessor:
    """Async batch processor for high-performance processing"""

    def __init__(self, batch_size: int = 100, max_concurrent: int = 10):
        """
        Initialize async batch processor

        Args:
            batch_size: Batch size
            max_concurrent: Maximum concurrent tasks
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.stats = ProcessingStats()
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_entries(self, entries: list[LogEntry], processor: Callable) -> list[Any]:
        """
        Process entries asynchronously

        Args:
            entries: Log entries to process
            processor: Async processing function

        Returns:
            List of results
        """
        start_time = time.time()

        async def process_with_limit(entry):
            async with self._semaphore:
                return await processor(entry)

        # Create tasks for all entries
        tasks = [process_with_limit(entry) for entry in entries]

        # Process in batches
        results = []
        for i in range(0, len(tasks), self.batch_size):
            batch_tasks = tasks[i : i + self.batch_size]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

        elapsed = time.time() - start_time
        self.stats.update(len(entries), elapsed)

        logger.info(
            "async_batch_processed",
            count=len(entries),
            elapsed=f"{elapsed:.2f}s",
            throughput=f"{self.stats.throughput:.2f} entries/s",
        )

        return results


class MemoryEfficientProcessor:
    """Memory-efficient log processing using generators"""

    def __init__(self, chunk_size: int = 1000):
        """
        Initialize memory-efficient processor

        Args:
            chunk_size: Number of entries to hold in memory at once
        """
        self.chunk_size = chunk_size

    def process_stream(self, entry_generator, processor: Callable):
        """
        Process log entries from generator without loading all into memory

        Args:
            entry_generator: Generator yielding LogEntry objects
            processor: Function to process each entry

        Yields:
            Processing results
        """
        chunk = []

        for entry in entry_generator:
            chunk.append(entry)

            if len(chunk) >= self.chunk_size:
                # Process chunk
                for e in chunk:
                    yield processor(e)
                chunk = []

        # Process remaining
        for e in chunk:
            yield processor(e)


class AnalysisCache:
    """LRU cache for analysis results to avoid redundant processing"""

    def __init__(self, maxsize: int = 1000):
        """
        Initialize analysis cache

        Args:
            maxsize: Maximum cache size
        """
        self.maxsize = maxsize
        self._cache: dict[str, Any] = {}
        self._access_count = 0
        self._hit_count = 0

        logger.info("analysis_cache_initialized", maxsize=maxsize)

    def _get_cache_key(self, entry: LogEntry) -> str:
        """Generate cache key for log entry"""
        # Use content hash as key
        content = f"{entry.raw}:{entry.timestamp}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, entry: LogEntry) -> Optional[Any]:
        """Get cached result for entry"""
        self._access_count += 1
        key = self._get_cache_key(entry)

        if key in self._cache:
            self._hit_count += 1
            logger.debug("cache_hit", key=key)
            return self._cache[key]

        return None

    def set(self, entry: LogEntry, result: Any):
        """Cache result for entry"""
        key = self._get_cache_key(entry)

        # Evict oldest if full
        if len(self._cache) >= self.maxsize:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[key] = result
        logger.debug("cache_set", key=key)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        hit_rate = (self._hit_count / self._access_count * 100) if self._access_count > 0 else 0
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "accesses": self._access_count,
            "hits": self._hit_count,
            "hit_rate": f"{hit_rate:.2f}%",
        }

    def clear(self):
        """Clear cache"""
        self._cache.clear()
        self._access_count = 0
        self._hit_count = 0
        logger.info("cache_cleared")


def cached_analysis(cache: AnalysisCache):
    """Decorator for caching analysis results"""

    def decorator(func):
        @wraps(func)
        def wrapper(entry: LogEntry, *args, **kwargs):
            # Check cache
            cached_result = cache.get(entry)
            if cached_result is not None:
                return cached_result

            # Compute and cache
            result = func(entry, *args, **kwargs)
            cache.set(entry, result)
            return result

        return wrapper

    return decorator


class ParallelProcessor:
    """Process logs in parallel using multiple processes"""

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize parallel processor

        Args:
            max_workers: Maximum number of worker processes (default: CPU count)
        """
        self.max_workers = max_workers
        self._executor = ProcessPoolExecutor(max_workers=max_workers)

        logger.info("parallel_processor_initialized", workers=max_workers or "auto")

    def process_entries(
        self, entries: list[LogEntry], processor: Callable[[LogEntry], Any]
    ) -> list[Any]:
        """
        Process entries in parallel across multiple processes

        Args:
            entries: Log entries to process
            processor: Processing function (must be picklable)

        Returns:
            List of results
        """
        start_time = time.time()

        results = list(self._executor.map(processor, entries))

        elapsed = time.time() - start_time
        throughput = len(entries) / elapsed if elapsed > 0 else 0

        logger.info(
            "parallel_processed",
            count=len(entries),
            elapsed=f"{elapsed:.2f}s",
            throughput=f"{throughput:.2f} entries/s",
        )

        return results

    def shutdown(self):
        """Shutdown executor"""
        self._executor.shutdown(wait=True)


class AdaptiveBatcher:
    """Adaptive batch size based on processing performance"""

    def __init__(self, min_batch: int = 10, max_batch: int = 1000, target_time: float = 1.0):
        """
        Initialize adaptive batcher

        Args:
            min_batch: Minimum batch size
            max_batch: Maximum batch size
            target_time: Target processing time per batch (seconds)
        """
        self.min_batch = min_batch
        self.max_batch = max_batch
        self.target_time = target_time
        self.current_batch = min_batch
        self._last_time = 0.0

    def adjust_batch_size(self, elapsed: float):
        """
        Adjust batch size based on last processing time

        Args:
            elapsed: Time taken for last batch
        """
        if elapsed < self.target_time * 0.8:
            # Too fast, increase batch size
            self.current_batch = min(int(self.current_batch * 1.5), self.max_batch)
        elif elapsed > self.target_time * 1.2:
            # Too slow, decrease batch size
            self.current_batch = max(int(self.current_batch * 0.7), self.min_batch)

        self._last_time = elapsed
        logger.debug("batch_size_adjusted", size=self.current_batch, elapsed=elapsed)

    def get_batch_size(self) -> int:
        """Get current optimal batch size"""
        return self.current_batch


class ConnectionPool:
    """Connection pool for LLM providers to reduce overhead"""

    def __init__(self, max_connections: int = 10):
        """
        Initialize connection pool

        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self._pool = []
        self._in_use = set()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a connection from pool"""
        async with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(conn)
                return conn
            if len(self._in_use) < self.max_connections:
                # Create new connection (placeholder)
                conn = object()
                self._in_use.add(conn)
                return conn
            # Wait for available connection
            raise Exception("No connections available")

    async def release(self, conn):
        """Release connection back to pool"""
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)


# Export public API
__all__ = [
    "BatchProcessor",
    "AsyncBatchProcessor",
    "MemoryEfficientProcessor",
    "AnalysisCache",
    "cached_analysis",
    "ParallelProcessor",
    "AdaptiveBatcher",
    "ConnectionPool",
    "ProcessingStats",
]
