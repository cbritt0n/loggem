"""
Pattern detector for identifying suspicious patterns without AI.

Rule-based detection for common attack patterns and misconfigurations.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from loggem.core.logging import get_logger
from loggem.core.models import Anomaly, AnomalyType, LogEntry, Severity

logger = get_logger(__name__)


class PatternDetector:
    """
    Rule-based pattern detector for common security threats.

    Complements AI detection with fast, deterministic rules.
    """

    # Thresholds for detection
    BRUTE_FORCE_THRESHOLD = 5  # Failed attempts in window
    BRUTE_FORCE_WINDOW = 300  # 5 minutes
    RATE_LIMIT_THRESHOLD = 100  # Requests per minute
    SUSPICIOUS_KEYWORDS = [
        "sql",
        "union",
        "select",
        "../",
        "etc/passwd",
        "cmd",
        "exec",
        "system",
        "<script>",
    ]

    def __init__(self) -> None:
        """Initialize pattern detector."""
        self.logger = logger.bind(component="pattern_detector")

    def detect_brute_force(self, entries: list[LogEntry]) -> list[Anomaly]:
        """
        Detect brute force authentication attempts.

        Args:
            entries: List of log entries to analyze

        Returns:
            List of detected brute force anomalies
        """
        anomalies = []

        # Group failed authentications by source (IP/user)
        failed_attempts: defaultdict[str, list[LogEntry]] = defaultdict(list)

        for entry in entries:
            # Check if this is a failed authentication
            if self._is_failed_auth(entry):
                # Key by IP or user
                key = entry.host or entry.user or "unknown"
                failed_attempts[key].append(entry)

        # Check for brute force patterns
        for source, attempts in failed_attempts.items():
            if len(attempts) < self.BRUTE_FORCE_THRESHOLD:
                continue

            # Sort by timestamp
            attempts_sorted = sorted(attempts, key=lambda e: e.timestamp)

            # Check if attempts are within time window
            for i in range(len(attempts_sorted) - self.BRUTE_FORCE_THRESHOLD + 1):
                window_start = attempts_sorted[i].timestamp
                window_end = attempts_sorted[i + self.BRUTE_FORCE_THRESHOLD - 1].timestamp
                time_diff = (window_end - window_start).total_seconds()

                if time_diff <= self.BRUTE_FORCE_WINDOW:
                    # Brute force detected
                    anomaly = Anomaly(
                        log_entry_id=attempts_sorted[i].id,
                        severity=Severity.HIGH,
                        anomaly_type=AnomalyType.BRUTE_FORCE,
                        description=f"Brute force attack detected: {len(attempts)} failed "
                        f"authentication attempts from {source}",
                        confidence=0.95,
                        indicators=[
                            f"{len(attempts)} failed attempts",
                            f"Source: {source}",
                            f"Time window: {time_diff:.0f} seconds",
                        ],
                        recommendation="Block source IP and investigate user account",
                        context=[a.message for a in attempts[:5]],
                    )
                    anomalies.append(anomaly)
                    break  # Only report once per source

        self.logger.info("brute_force_detection", anomalies_found=len(anomalies))
        return anomalies

    def detect_privilege_escalation(self, entries: list[LogEntry]) -> list[Anomaly]:
        """
        Detect potential privilege escalation attempts.

        Args:
            entries: List of log entries to analyze

        Returns:
            List of detected privilege escalation anomalies
        """
        anomalies = []

        for entry in entries:
            # Check for sudo usage
            if "sudo" in entry.message.lower():
                # Check for suspicious patterns
                suspicious = any(
                    keyword in entry.message.lower()
                    for keyword in ["su -", "passwd", "/etc/shadow", "visudo"]
                )

                if suspicious:
                    anomaly = Anomaly(
                        log_entry_id=entry.id,
                        severity=Severity.MEDIUM,
                        anomaly_type=AnomalyType.PRIVILEGE_ESCALATION,
                        description=f"Potential privilege escalation via sudo by {entry.user}",
                        confidence=0.75,
                        indicators=["sudo usage", "sensitive command"],
                        recommendation="Verify if this sudo usage is authorized",
                        context=[entry.message],
                    )
                    anomalies.append(anomaly)

        self.logger.info("privilege_escalation_detection", anomalies_found=len(anomalies))
        return anomalies

    def detect_suspicious_requests(self, entries: list[LogEntry]) -> list[Anomaly]:
        """
        Detect suspicious web requests (injection attempts, path traversal, etc.).

        Args:
            entries: List of log entries to analyze

        Returns:
            List of detected suspicious request anomalies
        """
        anomalies = []

        for entry in entries:
            # Check for suspicious keywords in message
            found_keywords = [
                keyword
                for keyword in self.SUSPICIOUS_KEYWORDS
                if keyword in entry.message.lower()
            ]

            if found_keywords:
                # Determine severity based on keywords
                severity = Severity.HIGH if len(found_keywords) > 1 else Severity.MEDIUM

                anomaly = Anomaly(
                    log_entry_id=entry.id,
                    severity=severity,
                    anomaly_type=AnomalyType.MALFORMED_REQUEST,
                    description="Suspicious request detected with potential injection attempt",
                    confidence=0.85,
                    indicators=[f"Suspicious keyword: {kw}" for kw in found_keywords],
                    recommendation="Block source and investigate for attack patterns",
                    context=[entry.message],
                )
                anomalies.append(anomaly)

        self.logger.info("suspicious_requests_detection", anomalies_found=len(anomalies))
        return anomalies

    def detect_rate_limit_violations(self, entries: list[LogEntry]) -> list[Anomaly]:
        """
        Detect rate limit violations (potential DoS).

        Args:
            entries: List of log entries to analyze

        Returns:
            List of detected rate limit anomalies
        """
        anomalies = []

        if not entries:
            return anomalies

        # Group by source and minute
        requests_per_minute: defaultdict[tuple[str, str], int] = defaultdict(int)

        for entry in entries:
            source = entry.host or "unknown"
            minute_key = entry.timestamp.strftime("%Y-%m-%d %H:%M")
            requests_per_minute[(source, minute_key)] += 1

        # Check for violations
        for (source, minute), count in requests_per_minute.items():
            if count > self.RATE_LIMIT_THRESHOLD:
                # Find a representative entry
                representative = next(
                    e
                    for e in entries
                    if (e.host == source or source == "unknown")
                    and e.timestamp.strftime("%Y-%m-%d %H:%M") == minute
                )

                anomaly = Anomaly(
                    log_entry_id=representative.id,
                    severity=Severity.MEDIUM,
                    anomaly_type=AnomalyType.RATE_LIMIT_EXCEEDED,
                    description=f"Rate limit exceeded: {count} requests per minute from {source}",
                    confidence=0.90,
                    indicators=[f"{count} requests in 1 minute", f"Source: {source}"],
                    recommendation="Consider rate limiting or blocking source",
                    context=[],
                )
                anomalies.append(anomaly)

        self.logger.info("rate_limit_detection", anomalies_found=len(anomalies))
        return anomalies

    def detect_all(self, entries: list[LogEntry]) -> list[Anomaly]:
        """
        Run all pattern detectors.

        Args:
            entries: List of log entries to analyze

        Returns:
            Combined list of all detected anomalies
        """
        self.logger.info("running_all_detectors", entry_count=len(entries))

        anomalies = []
        anomalies.extend(self.detect_brute_force(entries))
        anomalies.extend(self.detect_privilege_escalation(entries))
        anomalies.extend(self.detect_suspicious_requests(entries))
        anomalies.extend(self.detect_rate_limit_violations(entries))

        self.logger.info("all_detectors_complete", total_anomalies=len(anomalies))
        return anomalies

    @staticmethod
    def _is_failed_auth(entry: LogEntry) -> bool:
        """Check if log entry is a failed authentication attempt."""
        message_lower = entry.message.lower()

        # Check for failure keywords
        failure_keywords = ["failed", "failure", "invalid", "denied", "reject"]
        auth_keywords = ["password", "auth", "login", "ssh", "access"]

        has_failure = any(keyword in message_lower for keyword in failure_keywords)
        has_auth = any(keyword in message_lower for keyword in auth_keywords)

        return has_failure and has_auth
