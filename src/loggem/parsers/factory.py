"""
Factory for creating log parsers based on format type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from loggem.core.logging import get_logger
from loggem.parsers.apache import ApacheLogParser
from loggem.parsers.auth import AuthLogParser
from loggem.parsers.base import BaseParser
from loggem.parsers.docker import DockerParser
from loggem.parsers.haproxy import HAProxyParser
from loggem.parsers.json_parser import JSONParser
from loggem.parsers.kubernetes import KubernetesParser
from loggem.parsers.mysql import MySQLParser
from loggem.parsers.nginx import NginxParser
from loggem.parsers.postgresql import PostgreSQLParser
from loggem.parsers.redis import RedisParser
from loggem.parsers.syslog import SyslogParser
from loggem.parsers.windows_event import WindowsEventLogParser

logger = get_logger(__name__)


class LogParserFactory:
    """
    Factory for creating appropriate log parsers.

    Supports automatic format detection and manual format specification.
    """

    # Registry of available parsers
    _parsers: dict[str, type[BaseParser]] = {
        "syslog": SyslogParser,
        "json": JSONParser,
        "nginx": NginxParser,
        "auth": AuthLogParser,
        "apache": ApacheLogParser,
        "windows": WindowsEventLogParser,
        "postgresql": PostgreSQLParser,
        "mysql": MySQLParser,
        "docker": DockerParser,
        "kubernetes": KubernetesParser,
        "haproxy": HAProxyParser,
        "redis": RedisParser,
    }

    # File path patterns for auto-detection
    _path_patterns = {
        "syslog": ["/var/log/syslog", "/var/log/messages"],
        "auth": ["/var/log/auth.log", "/var/log/secure"],
        "nginx": ["/var/log/nginx/", "nginx"],
        "apache": ["/var/log/apache2/", "/var/log/httpd/", "apache", "httpd"],
        "windows": ["windows", "event", ".evtx", ".xml"],
        "postgresql": ["postgresql", "postgres", "pgsql"],
        "mysql": ["mysql", "mysqld", "mariadb"],
        "docker": ["docker", "container"],
        "kubernetes": ["kubectl", "kubernetes", "k8s", "pod"],
        "haproxy": ["haproxy"],
        "redis": ["redis"],
    }

    @classmethod
    def register_parser(cls, name: str, parser_class: type[BaseParser]) -> None:
        """
        Register a custom parser.

        Args:
            name: Name to identify the parser
            parser_class: Parser class (must inherit from BaseParser)
        """
        if not issubclass(parser_class, BaseParser):
            raise ValueError(f"Parser must inherit from BaseParser: {parser_class}")

        cls._parsers[name] = parser_class
        logger.info("parser_registered", name=name, parser=parser_class.__name__)

    @classmethod
    def create_parser(
        cls,
        format_type: Optional[str] = None,
        file_path: Optional[Path] = None,
        source_name: Optional[str] = None,
    ) -> BaseParser:
        """
        Create a parser for the specified format.

        Args:
            format_type: Explicit format type (syslog, json, nginx, auth)
            file_path: Path to log file (for auto-detection if format_type not specified)
            source_name: Name to identify the log source

        Returns:
            Appropriate parser instance

        Raises:
            ValueError: If format_type is invalid or cannot be detected
        """
        # Determine source name
        if source_name is None:
            source_name = str(file_path) if file_path else "unknown"

        # If format explicitly specified, use it
        if format_type:
            format_type = format_type.lower()
            if format_type not in cls._parsers:
                raise ValueError(
                    f"Unknown format: {format_type}. "
                    f"Available formats: {', '.join(cls._parsers.keys())}"
                )
            parser_class = cls._parsers[format_type]
            logger.info("parser_created", format=format_type, source=source_name)
            return parser_class(source_name=source_name)

        # Try to auto-detect from file path
        if file_path:
            detected_format = cls._detect_format(file_path)
            if detected_format:
                parser_class = cls._parsers[detected_format]
                logger.info(
                    "parser_auto_detected",
                    format=detected_format,
                    path=str(file_path),
                )
                return parser_class(source_name=source_name)

        # Default to syslog parser as fallback
        logger.warning(
            "parser_defaulting_to_syslog",
            path=str(file_path) if file_path else None,
        )
        return SyslogParser(source_name=source_name)

    @classmethod
    def _detect_format(cls, file_path: Path) -> Optional[str]:
        """
        Attempt to detect log format from file path.

        Args:
            file_path: Path to log file

        Returns:
            Detected format name or None
        """
        file_str = str(file_path).lower()

        # Check against known patterns
        for format_name, patterns in cls._path_patterns.items():
            for pattern in patterns:
                if pattern in file_str:
                    return format_name

        # Check file extension
        if file_path.suffix == ".json":
            return "json"

        # Try to detect from first few lines
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    # Read first few non-empty lines
                    lines = []
                    for line in f:
                        if line.strip():
                            lines.append(line.strip())
                        if len(lines) >= 5:
                            break

                    return cls._detect_format_from_content(lines)

            except Exception as e:
                logger.warning("format_detection_failed", error=str(e))

        return None

    @classmethod
    def _detect_format_from_content(cls, lines: list[str]) -> Optional[str]:
        """
        Detect format from log content.

        Args:
            lines: Sample log lines

        Returns:
            Detected format name or None
        """
        if not lines:
            return None

        # Check for JSON
        if all(line.startswith("{") for line in lines[:3]):
            return "json"

        # Check for Nginx access log (IP - user [timestamp])
        import re

        nginx_pattern = r'^\d+\.\d+\.\d+\.\d+ - .* \[.+\] ".+" \d{3} \d+'
        if any(re.match(nginx_pattern, line) for line in lines[:3]):
            return "nginx"

        # Check for auth log keywords
        auth_keywords = ["sshd", "sudo", "su:", "authentication", "login"]
        if any(any(keyword in line.lower() for keyword in auth_keywords) for line in lines[:3]):
            return "auth"

        # Default to syslog (most common format)
        return "syslog"

    @classmethod
    def list_formats(cls) -> list[str]:
        """
        List all available parser formats.

        Returns:
            List of format names
        """
        return list(cls._parsers.keys())
