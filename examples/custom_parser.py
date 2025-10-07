"""
Example: Custom log parser
"""

import re
from datetime import datetime
from loggem.parsers.base import BaseParser
from loggem.parsers.factory import LogParserFactory
from loggem.core.models import LogEntry


class CustomAppParser(BaseParser):
    """
    Example custom parser for a hypothetical application log format.
    
    Format: [TIMESTAMP] LEVEL [MODULE] MESSAGE
    Example: [2023-10-05 10:15:30] ERROR [database] Connection failed
    """
    
    PATTERN = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\]\s+'
        r'(?P<level>\w+)\s+'
        r'\[(?P<module>[^\]]+)\]\s+'
        r'(?P<message>.*)$'
    )
    
    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """Parse a custom format log line."""
        match = self.PATTERN.match(line)
        if not match:
            return None
        
        data = match.groupdict()
        
        # Parse timestamp
        timestamp = self._parse_timestamp(
            data['timestamp'],
            ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']
        )
        if not timestamp:
            timestamp = datetime.now()
        
        return LogEntry(
            timestamp=timestamp,
            source=self.source_name,
            message=data['message'],
            level=data['level'].upper(),
            process=data['module'],
            metadata={'module': data['module']},
            raw=line
        )


def main():
    """Demonstrate custom parser registration and usage."""
    
    # Register custom parser
    LogParserFactory.register_parser('custom', CustomAppParser)
    
    # Create parser instance
    parser = LogParserFactory.create_parser('custom', source_name='myapp')
    
    # Parse sample lines
    sample_lines = [
        '[2023-10-05 10:15:30] INFO [auth] User logged in',
        '[2023-10-05 10:15:31] ERROR [database] Connection timeout',
        '[2023-10-05 10:15:32] WARNING [api] Rate limit approaching',
        '[2023-10-05 10:15:33] DEBUG [cache] Cache miss for key: user_123',
    ]
    
    entries = parser.parse_lines(sample_lines)
    
    print("🔍 Parsed Custom Format Logs\n")
    for entry in entries:
        print(f"[{entry.timestamp}] {entry.level:8} {entry.process:12} {entry.message}")


if __name__ == "__main__":
    main()
