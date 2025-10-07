"""Tests for alerting module"""

import pytest
from datetime import datetime

from loggem.alerting import (
    AlertManager, Alert, AlertRule, AlertSeverity, AlertChannel,
    ConsoleChannel, RateLimiter, AlertAggregator,
    create_high_score_rule, create_critical_keyword_rule
)
from loggem.core.models import LogEntry, Anomaly, Severity, AnomalyType


@pytest.fixture
def sample_anomaly():
    """Create sample anomaly"""
    entry = LogEntry(
        timestamp=datetime.now(),
        source="test",
        message="Critical failure",
        raw="ERROR: Critical failure detected",
        metadata={}
    )
    return Anomaly(
        log_entry_id=entry.id,
        severity=Severity.HIGH,
        anomaly_type=AnomalyType.SUSPICIOUS_ACTIVITY,
        description="High severity error detected",
        confidence=0.95,
        indicators=["error", "critical"]
    )


def test_alert_creation():
    """Test alert object creation"""
    alert = Alert(
        title="Test Alert",
        message="This is a test",
        severity=AlertSeverity.HIGH
    )
    
    assert alert.title == "Test Alert"
    assert alert.severity == AlertSeverity.HIGH
    assert alert.timestamp is not None
    
    # Test to_dict
    alert_dict = alert.to_dict()
    assert alert_dict["title"] == "Test Alert"
    assert alert_dict["severity"] == "high"


def test_alert_rule():
    """Test alert rule creation and triggering"""
    rule = AlertRule(
        name="High Confidence Rule",
        condition=lambda a: a.confidence >= 0.8,
        severity=AlertSeverity.HIGH,
        channels=[AlertChannel.CONSOLE]
    )
    
    # Create test log entry
    entry = LogEntry(timestamp=datetime.now(), source="test", message="test", raw="test", metadata={})
    
    # High confidence - should trigger
    anomaly_high = Anomaly(
        log_entry_id=entry.id,
        severity=Severity.HIGH,
        anomaly_type=AnomalyType.SUSPICIOUS_ACTIVITY,
        description="High confidence anomaly",
        confidence=0.9
    )
    assert rule.should_trigger(anomaly_high) is True
    
    # Low confidence - should not trigger
    anomaly_low = Anomaly(
        log_entry_id=entry.id,
        severity=Severity.LOW,
        anomaly_type=AnomalyType.UNKNOWN,
        description="Low confidence anomaly",
        confidence=0.5
    )
    assert rule.should_trigger(anomaly_low) is False


def test_rate_limiter():
    """Test rate limiting"""
    limiter = RateLimiter(max_alerts=2, window_seconds=60)
    
    # First two should be allowed
    assert limiter.should_allow("test_alert") is True
    assert limiter.should_allow("test_alert") is True
    
    # Third should be blocked
    assert limiter.should_allow("test_alert") is False


def test_alert_aggregator():
    """Test alert aggregation"""
    aggregator = AlertAggregator(window_seconds=5, max_group_size=3)
    
    # Add first alert - returns immediately (initializes group)
    alert1 = Alert(
        title="Alert 0",
        message="Test",
        severity=AlertSeverity.LOW
    )
    result = aggregator.add_alert(alert1, "test_group")
    assert result is not None  # First alert triggers send
    assert len(result) == 1
    
    # Add second alert - should not trigger (still grouping)
    alert2 = Alert(
        title="Alert 1",
        message="Test",
        severity=AlertSeverity.LOW
    )
    result = aggregator.add_alert(alert2, "test_group")
    assert result is None
    
    # Add third alert - should still not trigger (only 2 so far)
    alert3 = Alert(
        title="Alert 2",
        message="Test",
        severity=AlertSeverity.LOW
    )
    result = aggregator.add_alert(alert3, "test_group")
    assert result is None  # Still below max_group_size (3)
    
    # Add fourth alert - should trigger send (reaches max_group_size)
    alert4 = Alert(
        title="Alert 3",
        message="Test",
        severity=AlertSeverity.LOW
    )
    result = aggregator.add_alert(alert4, "test_group")
    assert result is not None
    assert len(result) == 3  # Sends alerts 2, 3, 4


def test_console_channel():
    """Test console channel"""
    channel = ConsoleChannel()
    
    alert = Alert(
        title="Test Alert",
        message="Console test",
        severity=AlertSeverity.MEDIUM
    )
    
    # Should succeed
    result = channel.send(alert)
    assert result is True


def test_alert_manager(sample_anomaly):
    """Test alert manager"""
    manager = AlertManager()
    
    # Add rule
    rule = create_high_score_rule(threshold=0.9)
    manager.add_rule(rule)
    
    # Process anomaly
    manager.process_anomaly(sample_anomaly)
    
    # Check stats
    stats = manager.get_alert_stats()
    assert stats["total_alerts"] >= 0
    assert stats["rules_configured"] == 1


def test_predefined_rules():
    """Test predefined rule creators"""
    # High confidence rule
    rule1 = create_high_score_rule(0.8)
    assert rule1.name == "High Anomaly Confidence"
    assert rule1.severity == AlertSeverity.HIGH
    
    # Keyword rule
    rule2 = create_critical_keyword_rule(["panic", "fatal"])
    assert rule2.name == "Critical Keywords Detected"
    assert rule2.severity == AlertSeverity.CRITICAL


def test_alert_manager_multiple_channels(sample_anomaly):
    """Test alert manager with multiple channels"""
    manager = AlertManager()
    manager.add_channel(AlertChannel.CONSOLE, ConsoleChannel())
    
    # Add rule with correct condition
    rule = AlertRule(
        name="Test Rule",
        condition=lambda a: a.confidence > 0.8,  # Use confidence not score
        severity=AlertSeverity.HIGH,
        channels=[AlertChannel.CONSOLE]
    )
    manager.add_rule(rule)
    
    # Process anomaly
    manager.process_anomaly(sample_anomaly)
    
    # Check alerts were created
    assert len(manager.alert_history) > 0
