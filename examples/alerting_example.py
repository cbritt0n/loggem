"""
Example: Advanced Alerting System

Demonstrates:
- Multi-channel alerts (console, email, webhook, Slack)
- Alert rules engine
- Rate limiting
- Alert aggregation
"""

from datetime import datetime
from loggem.alerting import (
    AlertManager, Alert, AlertRule, AlertSeverity, AlertChannel,
    EmailChannel, WebhookChannel, SlackChannel,
    create_high_score_rule, create_critical_keyword_rule, create_error_pattern_rule
)
from loggem.core.models import LogEntry, Anomaly
from loggem.detector import AnomalyDetector


def basic_alerting_example():
    """Basic alerting with console output"""
    print("=== Basic Alerting Example ===\n")
    
    # Create alert manager
    manager = AlertManager()
    
    # Add predefined rules
    manager.add_rule(create_high_score_rule(threshold=0.8))
    manager.add_rule(create_error_pattern_rule())
    
    # Create sample anomaly
    entry = LogEntry(
        timestamp=datetime.now(),
        content="ERROR: Database connection failed",
        message="Database connection failed",
        metadata={"severity": "error"}
    )
    
    anomaly = Anomaly(
        log_entry=entry,
        score=0.95,
        reasoning="Critical database error detected",
        categories=["error", "database"]
    )
    
    # Process anomaly - will trigger alerts
    print("Processing anomaly...")
    manager.process_anomaly(anomaly)
    
    # Show stats
    print("\n📊 Alert Statistics:")
    stats = manager.get_alert_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


def multi_channel_alerting():
    """Alerting with multiple channels"""
    print("\n=== Multi-channel Alerting ===\n")
    
    manager = AlertManager()
    
    # Configure email channel (example - update with real credentials)
    # email_channel = EmailChannel(
    #     smtp_host="smtp.gmail.com",
    #     smtp_port=587,
    #     username="your-email@gmail.com",
    #     password="your-app-password",
    #     from_addr="alerts@loggem.com",
    #     to_addrs=["admin@example.com"]
    # )
    # manager.add_channel(AlertChannel.EMAIL, email_channel)
    
    # Configure webhook channel (example)
    # webhook_channel = WebhookChannel(
    #     url="https://your-webhook-url.com/alerts",
    #     headers={"Authorization": "Bearer YOUR-TOKEN"}
    # )
    # manager.add_channel(AlertChannel.WEBHOOK, webhook_channel)
    
    # Configure Slack channel (example - update with real webhook)
    # slack_channel = SlackChannel(
    #     webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    #     channel="#alerts"
    # )
    # manager.add_channel(AlertChannel.SLACK, slack_channel)
    
    # Create custom rule
    rule = AlertRule(
        name="Critical System Alert",
        condition=lambda a: a.score >= 0.9 or "panic" in a.log_entry.content.lower(),
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.CONSOLE]  # Add EMAIL, WEBHOOK, SLACK when configured
    )
    manager.add_rule(rule)
    
    # Test with critical anomaly
    entry = LogEntry(
        timestamp=datetime.now(),
        content="PANIC: Kernel panic - not syncing",
        message="Kernel panic",
        metadata={"severity": "critical"}
    )
    
    anomaly = Anomaly(
        log_entry=entry,
        score=0.98,
        reasoning="System panic detected",
        categories=["critical", "kernel"]
    )
    
    print("Sending critical alert through all channels...")
    manager.process_anomaly(anomaly)
    
    print("\n✅ Alerts sent!")


def rate_limiting_example():
    """Demonstrate rate limiting to prevent alert spam"""
    print("\n=== Rate Limiting Example ===\n")
    
    from loggem.alerting import RateLimiter
    
    # Create rate limiter: max 3 alerts per 10 seconds
    limiter = RateLimiter(max_alerts=3, window_seconds=10)
    
    print("Testing rate limiter (3 alerts max per 10 seconds)...")
    
    # Try to send 5 alerts
    for i in range(5):
        allowed = limiter.should_allow("test_alert")
        status = "✅ SENT" if allowed else "🚫 BLOCKED"
        print(f"Alert {i+1}: {status}")
    
    print("\n✅ First 3 alerts sent, remaining 2 blocked by rate limiter")


def alert_aggregation_example():
    """Demonstrate alert aggregation"""
    print("\n=== Alert Aggregation Example ===\n")
    
    from loggem.alerting import AlertAggregator
    
    # Create aggregator: group similar alerts
    aggregator = AlertAggregator(window_seconds=5, max_group_size=3)
    
    print("Aggregating similar alerts (max 3 per group)...")
    
    # Send similar alerts
    for i in range(5):
        alert = Alert(
            title="Database Connection Warning",
            message=f"Connection timeout #{i+1}",
            severity=AlertSeverity.MEDIUM
        )
        
        result = aggregator.add_alert(alert, "db_timeout_group")
        
        if result:
            print(f"\n📨 Sending aggregated batch of {len(result)} alerts:")
            for a in result:
                print(f"   - {a.message}")
        else:
            print(f"Alert {i+1}: Buffered (not yet sent)")
    
    print("\n✅ Alerts aggregated to reduce noise")


def custom_alert_rules():
    """Create custom alert rules"""
    print("\n=== Custom Alert Rules ===\n")
    
    manager = AlertManager()
    
    # Rule 1: Authentication failures
    auth_rule = AlertRule(
        name="Authentication Failures",
        condition=lambda a: "authentication" in a.log_entry.content.lower() and 
                           "fail" in a.log_entry.content.lower(),
        severity=AlertSeverity.HIGH,
        channels=[AlertChannel.CONSOLE]
    )
    manager.add_rule(auth_rule)
    
    # Rule 2: High CPU usage
    cpu_rule = AlertRule(
        name="High CPU Usage",
        condition=lambda a: a.score >= 0.75 and "cpu" in a.log_entry.content.lower(),
        severity=AlertSeverity.MEDIUM,
        channels=[AlertChannel.CONSOLE]
    )
    manager.add_rule(cpu_rule)
    
    # Rule 3: Security events
    security_rule = AlertRule(
        name="Security Event",
        condition=lambda a: any(kw in a.log_entry.content.lower() 
                               for kw in ["breach", "intrusion", "unauthorized"]),
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.CONSOLE]
    )
    manager.add_rule(security_rule)
    
    print(f"Created {len(manager.rules)} custom alert rules")
    
    # Test rules
    test_cases = [
        ("Authentication failure for user admin", 0.6, ["auth"]),
        ("CPU usage at 95%", 0.8, ["performance"]),
        ("Unauthorized access attempt detected", 0.95, ["security"])
    ]
    
    print("\nTesting rules with sample anomalies:\n")
    
    for content, score, categories in test_cases:
        entry = LogEntry(
            timestamp=datetime.now(),
            content=content,
            message=content,
            metadata={}
        )
        anomaly = Anomaly(entry, score, f"Detected: {content}", categories)
        
        print(f"Input: {content}")
        manager.process_anomaly(anomaly)
        print()


def real_world_alerting():
    """Real-world alerting scenario"""
    print("\n=== Real-world Alerting Scenario ===\n")
    
    # Setup
    manager = AlertManager()
    manager.add_rule(create_high_score_rule(0.8))
    manager.add_rule(create_critical_keyword_rule([
        "panic", "fatal", "critical", "emergency"
    ]))
    
    # Simulate log analysis
    detector = AnomalyDetector(
        provider="huggingface",
        model_id="google/gemma-3-4b-it"
    )
    
    test_logs = [
        "Oct  5 12:00:00 server sshd: Accepted password for admin",
        "Oct  5 12:01:00 server kernel: CRITICAL: Memory allocation failed",
        "Oct  5 12:02:00 server app: Processing request #1234",
        "Oct  5 12:03:00 server db: FATAL: Database connection lost"
    ]
    
    print("Analyzing logs and triggering alerts...\n")
    
    for log_line in test_logs:
        # Parse log
        from loggem.parsers import LogParserFactory
        parser = LogParserFactory.create_parser("syslog")
        entry = parser.parse_line(log_line)
        
        if entry:
            # Analyze for anomalies
            result = detector.analyze_entry(entry)
            
            # Process anomalies through alert system
            for anomaly in result.anomalies:
                manager.process_anomaly(anomaly)
    
    # Final stats
    print("\n📊 Final Alert Statistics:")
    stats = manager.get_alert_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    print("LogGem - Advanced Alerting Examples")
    print("=" * 50)
    
    try:
        basic_alerting_example()
        # multi_channel_alerting()  # Requires channel configuration
        rate_limiting_example()
        alert_aggregation_example()
        custom_alert_rules()
        # real_world_alerting()  # Requires LLM setup
        
        print("\n✅ All examples completed!")
        
    except KeyboardInterrupt:
        print("\n\n✅ Examples stopped by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
