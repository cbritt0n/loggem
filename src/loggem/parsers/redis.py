"""Redis database log parser."""

import re
from datetime import datetime

from .base import BaseParser, LogEntry


class RedisParser(BaseParser):
    """Parser for Redis database logs."""

    # Redis log pattern
    # pid:role timestamp * level message
    # 1234:M 15 Jan 2024 10:30:45.123 * Server started, Redis version 7.0.0
    # 1234:M 15 Jan 2024 10:30:45.123 # WARNING overcommit_memory is set to 0
    LOG_PATTERN = re.compile(
        r"(?P<pid>\d+):(?P<role>[CMSX])\s+"
        r"(?P<day>\d{1,2})\s+(?P<month>\w{3})\s+(?P<year>\d{4})\s+"
        r"(?P<time>\d{2}:\d{2}:\d{2}\.\d{3})\s+"
        r"(?P<level>[*#\-.])\s+"
        r"(?P<message>.*)"
    )

    # Role mapping
    ROLE_MAP = {"M": "master", "C": "child", "S": "sentinel", "X": "cluster"}

    # Level mapping
    LEVEL_MAP = {"*": "INFO", "#": "WARNING", "-": "NOTICE", ".": "DEBUG"}

    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """
        Parse a single Redis log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        match = self.LOG_PATTERN.search(line)
        if not match:
            return None

        # Parse timestamp
        try:
            timestamp_str = (
                f"{match.group('day')} {match.group('month')} "
                f"{match.group('year')} {match.group('time')}"
            )
            timestamp = datetime.strptime(timestamp_str, "%d %b %Y %H:%M:%S.%f")
        except ValueError:
            timestamp = datetime.now()

        level_char = match.group("level")
        level = self.LEVEL_MAP.get(level_char, "INFO")

        role_char = match.group("role")
        role = self.ROLE_MAP.get(role_char, "unknown")

        message = match.group("message").strip()

        metadata = {"pid": match.group("pid"), "role": role, "level_char": level_char}

        # Detect specific Redis events
        if "starting" in message.lower() or "ready to accept" in message.lower():
            metadata["event"] = "startup"
        elif "shutdown" in message.lower() or "signal received" in message.lower():
            metadata["event"] = "shutdown"
        elif "saving" in message.lower() or "background save" in message.lower():
            metadata["event"] = "persistence"
        elif "replica" in message.lower() or "master" in message.lower():
            metadata["event"] = "replication"
        elif "warning" in message.lower():
            level = "WARNING"

        return LogEntry(
            timestamp=timestamp,
            source="redis",
            message=message,
            level=level,
            raw=line,
            metadata=metadata,
        )

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be Redis logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be Redis format
        """
        return bool(
            self.LOG_PATTERN.search(sample)
            or "redis" in sample.lower()
            or ":M " in sample
            or ":C " in sample
            or ":S " in sample
        )
