"""
Syslog parser supporting RFC 3164 and RFC 5424 formats.
"""

from __future__ import annotations
from typing import Optional

import re
from datetime import datetime

from loggem.core.models import LogEntry
from loggem.parsers.base import BaseParser


class SyslogParser(BaseParser):
    """
    Parser for syslog format logs (RFC 3164 and RFC 5424).

    Supports both traditional BSD syslog and modern structured syslog formats.
    """

    # RFC 3164 pattern: <priority>timestamp hostname process[pid]: message
    RFC3164_PATTERN = re.compile(
        r"^(?:<(?P<priority>\d+)>)?"
        r"(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
        r"(?P<message>.*)$"
    )

    # RFC 5424 pattern: <priority>version timestamp hostname app-name procid msgid [structured-data] message
    RFC5424_PATTERN = re.compile(
        r"^<(?P<priority>\d+)>"
        r"(?P<version>\d+)\s+"
        r"(?P<timestamp>\S+)\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<appname>\S+)\s+"
        r"(?P<procid>\S+)\s+"
        r"(?P<msgid>\S+)\s+"
        r"(?P<structured_data>\[.*?\]|-)\s*"
        r"(?P<message>.*)$"
    )

    # Syslog facilities and severities
    FACILITIES = {
        0: "kern",
        1: "user",
        2: "mail",
        3: "daemon",
        4: "auth",
        5: "syslog",
        6: "lpr",
        7: "news",
        8: "uucp",
        9: "cron",
        10: "authpriv",
        11: "ftp",
        16: "local0",
        17: "local1",
        18: "local2",
        19: "local3",
        20: "local4",
        21: "local5",
        22: "local6",
        23: "local7",
    }

    SEVERITIES = {
        0: "EMERGENCY",
        1: "ALERT",
        2: "CRITICAL",
        3: "ERROR",
        4: "WARNING",
        5: "NOTICE",
        6: "INFO",
        7: "DEBUG",
    }

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single syslog line.

        Args:
            line: Raw syslog line
            line_number: Line number for error reporting

        Returns:
            LogEntry or None if line cannot be parsed
        """
        # Try RFC 5424 first (more structured)
        entry = self._parse_rfc5424(line)
        if entry:
            return entry

        # Fall back to RFC 3164
        entry = self._parse_rfc3164(line)
        if entry:
            return entry

        # If both fail, create a basic entry
        self.logger.debug("unstructured_syslog", line=line[:100])
        return LogEntry(
            timestamp=datetime.now(),
            source=self.source_name,
            message=line,
            level="INFO",
            raw=line,
        )

    def _parse_rfc3164(self, line: str) -> Optional[LogEntry]:
        """Parse RFC 3164 format syslog."""
        match = self.RFC3164_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()

        # Parse priority (default to 13 = user.notice if not present)
        priority_str = data.get("priority")
        priority = int(priority_str) if priority_str else 13
        facility = priority >> 3
        severity = priority & 0x07

        # Parse timestamp (BSD syslog format doesn't include year)
        timestamp_str = data["timestamp"]
        timestamp = self._parse_timestamp(
            timestamp_str,
            ["%b %d %H:%M:%S", "%b  %d %H:%M:%S"],  # Note: double space for single digit days
        )
        if not timestamp:
            timestamp = datetime.now()

        # Build metadata
        metadata = {
            "facility": self.FACILITIES.get(facility, f"unknown({facility})"),
            "severity": self.SEVERITIES.get(severity, f"unknown({severity})"),
            "priority": priority,
        }

        if data.get("pid"):
            metadata["pid"] = data["pid"]

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=data["message"],
            level=self.SEVERITIES.get(severity, "INFO"),
            host=data["hostname"],
            process=data["process"],
            metadata=metadata,
            raw=line,
        )

    def _parse_rfc5424(self, line: str) -> Optional[LogEntry]:
        """Parse RFC 5424 format syslog."""
        match = self.RFC5424_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()

        # Parse priority
        priority = int(data["priority"])
        facility = priority >> 3
        severity = priority & 0x07

        # Parse timestamp (ISO 8601 format)
        timestamp = self._parse_timestamp(
            data["timestamp"],
            ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"],
        )
        if not timestamp:
            timestamp = datetime.now()

        # Build metadata
        metadata = {
            "facility": self.FACILITIES.get(facility, f"unknown({facility})"),
            "severity": self.SEVERITIES.get(severity, f"unknown({severity})"),
            "priority": priority,
            "version": data["version"],
            "msgid": data["msgid"],
        }

        # Parse structured data if present
        if data["structured_data"] != "-":
            metadata["structured_data"] = data["structured_data"]

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=data["message"],
            level=self.SEVERITIES.get(severity, "INFO"),
            host=data["hostname"] if data["hostname"] != "-" else None,
            process=data["appname"] if data["appname"] != "-" else None,
            metadata=metadata,
            raw=line,
        )
