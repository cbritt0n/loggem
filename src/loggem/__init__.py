"""
LogGem: AI-Assisted Log Anomaly Detector

A lightweight, modular, open-source tool for detecting anomalies in logs using
configurable LLM providers (HuggingFace, OpenAI, Anthropic, Ollama).
"""

__version__ = "1.0.0"
__author__ = "Christian Britton"
__license__ = "MIT"

from loggem.analyzer.log_analyzer import LogAnalyzer
from loggem.core.models import Anomaly, LogEntry, Severity
from loggem.detector.anomaly_detector import AnomalyDetector
from loggem.detector.model_manager import ModelManager
from loggem.parsers.factory import LogParserFactory

__all__ = [
    "LogEntry",
    "Anomaly",
    "Severity",
    "LogParserFactory",
    "AnomalyDetector",
    "ModelManager",
    "LogAnalyzer",
]
