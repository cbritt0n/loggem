"""
Real-time log streaming and monitoring module.

Provides capabilities for:
- Live log file tailing
- Real-time anomaly detection
- File watching with watchdog
- Stream processing
- Async streaming support
"""

import time
import asyncio
import threading
from pathlib import Path
from typing import Callable, Optional, List, Generator, AsyncGenerator
from queue import Queue, Empty
from dataclasses import dataclass
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from ..core.logging import get_logger
from ..core.models import LogEntry
from ..parsers.factory import LogParserFactory

logger = get_logger(__name__)


@dataclass
class StreamEvent:
    """Event from log stream"""
    entry: LogEntry
    timestamp: datetime
    file_path: str


class FileWatchHandler(FileSystemEventHandler):
    """Handle file system events for log file watching"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path)


class LogStreamer:
    """Real-time log file streamer with tail functionality and watchdog support"""
    
    def __init__(self, file_path: str, parser_type: str = "auto", 
                 buffer_size: int = 1000, follow: bool = True,
                 use_watchdog: bool = True):
        """
        Initialize log streamer
        
        Args:
            file_path: Path to log file to stream
            parser_type: Type of parser to use
            buffer_size: Maximum events to buffer
            follow: Continue watching file for new entries
            use_watchdog: Use watchdog for file watching (more efficient)
        """
        self.file_path = Path(file_path)
        self.parser_type = parser_type
        self.buffer_size = buffer_size
        self.follow = follow
        self.use_watchdog = use_watchdog and WATCHDOG_AVAILABLE
        
        self._queue: Queue = Queue(maxsize=buffer_size)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._parser = None
        self._position = 0
        self._observer = None
        self._file_handle = None
        
        logger.info(
            "streamer_created",
            file_path=str(self.file_path),
            parser_type=parser_type,
            follow=follow,
            watchdog=self.use_watchdog
        )
    
    def start(self) -> None:
        """Start streaming in background thread"""
        if self._thread and self._thread.is_alive():
            logger.warning("streamer_already_running")
            return
        
        self._stop_event.clear()
        
        # Start watchdog observer if enabled
        if self.use_watchdog and self.follow:
            handler = FileWatchHandler(self._on_file_modified)
            self._observer = Observer()
            self._observer.schedule(handler, str(self.file_path.parent), recursive=False)
            self._observer.start()
        
        self._thread = threading.Thread(target=self._stream_worker, daemon=True)
        self._thread.start()
        
        logger.info("streamer_started", file_path=str(self.file_path))
    
    def stop(self) -> None:
        """Stop streaming"""
        self._stop_event.set()
        
        # Stop watchdog observer
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        # Close file handle
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
        
        if self._thread:
            self._thread.join(timeout=5)
        
        logger.info("streamer_stopped", file_path=str(self.file_path))
    
    def _on_file_modified(self, file_path: str) -> None:
        """Callback for watchdog file modification events"""
        if Path(file_path) == self.file_path:
            # File was modified, read will pick up changes
            pass
    
    def _stream_worker(self) -> None:
        """Background worker that reads and queues log entries"""
        try:
            # Initialize parser
            self._parser = LogParserFactory.create_parser(self.parser_type)
            
            # Open file
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Seek to end if following, otherwise start from beginning
                if self.follow:
                    f.seek(0, 2)  # Seek to end
                    self._position = f.tell()
                
                while not self._stop_event.is_set():
                    # Read new lines
                    line = f.readline()
                    
                    if line:
                        # Parse line
                        entry = self._parser.parse_line(line.strip())
                        if entry:
                            event = StreamEvent(
                                entry=entry,
                                timestamp=datetime.now(),
                                file_path=str(self.file_path)
                            )
                            
                            # Add to queue (non-blocking)
                            try:
                                self._queue.put_nowait(event)
                            except:
                                # Queue full, drop oldest
                                try:
                                    self._queue.get_nowait()
                                    self._queue.put_nowait(event)
                                except:
                                    pass
                        
                        self._position = f.tell()
                    else:
                        # No new data
                        if not self.follow:
                            break  # Stop if not following
                        time.sleep(0.1)  # Poll interval
                        
                        # Check if file was truncated/rotated
                        current_size = self.file_path.stat().st_size
                        if current_size < self._position:
                            f.seek(0)
                            self._position = 0
                            logger.info("file_rotated", file_path=str(self.file_path))
        
        except Exception as e:
            logger.error("stream_worker_error", error=str(e), file_path=str(self.file_path))
    
    def read(self, timeout: Optional[float] = None) -> Optional[StreamEvent]:
        """
        Read next event from stream
        
        Args:
            timeout: Maximum time to wait for event
            
        Returns:
            StreamEvent or None if timeout
        """
        try:
            return self._queue.get(timeout=timeout)
        except Empty:
            return None
    
    def iter_events(self, timeout: float = 1.0) -> Generator[StreamEvent, None, None]:
        """
        Iterate over stream events
        
        Args:
            timeout: Timeout for each read
            
        Yields:
            StreamEvent objects
        """
        while not self._stop_event.is_set():
            event = self.read(timeout=timeout)
            if event:
                yield event
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class MultiFileStreamer:
    """Stream from multiple log files simultaneously"""
    
    def __init__(self, file_paths: List[str], parser_type: str = "auto"):
        """
        Initialize multi-file streamer
        
        Args:
            file_paths: List of file paths to stream
            parser_type: Parser type for all files
        """
        self.file_paths = file_paths
        self.parser_type = parser_type
        self.streamers: List[LogStreamer] = []
        
        logger.info("multi_streamer_created", file_count=len(file_paths))
    
    def start(self) -> None:
        """Start all streamers"""
        for file_path in self.file_paths:
            streamer = LogStreamer(file_path, self.parser_type)
            streamer.start()
            self.streamers.append(streamer)
        
        logger.info("multi_streamer_started", streamer_count=len(self.streamers))
    
    def stop(self) -> None:
        """Stop all streamers"""
        for streamer in self.streamers:
            streamer.stop()
        
        logger.info("multi_streamer_stopped")
    
    def iter_events(self, timeout: float = 1.0) -> Generator[StreamEvent, None, None]:
        """
        Iterate over events from all streams
        
        Args:
            timeout: Timeout per streamer check
            
        Yields:
            StreamEvent objects from any stream
        """
        while True:
            found_event = False
            for streamer in self.streamers:
                event = streamer.read(timeout=0.01)  # Quick check
                if event:
                    found_event = True
                    yield event
            
            if not found_event:
                time.sleep(0.1)  # Brief pause if no events
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class StreamProcessor:
    """Process stream events with callbacks"""
    
    def __init__(self, streamer: LogStreamer):
        """
        Initialize stream processor
        
        Args:
            streamer: LogStreamer instance
        """
        self.streamer = streamer
        self._callbacks: List[Callable[[StreamEvent], None]] = []
        self._running = False
        
        logger.info("stream_processor_created")
    
    def add_callback(self, callback: Callable[[StreamEvent], None]) -> None:
        """
        Add callback for stream events
        
        Args:
            callback: Function to call for each event
        """
        self._callbacks.append(callback)
        logger.info("callback_added", total_callbacks=len(self._callbacks))
    
    def process(self, timeout: float = 1.0) -> None:
        """
        Process stream with callbacks
        
        Args:
            timeout: Event read timeout
        """
        self._running = True
        processed = 0
        
        try:
            for event in self.streamer.iter_events(timeout=timeout):
                if not self._running:
                    break
                
                # Execute callbacks
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error("callback_error", error=str(e))
                
                processed += 1
                
                if processed % 1000 == 0:
                    logger.info("stream_processed", count=processed)
        
        except KeyboardInterrupt:
            logger.info("stream_interrupted")
        finally:
            self._running = False
            logger.info("stream_processing_stopped", total_processed=processed)
    
    def stop(self) -> None:
        """Stop processing"""
        self._running = False


def tail_file(file_path: str, lines: int = 10, follow: bool = False, 
              parser_type: str = "syslog") -> Generator[LogEntry, None, None]:
    """
    Tail a log file (like tail -f)
    
    Args:
        file_path: Path to log file
        lines: Number of lines to show initially
        follow: Continue watching file
        parser_type: Parser type to use (default: syslog)
        
    Yields:
        LogEntry objects
    """
    path = Path(file_path)
    parser = LogParserFactory.create_parser(parser_type)
    
    # Read last N lines
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        # Simple tail implementation
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            entry = parser.parse_line(line.strip())
            if entry:
                yield entry
    
    # Follow if requested
    if follow:
        with LogStreamer(file_path, parser_type, follow=True) as streamer:
            for event in streamer.iter_events():
                yield event.entry


class AsyncLogStreamer:
    """Async version of LogStreamer for high-performance streaming"""
    
    def __init__(self, file_path: str, parser_type: str = "auto",
                 buffer_size: int = 1000):
        self.file_path = Path(file_path)
        self.parser_type = parser_type
        self.buffer_size = buffer_size
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        self._parser = None
        self._position = 0
        self._running = False
        
    async def start(self):
        """Start async streaming"""
        self._running = True
        self._parser = LogParserFactory.create_parser(self.parser_type)
        asyncio.create_task(self._stream_worker())
        
    async def stop(self):
        """Stop async streaming"""
        self._running = False
        
    async def _stream_worker(self):
        """Async worker that reads log entries"""
        try:
            async with asyncio.Lock():
                with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                    f.seek(0, 2)  # Seek to end
                    self._position = f.tell()
                    
                    while self._running:
                        line = f.readline()
                        if line:
                            entry = self._parser.parse_line(line.strip())
                            if entry:
                                event = StreamEvent(
                                    entry=entry,
                                    timestamp=datetime.now(),
                                    file_path=str(self.file_path)
                                )
                                await self._queue.put(event)
                            self._position = f.tell()
                        else:
                            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error("async_stream_error", error=str(e))
    
    async def read(self) -> Optional[StreamEvent]:
        """Read next event asynchronously"""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    async def iter_events(self) -> AsyncGenerator[StreamEvent, None]:
        """Async iterator over stream events"""
        while self._running:
            event = await self.read()
            if event:
                yield event


# Export all public classes
__all__ = [
    'LogStreamer',
    'MultiFileStreamer', 
    'StreamProcessor',
    'StreamEvent',
    'AsyncLogStreamer',
    'tail_file'
]
