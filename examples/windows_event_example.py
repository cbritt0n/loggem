"""
Example: Windows Event Log Parsing

Demonstrates:
- Parsing XML Windows Event Logs
- Parsing text format events
- Security, System, and Application logs
- Event ID mapping and descriptions
"""

from loggem.parsers.windows_event import WindowsEventLogParser


def parse_xml_events():
    """Parse XML-formatted Windows Event Logs"""
    print("=== XML Event Log Parsing ===\n")
    
    parser = WindowsEventLogParser()
    
    # Sample XML events
    security_event = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'>
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
        <Data Name='TargetUserName'>JohnDoe</Data>
        <Data Name='LogonType'>3</Data>
    </EventData>
</Event>"""
    
    system_event = """<Event xmlns='http://schemas.microsoft.com/win/2004/08/events/event'>
    <System>
        <Provider Name='Microsoft-Windows-Kernel-General' />
        <EventID>6008</EventID>
        <Level>2</Level>
        <TimeCreated SystemTime='2025-10-05T08:15:30.000000Z' />
        <Computer>WORKSTATION</Computer>
        <Channel>System</Channel>
    </System>
    <EventData>
        <Data>Unexpected shutdown</Data>
    </EventData>
</Event>"""
    
    # Parse security event
    entry = parser.parse_line(security_event)
    if entry:
        print("Security Event (4624 - Account Logon):")
        print(f"  Computer: {entry.metadata['computer']}")
        print(f"  Level: {entry.metadata['level']}")
        print(f"  Event ID: {entry.metadata['event_id']}")
        print(f"  Description: {entry.metadata.get('event_description', 'N/A')}")
        print(f"  User: {entry.metadata['event_data'].get('TargetUserName', 'N/A')}")
        print()
    
    # Parse system event
    entry = parser.parse_line(system_event)
    if entry:
        print("System Event (6008 - Unexpected Shutdown):")
        print(f"  Computer: {entry.metadata['computer']}")
        print(f"  Level: {entry.metadata['level']}")
        print(f"  Event ID: {entry.metadata['event_id']}")
        print(f"  Description: {entry.metadata.get('event_description', 'N/A')}")
        print()


def parse_text_events():
    """Parse text-formatted Windows Event Logs"""
    print("\n=== Text Event Log Parsing ===\n")
    
    parser = WindowsEventLogParser()
    
    # Sample text event (from Event Viewer copy)
    text_event = """Log Name: Application
Source: Application Error
Date: 10/5/2025 2:30:45 PM
Event ID: 1000
Task Category: (100)
Level: Error
Keywords: Classic
User: N/A
Computer: DESKTOP-ABC123
Description: Faulting application name: app.exe, version: 1.0.0.0, time stamp: 0x12345678
Faulting module name: kernel32.dll, version: 10.0.19041.1, time stamp: 0x87654321"""
    
    entry = parser.parse_line(text_event)
    if entry:
        print("Application Error Event:")
        print(f"  Computer: {entry.metadata.get('computer', 'N/A')}")
        print(f"  Event ID: {entry.metadata.get('event_id', 'N/A')}")
        print(f"  Level: {entry.metadata.get('level', 'N/A')}")
        print(f"  Channel: {entry.metadata.get('channel', 'N/A')}")
        print(f"  Source: {entry.metadata.get('source', 'N/A')}")
        print(f"  Description: {entry.metadata.get('description', 'N/A')[:80]}...")
        print()


def common_security_events():
    """Show common Windows Security event IDs"""
    print("\n=== Common Security Event IDs ===\n")
    
    parser = WindowsEventLogParser()
    
    security_events = [
        (4624, "Account Logon"),
        (4625, "Account Logon Failed"),
        (4634, "Account Logoff"),
        (4720, "User account created"),
        (4726, "User account deleted"),
        (4740, "User account locked out")
    ]
    
    print("Security Event IDs:")
    for event_id, description in security_events:
        desc = parser._get_event_description(event_id, "Security")
        status = "✓" if desc else "✗"
        print(f"  {status} {event_id}: {description}")
    print()


def common_system_events():
    """Show common Windows System event IDs"""
    print("\n=== Common System Event IDs ===\n")
    
    parser = WindowsEventLogParser()
    
    system_events = [
        (6005, "Event Log Service Started"),
        (6006, "Event Log Service Stopped"),
        (6008, "Unexpected System Shutdown"),
        (7000, "Service Start Failed"),
        (7034, "Service Crashed Unexpectedly")
    ]
    
    print("System Event IDs:")
    for event_id, description in system_events:
        desc = parser._get_event_description(event_id, "System")
        status = "✓" if desc else "✗"
        print(f"  {status} {event_id}: {description}")
    print()


def parse_critical_events():
    """Parse and identify critical Windows events"""
    print("\n=== Critical Event Detection ===\n")
    
    parser = WindowsEventLogParser()
    
    # Critical events to watch for
    critical_events = [
        # Account lockout
        """<Event><System><EventID>4740</EventID><Level>0</Level>
        <Computer>SERVER01</Computer><Channel>Security</Channel></System></Event>""",
        
        # Service crash
        """<Event><System><EventID>7034</EventID><Level>2</Level>
        <Computer>SERVER01</Computer><Channel>System</Channel></System></Event>""",
        
        # Unexpected shutdown
        """<Event><System><EventID>6008</EventID><Level>2</Level>
        <Computer>SERVER01</Computer><Channel>System</Channel></System></Event>"""
    ]
    
    print("Parsing critical events:\n")
    
    for event_xml in critical_events:
        entry = parser.parse_line(event_xml)
        if entry:
            event_id = entry.metadata.get('event_id', 'Unknown')
            desc = entry.metadata.get('event_description', 'Unknown')
            level = entry.metadata.get('level', 'Unknown')
            
            # Determine criticality
            if level in ['Critical', 'Error'] or event_id in ['6008', '7034', '4740']:
                icon = "🚨"
            else:
                icon = "⚠️"
            
            print(f"{icon} Event ID {event_id}: {desc}")
            print(f"   Level: {level}")
            print(f"   Computer: {entry.metadata.get('computer', 'N/A')}")
            print()


def validate_event_formats():
    """Validate different Windows Event formats"""
    print("\n=== Format Validation ===\n")
    
    parser = WindowsEventLogParser()
    
    test_cases = [
        ("<Event xmlns='http://schemas.microsoft.com'>", "XML Event"),
        ("Event ID: 1234\nLog Name: Application", "Text Event"),
        ("Oct  5 12:00:00 host syslog: message", "Not Windows Event"),
        ("", "Empty string")
    ]
    
    print("Validating event formats:\n")
    
    for test_input, description in test_cases:
        is_valid = parser.validate(test_input)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"{status}: {description}")
    print()


def parse_from_file():
    """Parse Windows Event Logs from exported XML file"""
    print("\n=== Parsing from File ===\n")
    
    # This would typically read from an exported .xml or .evtx file
    print("To parse Windows Event Logs from a file:")
    print("1. Export events from Event Viewer to XML format")
    print("2. Use LogGem with 'windows' parser type:")
    print()
    print("   from loggem.parsers import LogParserFactory")
    print("   from loggem.reader import LogReader")
    print()
    print("   parser = LogParserFactory.create_parser('windows')")
    print("   reader = LogReader('exported_events.xml', parser)")
    print("   entries = reader.read_all()")
    print()


if __name__ == "__main__":
    print("LogGem - Windows Event Log Parser Examples")
    print("=" * 50)
    
    try:
        parse_xml_events()
        parse_text_events()
        common_security_events()
        common_system_events()
        parse_critical_events()
        validate_event_formats()
        parse_from_file()
        
        print("✅ All examples completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
