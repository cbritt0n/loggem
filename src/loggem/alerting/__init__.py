"""
Advanced alerting system for LogGem.

Supports:
- Multi-channel alerts (email, webhook, Slack, console)
- Alert rules engine
- Rate limiting to prevent spam
- Alert aggregation
- Customizable alert conditions
"""

import time
import smtplib
import requests
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
from enum import Enum

from ..core.logging import get_logger
from ..core.models import Anomaly, AnalysisResult

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Supported alert channels"""
    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"


@dataclass
class Alert:
    """Represents an alert"""
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    anomaly: Optional[Anomaly] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "anomaly": {
                "confidence": self.anomaly.confidence,
                "description": self.anomaly.description,
                "log_content": self.anomaly.log_entry_id if hasattr(self.anomaly, 'log_entry_id') else None
            } if self.anomaly else None,
            "metadata": self.metadata
        }


class AlertRule:
    """Rule for triggering alerts based on conditions"""
    
    def __init__(self, name: str, condition: Callable[[Anomaly], bool],
                 severity: AlertSeverity, channels: List[AlertChannel],
                 enabled: bool = True):
        """
        Initialize alert rule
        
        Args:
            name: Rule name
            condition: Function that returns True if alert should trigger
            severity: Severity level for triggered alerts
            channels: Channels to send alerts to
            enabled: Whether rule is active
        """
        self.name = name
        self.condition = condition
        self.severity = severity
        self.channels = channels
        self.enabled = enabled
        self.triggered_count = 0
        
    def should_trigger(self, anomaly: Anomaly) -> bool:
        """Check if rule should trigger for anomaly"""
        if not self.enabled:
            return False
        try:
            return self.condition(anomaly)
        except Exception as e:
            logger.error("rule_condition_error", rule=self.name, error=str(e))
            return False
    
    def trigger(self) -> None:
        """Mark rule as triggered"""
        self.triggered_count += 1


class RateLimiter:
    """Rate limiter to prevent alert spam"""
    
    def __init__(self, max_alerts: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_alerts: Maximum alerts allowed in window
            window_seconds: Time window in seconds
        """
        self.max_alerts = max_alerts
        self.window = timedelta(seconds=window_seconds)
        self._alert_times: Dict[str, List[datetime]] = defaultdict(list)
        
    def should_allow(self, alert_key: str) -> bool:
        """
        Check if alert should be allowed
        
        Args:
            alert_key: Unique key for alert type
            
        Returns:
            True if alert should be sent
        """
        now = datetime.now()
        
        # Remove old timestamps outside window
        self._alert_times[alert_key] = [
            t for t in self._alert_times[alert_key]
            if now - t < self.window
        ]
        
        # Check if under limit
        if len(self._alert_times[alert_key]) < self.max_alerts:
            self._alert_times[alert_key].append(now)
            return True
        
        logger.warning("alert_rate_limited", alert_key=alert_key)
        return False


class AlertAggregator:
    """Aggregates similar alerts to reduce noise"""
    
    def __init__(self, window_seconds: int = 300, max_group_size: int = 50):
        """
        Initialize alert aggregator
        
        Args:
            window_seconds: Time window for aggregation
            max_group_size: Maximum alerts to aggregate
        """
        self.window = timedelta(seconds=window_seconds)
        self.max_group_size = max_group_size
        self._groups: Dict[str, List[Alert]] = defaultdict(list)
        self._last_sent: Dict[str, datetime] = {}
        
    def add_alert(self, alert: Alert, group_key: str) -> Optional[List[Alert]]:
        """
        Add alert to aggregation
        
        Args:
            alert: Alert to add
            group_key: Key for grouping similar alerts
            
        Returns:
            List of aggregated alerts if ready to send, None otherwise
        """
        now = datetime.now()
        self._groups[group_key].append(alert)
        
        # Check if should send aggregated alerts
        last_sent = self._last_sent.get(group_key)
        group = self._groups[group_key]
        
        if (len(group) >= self.max_group_size or 
            (last_sent and now - last_sent >= self.window) or
            not last_sent):
            # Time to send
            alerts_to_send = list(group)
            self._groups[group_key] = []
            self._last_sent[group_key] = now
            return alerts_to_send
        
        return None


class ConsoleChannel:
    """Console output channel"""
    
    def send(self, alert: Alert) -> bool:
        """Send alert to console"""
        try:
            severity_emoji = {
                AlertSeverity.LOW: "ℹ️",
                AlertSeverity.MEDIUM: "⚠️",
                AlertSeverity.HIGH: "🔥",
                AlertSeverity.CRITICAL: "🚨"
            }
            
            print(f"\n{severity_emoji.get(alert.severity, '❗')} [{alert.severity.value.upper()}] {alert.title}")
            print(f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Message: {alert.message}")
            if alert.anomaly:
                print(f"Anomaly Confidence: {alert.anomaly.confidence:.2f}")
                print(f"Description: {alert.anomaly.description}")
            print()
            
            logger.info("alert_sent_console", title=alert.title, severity=alert.severity.value)
            return True
        except Exception as e:
            logger.error("console_send_error", error=str(e))
            return False


class EmailChannel:
    """Email alert channel"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str,
                 password: str, from_addr: str, to_addrs: List[str],
                 use_tls: bool = True):
        """
        Initialize email channel
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_addr: From email address
            to_addrs: List of recipient email addresses
            use_tls: Use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs
        self.use_tls = use_tls
        
    def send(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
Alert Details:
--------------
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Severity: {alert.severity.value.upper()}

Message:
{alert.message}
"""
            
            if alert.anomaly:
                body += f"""
Anomaly Details:
----------------
Confidence: {alert.anomaly.confidence:.2f}
Description: {alert.anomaly.description}
Type: {alert.anomaly.anomaly_type.value}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info("alert_sent_email", title=alert.title, recipients=len(self.to_addrs))
            return True
        except Exception as e:
            logger.error("email_send_error", error=str(e))
            return False


class WebhookChannel:
    """Webhook alert channel"""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None,
                 timeout: int = 10):
        """
        Initialize webhook channel
        
        Args:
            url: Webhook URL
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
        """
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        
    def send(self, alert: Alert) -> bool:
        """Send alert to webhook"""
        try:
            payload = alert.to_dict()
            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info("alert_sent_webhook", title=alert.title, status=response.status_code)
            return True
        except Exception as e:
            logger.error("webhook_send_error", error=str(e))
            return False


class SlackChannel:
    """Slack alert channel"""
    
    def __init__(self, webhook_url: str, channel: Optional[str] = None,
                 username: str = "LogGem", timeout: int = 10):
        """
        Initialize Slack channel
        
        Args:
            webhook_url: Slack webhook URL
            channel: Optional channel override
            username: Bot username
            timeout: Request timeout
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.timeout = timeout
        
    def send(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            color_map = {
                AlertSeverity.LOW: "#36a64f",
                AlertSeverity.MEDIUM: "#ff9900",
                AlertSeverity.HIGH: "#ff0000",
                AlertSeverity.CRITICAL: "#8b0000"
            }
            
            payload = {
                "username": self.username,
                "attachments": [{
                    "color": color_map.get(alert.severity, "#808080"),
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.value.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "LogGem Alert System",
                    "ts": int(alert.timestamp.timestamp())
                }]
            }
            
            if self.channel:
                payload["channel"] = self.channel
            
            if alert.anomaly:
                payload["attachments"][0]["fields"].extend([
                    {
                        "title": "Anomaly Confidence",
                        "value": f"{alert.anomaly.confidence:.2f}",
                        "short": True
                    },
                    {
                        "title": "Description",
                        "value": alert.anomaly.description[:100],
                        "short": False
                    }
                ])
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            logger.info("alert_sent_slack", title=alert.title)
            return True
        except Exception as e:
            logger.error("slack_send_error", error=str(e))
            return False


class AlertManager:
    """Central alert management system"""
    
    def __init__(self):
        """Initialize alert manager"""
        self.rules: List[AlertRule] = []
        self.channels: Dict[AlertChannel, Any] = {}
        self.rate_limiter = RateLimiter()
        self.aggregator = AlertAggregator()
        self.alert_history: List[Alert] = []
        
        # Add default console channel
        self.channels[AlertChannel.CONSOLE] = ConsoleChannel()
        
        logger.info("alert_manager_initialized")
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule"""
        self.rules.append(rule)
        logger.info("rule_added", name=rule.name)
    
    def add_channel(self, channel_type: AlertChannel, channel: Any) -> None:
        """Add alert channel"""
        self.channels[channel_type] = channel
        logger.info("channel_added", type=channel_type.value)
    
    def process_anomaly(self, anomaly: Anomaly) -> None:
        """
        Process anomaly and trigger alerts if rules match
        
        Args:
            anomaly: Anomaly to process
        """
        for rule in self.rules:
            if rule.should_trigger(anomaly):
                alert = Alert(
                    title=f"Alert: {rule.name}",
                    message=f"Anomaly detected: {anomaly.description}",
                    severity=rule.severity,
                    anomaly=anomaly
                )
                
                self.send_alert(alert, rule.channels)
                rule.trigger()
    
    def send_alert(self, alert: Alert, channels: List[AlertChannel]) -> None:
        """
        Send alert through specified channels
        
        Args:
            alert: Alert to send
            channels: List of channels to use
        """
        # Check rate limiting
        rate_key = f"{alert.title}:{alert.severity.value}"
        if not self.rate_limiter.should_allow(rate_key):
            return
        
        # Store in history
        self.alert_history.append(alert)
        
        # Send through each channel
        for channel_type in channels:
            channel = self.channels.get(channel_type)
            if channel:
                try:
                    channel.send(alert)
                except Exception as e:
                    logger.error("channel_send_failed", 
                               channel=channel_type.value, error=str(e))
            else:
                logger.warning("channel_not_configured", channel=channel_type.value)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total = len(self.alert_history)
        by_severity = defaultdict(int)
        
        for alert in self.alert_history:
            by_severity[alert.severity.value] += 1
        
        return {
            "total_alerts": total,
            "by_severity": dict(by_severity),
            "rules_configured": len(self.rules),
            "channels_configured": len(self.channels)
        }


# Predefined alert rules
def create_high_score_rule(threshold: float = 0.8) -> AlertRule:
    """Create rule for high anomaly confidence scores"""
    return AlertRule(
        name="High Anomaly Confidence",
        condition=lambda a: a.confidence >= threshold,
        severity=AlertSeverity.HIGH,
        channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL]
    )


def create_critical_keyword_rule(keywords: List[str]) -> AlertRule:
    """Create rule for critical keywords in logs"""
    keywords_lower = [k.lower() for k in keywords]
    return AlertRule(
        name="Critical Keywords Detected",
        condition=lambda a: any(kw in a.description.lower() for kw in keywords_lower),
        severity=AlertSeverity.CRITICAL,
        channels=[AlertChannel.CONSOLE, AlertChannel.SLACK]
    )


def create_error_pattern_rule() -> AlertRule:
    """Create rule for common error patterns"""
    error_patterns = ['error', 'fatal', 'exception', 'failed', 'panic']
    return AlertRule(
        name="Error Pattern Detected",
        condition=lambda a: any(p in a.description.lower() for p in error_patterns),
        severity=AlertSeverity.MEDIUM,
        channels=[AlertChannel.CONSOLE]
    )


# Export public API
__all__ = [
    'AlertManager',
    'Alert',
    'AlertRule',
    'AlertSeverity',
    'AlertChannel',
    'ConsoleChannel',
    'EmailChannel',
    'WebhookChannel',
    'SlackChannel',
    'RateLimiter',
    'AlertAggregator',
    'create_high_score_rule',
    'create_critical_keyword_rule',
    'create_error_pattern_rule'
]
