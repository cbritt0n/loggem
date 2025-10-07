"""
Structured logging configuration for LogGem.

Uses structlog for structured, machine-readable logs with human-friendly output.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.types import Processor

from loggem.core.config import get_settings


def setup_logging(log_file: Optional[Path] = None, level: str = "INFO") -> None:
    """
    Configure structured logging for LogGem.

    Args:
        log_file: Optional file path for logging output
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    settings = get_settings()

    if log_file is None:
        log_file = settings.logging.file

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Structlog processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure formatters
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=shared_processors,
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper()))

    # Quiet noisy libraries
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """
    Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class AuditLogger:
    """
    Audit logger for security-relevant events.

    Provides a separate audit trail for compliance and security analysis.
    """

    def __init__(self, audit_file: Optional[Path] = None) -> None:
        """
        Initialize audit logger.

        Args:
            audit_file: Optional separate file for audit logs
        """
        settings = get_settings()
        self.enabled = settings.security.enable_audit_log

        if not self.enabled:
            return

        if audit_file is None:
            audit_file = settings.data_dir / "audit.log"

        audit_file.parent.mkdir(parents=True, exist_ok=True)

        # Create separate audit logger
        self.logger = logging.getLogger("loggem.audit")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # File handler for audit logs
        handler = logging.FileHandler(str(audit_file))
        handler.setFormatter(
            logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"event": "%(message)s", "extra": %(extra)s}'
            )
        )
        self.logger.addHandler(handler)

    def log_event(self, event: str, severity: str = "INFO", **kwargs: Any) -> None:
        """
        Log an audit event.

        Args:
            event: Event description
            severity: Severity level
            **kwargs: Additional event context
        """
        if not self.enabled:
            return

        import json

        extra_json = json.dumps(kwargs)
        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(event, extra={"extra": extra_json})

    def log_file_access(self, file_path: Path, operation: str, user: Optional[str] = None) -> None:
        """Log file access for audit purposes."""
        self.log_event(
            "file_access",
            severity="INFO",
            file=str(file_path),
            operation=operation,
            user=user or "unknown",
        )

    def log_model_load(self, model_name: str, device: str) -> None:
        """Log model loading for audit purposes."""
        self.log_event(
            "model_load",
            severity="INFO",
            model=model_name,
            device=device,
        )

    def log_anomaly_detection(self, anomaly_count: int, severity: str, source: str) -> None:
        """Log anomaly detection results."""
        self.log_event(
            "anomaly_detection",
            severity="WARNING" if anomaly_count > 0 else "INFO",
            count=anomaly_count,
            max_severity=severity,
            source=source,
        )


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
