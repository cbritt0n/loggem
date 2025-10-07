"""HAProxy load balancer log parser."""

import re
from datetime import datetime
from typing import Optional

from .base import BaseParser, LogEntry


class HAProxyParser(BaseParser):
    """Parser for HAProxy load balancer logs."""

    # HAProxy HTTP log format
    # timestamp frontend_name backend_name/server_name timers status bytes headers...
    HTTP_PATTERN = re.compile(
        r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<process>\S+):\s+"
        r"(?P<client_ip>[\d.]+):(?P<client_port>\d+)\s+"
        r"\[(?P<accept_date>[^\]]+)\]\s+"
        r"(?P<frontend>\S+)\s+"
        r"(?P<backend>\S+)/(?P<server>\S+)\s+"
        r"(?P<tq>-?\d+)/(?P<tw>-?\d+)/(?P<tc>-?\d+)/(?P<tr>-?\d+)/(?P<tt>\+?\d+)\s+"
        r"(?P<status>\d{3})\s+"
        r"(?P<bytes>\d+)\s+"
        r".*?"
        r'"(?P<request>[^"]*)"'
    )

    # HAProxy TCP log format
    TCP_PATTERN = re.compile(
        r"(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<process>\S+):\s+"
        r"(?P<client_ip>[\d.]+):(?P<client_port>\d+)\s+"
        r"\[(?P<accept_date>[^\]]+)\]\s+"
        r"(?P<frontend>\S+)\s+"
        r"(?P<backend>\S+)/(?P<server>\S+)\s+"
        r"(?P<tw>-?\d+)/(?P<tc>-?\d+)/(?P<tt>\d+)\s+"
        r"(?P<bytes_read>\d+)\s+"
        r"(?P<termination_state>\S+)"
    )

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single HAProxy log line.

        Args:
            line: Raw log line
            line_number: Line number in file

        Returns:
            Parsed LogEntry or None if parsing fails
        """
        # Try HTTP format
        match = self.HTTP_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                current_year = datetime.now().year
                timestamp = datetime.strptime(
                    f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S"
                )
            except ValueError:
                timestamp = datetime.now()

            status = int(match.group("status"))
            level = "ERROR" if status >= 500 else "WARNING" if status >= 400 else "INFO"

            metadata = {
                "client_ip": match.group("client_ip"),
                "client_port": match.group("client_port"),
                "frontend": match.group("frontend"),
                "backend": match.group("backend"),
                "server": match.group("server"),
                "status": status,
                "bytes": int(match.group("bytes")),
                "request": match.group("request"),
                "timers": {
                    "tq": int(match.group("tq")),
                    "tw": int(match.group("tw")),
                    "tc": int(match.group("tc")),
                    "tr": int(match.group("tr")),
                    "tt": int(match.group("tt")),
                },
                "log_type": "http",
            }

            message = f"{match.group('request')} -> {status}"

            return LogEntry(
                timestamp=timestamp,
                source="haproxy",
                message=message,
                level=level,
                raw=line,
                metadata=metadata,
            )

        # Try TCP format
        match = self.TCP_PATTERN.search(line)
        if match:
            timestamp_str = match.group("timestamp")
            try:
                current_year = datetime.now().year
                timestamp = datetime.strptime(
                    f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S"
                )
            except ValueError:
                timestamp = datetime.now()

            metadata = {
                "client_ip": match.group("client_ip"),
                "client_port": match.group("client_port"),
                "frontend": match.group("frontend"),
                "backend": match.group("backend"),
                "server": match.group("server"),
                "bytes_read": int(match.group("bytes_read")),
                "termination_state": match.group("termination_state"),
                "timers": {
                    "tw": int(match.group("tw")),
                    "tc": int(match.group("tc")),
                    "tt": int(match.group("tt")),
                },
                "log_type": "tcp",
            }

            message = f"TCP connection: {match.group('client_ip')} -> {match.group('backend')}/{match.group('server')}"

            return LogEntry(
                timestamp=timestamp,
                source="haproxy",
                message=message,
                level="INFO",
                raw=line,
                metadata=metadata,
            )

        return None

    def validate(self, sample: str) -> bool:
        """
        Check if sample text appears to be HAProxy logs.

        Args:
            sample: Sample text to validate

        Returns:
            True if appears to be HAProxy format
        """
        return bool(
            self.HTTP_PATTERN.search(sample)
            or self.TCP_PATTERN.search(sample)
            or "haproxy[" in sample.lower()
        )
