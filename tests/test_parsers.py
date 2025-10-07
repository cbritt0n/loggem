"""
Unit tests for syslog parser.
"""

import pytest
from datetime import datetime
from loggem.parsers.syslog import SyslogParser
from loggem.core.models import LogEntry


class TestSyslogParser:
    """Test cases for SyslogParser."""

    def test_parse_rfc3164_basic(self):
        """Test parsing basic RFC 3164 format."""
        parser = SyslogParser(source_name="test")
        line = "Oct  5 10:15:30 hostname sshd[12345]: Failed password for user from 192.168.1.1"
        
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.host == "hostname"
        assert entry.process == "sshd"
        assert "Failed password" in entry.message
        assert entry.metadata["pid"] == "12345"

    def test_parse_rfc3164_with_priority(self):
        """Test parsing RFC 3164 with priority."""
        parser = SyslogParser(source_name="test")
        line = "<34>Oct  5 10:15:30 hostname sshd[12345]: Connection established"
        
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.metadata["priority"] == 34
        assert entry.metadata["facility"] == "auth"
        assert entry.metadata["severity"] == "CRITICAL"

    def test_parse_rfc5424_basic(self):
        """Test parsing RFC 5424 format."""
        parser = SyslogParser(source_name="test")
        line = '<34>1 2023-10-05T10:15:30.123Z hostname app 12345 ID47 - Test message'
        
        entry = parser.parse_line(line)
        
        assert entry is not None
        assert entry.host == "hostname"
        assert entry.process == "app"
        assert entry.message == "Test message"
        assert entry.metadata["version"] == "1"
        assert entry.metadata["msgid"] == "ID47"

    def test_parse_empty_line(self):
        """Test parsing empty line."""
        parser = SyslogParser(source_name="test")
        lines = ["", "  ", "\n"]
        
        for line in lines:
            entry = parser.parse_line(line)
            # Empty lines should still create entries with the raw line
            assert entry is not None

    def test_parse_malformed_line(self):
        """Test parsing malformed line."""
        parser = SyslogParser(source_name="test")
        line = "This is not a valid syslog line"
        
        entry = parser.parse_line(line)
        
        # Should create a basic entry even if format doesn't match
        assert entry is not None
        assert entry.message == line


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
