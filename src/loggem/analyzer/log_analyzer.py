"""
Log analyzer for statistical analysis and pattern detection.

Complements AI detection with rule-based analysis.
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from loggem.core.logging import get_logger
from loggem.core.models import Anomaly, AnalysisResult, LogEntry, AnomalyType, Severity

logger = get_logger(__name__)


class LogAnalyzer:
    """
    Analyzes logs for patterns, statistics, and trends.

    Provides rule-based analysis to complement AI-based detection.
    """

    def __init__(self) -> None:
        """Initialize the log analyzer."""
        self.logger = logger.bind(component="log_analyzer")

    def analyze(
        self, entries: list[LogEntry], anomalies: list[Anomaly] | None = None
    ) -> AnalysisResult:
        """
        Analyze a batch of log entries.

        Args:
            entries: List of log entries to analyze
            anomalies: Optional list of detected anomalies

        Returns:
            Analysis result with patterns and statistics
        """
        start_time = time.time()
        self.logger.info("starting_analysis", entry_count=len(entries))

        # Detect patterns
        patterns = self._detect_patterns(entries)

        # Generate statistics
        statistics = self._generate_statistics(entries, anomalies or [])

        # Create result
        result = AnalysisResult(
            total_entries=len(entries),
            anomalies=anomalies or [],
            patterns=patterns,
            statistics=statistics,
            duration=time.time() - start_time,
        )

        self.logger.info(
            "analysis_complete",
            duration=result.duration,
            patterns_found=len(patterns),
        )

        return result

    def _detect_patterns(self, entries: list[LogEntry]) -> dict[str, int]:
        """
        Detect common patterns in log entries.

        Args:
            entries: List of log entries

        Returns:
            Dictionary of pattern names to occurrence counts
        """
        patterns: dict[str, int] = {}

        # Count by level
        level_counts = Counter(entry.level for entry in entries)
        for level, count in level_counts.items():
            patterns[f"level_{level.lower()}"] = count

        # Count by source
        source_counts = Counter(entry.source for entry in entries)
        patterns["unique_sources"] = len(source_counts)

        # Count by host
        host_counts = Counter(entry.host for entry in entries if entry.host)
        patterns["unique_hosts"] = len(host_counts)

        # Count by user
        user_counts = Counter(entry.user for entry in entries if entry.user)
        patterns["unique_users"] = len(user_counts)

        # Detect repeated failures (brute force indicator)
        failed_auth_count = sum(
            1
            for entry in entries
            if any(
                keyword in entry.message.lower()
                for keyword in ["failed", "failure", "denied", "invalid"]
            )
            and any(keyword in entry.message.lower() for keyword in ["password", "auth", "login"])
        )
        if failed_auth_count > 0:
            patterns["failed_authentications"] = failed_auth_count

        # Detect errors
        error_count = sum(1 for entry in entries if entry.level in ("ERROR", "CRITICAL"))
        if error_count > 0:
            patterns["errors"] = error_count

        # Detect time-based patterns
        time_patterns = self._detect_time_patterns(entries)
        patterns.update(time_patterns)

        return patterns

    def _detect_time_patterns(self, entries: list[LogEntry]) -> dict[str, int]:
        """
        Detect time-based patterns.

        Args:
            entries: List of log entries

        Returns:
            Dictionary of time-based patterns
        """
        if not entries:
            return {}

        patterns = {}

        # Group by hour
        hour_counts: dict[int, int] = defaultdict(int)
        for entry in entries:
            hour_counts[entry.timestamp.hour] += 1

        # Find peak hour
        if hour_counts:
            peak_hour = max(hour_counts, key=hour_counts.get)  # type: ignore
            patterns["peak_hour"] = peak_hour
            patterns["peak_hour_count"] = hour_counts[peak_hour]

        # Detect activity spikes (more than 2x average)
        if len(hour_counts) > 1:
            avg_per_hour = sum(hour_counts.values()) / len(hour_counts)
            spikes = sum(1 for count in hour_counts.values() if count > avg_per_hour * 2)
            if spikes > 0:
                patterns["activity_spikes"] = spikes

        # Time range
        if len(entries) > 1:
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            time_range = (sorted_entries[-1].timestamp - sorted_entries[0].timestamp).total_seconds()
            patterns["time_range_seconds"] = int(time_range)

        return patterns

    def _generate_statistics(
        self, entries: list[LogEntry], anomalies: list[Anomaly]
    ) -> dict[str, Any]:
        """
        Generate statistical analysis.

        Args:
            entries: List of log entries
            anomalies: List of detected anomalies

        Returns:
            Dictionary of statistics
        """
        stats: dict[str, Any] = {}

        if not entries:
            return stats

        # Basic counts
        stats["total_entries"] = len(entries)
        stats["total_anomalies"] = len(anomalies)

        # Anomaly breakdown by severity
        if anomalies:
            severity_counts = Counter(a.severity for a in anomalies)
            stats["anomalies_by_severity"] = {
                severity.value: count for severity, count in severity_counts.items()
            }

            # Anomaly types
            type_counts = Counter(a.anomaly_type for a in anomalies)
            stats["anomalies_by_type"] = {
                atype.value: count for atype, count in type_counts.items()
            }

            # Average confidence
            avg_confidence = sum(a.confidence for a in anomalies) / len(anomalies)
            stats["average_confidence"] = round(avg_confidence, 2)

        # Top sources
        source_counts = Counter(entry.source for entry in entries)
        stats["top_sources"] = dict(source_counts.most_common(10))

        # Top hosts
        host_counts = Counter(entry.host for entry in entries if entry.host)
        if host_counts:
            stats["top_hosts"] = dict(host_counts.most_common(10))

        # Top users
        user_counts = Counter(entry.user for entry in entries if entry.user)
        if user_counts:
            stats["top_users"] = dict(user_counts.most_common(10))

        # Time range
        if len(entries) > 1:
            sorted_entries = sorted(entries, key=lambda e: e.timestamp)
            stats["first_entry"] = sorted_entries[0].timestamp.isoformat()
            stats["last_entry"] = sorted_entries[-1].timestamp.isoformat()

            time_delta = sorted_entries[-1].timestamp - sorted_entries[0].timestamp
            stats["time_span_hours"] = round(time_delta.total_seconds() / 3600, 2)

        return stats
