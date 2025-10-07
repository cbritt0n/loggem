"""
Nginx access and error log parser.
"""

from __future__ import annotations

import re
from datetime import datetime

from loggem.core.models import LogEntry
from loggem.parsers.base import BaseParser


class NginxParser(BaseParser):
    """
    Parser for Nginx access and error logs.

    Supports combined log format and common error log formats.
    """

    # Nginx combined log format:
    # $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"
    ACCESS_LOG_PATTERN = re.compile(
        r'^(?P<remote_addr>[\d\.]+)\s+-\s+'
        r'(?P<remote_user>\S+)\s+'
        r'\[(?P<time_local>[^\]]+)\]\s+'
        r'"(?P<request>[^"]*)"\s+'
        r'(?P<status>\d{3})\s+'
        r'(?P<body_bytes_sent>\d+)\s+'
        r'"(?P<http_referer>[^"]*)"\s+'
        r'"(?P<http_user_agent>[^"]*)"'
    )

    # Nginx error log format:
    # 2023/10/05 10:15:30 [level] pid#tid: *connection_id message
    ERROR_LOG_PATTERN = re.compile(
        r'^(?P<timestamp>\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+'
        r'\[(?P<level>\w+)\]\s+'
        r'(?P<pid>\d+)#(?P<tid>\d+):\s+'
        r'(?:\*(?P<connection_id>\d+)\s+)?'
        r'(?P<message>.*)$'
    )

    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """
        Parse a single Nginx log line.

        Args:
            line: Raw Nginx log line
            line_number: Line number for error reporting

        Returns:
            LogEntry or None if line cannot be parsed
        """
        # Try access log format first
        entry = self._parse_access_log(line)
        if entry:
            return entry

        # Try error log format
        entry = self._parse_error_log(line)
        if entry:
            return entry

        # If both fail, return None
        self.logger.debug("unrecognized_nginx_format", line=line[:100])
        return None

    def _parse_access_log(self, line: str) -> LogEntry | None:
        """Parse Nginx access log line."""
        match = self.ACCESS_LOG_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()

        # Parse timestamp
        timestamp = self._parse_timestamp(
            data["time_local"],
            ["%d/%b/%Y:%H:%M:%S %z", "%d/%b/%Y:%H:%M:%S"],
        )
        if not timestamp:
            timestamp = datetime.now()

        # Parse request
        request = data["request"]
        method, path, protocol = self._parse_request(request)

        # Determine level based on status code
        status = int(data["status"])
        if status >= 500:
            level = "ERROR"
        elif status >= 400:
            level = "WARNING"
        else:
            level = "INFO"

        # Build metadata
        metadata = {
            "remote_addr": data["remote_addr"],
            "remote_user": data["remote_user"] if data["remote_user"] != "-" else None,
            "status": status,
            "body_bytes_sent": int(data["body_bytes_sent"]),
            "http_referer": data["http_referer"] if data["http_referer"] != "-" else None,
            "http_user_agent": data["http_user_agent"],
            "method": method,
            "path": path,
            "protocol": protocol,
        }

        # Create message
        message = f"{method} {path} {protocol} - {status}"

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=message,
            level=level,
            host=data["remote_addr"],
            user=data["remote_user"] if data["remote_user"] != "-" else None,
            metadata=metadata,
            raw=line,
        )

    def _parse_error_log(self, line: str) -> LogEntry | None:
        """Parse Nginx error log line."""
        match = self.ERROR_LOG_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()

        # Parse timestamp
        timestamp = self._parse_timestamp(
            data["timestamp"],
            ["%Y/%m/%d %H:%M:%S"],
        )
        if not timestamp:
            timestamp = datetime.now()

        # Normalize level
        level = data["level"].upper()
        level_map = {
            "EMERG": "CRITICAL",
            "ALERT": "CRITICAL",
            "CRIT": "CRITICAL",
            "ERR": "ERROR",
            "WARN": "WARNING",
            "NOTICE": "INFO",
            "INFO": "INFO",
            "DEBUG": "DEBUG",
        }
        level = level_map.get(level, level)

        # Build metadata
        metadata = {
            "pid": data["pid"],
            "tid": data["tid"],
        }
        if data.get("connection_id"):
            metadata["connection_id"] = data["connection_id"]

        # Extract client IP from message if present
        client_ip = self._extract_ip(data["message"])

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=data["message"],
            level=level,
            host=client_ip,
            process=f"nginx[{data['pid']}]",
            metadata=metadata,
            raw=line,
        )

    def _parse_request(self, request: str) -> tuple[str, str, str]:
        """
        Parse HTTP request string.

        Returns:
            Tuple of (method, path, protocol)
        """
        parts = request.split()
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return parts[0], parts[1], "HTTP/1.0"
        elif len(parts) == 1:
            return "GET", parts[0], "HTTP/1.0"
        else:
            return "UNKNOWN", "/", "HTTP/1.0"
