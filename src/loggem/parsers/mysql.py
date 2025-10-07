from typing import Optional
"""MySQL database log parser."""

import re
from datetime import datetime

from .base import BaseParser, LogEntry


class MySQLParser(BaseParser):
    """Parser for MySQL database logs."""

    # MySQL error log pattern
    # Format: 2024-01-15T10:30:45.123456Z 0 [Note] Event Scheduler: scheduler thread started
    # Format: 2024-01-15T10:30:45.123456Z 123 [ERROR] Access denied for user 'root'@'localhost'
    LOG_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)\s+"
        r"(?P<thread_id>\d+)\s+"
        r"\[(?P<level>[^\]]+)\]\s+"
        r"(?P<message>.*)"
    )

    # Legacy format (MySQL 5.x)
    LEGACY_PATTERN = re.compile(
        r"(?P<timestamp>\d{6}\s+\d{1,2}:\d{2}:\d{2})\s+"
        r"\[(?P<level>[^\]]+)\]\s+"
        r"(?P<message>.*)"
    )

    # Slow query log
    SLOW_QUERY_PATTERN = re.compile(
        r"# Time: (?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z)"
    )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single MySQL log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        # Try standard format
        match = self.LOG_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                timestamp = datetime.now()

            return LogEntry(
                timestamp=timestamp,
                source="mysql",
                message=match.group("message").strip(),
                level=match.group("level"),
                raw=line,
                metadata={"thread_id": match.group("thread_id")},
            )

        # Try legacy format
        match = self.LEGACY_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                # Format: YYMMDD HH:MM:SS
                timestamp = datetime.strptime(timestamp_str, "%y%m%d %H:%M:%S")
            except ValueError:
                timestamp = datetime.now()

            return LogEntry(
                timestamp=timestamp,
                source="mysql",
                message=match.group("message").strip(),
                level=match.group("level"),
                raw=line,
                metadata={},
            )

        # Try slow query log
        match = self.SLOW_QUERY_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                timestamp = datetime.now()

            return LogEntry(
                timestamp=timestamp,
                source="mysql",
                message="Slow query detected",
                level="WARNING",
                raw=line,
                metadata={"type": "slow_query"},
            )

        return None

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be MySQL logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be MySQL format
        """
        return bool(
            self.LOG_PATTERN.search(sample)
            or self.LEGACY_PATTERN.search(sample)
            or self.SLOW_QUERY_PATTERN.search(sample)
            or "mysqld" in sample.lower()
            or "[mysqld]" in sample.lower()
        )
