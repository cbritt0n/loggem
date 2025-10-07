"""Kubernetes cluster log parser."""

import re
from datetime import datetime

from .base import BaseParser, LogEntry


class KubernetesParser(BaseParser):
    """Parser for Kubernetes cluster logs."""

    # kubectl logs format
    # timestamp level message
    # 2024-01-15T10:30:45.123Z INFO Starting application...
    KUBECTL_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)\s+"
        r"(?P<level>[A-Z]+)\s+"
        r"(?P<message>.*)"
    )

    # Kubernetes event format
    # LAST SEEN   TYPE      REASON              OBJECT                     MESSAGE
    EVENT_PATTERN = re.compile(
        r"(?P<age>\d+[smh])\s+"
        r"(?P<type>Normal|Warning)\s+"
        r"(?P<reason>\S+)\s+"
        r"(?P<object>\S+)\s+"
        r"(?P<message>.*)"
    )

    # Container runtime log (containerd/CRI-O)
    # timestamp stream flags log_message
    RUNTIME_PATTERN = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+"
        r"(?P<stream>stdout|stderr)\s+"
        r"(?P<flags>[FP])\s+"
        r"(?P<message>.*)"
    )

    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """
        Parse a single Kubernetes log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        # Try kubectl logs format
        match = self.KUBECTL_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                timestamp = datetime.strptime(timestamp_str[:26] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    timestamp = datetime.now()

            return LogEntry(
                timestamp=timestamp,
                source="kubernetes",
                message=match.group("message").strip(),
                level=match.group("level"),
                raw=line,
                metadata={"log_type": "application"},
            )

        # Try event format
        match = self.EVENT_PATTERN.search(line)
        if match:
            return LogEntry(
                timestamp=datetime.now(),
                source="kubernetes",
                message=match.group("message").strip(),
                level="WARNING" if match.group("type") == "Warning" else "INFO",
                raw=line,
                metadata={
                    "event_type": match.group("type"),
                    "reason": match.group("reason"),
                    "object": match.group("object"),
                    "age": match.group("age"),
                    "log_type": "event",
                },
            )

        # Try container runtime format
        match = self.RUNTIME_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                timestamp = datetime.strptime(timestamp_str[:26] + "Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                timestamp = datetime.now()

            stream = match.group("stream")
            return LogEntry(
                timestamp=timestamp,
                source="kubernetes",
                message=match.group("message").strip(),
                level="ERROR" if stream == "stderr" else "INFO",
                raw=line,
                metadata={
                    "stream": stream,
                    "flags": match.group("flags"),
                    "log_type": "container",
                },
            )

        return None

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be Kubernetes logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be Kubernetes format
        """
        return bool(
            self.KUBECTL_PATTERN.search(sample)
            or self.EVENT_PATTERN.search(sample)
            or self.RUNTIME_PATTERN.search(sample)
            or "kubectl" in sample.lower()
            or any(
                keyword in sample.lower()
                for keyword in ["pod/", "deployment/", "service/", "namespace/"]
            )
        )
