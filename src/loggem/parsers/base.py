"""
Base parser interface for log parsers.

All log parsers inherit from BaseParser and implement the parse methods.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from loggem.core.config import get_settings
from loggem.core.logging import get_logger
from loggem.core.models import LogEntry

logger = get_logger(__name__)


class ParserError(Exception):
    """Raised when parsing fails."""

    pass


class BaseParser(ABC):
    """
    Abstract base class for log parsers.

    All parsers must implement parse_line() and can optionally override
    parse_file() for optimized batch parsing.
    """

    def __init__(self, source_name: str = "unknown") -> None:
        """
        Initialize parser.

        Args:
            source_name: Name to identify the source of logs
        """
        self.source_name = source_name
        self.settings = get_settings()
        self.max_line_length = self.settings.security.max_line_length
        self.logger = logger.bind(parser=self.__class__.__name__)

    @abstractmethod
    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """
        Parse a single log line.

        Args:
            line: Raw log line to parse
            line_number: Line number in the file (for error reporting)

        Returns:
            LogEntry if parsing succeeded, None if line should be skipped

        Raises:
            ParserError: If parsing fails critically
        """
        pass

    def parse_file(self, file_path: Path) -> Iterator[LogEntry]:
        """
        Parse an entire log file.

        Args:
            file_path: Path to the log file

        Yields:
            LogEntry objects for each successfully parsed line

        Raises:
            ParserError: If file cannot be read or parsing fails
        """
        if not file_path.exists():
            raise ParserError(f"File not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.settings.security.max_file_size:
            raise ParserError(
                f"File too large: {file_size} bytes (max: {self.settings.security.max_file_size})"
            )

        self.logger.info("parsing_file", path=str(file_path), size=file_size)

        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                for line_number, line in enumerate(f, start=1):
                    # Skip empty lines
                    if not line.strip():
                        continue

                    # Enforce line length limit
                    if len(line) > self.max_line_length:
                        self.logger.warning(
                            "line_too_long",
                            line_number=line_number,
                            length=len(line),
                            max=self.max_line_length,
                        )
                        line = line[: self.max_line_length]

                    try:
                        entry = self.parse_line(line.rstrip("\n"), line_number)
                        if entry:
                            yield entry
                    except Exception as e:
                        self.logger.warning(
                            "parse_error",
                            line_number=line_number,
                            error=str(e),
                            line=line[:100],  # Log first 100 chars
                        )
                        continue

        except Exception as e:
            raise ParserError(f"Failed to read file {file_path}: {e}") from e

    def parse_lines(self, lines: list[str]) -> list[LogEntry]:
        """
        Parse multiple log lines.

        Args:
            lines: List of raw log lines

        Returns:
            List of successfully parsed LogEntry objects
        """
        entries = []
        for i, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            try:
                entry = self.parse_line(line.rstrip("\n"), i)
                if entry:
                    entries.append(entry)
            except Exception as e:
                self.logger.warning("parse_error", line_number=i, error=str(e))
                continue

        return entries

    def _parse_timestamp(self, timestamp_str: str, formats: list[str]) -> datetime | None:
        """
        Try to parse timestamp using multiple formats.

        Args:
            timestamp_str: Timestamp string to parse
            formats: List of strftime format strings to try

        Returns:
            Parsed datetime or None if all formats fail
        """
        from dateutil import parser as dateutil_parser

        # First try dateutil for flexibility
        try:
            return dateutil_parser.parse(timestamp_str)
        except Exception:
            pass

        # Try specific formats
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        return None

    def _extract_user(self, text: str) -> str | None:
        """
        Extract username from text using common patterns.

        Args:
            text: Text to search for username

        Returns:
            Extracted username or None
        """
        patterns = [
            r"user[=:]?\s*([a-zA-Z0-9_-]+)",
            r"for\s+([a-zA-Z0-9_-]+)",
            r"by\s+([a-zA-Z0-9_-]+)",
            r"from\s+user\s+([a-zA-Z0-9_-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_ip(self, text: str) -> str | None:
        """
        Extract IP address from text.

        Args:
            text: Text to search for IP address

        Returns:
            Extracted IP address or None
        """
        # IPv4 pattern
        ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        match = re.search(ipv4_pattern, text)
        if match:
            return match.group(0)

        # IPv6 pattern (simplified)
        ipv6_pattern = r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"
        match = re.search(ipv6_pattern, text)
        if match:
            return match.group(0)

        return None
