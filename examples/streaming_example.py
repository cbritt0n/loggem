"""
Example: Real-time Log Streaming

Demonstrates:
- Live log tailing
- Real-time anomaly detection
- Stream processing with callbacks
"""

import time
from loggem.streaming import LogStreamer, StreamProcessor, tail_file
from loggem.detector import AnomalyDetector

def simple_tail_example():
    """Simple tail example - like 'tail -f'"""
    print("=== Simple Tail Example ===\n")
    
    log_file = "/var/log/syslog"  # Adjust path for your system
    
    print(f"Tailing last 5 lines from {log_file}...")
    for entry in tail_file(log_file, lines=5, follow=False):
        print(f"[{entry.timestamp}] {entry.message}")


def real_time_monitoring():
    """Real-time log monitoring with anomaly detection"""
    print("\n=== Real-time Monitoring ===\n")
    
    log_file = "/var/log/syslog"  # Adjust path
    
    # Create streamer
    with LogStreamer(log_file, parser_type="syslog", follow=True) as streamer:
        print(f"Monitoring {log_file} in real-time...")
        print("Press Ctrl+C to stop\n")
        
        # Initialize detector
        detector = AnomalyDetector()
        
        try:
            for event in streamer.iter_events(timeout=1.0):
                # Analyze entry for anomalies
                result = detector.analyze_entry(event.entry)
                
                if result.anomalies:
                    anomaly = result.anomalies[0]
                    print(f"🚨 ANOMALY DETECTED!")
                    print(f"   Score: {anomaly.score:.2f}")
                    print(f"   Reason: {anomaly.reasoning}")
                    print(f"   Log: {event.entry.content[:100]}...")
                    print()
                else:
                    print(f"✓ [{event.timestamp}] {event.entry.message[:80]}")
        
        except KeyboardInterrupt:
            print("\n\nStopped monitoring.")


def callback_based_processing():
    """Stream processing with custom callbacks"""
    print("\n=== Callback-based Processing ===\n")
    
    log_file = "/var/log/syslog"
    
    # Create streamer and processor
    streamer = LogStreamer(log_file, follow=False)
    processor = StreamProcessor(streamer)
    
    # Statistics
    stats = {"total": 0, "errors": 0, "warnings": 0}
    
    def analyze_callback(event):
        """Callback to analyze each event"""
        stats["total"] += 1
        
        content_lower = event.entry.content.lower()
        if "error" in content_lower or "fail" in content_lower:
            stats["errors"] += 1
            print(f"❌ ERROR: {event.entry.message[:60]}")
        elif "warn" in content_lower:
            stats["warnings"] += 1
            print(f"⚠️  WARNING: {event.entry.message[:60]}")
    
    # Add callback
    processor.add_callback(analyze_callback)
    
    # Start processing
    streamer.start()
    print("Processing logs...")
    
    # Process for 5 seconds
    time.sleep(5)
    
    processor.stop()
    streamer.stop()
    
    print(f"\n📊 Statistics:")
    print(f"   Total logs: {stats['total']}")
    print(f"   Errors: {stats['errors']}")
    print(f"   Warnings: {stats['warnings']}")


def multi_file_monitoring():
    """Monitor multiple log files simultaneously"""
    print("\n=== Multi-file Monitoring ===\n")
    
    from loggem.streaming import MultiFileStreamer
    
    log_files = [
        "/var/log/syslog",
        "/var/log/auth.log"
    ]
    
    print(f"Monitoring {len(log_files)} files...")
    
    with MultiFileStreamer(log_files) as streamer:
        # Monitor for 10 seconds
        timeout = time.time() + 10
        
        for event in streamer.iter_events(timeout=1.0):
            if time.time() > timeout:
                break
            
            print(f"[{event.file_path}] {event.entry.message[:70]}")
    
    print("\nMonitoring complete.")


if __name__ == "__main__":
    print("LogGem - Real-time Streaming Examples")
    print("=" * 50)
    
    # Run examples
    try:
        # simple_tail_example()
        # real_time_monitoring()  # Requires Ctrl+C to stop
        callback_based_processing()
        # multi_file_monitoring()
        
        print("\n✅ Examples completed!")
    except FileNotFoundError as e:
        print(f"\n⚠️  Log file not found: {e}")
        print("Please adjust the log file paths in the examples.")
    except KeyboardInterrupt:
        print("\n\n✅ Examples stopped by user.")
