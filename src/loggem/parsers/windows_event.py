"""
Windows Event Log Parser for LogGem.

Supports parsing Windows Event Logs in XML and EVTX formats:
- Security logs
- Application logs
- System logs
- Custom event logs
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

from ..core.logging import get_logger
from ..core.models import LogEntry
from .base import BaseParser

logger = get_logger(__name__)


class WindowsEventLogParser(BaseParser):
    """Parser for Windows Event Logs"""

    # Windows Event Log XML namespaces
    NAMESPACES = {"evt": "http://schemas.microsoft.com/win/2004/08/events/event"}

    # Event levels
    EVENT_LEVELS = {
        "0": "LogAlways",
        "1": "Critical",
        "2": "Error",
        "3": "Warning",
        "4": "Information",
        "5": "Verbose",
    }

    # Common event IDs by category
    SECURITY_EVENTS = {
        4624: "Account Logon",
        4625: "Account Logon Failed",
        4634: "Account Logoff",
        4648: "Logon using explicit credentials",
        4672: "Special privileges assigned",
        4720: "User account created",
        4722: "User account enabled",
        4723: "User account password change attempt",
        4725: "User account disabled",
        4726: "User account deleted",
        4732: "Member added to security-enabled local group",
        4735: "Security-enabled local group changed",
        4738: "User account changed",
        4740: "User account locked out",
        4756: "Member added to security-enabled universal group",
    }

    SYSTEM_EVENTS = {
        6005: "Event Log Service Started",
        6006: "Event Log Service Stopped",
        6008: "Unexpected System Shutdown",
        6009: "System Boot",
        6013: "System Uptime",
        7000: "Service Start Failed",
        7001: "Service Start Error",
        7026: "Boot-start driver failed",
        7031: "Service Crashed",
        7034: "Service Crashed Unexpectedly",
    }

    APPLICATION_EVENTS = {
        1000: "Application Error",
        1001: "Windows Error Reporting",
        1002: "Application Hang",
        1026: ".NET Runtime Error",
    }

    def __init__(self):
        """Initialize Windows Event Log parser"""
        super().__init__()
        logger.info("windows_event_parser_initialized")

    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a Windows Event Log entry

        Supports:
        - XML format (exported event logs)
        - Plain text format (event log viewer copy)

        Args:
            line: Log line to parse

        Returns:
            LogEntry or None if parsing fails
        """
        if not line or not line.strip():
            return None

        # Try XML format first
        if line.strip().startswith("<Event"):
            return self._parse_xml_event(line)

        # Try plain text format
        return self._parse_text_event(line)

    def _parse_xml_event(self, xml_string: str) -> Optional[LogEntry]:
        """
        Parse XML-formatted Windows Event

        Args:
            xml_string: XML event string

        Returns:
            LogEntry or None
        """
        try:
            root = ET.fromstring(xml_string)

            # Remove namespace from tags for easier parsing
            for elem in root.iter():
                if "}" in elem.tag:
                    elem.tag = elem.tag.split("}", 1)[1]

            # Extract System section
            system = root.find("System")
            if system is None:
                return None

            # Extract event metadata
            event_id_elem = system.find(".//EventID")
            level_elem = system.find(".//Level")
            time_created = system.find(".//TimeCreated")
            provider_elem = system.find(".//Provider")
            computer_elem = system.find(".//Computer")
            channel_elem = system.find(".//Channel")

            event_id = event_id_elem.text if event_id_elem is not None else "Unknown"
            level = level_elem.text if level_elem is not None else "4"
            level_name = self.EVENT_LEVELS.get(level, "Information")

            timestamp_str = time_created.get("SystemTime") if time_created is not None else None
            timestamp = self._parse_timestamp(timestamp_str) if timestamp_str else None

            provider = provider_elem.get("Name") if provider_elem is not None else "Unknown"
            computer = computer_elem.text if computer_elem is not None else "Unknown"
            channel = channel_elem.text if channel_elem is not None else "Unknown"

            # Extract EventData
            event_data = root.find(".//EventData")
            data_items = {}
            if event_data is not None:
                for data in event_data.findall(".//Data"):
                    name = data.get("Name")
                    if name:
                        data_items[name] = data.text or ""

            # Get event description
            event_description = self._get_event_description(int(event_id), channel)

            # Build message
            message_parts = [
                f"EventID: {event_id}",
                f"Level: {level_name}",
                f"Source: {provider}",
                f"Computer: {computer}",
                f"Channel: {channel}",
            ]

            if event_description:
                message_parts.append(f"Description: {event_description}")

            if data_items:
                message_parts.append(f"Data: {data_items}")

            message = " | ".join(message_parts)

            # Create metadata
            metadata = {
                "event_id": event_id,
                "level": level_name,
                "provider": provider,
                "computer": computer,
                "channel": channel,
                "event_data": data_items,
                "log_type": "windows_event",
            }

            if event_description:
                metadata["event_description"] = event_description

            return LogEntry(
                timestamp=timestamp,
                source="windows_event",
                message=message,
                raw=xml_string.strip(),
                metadata=metadata,
            )

        except ET.ParseError as e:
            logger.debug("xml_parse_error", error=str(e))
            return None
        except Exception as e:
            logger.error("windows_event_parse_error", error=str(e))
            return None

    def _parse_text_event(self, text: str) -> Optional[LogEntry]:
        """
        Parse plain text Windows Event (from Event Viewer copy)

        Format example:
        Log Name: Security
        Source: Microsoft-Windows-Security-Auditing
        Date: 10/5/2025 2:30:45 PM
        Event ID: 4624
        Task Category: Logon
        Level: Information
        Keywords: Audit Success
        User: N/A
        Computer: SERVER01
        Description: An account was successfully logged on.

        Args:
            text: Plain text event

        Returns:
            LogEntry or None
        """
        try:
            lines = text.strip().split("\n")
            metadata = {"log_type": "windows_event"}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    value = value.strip()

                    if key == "date":
                        timestamp = self._parse_text_timestamp(value)
                        metadata["timestamp"] = value
                    elif key == "event_id":
                        metadata["event_id"] = value
                    elif key == "level":
                        metadata["level"] = value
                    elif key == "source":
                        metadata["provider"] = value
                    elif key == "computer":
                        metadata["computer"] = value
                    elif key == "log_name":
                        metadata["channel"] = value
                    elif key == "description":
                        metadata["description"] = value
                    else:
                        metadata[key] = value

            # Build message
            event_id = metadata.get("event_id", "Unknown")
            level = metadata.get("level", "Information")
            channel = metadata.get("channel", "Unknown")
            description = metadata.get("description", "")

            message = f"EventID: {event_id} | Level: {level} | Channel: {channel}"
            if description:
                message += f" | {description}"

            timestamp = self._parse_text_timestamp(metadata.get("timestamp", ""))

            return LogEntry(
                timestamp=timestamp,
                source="windows_event",
                message=message,
                raw=text.strip(),
                metadata=metadata,
            )

        except Exception as e:
            logger.error("text_event_parse_error", error=str(e))
            return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Windows Event timestamp (ISO format)"""
        try:
            # Windows uses ISO 8601 with Z suffix
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except:
            return None

    def _parse_text_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse text format timestamp"""
        formats = [
            "%m/%d/%Y %I:%M:%S %p",  # 10/5/2025 2:30:45 PM
            "%m/%d/%Y %H:%M:%S",  # 10/5/2025 14:30:45
            "%Y-%m-%d %H:%M:%S",  # 2025-10-05 14:30:45
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except:
                continue

        return None

    def _get_event_description(self, event_id: int, channel: str) -> Optional[str]:
        """Get human-readable description for event ID"""
        channel_lower = channel.lower()

        if "security" in channel_lower:
            return self.SECURITY_EVENTS.get(event_id)
        if "system" in channel_lower:
            return self.SYSTEM_EVENTS.get(event_id)
        if "application" in channel_lower:
            return self.APPLICATION_EVENTS.get(event_id)

        return None

    def validate(self, line: str) -> bool:
        """
        Validate if line is a Windows Event Log entry

        Args:
            line: Line to validate

        Returns:
            True if valid Windows Event Log format
        """
        if not line:
            return False

        # Check for XML format
        if line.strip().startswith("<Event"):
            return True

        # Check for text format
        return bool("Event ID:" in line or "Log Name:" in line)


# Export parser
__all__ = ["WindowsEventLogParser"]
