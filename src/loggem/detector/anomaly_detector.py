"""
AI-powered anomaly detector for log entries.

Uses Gemma 3 (or other LLMs) to identify suspicious patterns and anomalies.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from loggem.core.config import get_settings
from loggem.core.logging import get_audit_logger, get_logger
from loggem.core.models import Anomaly, AnomalyType, LogEntry, Severity
from loggem.detector.model_manager import ModelManager

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class AnomalyDetector:
    """
    AI-powered anomaly detector.

    Analyzes log entries using an LLM to identify security threats,
    misconfigurations, and unusual patterns.
    """

    # System prompt for anomaly detection
    SYSTEM_PROMPT = """You are a security analyst specializing in log analysis and anomaly detection.
Your task is to analyze log entries and identify potential security threats, misconfigurations, and unusual patterns.

For each log entry, respond with a JSON object containing:
- "is_anomaly": boolean indicating if this is anomalous
- "confidence": float between 0.0 and 1.0
- "severity": one of "low", "medium", "high", "critical"
- "anomaly_type": one of "brute_force", "privilege_escalation", "unusual_access", "data_exfiltration", "misconfiguration", "suspicious_activity", "authentication_failure", "rate_limit_exceeded", "malformed_request", "unknown"
- "description": brief explanation of the anomaly
- "indicators": list of specific indicators
- "recommendation": suggested action

Focus on:
- Failed authentication attempts (especially repeated)
- Unusual access patterns or times
- Privilege escalation attempts
- Data exfiltration indicators
- Malformed or suspicious requests
- Configuration errors
- Rate limit violations

Respond ONLY with the JSON object, no additional text."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        sensitivity: Optional[float] = None,
        min_confidence: Optional[float] = None,
    ) -> None:
        """
        Initialize anomaly detector.

        Args:
            model_name: Model to use (default from config)
            sensitivity: Detection sensitivity 0.0-1.0 (default from config)
            min_confidence: Minimum confidence to report anomaly (default from config)
        """
        self.settings = get_settings()
        self.sensitivity = sensitivity or self.settings.detection.sensitivity
        self.min_confidence = min_confidence or self.settings.detection.min_confidence

        self.model_manager = ModelManager(model_name=model_name)
        self._model_loaded = False

        logger.info(
            "anomaly_detector_initialized",
            sensitivity=self.sensitivity,
            min_confidence=self.min_confidence,
        )

    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded."""
        if not self._model_loaded:
            self.model_manager.load_model()
            self._model_loaded = True

    def detect(
        self, entry: LogEntry, context: Optional[list[LogEntry]] = None
    ) -> Optional[Anomaly]:
        """
        Detect anomalies in a single log entry.

        Args:
            entry: Log entry to analyze
            context: Optional context entries (previous logs)

        Returns:
            Anomaly if detected, None otherwise
        """
        self._ensure_model_loaded()

        # Build prompt with context
        prompt = self._build_prompt(entry, context)

        # Get AI response
        try:
            response = self.model_manager.generate_response(
                prompt,
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            # Parse response
            anomaly = self._parse_response(response, entry)

            # Apply confidence threshold
            if anomaly and anomaly.confidence >= self.min_confidence:
                logger.info(
                    "anomaly_detected",
                    entry_id=str(entry.id),
                    severity=anomaly.severity.value,
                    confidence=anomaly.confidence,
                )
                return anomaly

        except Exception as e:
            logger.error("detection_failed", entry_id=str(entry.id), error=str(e))

        return None

    def detect_batch(self, entries: list[LogEntry], use_context: bool = True) -> list[Anomaly]:
        """
        Detect anomalies in a batch of log entries.

        Args:
            entries: List of log entries to analyze
            use_context: Whether to use previous entries as context

        Returns:
            List of detected anomalies
        """
        self._ensure_model_loaded()

        anomalies = []
        context_window = self.settings.detection.context_window

        for i, entry in enumerate(entries):
            # Get context from previous entries
            context = None
            if use_context and i > 0:
                start_idx = max(0, i - context_window)
                context = entries[start_idx:i]

            # Detect anomaly
            anomaly = self.detect(entry, context)
            if anomaly:
                anomalies.append(anomaly)

        logger.info(
            "batch_detection_complete",
            total_entries=len(entries),
            anomalies_found=len(anomalies),
        )

        # Log to audit trail
        if anomalies:
            max_severity = max(a.severity for a in anomalies)
            audit_logger.log_anomaly_detection(
                anomaly_count=len(anomalies),
                severity=max_severity.value,
                source=entries[0].source if entries else "unknown",
            )

        return anomalies

    def _build_prompt(self, entry: LogEntry, context: Optional[list[LogEntry]] = None) -> str:
        """
        Build prompt for the model.

        Args:
            entry: Log entry to analyze
            context: Optional context entries

        Returns:
            Formatted prompt string
        """
        prompt_parts = [self.SYSTEM_PROMPT, "\n\n"]

        # Add context if available
        if context:
            prompt_parts.append("Context (previous log entries):\n")
            for ctx_entry in context[-10:]:  # Last 10 entries
                prompt_parts.append(
                    f"[{ctx_entry.timestamp.isoformat()}] {ctx_entry.level}: {ctx_entry.message}\n"
                )
            prompt_parts.append("\n")

        # Add the entry to analyze
        prompt_parts.append("Analyze this log entry:\n")
        prompt_parts.append(f"Timestamp: {entry.timestamp.isoformat()}\n")
        prompt_parts.append(f"Source: {entry.source}\n")
        prompt_parts.append(f"Level: {entry.level}\n")
        if entry.host:
            prompt_parts.append(f"Host: {entry.host}\n")
        if entry.user:
            prompt_parts.append(f"User: {entry.user}\n")
        if entry.process:
            prompt_parts.append(f"Process: {entry.process}\n")
        prompt_parts.append(f"Message: {entry.message}\n\n")

        # Add metadata if relevant
        if entry.metadata:
            relevant_metadata = {
                k: v
                for k, v in entry.metadata.items()
                if k in ["status", "method", "path", "event_type", "command"]
            }
            if relevant_metadata:
                prompt_parts.append(f"Metadata: {json.dumps(relevant_metadata)}\n\n")

        prompt_parts.append("Response (JSON only):")

        return "".join(prompt_parts)

    def _parse_response(self, response: str, entry: LogEntry) -> Optional[Anomaly]:
        """
        Parse model response into Anomaly object.

        Args:
            response: Model's response text
            entry: Original log entry

        Returns:
            Anomaly if valid response, None otherwise
        """
        try:
            # Extract JSON from response (model might add extra text)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if not json_match:
                logger.warning("no_json_in_response", response=response[:200])
                return None

            data = json.loads(json_match.group(0))

            # Check if it's an anomaly
            if not data.get("is_anomaly", False):
                return None

            # Extract fields with validation
            confidence = float(data.get("confidence", 0.5))
            severity_str = data.get("severity", "low").lower()
            anomaly_type_str = data.get("anomaly_type", "unknown").lower()

            # Map to enums
            severity_map = {
                "low": Severity.LOW,
                "medium": Severity.MEDIUM,
                "high": Severity.HIGH,
                "critical": Severity.CRITICAL,
            }
            severity = severity_map.get(severity_str, Severity.LOW)

            anomaly_type_map = {
                "brute_force": AnomalyType.BRUTE_FORCE,
                "privilege_escalation": AnomalyType.PRIVILEGE_ESCALATION,
                "unusual_access": AnomalyType.UNUSUAL_ACCESS,
                "data_exfiltration": AnomalyType.DATA_EXFILTRATION,
                "misconfiguration": AnomalyType.MISCONFIGURATION,
                "suspicious_activity": AnomalyType.SUSPICIOUS_ACTIVITY,
                "authentication_failure": AnomalyType.AUTHENTICATION_FAILURE,
                "rate_limit_exceeded": AnomalyType.RATE_LIMIT_EXCEEDED,
                "malformed_request": AnomalyType.MALFORMED_REQUEST,
                "unknown": AnomalyType.UNKNOWN,
            }
            anomaly_type = anomaly_type_map.get(anomaly_type_str, AnomalyType.UNKNOWN)

            # Adjust confidence based on sensitivity
            adjusted_confidence = confidence * (0.5 + self.sensitivity * 0.5)

            # Create anomaly
            return Anomaly(
                log_entry_id=entry.id,
                severity=severity,
                anomaly_type=anomaly_type,
                description=data.get("description", "Anomaly detected"),
                confidence=adjusted_confidence,
                indicators=data.get("indicators", []),
                recommendation=data.get("recommendation"),
                context=[entry.message],
                metadata={"raw_response": response, "original_confidence": confidence},
            )

        except Exception as e:
            logger.warning("response_parse_failed", error=str(e), response=response[:200])
            return None

    def cleanup(self) -> None:
        """Clean up resources (unload model)."""
        if self._model_loaded:
            self.model_manager.unload_model()
            self._model_loaded = False
        logger.info("detector_cleanup_complete")
