"""
Authentication log parser for Linux auth.log and secure logs.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from loggem.core.models import LogEntry
from loggem.parsers.base import BaseParser


class AuthLogParser(BaseParser):
    """
    Parser for Linux authentication logs (auth.log, secure).

    Focuses on security-relevant authentication events like SSH logins,
    sudo usage, and authentication failures.
    """

    # Common auth log pattern
    # Oct  5 10:15:30 hostname sshd[12345]: Failed password for invalid user admin from 192.168.1.1 port 22 ssh2
    AUTH_PATTERN = re.compile(
        r"^(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+"
        r"(?P<hostname>\S+)\s+"
        r"(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
        r"(?P<message>.*)$"
    )

    # SSH-specific patterns
    SSH_PATTERNS = {
        "failed_password": re.compile(
            r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>[\d\.]+) port (?P<port>\d+)"
        ),
        "accepted_password": re.compile(
            r"Accepted password for (?P<user>\S+) from (?P<ip>[\d\.]+) port (?P<port>\d+)"
        ),
        "accepted_publickey": re.compile(
            r"Accepted publickey for (?P<user>\S+) from (?P<ip>[\d\.]+) port (?P<port>\d+)"
        ),
        "invalid_user": re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>[\d\.]+)"),
        "connection_closed": re.compile(
            r"Connection closed by (authenticating user )?(?P<user>\S+)? ?(?P<ip>[\d\.]+) port (?P<port>\d+)"
        ),
    }

    # Sudo patterns
    SUDO_PATTERNS = {
        "sudo_command": re.compile(
            r"(?P<user>\S+) : TTY=(?P<tty>\S+) ; PWD=(?P<pwd>\S+) ; USER=(?P<target_user>\S+) ; COMMAND=(?P<command>.*)"
        ),
        "sudo_failed": re.compile(
            r"(?P<user>\S+) : (?P<failure_count>\d+) incorrect password attempt"
        ),
    }

    def parse_line(self, line: str, line_number: int = 0) -> Optional[LogEntry]:
        """
        Parse a single authentication log line.

        Args:
            line: Raw auth log line
            line_number: Line number for error reporting

        Returns:
            LogEntry or None if line cannot be parsed
        """
        match = self.AUTH_PATTERN.match(line)
        if not match:
            self.logger.debug("unrecognized_auth_format", line=line[:100])
            return None

        data = match.groupdict()

        # Parse timestamp (auth logs don't include year)
        timestamp = self._parse_timestamp(
            data["timestamp"],
            ["%b %d %H:%M:%S", "%b  %d %H:%M:%S"],
        )
        if not timestamp:
            timestamp = datetime.now()

        message = data["message"]
        process = data["process"]

        # Determine log level and extract security events
        level = "INFO"
        metadata = {}
        user = None
        host = None

        # Check for SSH events
        if "sshd" in process.lower():
            level, metadata, user, host = self._parse_ssh_event(message)
        # Check for sudo events
        elif "sudo" in process.lower():
            level, metadata, user = self._parse_sudo_event(message)
        # Check for su events
        elif process in ["su", "su-session"]:
            level = "WARNING" if "failed" in message.lower() else "INFO"
            user = self._extract_user(message)
        # Check for authentication failures
        elif any(
            keyword in message.lower() for keyword in ["failed", "failure", "error", "denied"]
        ):
            level = "WARNING"
            user = self._extract_user(message)
            host = self._extract_ip(message)

        # Add process info to metadata
        if data.get("pid"):
            metadata["pid"] = data["pid"]

        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=message,
            level=level,
            host=host or data["hostname"],
            user=user,
            process=process,
            metadata=metadata,
            raw=line,
        )

    def _parse_ssh_event(self, message: str) -> tuple[str, dict, str | None, str | None]:
        """
        Parse SSH-specific events.

        Returns:
            Tuple of (level, metadata, user, host)
        """
        level = "INFO"
        metadata = {"service": "ssh"}
        user = None
        host = None

        for event_type, pattern in self.SSH_PATTERNS.items():
            match = pattern.search(message)
            if match:
                event_data = match.groupdict()
                metadata["event_type"] = event_type
                metadata.update({k: v for k, v in event_data.items() if v})

                user = event_data.get("user")
                host = event_data.get("ip")

                # Set appropriate level
                if "failed" in event_type or "invalid" in event_type:
                    level = "WARNING"
                elif "accepted" in event_type:
                    level = "INFO"

                break

        return level, metadata, user, host

    def _parse_sudo_event(self, message: str) -> tuple[str, dict, str | None]:
        """
        Parse sudo-specific events.

        Returns:
            Tuple of (level, metadata, user)
        """
        level = "INFO"
        metadata = {"service": "sudo"}
        user = None

        for event_type, pattern in self.SUDO_PATTERNS.items():
            match = pattern.search(message)
            if match:
                event_data = match.groupdict()
                metadata["event_type"] = event_type
                metadata.update({k: v for k, v in event_data.items() if v})

                user = event_data.get("user")

                # Sudo commands are security-relevant
                if "command" in event_type:
                    level = "WARNING"  # All sudo usage is noteworthy
                elif "failed" in event_type:
                    level = "ERROR"

                break

        return level, metadata, user
