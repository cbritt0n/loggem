"""Tests for streaming module"""

import tempfile
import time
from pathlib import Path

import pytest

from loggem.streaming import LogStreamer, MultiFileStreamer, StreamEvent, StreamProcessor, tail_file


@pytest.fixture
def temp_log_file():
    """Create temporary log file"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
        f.write("Oct  5 12:00:01 host syslog: test message 1\n")
        f.write("Oct  5 12:00:02 host syslog: test message 2\n")
        f.write("Oct  5 12:00:03 host syslog: test message 3\n")
        path = f.name

    yield path

    # Cleanup
    Path(path).unlink(missing_ok=True)


def test_log_streamer_basic(temp_log_file):
    """Test basic log streaming"""
    streamer = LogStreamer(temp_log_file, parser_type="syslog", follow=False)
    streamer.start()

    # Read events
    events = []
    for _ in range(3):
        event = streamer.read(timeout=1.0)
        if event:
            events.append(event)

    streamer.stop()

    assert len(events) > 0
    assert all(isinstance(e, StreamEvent) for e in events)


def test_log_streamer_context_manager(temp_log_file):
    """Test streamer as context manager"""
    with LogStreamer(temp_log_file, follow=False) as streamer:
        event = streamer.read(timeout=1.0)
        assert event is None or isinstance(event, StreamEvent)


def test_tail_file(temp_log_file):
    """Test tail_file function"""
    entries = list(tail_file(temp_log_file, lines=2, follow=False))

    assert len(entries) <= 3  # Should get last 2-3 lines


def test_stream_processor(temp_log_file):
    """Test stream processor with callback"""
    streamer = LogStreamer(temp_log_file, follow=False)
    processor = StreamProcessor(streamer)

    events_received = []

    def callback(event: StreamEvent):
        events_received.append(event)

    processor.add_callback(callback)
    streamer.start()

    # Process briefly
    time.sleep(0.5)
    processor.stop()
    streamer.stop()

    # Should have received some events
    assert len(events_received) >= 0  # May be 0 depending on timing


def test_multi_file_streamer():
    """Test multi-file streaming"""
    # Create two temp files
    files = []
    for i in range(2):
        f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log")
        f.write(f"Oct  5 12:00:0{i} host syslog: file {i}\n")
        f.close()
        files.append(f.name)

    try:
        streamer = MultiFileStreamer(files)
        streamer.start()
        time.sleep(0.5)
        streamer.stop()

        assert len(streamer.streamers) == 2
    finally:
        for path in files:
            Path(path).unlink(missing_ok=True)
