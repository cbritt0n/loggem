"""
Core data models for LogGem.

This module defines the fundamental data structures used throughout LogGem
for representing log entries, anomalies, and related metadata.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Severity(str, Enum):
    """Severity levels for anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __lt__(self, other: Severity) -> bool:
        """Allow severity comparison."""
        order = [self.LOW, self.MEDIUM, self.HIGH, self.CRITICAL]
        return order.index(self) < order.index(other)

    def __le__(self, other: Severity) -> bool:
        """Allow severity comparison."""
        return self == other or self < other


class AnomalyType(str, Enum):
    """Types of anomalies that can be detected."""

    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNUSUAL_ACCESS = "unusual_access"
    DATA_EXFILTRATION = "data_exfiltration"
    MISCONFIGURATION = "misconfiguration"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    AUTHENTICATION_FAILURE = "authentication_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MALFORMED_REQUEST = "malformed_request"
    UNKNOWN = "unknown"


class LogEntry(BaseModel):
    """
    Represents a single log entry from any source.

    This is the fundamental unit of data in LogGem. All parsers convert their
    specific log formats into this standardized structure.

    Attributes:
        id: Unique identifier for this log entry
        timestamp: When the log entry was created
        source: Origin of the log (e.g., filename, host, application)
        message: The actual log message content
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        host: Hostname or IP where the log originated
        user: User associated with the log entry (if applicable)
        process: Process name or ID that generated the log
        metadata: Additional structured data from the log
        raw: Original raw log line
    """

    model_config = ConfigDict(frozen=False, validate_assignment=True)

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    timestamp: datetime = Field(description="Log entry timestamp")
    source: str = Field(description="Source of the log entry")
    message: str = Field(description="Log message content")
    level: str = Field(default="INFO", description="Log level")
    host: Optional[str] = Field(default=None, description="Hostname or IP")
    user: Optional[str] = Field(default=None, description="Associated user")
    process: Optional[str] = Field(default=None, description="Process name or PID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    raw: str = Field(description="Original raw log line")

    @field_validator("message", "raw")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        """Sanitize string inputs to prevent injection attacks."""
        if not isinstance(v, str):
            raise ValueError("Must be a string")
        # Remove null bytes and control characters (except newlines/tabs)
        sanitized = "".join(char for char in v if char.isprintable() or char in "\n\t")
        return sanitized[:10000]  # Limit length to prevent memory issues

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "NOTICE", "ALERT"]
        normalized = v.upper()
        if normalized not in valid_levels:
            return "INFO"  # Default to INFO for unknown levels
        return normalized

    def get_hash(self) -> str:
        """Generate a hash of the log entry for deduplication."""
        content = f"{self.timestamp}{self.source}{self.message}{self.host}{self.user}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "message": self.message,
            "level": self.level,
            "host": self.host,
            "user": self.user,
            "process": self.process,
            "metadata": self.metadata,
            "raw": self.raw,
        }


class Anomaly(BaseModel):
    """
    Represents a detected anomaly in logs.

    Attributes:
        id: Unique identifier for this anomaly
        log_entry_id: ID of the log entry that triggered this anomaly
        timestamp: When the anomaly was detected
        severity: Severity level of the anomaly
        anomaly_type: Type/category of the anomaly
        description: Human-readable description of the anomaly
        confidence: Confidence score (0.0 to 1.0) from the AI model
        context: Related log entries that provide context
        indicators: Specific indicators that triggered the detection
        recommendation: Suggested action to take
        metadata: Additional detection metadata
    """

    model_config = ConfigDict(frozen=False)

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    log_entry_id: UUID = Field(description="Associated log entry ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Detection time")
    severity: Severity = Field(description="Severity level")
    anomaly_type: AnomalyType = Field(description="Type of anomaly")
    description: str = Field(description="Human-readable description")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")
    context: list[str] = Field(default_factory=list, description="Contextual log entries")
    indicators: list[str] = Field(default_factory=list, description="Detection indicators")
    recommendation: Optional[str] = Field(default=None, description="Recommended action")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        return max(0.0, min(1.0, v))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "log_entry_id": str(self.log_entry_id),
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "anomaly_type": self.anomaly_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "context": self.context,
            "indicators": self.indicators,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


class AnalysisResult(BaseModel):
    """
    Results from analyzing a batch of logs.

    Attributes:
        total_entries: Total number of log entries analyzed
        anomalies: List of detected anomalies
        patterns: Detected patterns in the logs
        statistics: Statistical analysis of the logs
        duration: Time taken for analysis (seconds)
        timestamp: When the analysis was completed
    """

    model_config = ConfigDict(frozen=False)

    total_entries: int = Field(ge=0, description="Total entries analyzed")
    anomalies: list[Anomaly] = Field(default_factory=list, description="Detected anomalies")
    patterns: dict[str, int] = Field(default_factory=dict, description="Detected patterns")
    statistics: dict[str, Any] = Field(default_factory=dict, description="Statistical analysis")
    duration: float = Field(ge=0.0, description="Analysis duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")

    def get_anomalies_by_severity(self, severity: Severity) -> list[Anomaly]:
        """Get all anomalies of a specific severity level."""
        return [a for a in self.anomalies if a.severity == severity]

    def get_critical_anomalies(self) -> list[Anomaly]:
        """Get all critical and high severity anomalies."""
        return [a for a in self.anomalies if a.severity in (Severity.CRITICAL, Severity.HIGH)]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_entries": self.total_entries,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "patterns": self.patterns,
            "statistics": self.statistics,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat(),
        }
