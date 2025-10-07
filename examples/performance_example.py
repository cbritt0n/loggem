"""
Example: Performance Optimization

Demonstrates:
- Batch processing
- Async processing
- Memory-efficient streaming
- Analysis caching
- Adaptive batch sizing
"""

import time
import asyncio
from datetime import datetime

from loggem.performance import (
    BatchProcessor, AsyncBatchProcessor, MemoryEfficientProcessor,
    AnalysisCache, cached_analysis, AdaptiveBatcher
)
from loggem.core.models import LogEntry


def create_sample_logs(count=1000):
    """Create sample log entries for testing"""
    return [
        LogEntry(
            timestamp=datetime.now(),
            content=f"Log entry {i}: Sample message with data",
            message=f"Sample message {i}",
            metadata={"index": i}
        )
        for i in range(count)
    ]


def batch_processing_example():
    """Demonstrate batch processing for better performance"""
    print("=== Batch Processing Example ===\n")
    
    # Create test data
    entries = create_sample_logs(1000)
    
    # Define processing function
    def process_entry(entry):
        # Simulate some processing
        return {
            "length": len(entry.content),
            "has_error": "error" in entry.content.lower(),
            "timestamp": entry.timestamp
        }
    
    # Create batch processor
    processor = BatchProcessor(batch_size=100, max_workers=4)
    
    print(f"Processing {len(entries)} log entries in batches...")
    start_time = time.time()
    
    results = processor.process_entries(entries, process_entry)
    
    elapsed = time.time() - start_time
    
    print(f"\n📊 Results:")
    print(f"   Processed: {len(results)} entries")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Throughput: {processor.stats.throughput:.2f} entries/sec")
    print(f"   Avg time per entry: {processor.stats.avg_time_per_entry*1000:.2f}ms")
    
    processor.shutdown()


async def async_processing_example():
    """Demonstrate async batch processing"""
    print("\n=== Async Batch Processing ===\n")
    
    entries = create_sample_logs(1000)
    
    async def async_process(entry):
        # Simulate async operation
        await asyncio.sleep(0.001)
        return entry.content.upper()
    
    processor = AsyncBatchProcessor(batch_size=50, max_concurrent=10)
    
    print(f"Processing {len(entries)} entries asynchronously...")
    start_time = time.time()
    
    results = await processor.process_entries(entries, async_process)
    
    elapsed = time.time() - start_time
    
    print(f"\n📊 Results:")
    print(f"   Processed: {len(results)} entries")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Throughput: {processor.stats.throughput:.2f} entries/sec")


def memory_efficient_example():
    """Demonstrate memory-efficient processing"""
    print("\n=== Memory-efficient Processing ===\n")
    
    def log_generator(count):
        """Generator that yields logs without loading all in memory"""
        for i in range(count):
            yield LogEntry(
                timestamp=datetime.now(),
                content=f"Log {i}",
                message=f"Message {i}",
                metadata={}
            )
    
    processor = MemoryEfficientProcessor(chunk_size=100)
    
    def process_entry(entry):
        return len(entry.content)
    
    print("Processing 10,000 entries with memory-efficient streaming...")
    start_time = time.time()
    
    # Process entries as they're generated
    result_count = 0
    for result in processor.process_stream(log_generator(10000), process_entry):
        result_count += 1
        if result_count % 1000 == 0:
            print(f"  Processed {result_count} entries...")
    
    elapsed = time.time() - start_time
    
    print(f"\n📊 Results:")
    print(f"   Total processed: {result_count}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Throughput: {result_count/elapsed:.2f} entries/sec")
    print(f"   Memory usage: Low (streaming mode)")


def caching_example():
    """Demonstrate analysis caching"""
    print("\n=== Analysis Caching ===\n")
    
    cache = AnalysisCache(maxsize=100)
    
    # Define analysis function with caching
    @cached_analysis(cache)
    def analyze_log(entry):
        # Simulate expensive analysis
        time.sleep(0.01)
        return {
            "score": 0.75,
            "category": "normal"
        }
    
    # Create test entries (with duplicates)
    entries = create_sample_logs(50)
    entries.extend(entries[:25])  # Add 25 duplicates
    
    print(f"Analyzing {len(entries)} entries (25 duplicates)...")
    start_time = time.time()
    
    results = []
    for entry in entries:
        result = analyze_log(entry)
        results.append(result)
    
    elapsed = time.time() - start_time
    
    # Show cache statistics
    stats = cache.get_stats()
    
    print(f"\n📊 Results:")
    print(f"   Total analyzed: {len(results)}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Cache hits: {stats['hits']}")
    print(f"   Cache hit rate: {stats['hit_rate']}")
    print(f"   Time saved: ~{stats['hits'] * 0.01:.2f}s (estimated)")


def adaptive_batching_example():
    """Demonstrate adaptive batch sizing"""
    print("\n=== Adaptive Batch Sizing ===\n")
    
    batcher = AdaptiveBatcher(min_batch=10, max_batch=200, target_time=1.0)
    entries = create_sample_logs(1000)
    
    def process_batch(batch):
        # Simulate processing
        time.sleep(len(batch) * 0.001)
        return len(batch)
    
    print("Processing with adaptive batch sizes...")
    print(f"Target: 1.0s per batch\n")
    
    processed = 0
    batch_count = 0
    
    while processed < len(entries):
        # Get current batch size
        batch_size = batcher.get_batch_size()
        batch = entries[processed:processed + batch_size]
        
        # Process batch
        start = time.time()
        result = process_batch(batch)
        elapsed = time.time() - start
        
        # Update statistics
        batcher.adjust_batch_size(elapsed)
        
        processed += len(batch)
        batch_count += 1
        
        print(f"Batch {batch_count}: size={len(batch):3d}, "
              f"time={elapsed:.3f}s, "
              f"next_size={batcher.get_batch_size():3d}")
    
    print(f"\n✅ Processed {processed} entries in {batch_count} adaptive batches")


def comparison_example():
    """Compare different processing strategies"""
    print("\n=== Performance Comparison ===\n")
    
    entries = create_sample_logs(500)
    
    def simple_process(entry):
        # Simple processing
        return entry.content.upper()
    
    # 1. Sequential processing
    print("1. Sequential processing...")
    start = time.time()
    results_seq = [simple_process(e) for e in entries]
    time_seq = time.time() - start
    print(f"   Time: {time_seq:.2f}s")
    
    # 2. Batch processing
    print("\n2. Batch processing...")
    processor = BatchProcessor(batch_size=50, max_workers=4)
    start = time.time()
    results_batch = processor.process_entries(entries, simple_process)
    time_batch = time.time() - start
    print(f"   Time: {time_batch:.2f}s")
    processor.shutdown()
    
    # 3. With caching
    print("\n3. With caching (25% duplicates)...")
    entries_dup = entries + entries[:125]  # Add 25% duplicates
    cache = AnalysisCache(maxsize=500)
    
    @cached_analysis(cache)
    def cached_process(entry):
        return simple_process(entry)
    
    start = time.time()
    results_cache = [cached_process(e) for e in entries_dup]
    time_cache = time.time() - start
    print(f"   Time: {time_cache:.2f}s")
    print(f"   Cache hit rate: {cache.get_stats()['hit_rate']}")
    
    # Summary
    print("\n📊 Performance Summary:")
    print(f"   Sequential:     {time_seq:.2f}s (baseline)")
    print(f"   Batch:          {time_batch:.2f}s ({time_seq/time_batch:.1f}x speedup)")
    print(f"   With caching:   {time_cache:.2f}s (with 25% duplicates)")


if __name__ == "__main__":
    print("LogGem - Performance Optimization Examples")
    print("=" * 50)
    
    try:
        batch_processing_example()
        
        # Async example
        print("\nRunning async example...")
        asyncio.run(async_processing_example())
        
        memory_efficient_example()
        caching_example()
        adaptive_batching_example()
        comparison_example()
        
        print("\n✅ All performance examples completed!")
        
    except KeyboardInterrupt:
        print("\n\n✅ Examples stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
