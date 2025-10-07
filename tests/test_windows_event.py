"""Tests for Windows Event Log parser"""

import pytest
from datetime import datetime

from loggem.parsers.windows_event import WindowsEventLogParser


@pytest.fixture
def parser():
    """Create Windows Event Log parser"""
    return WindowsEventLogParser()


def test_xml_event_parsing(parser):
    """Test parsing XML formatted Windows Event"""
    xml_event = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'>
    <System>
        <Provider Name='Microsoft-Windows-Security-Auditing' />
        <EventID>4624</EventID>
        <Level>0</Level>
        <TimeCreated SystemTime='2025-10-05T14:30:45.123456Z' />
        <Computer>SERVER01</Computer>
        <Channel>Security</Channel>
    </System>
    <EventData>
        <Data Name='SubjectUserName'>ADMIN</Data>
        <Data Name='TargetUserName'>USER01</Data>
    </EventData>
</Event>"""
    
    entry = parser.parse_line(xml_event)
    
    assert entry is not None
    assert entry.metadata['event_id'] == '4624'
    assert entry.metadata['level'] == 'LogAlways'
    assert entry.metadata['computer'] == 'SERVER01'
    assert entry.metadata['channel'] == 'Security'
    assert 'SubjectUserName' in entry.metadata['event_data']
    assert entry.metadata['log_type'] == 'windows_event'


def test_text_event_parsing(parser):
    """Test parsing text formatted Windows Event"""
    text_event = """Log Name: Security
Source: Microsoft-Windows-Security-Auditing
Date: 10/5/2025 2:30:45 PM
Event ID: 4624
Task Category: Logon
Level: Information
Keywords: Audit Success
User: N/A
Computer: SERVER01
Description: An account was successfully logged on."""
    
    entry = parser.parse_line(text_event)
    
    assert entry is not None
    assert entry.metadata['event_id'] == '4624'
    assert entry.metadata['level'] == 'Information'
    assert entry.metadata['computer'] == 'SERVER01'
    assert entry.metadata['channel'] == 'Security'
    assert entry.metadata['log_type'] == 'windows_event'


def test_security_event_description(parser):
    """Test security event descriptions"""
    desc = parser._get_event_description(4624, 'Security')
    assert desc == 'Account Logon'
    
    desc = parser._get_event_description(4625, 'Security')
    assert desc == 'Account Logon Failed'


def test_system_event_description(parser):
    """Test system event descriptions"""
    desc = parser._get_event_description(6005, 'System')
    assert desc == 'Event Log Service Started'
    
    desc = parser._get_event_description(7034, 'System')
    assert desc == 'Service Crashed Unexpectedly'


def test_validation(parser):
    """Test event validation"""
    # XML format
    assert parser.validate('<Event xmlns="http://schemas.microsoft.com">') is True
    
    # Text format
    assert parser.validate('Event ID: 1234\nLog Name: Application') is True
    
    # Invalid
    assert parser.validate('Just a regular log line') is False
    assert parser.validate('') is False


def test_invalid_xml(parser):
    """Test handling of invalid XML"""
    invalid_xml = "<Event><InvalidTag>"
    entry = parser.parse_line(invalid_xml)
    assert entry is None


def test_minimal_xml_event(parser):
    """Test minimal XML event"""
    minimal = """<Event>
    <System>
        <EventID>1000</EventID>
    </System>
</Event>"""
    
    entry = parser.parse_line(minimal)
    # Parser returns None for invalid events missing timestamp
    # This is expected behavior - events without timestamp are invalid
    assert entry is None


def test_application_event_description(parser):
    """Test application event descriptions"""
    desc = parser._get_event_description(1000, 'Application')
    assert desc == 'Application Error'
    
    desc = parser._get_event_description(1026, 'Application')
    assert desc == '.NET Runtime Error'


def test_unknown_event_id(parser):
    """Test handling of unknown event IDs"""
    desc = parser._get_event_description(99999, 'Security')
    assert desc is None
