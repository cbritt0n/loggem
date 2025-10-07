"""
Apache Log Parser

Supports Apache web server logs in various formats:
- Common Log Format (CLF)
- Combined Log Format
- Custom formats with configurable patterns

Example formats:
    Common: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
    Combined: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08"
"""

import re
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .base import BaseParser
from ..core.models import LogEntry
from ..core.logging import get_logger

logger = get_logger(__name__)


class ApacheLogParser(BaseParser):
    """Parser for Apache web server logs (access and error logs)"""
    
    # Common Log Format (CLF)
    COMMON_LOG_PATTERN = re.compile(
        r'^(?P<ip>[\d\.]+|\S+)\s+'  # IP address or hostname
        r'(?P<identity>\S+)\s+'  # RFC 1413 identity
        r'(?P<user>\S+)\s+'  # HTTP auth user
        r'\[(?P<timestamp>[^\]]+)\]\s+'  # Timestamp
        r'"(?P<request>[^"]*?)"\s+'  # Request line
        r'(?P<status>\d{3})\s+'  # Status code
        r'(?P<size>\d+|-)'  # Response size
    )
    
    # Combined Log Format (includes referer and user agent)
    COMBINED_LOG_PATTERN = re.compile(
        r'^(?P<ip>[\d\.]+|\S+)\s+'
        r'(?P<identity>\S+)\s+'
        r'(?P<user>\S+)\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<request>[^"]*?)"\s+'
        r'(?P<status>\d{3})\s+'
        r'(?P<size>\d+|-)\s+'
        r'"(?P<referer>[^"]*)"\s+'  # Referer
        r'"(?P<user_agent>[^"]*)"'  # User-Agent
    )
    
    # Apache Error Log Pattern
    ERROR_LOG_PATTERN = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\]\s+'
        r'\[(?P<level>[^\]]+)\]\s+'
        r'(?:\[client (?P<client>[^\]]+)\]\s+)?'
        r'(?P<message>.+)'
    )
    
    def __init__(self, log_type: str = "access", custom_pattern: Optional[str] = None):
        """
        Initialize Apache log parser
        
        Args:
            log_type: Type of log ('access' or 'error')
            custom_pattern: Custom regex pattern for non-standard formats
        """
        super().__init__()
        self.log_type = log_type
        self.custom_pattern = re.compile(custom_pattern) if custom_pattern else None
        self._pattern_cache = None
        
        logger.info(
            "apache_parser_created",
            log_type=log_type,
            has_custom_pattern=custom_pattern is not None
        )
    
    def _get_pattern(self, line: str):
        """Determine which pattern to use based on line content"""
        if self.custom_pattern:
            return self.custom_pattern
        
        if self.log_type == "error":
            return self.ERROR_LOG_PATTERN
        
        # For access logs, try combined first (has more fields)
        if '"' in line and line.count('"') >= 4:
            return self.COMBINED_LOG_PATTERN
        return self.COMMON_LOG_PATTERN
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single Apache log line
        
        Args:
            line: Raw log line
            
        Returns:
            LogEntry if parsing succeeds, None otherwise
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        try:
            pattern = self._get_pattern(line)
            match = pattern.match(line)
            
            if not match:
                logger.debug("unrecognized_apache_format", line=line[:100], parser="ApacheLogParser")
                return None
            
            data = match.groupdict()
            
            # Parse based on log type
            if self.log_type == "error":
                return self._parse_error_log(data, line)
            else:
                return self._parse_access_log(data, line)
                
        except Exception as e:
            logger.error("apache_parse_error", error=str(e), line=line[:100])
            return None
    
    def _parse_access_log(self, data: dict, raw_line: str) -> LogEntry:
        """Parse access log entry"""
        # Parse timestamp (Apache format: 10/Oct/2000:13:55:36 -0700)
        try:
            timestamp_str = data.get('timestamp', '')
            # Remove timezone for easier parsing
            timestamp_base = timestamp_str.rsplit(' ', 1)[0] if ' ' in timestamp_str else timestamp_str
            timestamp = datetime.strptime(timestamp_base, '%d/%b/%Y:%H:%M:%S')
        except:
            timestamp = datetime.now()
        
        # Parse request
        request = data.get('request', '')
        method, path, protocol = '', '', ''
        if request:
            parts = request.split(' ', 2)
            method = parts[0] if len(parts) > 0 else ''
            path = parts[1] if len(parts) > 1 else ''
            protocol = parts[2] if len(parts) > 2 else ''
        
        # Determine severity based on status code
        status = int(data.get('status', 0))
        if status >= 500:
            level = "error"
        elif status >= 400:
            level = "warning"
        else:
            level = "info"
        
        # Build message
        user = data.get('user', '-')
        user_info = f" (user: {user})" if user != '-' else ""
        
        message = f"{method} {path} {protocol} - Status {status}{user_info}"
        
        # Add referer and user agent if available
        if 'referer' in data:
            message += f" | Referer: {data['referer']}"
        if 'user_agent' in data:
            message += f" | UA: {data['user_agent']}"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=data.get('ip', 'unknown'),
            raw=raw_line,
            metadata={
                'ip': data.get('ip'),
                'user': data.get('user'),
                'method': method,
                'path': path,
                'protocol': protocol,
                'status': status,
                'size': data.get('size', '-'),
                'referer': data.get('referer'),
                'user_agent': data.get('user_agent'),
            }
        )
    
    def _parse_error_log(self, data: dict, raw_line: str) -> LogEntry:
        """Parse error log entry"""
        # Parse timestamp
        try:
            timestamp_str = data.get('timestamp', '')
            # Apache error log: Mon Oct 10 13:55:36 2000
            timestamp = datetime.strptime(timestamp_str.split('.')[0], '%a %b %d %H:%M:%S %Y')
        except:
            timestamp = datetime.now()
        
        level_map = {
            'emerg': 'critical',
            'alert': 'critical',
            'crit': 'critical',
            'error': 'error',
            'warn': 'warning',
            'notice': 'info',
            'info': 'info',
            'debug': 'debug',
        }
        
        apache_level = data.get('level', 'info').lower()
        level = level_map.get(apache_level, 'info')
        
        message = data.get('message', '')
        client = data.get('client', 'unknown')
        
        if client != 'unknown':
            message = f"[Client: {client}] {message}"
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=client,
            raw=raw_line,
            metadata={
                'apache_level': apache_level,
                'client': client,
            }
        )
    
    def can_parse(self, sample: str) -> bool:
        """
        Check if this parser can handle the given log sample
        
        Args:
            sample: Sample log content
            
        Returns:
            True if parser can handle this format
        """
        # Check for Apache access log patterns
        if self.COMMON_LOG_PATTERN.search(sample) or self.COMBINED_LOG_PATTERN.search(sample):
            return True
        
        # Check for Apache error log patterns
        if self.ERROR_LOG_PATTERN.search(sample):
            return True
        
        return False
    
    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        Parse an Apache log file
        
        Args:
            file_path: Path to log file
            
        Returns:
            List of parsed log entries
        """
        path = Path(file_path)
        if not path.exists():
            logger.error("file_not_found", path=str(path))
            return []
        
        logger.info(
            "parsing_file",
            parser="ApacheLogParser",
            path=str(path),
            size=path.stat().st_size,
            log_type=self.log_type
        )
        
        entries = []
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                entry = self.parse_line(line)
                if entry:
                    entries.append(entry)
        
        logger.info(
            "parsed_file",
            parser="ApacheLogParser",
            path=str(path),
            entries=len(entries),
            log_type=self.log_type
        )
        
        return entries
