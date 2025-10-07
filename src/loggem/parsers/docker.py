"""Docker container log parser."""

import re
from datetime import datetime
from typing import Optional

from .base import BaseParser, LogEntry


class DockerParser(BaseParser):
    """Parser for Docker container logs."""

    # Docker JSON log format
    # {"log":"message\n","stream":"stdout","time":"2024-01-15T10:30:45.123456789Z"}
    JSON_PATTERN = re.compile(
        r'\{"log":"(?P<message>[^"]*)".*?"stream":"(?P<stream>[^"]*)".*?"time":"(?P<timestamp>[^"]*)"\}'
    )

    # Docker compose logs with container name
    # container_name | message
    COMPOSE_PATTERN = re.compile(r"^(?P<container>[^\s|]+)\s*\|\s*(?P<message>.*)")

    # Standard Docker CLI output
    # timestamp container_id message
    CLI_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+"
        r"(?P<container_id>[a-f0-9]{12})\s+"
        r"(?P<message>.*)"
    )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single Docker log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        # Try JSON format
        match = self.JSON_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                # ISO 8601 format with nanoseconds
                timestamp = datetime.strptime(timestamp_str[:26] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                timestamp = datetime.now()

            message = match.group("message").replace("\\n", "\n").replace('\\"', '"')
            stream = match.group("stream")

            return LogEntry(
                timestamp=timestamp,
                source="docker",
                message=message.strip(),
                level="INFO" if stream == "stdout" else "ERROR",
                raw=line,
                metadata={"stream": stream},
            )

        # Try Docker Compose format
        match = self.COMPOSE_PATTERN.search(line)
        if match:
            return LogEntry(
                timestamp=datetime.now(),
                source="docker",
                message=match.group("message").strip(),
                level="INFO",
                raw=line,
                metadata={"container": match.group("container")},
            )

        # Try CLI format
        match = self.CLI_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                timestamp = datetime.strptime(timestamp_str[:26] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                timestamp = datetime.now()

            return LogEntry(
                timestamp=timestamp,
                source="docker",
                message=match.group("message").strip(),
                level="INFO",
                raw=line,
                metadata={"container_id": match.group("container_id")},
            )

        # Fallback: treat as plain Docker log
        if line.strip():
            return LogEntry(
                timestamp=datetime.now(),
                source="docker",
                message=line.strip(),
                level="INFO",
                raw=line,
                metadata={},
            )

        return None

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be Docker logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be Docker format
        """
        return bool(
            self.JSON_PATTERN.search(sample)
            or self.COMPOSE_PATTERN.search(sample)
            or self.CLI_PATTERN.search(sample)
            or '"stream":"std' in sample
        )
