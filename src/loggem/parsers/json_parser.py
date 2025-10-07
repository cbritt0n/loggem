"""
JSON log parser for structured application logs.
"""

from __future__ import annotations

import json
from datetime import datetime

from loggem.core.models import LogEntry
from loggem.parsers.base import BaseParser


class JSONParser(BaseParser):
    """
    Parser for JSON-formatted logs.

    Handles various JSON log formats from applications, containers, and cloud services.
    """

    # Common timestamp field names
    TIMESTAMP_FIELDS = [
        "timestamp",
        "time",
        "@timestamp",
        "datetime",
        "ts",
        "date",
        "created_at",
    ]

    # Common message field names
    MESSAGE_FIELDS = [
        "message",
        "msg",
        "text",
        "log",
        "content",
        "body",
    ]

    # Common level field names
    LEVEL_FIELDS = [
        "level",
        "severity",
        "log_level",
        "loglevel",
        "priority",
    ]

    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """
        Parse a single JSON log line.

        Args:
            line: Raw JSON log line
            line_number: Line number for error reporting

        Returns:
            LogEntry or None if line cannot be parsed
        """
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            self.logger.warning(
                "invalid_json",
                line_number=line_number,
                error=str(e),
                line=line[:100],
            )
            return None

        if not isinstance(data, dict):
            self.logger.warning("json_not_object", line_number=line_number)
            return None

        # Extract timestamp
        timestamp = self._extract_timestamp(data)
        if not timestamp:
            timestamp = datetime.now()

        # Extract message
        message = self._extract_message(data)
        if not message:
            # If no message field, use entire JSON as message
            message = line

        # Extract level
        level = self._extract_level(data)

        # Extract common fields
        host = self._extract_field(data, ["host", "hostname", "server", "node"])
        user = self._extract_field(data, ["user", "username", "uid", "account"])
        process = self._extract_field(data, ["process", "service", "application", "app"])

        # Store remaining fields as metadata
        metadata = {k: v for k, v in data.items() if k not in ["message", "msg", "text"]}

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=message,
            level=level,
            host=host,
            user=user,
            process=process,
            metadata=metadata,
            raw=line,
        )

    def _extract_timestamp(self, data: dict) -> datetime | None:
        """Extract timestamp from JSON data."""
        for field in self.TIMESTAMP_FIELDS:
            if field in data:
                value = data[field]

                # Handle numeric timestamps (Unix epoch)
                if isinstance(value, (int, float)):
                    try:
                        # Assume milliseconds if value is too large for seconds
                        if value > 1e10:
                            return datetime.fromtimestamp(value / 1000)
                        return datetime.fromtimestamp(value)
                    except (ValueError, OSError):
                        continue

                # Handle string timestamps
                if isinstance(value, str):
                    parsed = self._parse_timestamp(
                        value,
                        [
                            "%Y-%m-%dT%H:%M:%S.%fZ",
                            "%Y-%m-%dT%H:%M:%SZ",
                            "%Y-%m-%dT%H:%M:%S%z",
                            "%Y-%m-%d %H:%M:%S",
                            "%Y/%m/%d %H:%M:%S",
                        ],
                    )
                    if parsed:
                        return parsed

        return None

    def _extract_message(self, data: dict) -> str | None:
        """Extract message from JSON data."""
        for field in self.MESSAGE_FIELDS:
            if field in data:
                value = data[field]
                if isinstance(value, str):
                    return value
                # Convert non-string values to string
                return str(value)
        return None

    def _extract_level(self, data: dict) -> str:
        """Extract log level from JSON data."""
        for field in self.LEVEL_FIELDS:
            if field in data:
                level = str(data[field]).upper()
                # Normalize common level names
                level_map = {
                    "TRACE": "DEBUG",
                    "VERBOSE": "DEBUG",
                    "WARN": "WARNING",
                    "ERR": "ERROR",
                    "FATAL": "CRITICAL",
                    "EMERG": "CRITICAL",
                    "EMERGENCY": "CRITICAL",
                }
                return level_map.get(level, level)
        return "INFO"

    def _extract_field(self, data: dict, possible_keys: list[str]) -> str | None:
        """Extract a field from JSON data given possible key names."""
        for key in possible_keys:
            if key in data:
                value = data[key]
                if value and isinstance(value, (str, int, float)):
                    return str(value)
        return None
