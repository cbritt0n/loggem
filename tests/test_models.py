"""
Unit tests for core models.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from loggem.core.models import LogEntry, Anomaly, Severity, AnomalyType, AnalysisResult


class TestLogEntry:
    """Test cases for LogEntry model."""

    def test_create_basic_entry(self):
        """Test creating a basic log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test message",
            raw="raw log line"
        )
        
        assert entry.source == "test"
        assert entry.message == "Test message"
        assert entry.level == "INFO"  # Default level

    def test_sanitize_message(self):
        """Test message sanitization."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test\x00message\x01with\x02control",
            raw="raw"
        )
        
        # Control characters should be removed
        assert "\x00" not in entry.message
        assert "\x01" not in entry.message

    def test_validate_level(self):
        """Test log level validation."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test",
            level="invalid",
            raw="raw"
        )
        
        # Invalid level should default to INFO
        assert entry.level == "INFO"

    def test_get_hash(self):
        """Test hash generation for deduplication."""
        entry1 = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Same message",
            raw="raw1"
        )
        entry2 = LogEntry(
            timestamp=entry1.timestamp,
            source="test",
            message="Same message",
            raw="raw2"
        )
        
        # Same content should produce same hash
        assert entry1.get_hash() == entry2.get_hash()


class TestAnomaly:
    """Test cases for Anomaly model."""

    def test_create_anomaly(self):
        """Test creating an anomaly."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test",
            raw="raw"
        )
        
        anomaly = Anomaly(
            log_entry_id=entry.id,
            severity=Severity.HIGH,
            anomaly_type=AnomalyType.BRUTE_FORCE,
            description="Brute force detected",
            confidence=0.95
        )
        
        assert anomaly.severity == Severity.HIGH
        assert anomaly.anomaly_type == AnomalyType.BRUTE_FORCE
        assert anomaly.confidence == 0.95

    def test_confidence_validation(self):
        """Test that confidence is validated."""
        # Test that invalid confidence raises ValidationError
        with pytest.raises(Exception):  # Pydantic ValidationError
            Anomaly(
                log_entry_id=uuid4(),
                severity=Severity.HIGH,
                anomaly_type=AnomalyType.BRUTE_FORCE,
                description="Test anomaly",
                confidence=1.5,  # Invalid - should fail
            )


class TestAnalysisResult:
    """Test cases for AnalysisResult model."""

    def test_get_anomalies_by_severity(self):
        """Test filtering anomalies by severity."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test",
            raw="raw"
        )
        
        anomalies = [
            Anomaly(
                log_entry_id=entry.id,
                severity=Severity.HIGH,
                anomaly_type=AnomalyType.BRUTE_FORCE,
                description="High severity",
                confidence=0.9
            ),
            Anomaly(
                log_entry_id=entry.id,
                severity=Severity.LOW,
                anomaly_type=AnomalyType.UNKNOWN,
                description="Low severity",
                confidence=0.7
            ),
        ]
        
        result = AnalysisResult(
            total_entries=1,
            anomalies=anomalies,
            duration=1.0
        )
        
        high_anomalies = result.get_anomalies_by_severity(Severity.HIGH)
        assert len(high_anomalies) == 1
        assert high_anomalies[0].severity == Severity.HIGH

    def test_get_critical_anomalies(self):
        """Test getting critical and high severity anomalies."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test",
            raw="raw"
        )
        
        anomalies = [
            Anomaly(
                log_entry_id=entry.id,
                severity=Severity.CRITICAL,
                anomaly_type=AnomalyType.DATA_EXFILTRATION,
                description="Critical",
                confidence=0.95
            ),
            Anomaly(
                log_entry_id=entry.id,
                severity=Severity.MEDIUM,
                anomaly_type=AnomalyType.UNKNOWN,
                description="Medium",
                confidence=0.7
            ),
        ]
        
        result = AnalysisResult(
            total_entries=1,
            anomalies=anomalies,
            duration=1.0
        )
        
        critical = result.get_critical_anomalies()
        assert len(critical) == 1
        assert critical[0].severity == Severity.CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
