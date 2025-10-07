from typing import Optional
"""PostgreSQL database log parser."""

import re
from datetime import datetime

from .base import BaseParser, LogEntry


class PostgreSQLParser(BaseParser):
    """Parser for PostgreSQL database logs."""

    # PostgreSQL log patterns
    # Format: timestamp [pid] LOG:  statement: SELECT ...
    # Format: timestamp [pid] ERROR:  syntax error at or near "..."
    LOG_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?(?: [A-Z]{3,4})?)\s+"
        r"\[(?P<pid>\d+)\]\s+"
        r"(?P<level>[A-Z]+):\s+"
        r"(?P<message>.*)"
    )

    # CSV log format (common with log_destination = 'csvlog')
    CSV_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?(?: [A-Z]{3,4})?),.*?"
        r",(?P<level>[A-Z]+),"
    )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single PostgreSQL log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        match = self.LOG_PATTERN.search(line)
        if not match:
            # Try CSV format
            match = self.CSV_PATTERN.search(line)
            if not match:
                return None

        timestamp_str = match.group("timestamp")
        try:
            # Try multiple timestamp formats
            for fmt in [
                "%Y-%m-%d %H:%M:%S.%f %Z",
                "%Y-%m-%d %H:%M:%S %Z",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
            ]:
                try:
                    timestamp = datetime.strptime(timestamp_str.strip(), fmt)
                    break
                except ValueError:
                    continue
            else:
                timestamp = datetime.now()
        except Exception:
            timestamp = datetime.now()

        level = match.group("level")
        message = match.group("message") if "message" in match.groupdict() else line

        # Extract metadata
        metadata = {"pid": match.group("pid")} if "pid" in match.groupdict() else {}

        # Detect SQL queries
        if "statement:" in message.lower() or "query:" in message.lower():
            metadata["type"] = "query"
        elif "error" in level.lower():
            metadata["type"] = "error"
        elif "fatal" in level.lower():
            metadata["type"] = "fatal"
        elif "warning" in level.lower():
            metadata["type"] = "warning"

        return LogEntry(
            timestamp=timestamp,
            source="postgresql",
            message=message.strip(),
            level=level,
            raw=line,
            metadata=metadata,
        )

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be PostgreSQL logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be PostgreSQL format
        """
        return bool(
            self.LOG_PATTERN.search(sample)
            or self.CSV_PATTERN.search(sample)
            or "postgres" in sample.lower()
            or "[postgres]" in sample.lower()
        )
