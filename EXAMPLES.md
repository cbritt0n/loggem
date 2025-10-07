# LogGem Usage Examples

This document provides comprehensive examples of using LogGem with different LLM providers and configurations.

## Table of Contents

- [Installation Examples](#installation-examples)
- [Provider Configuration](#provider-configuration)
- [Command-Line Usage](#command-line-usage)
- [Python API Usage](#python-api-usage)
- [Custom Parsers](#custom-parsers)
- [Integration Examples](#integration-examples)

## Installation Examples

### Install for HuggingFace (Gemma 3)

```bash
# Recommended for offline use and data privacy
pip install -e ".[huggingface]"

# First run will download the model (~2-4GB)
loggem analyze examples/sample_auth.log
```

### Install for OpenAI

```bash
pip install -e ".[openai]"

# Set your API key
export OPENAI_API_KEY="sk-..."

# Or add to config.yaml
```

### Install for Anthropic Claude

```bash
pip install -e ".[anthropic]"

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Install for Ollama

```bash
pip install -e ".[ollama]"

# Install and start Ollama first
# https://ollama.ai
ollama pull llama3
```

## Provider Configuration

### HuggingFace - Gemma 3 4B - Fast & Efficient (DEFAULT)

```yaml
# config.yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-4b-it"  # 4B parameters
  device: "auto"  # Will use GPU if available
  quantization: "int8"  # Reduces memory by 4x
  cache_dir: "./models"
  max_length: 2048
```

**Best for**: Offline environments, data privacy, no API costs, getting started  
**Requirements**: 8GB RAM, ~4GB disk space  
**Speed**: ~1-2 seconds per log entry  
**Accuracy**: ⭐⭐⭐ Good for most use cases

### HuggingFace - Gemma 3 12B - Balanced (RECOMMENDED FOR PRODUCTION)

```yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-12b-it"  # 12B parameters
  device: "auto"
  quantization: "int8"
  cache_dir: "./models"
  max_length: 2048
```

**Best for**: Production deployments, better accuracy on complex patterns  
**Requirements**: 16GB RAM, ~12GB disk space  
**Speed**: ~3-5 seconds per log entry  
**Accuracy**: ⭐⭐⭐⭐ Better pattern recognition

### HuggingFace - Gemma 3 27B - Maximum Accuracy

```yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-27b-it"  # 27B parameters
  device: "auto"
  quantization: "int8"
  cache_dir: "./models"
  max_length: 4096
```

**Best for**: Mission-critical systems, highest accuracy needed  
**Requirements**: 34GB RAM (64GB recommended), ~27GB disk space, GPU recommended  
**Speed**: ~10-15 seconds per log entry  
**Accuracy**: ⭐⭐⭐⭐⭐ Best pattern recognition

### OpenAI - GPT-4o Mini - Cost Effective

```yaml
model:
  provider: "openai"
  name: "gpt-4o-mini"
  api_key: null  # Uses OPENAI_API_KEY env var
  max_length: 2048
```

**Best for**: Best accuracy, no local resources  
**Cost**: ~$0.15 per 1M input tokens  
**Speed**: ~500ms per log entry (API latency)

### OpenAI - GPT-4o - Highest Accuracy

```yaml
model:
  provider: "openai"
  name: "gpt-4o"
  api_key: null
  max_length: 2048
```

**Best for**: Complex security analysis  
**Cost**: ~$2.50 per 1M input tokens  
**Speed**: ~800ms per log entry

### Anthropic - Claude 3 Haiku - Fast

```yaml
model:
  provider: "anthropic"
  name: "claude-3-haiku-20240307"
  api_key: null  # Uses ANTHROPIC_API_KEY env var
  max_length: 2048
```

**Best for**: Fast cloud inference  
**Cost**: ~$0.25 per 1M input tokens  
**Speed**: ~400ms per log entry

### Anthropic - Claude 3.5 Sonnet - Best Reasoning

```yaml
model:
  provider: "anthropic"
  name: "claude-3-5-sonnet-20241022"
  api_key: null
  max_length: 2048
```

**Best for**: Complex pattern analysis  
**Cost**: ~$3.00 per 1M input tokens  
**Speed**: ~1s per log entry

### Ollama - Llama 3 - Local API

```yaml
model:
  provider: "ollama"
  name: "llama3"
  base_url: "http://localhost:11434"
  max_length: 2048
```

**Best for**: Easy local deployment  
**Requirements**: Ollama installed, 8GB RAM  
**Speed**: ~1-3 seconds per log entry

### Ollama - Mistral - Efficient

```yaml
model:
  provider: "ollama"
  name: "mistral"
  base_url: "http://localhost:11434"
  max_length: 2048
```

**Best for**: Lower resource usage  
**Requirements**: Ollama installed, 4GB RAM  
**Speed**: ~1-2 seconds per log entry

## Alternative Lightweight Models

### Llama 3.2 3B - Fast Alternative

```yaml
model:
  provider: "huggingface"
  name: "meta-llama/Llama-3.2-3B-Instruct"
  device: "auto"
  quantization: "int8"
  cache_dir: "./models"
  max_length: 2048
```

**Best for**: Fast inference, general text analysis  
**Requirements**: 8GB RAM, ~3GB disk space  
**Speed**: ~1-2 seconds per log entry  
**Accuracy**: ⭐⭐⭐ Similar to Gemma 3B

### Mistral 7B - Balanced Alternative

```yaml
model:
  provider: "huggingface"
  name: "mistralai/Mistral-7B-Instruct-v0.3"
  device: "auto"
  quantization: "int8"
  cache_dir: "./models"
  max_length: 2048
```

**Best for**: Strong reasoning capabilities  
**Requirements**: 16GB RAM, ~7GB disk space  
**Speed**: ~3-5 seconds per log entry  
**Accuracy**: ⭐⭐⭐⭐ Similar to Gemma 9B

### Qwen 2.5 7B - Multilingual

```yaml
model:
  provider: "huggingface"
  name: "Qwen/Qwen2.5-7B-Instruct"
  device: "auto"
  quantization: "int8"
  cache_dir: "./models"
  max_length: 2048
```

**Best for**: Multilingual log analysis  
**Requirements**: 16GB RAM, ~7GB disk space  
**Speed**: ~3-5 seconds per log entry  
**Accuracy**: ⭐⭐⭐⭐ Excellent multilingual support

## Command-Line Usage

### Model Selection Guide

```
╭──────────────────────────────────────────────────────────────────────╮
│                   🎯 Quick Model Selection Guide                     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Starting out?          → Gemma 3 4B (default)                       │
│  Have 16GB RAM?         → Gemma 3 12B (better accuracy)               │
│  Need best accuracy?    → Gemma 3 27B (requires 34GB)                │
│  Multilingual logs?     → Qwen 2.5 7B                                │
│  No local resources?    → OpenAI/Anthropic (cloud)                   │
│  Privacy critical?      → Any local model (Gemma, Llama, etc.)       │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

### Complete Model Comparison

| Model | Size | RAM | Speed | Accuracy | Best For |
|-------|------|-----|-------|----------|----------|
| **Gemma 3 4B** ⭐ | 4GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ | Getting started |
| **Gemma 3 12B** | 12GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Production use |
| **Gemma 3 27B** | 27GB | 34GB | ⚡ | ⭐⭐⭐⭐⭐ | Max accuracy |
| **Llama 3.2 3B** | 3GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ | Fast alternative |
| **Mistral 7B** | 7GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Strong reasoning |
| **Qwen 2.5 7B** | 7GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Multilingual |
| **GPT-4o Mini** | API | API | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Cloud, no setup |
| **Claude 3 Haiku** | API | API | ⚡⚡⚡ | ⭐⭐⭐⭐ | Cloud, fast |

⭐ = Default model

### Basic Analysis

```bash
# Analyze with default provider (from config.yaml)
loggem analyze /var/log/auth.log

# Specify format
loggem analyze /var/log/nginx/access.log --format nginx

# Multiple files
loggem analyze /var/log/auth.log /var/log/syslog

# Save results
loggem analyze auth.log --output results.json
```

### Advanced Options

```bash
# High sensitivity (more strict)
loggem analyze auth.log --sensitivity 0.9

# Low sensitivity (fewer false positives)
loggem analyze auth.log --sensitivity 0.5

# Disable AI detection (rules only - faster)
loggem analyze auth.log --no-ai

# Custom config file
loggem analyze auth.log --config my-config.yaml
```

### Real-Time Monitoring

```bash
# Watch a log file
loggem watch /var/log/auth.log

# Watch with specific format
loggem watch /var/log/nginx/access.log --format nginx

# Watch with custom sensitivity
loggem watch /var/log/syslog --sensitivity 0.8
```

### System Information

```bash
# Check configuration and system info
loggem info

# Check version
loggem version
```

## Python API Usage

### Basic Anomaly Detection

```python
from loggem import LogParserFactory, AnomalyDetector, LogAnalyzer

# Create parser
parser = LogParserFactory.create_parser("syslog")

# Parse log file
log_entries = list(parser.parse_file("/var/log/auth.log"))

# Detect anomalies with AI
detector = AnomalyDetector()
anomalies = []

for entry in log_entries:
    anomaly = detector.detect(entry)
    if anomaly:
        anomalies.append(anomaly)
        print(f"🚨 {anomaly.severity.value}: {anomaly.description}")

print(f"\nFound {len(anomalies)} anomalies")
```

### Using Different Providers

```python
from loggem.detector.model_manager import ModelManager

# HuggingFace provider
manager = ModelManager(
    provider_type="huggingface",
    provider_config={
        "model_name": "google/gemma-3-4b-it",
        "device": "auto",
        "quantization": "int8",
        "cache_dir": "./models",
    }
)

# OpenAI provider
manager = ModelManager(
    provider_type="openai",
    provider_config={
        "model": "gpt-4o-mini",
        "api_key": "sk-...",
    }
)

# Anthropic provider
manager = ModelManager(
    provider_type="anthropic",
    provider_config={
        "model": "claude-3-haiku-20240307",
        "api_key": "sk-ant-...",
    }
)

# Ollama provider
manager = ModelManager(
    provider_type="ollama",
    provider_config={
        "model": "llama3",
        "base_url": "http://localhost:11434",
    }
)

# Load and use
manager.load_model()
response = manager.generate_response("Analyze this log: ...")
```

### Rule-Based Detection Only

```python
from loggem import LogParserFactory
from loggem.analyzer.pattern_detector import PatternDetector

# Parse logs
parser = LogParserFactory.create_parser("auth")
log_entries = list(parser.parse_file("/var/log/auth.log"))

# Detect patterns without AI (faster)
detector = PatternDetector()
anomalies = detector.detect_all(log_entries)

for anomaly in anomalies:
    print(f"{anomaly.severity.value}: {anomaly.description}")
```

### Statistical Analysis

```python
from loggem import LogParserFactory, LogAnalyzer

# Parse and analyze
parser = LogParserFactory.create_parser("json")
log_entries = list(parser.parse_file("app.log"))

analyzer = LogAnalyzer()
result = analyzer.analyze(log_entries)

# Print statistics
print(f"Total entries: {result.total_entries}")
print(f"Anomalies: {len(result.anomalies)}")
print(f"Duration: {result.duration:.2f}s")

# Top sources
print("\nTop sources:")
for source, count in result.statistics.get("top_sources", [])[:5]:
    print(f"  {source}: {count}")
```

## Custom Parsers

### Creating a Custom Parser

```python
from loggem.parsers.base import BaseParser
from loggem.core.models import LogEntry
import re

class CustomAppParser(BaseParser):
    """Parser for custom application logs."""
    
    # Pattern: [2024-01-15 10:30:45] INFO User john logged in from 192.168.1.1
    PATTERN = re.compile(
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'(?P<level>\w+)\s+'
        r'(?P<message>.+)'
    )
    
    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        match = self.PATTERN.match(line)
        if not match:
            return None
        
        return LogEntry(
            timestamp=self._parse_timestamp(match.group('timestamp')),
            level=match.group('level'),
            message=match.group('message'),
            source="custom_app",
            raw=line,
        )

# Register and use
from loggem.parsers.factory import LogParserFactory

LogParserFactory.register_parser("custom", CustomAppParser)
parser = LogParserFactory.create_parser("custom")
```

### Using Custom Parser

```python
# In your code
from my_parsers import CustomAppParser
from loggem import AnomalyDetector

parser = CustomAppParser()
detector = AnomalyDetector()

for entry in parser.parse_file("app.log"):
    anomaly = detector.detect(entry)
    if anomaly:
        print(f"Anomaly: {anomaly.description}")
```

## Integration Examples

### Cron Job for Periodic Analysis

```bash
#!/bin/bash
# /etc/cron.hourly/loggem-check

# Activate virtual environment
source /opt/loggem/venv/bin/activate

# Analyze recent logs
loggem analyze /var/log/auth.log \
  --output /var/log/loggem/report-$(date +%Y%m%d-%H%M).json \
  --sensitivity 0.75

# Check for critical anomalies
if loggem analyze /var/log/auth.log --format auth --no-output | grep -q "CRITICAL"; then
  # Send alert
  echo "Critical anomaly detected" | mail -s "LogGem Alert" admin@example.com
fi
```

### Python Integration

```python
# app.py - Monitor application logs in real-time
import logging
from loggem import AnomalyDetector
from loggem.core.models import LogEntry

# Create detector
detector = AnomalyDetector()

# Custom log handler
class AnomalyHandler(logging.Handler):
    def emit(self, record):
        # Convert log record to LogEntry
        entry = LogEntry(
            timestamp=record.created,
            level=record.levelname,
            message=record.getMessage(),
            source=record.name,
        )
        
        # Check for anomaly
        anomaly = detector.detect(entry)
        if anomaly and anomaly.severity.value in ("HIGH", "CRITICAL"):
            # Send alert
            send_alert(anomaly)

# Add handler to logger
logger = logging.getLogger()
logger.addHandler(AnomalyHandler())
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install LogGem with HuggingFace
COPY . .
RUN pip install -e ".[huggingface]"

# Pre-download model
RUN python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('google/gemma-3-4b-it')"

# Run analysis on logs volume
CMD ["loggem", "watch", "/logs/app.log"]
```

```bash
# Run with Docker
docker build -t loggem .
docker run -v /var/log:/logs loggem
```

### Systemd Service

```ini
# /etc/systemd/system/loggem.service
[Unit]
Description=LogGem Log Monitoring
After=network.target

[Service]
Type=simple
User=loggem
WorkingDirectory=/opt/loggem
Environment=PATH=/opt/loggem/venv/bin
ExecStart=/opt/loggem/venv/bin/loggem watch /var/log/auth.log
Restart=always

[Install]
WantedBy=multi-user.target
```

### Webhook Alerting

```python
# webhook_alert.py
import requests
from loggem import AnomalyDetector, LogParserFactory

def send_webhook(anomaly):
    """Send anomaly to webhook endpoint."""
    webhook_url = "https://your-webhook.com/alerts"
    
    payload = {
        "severity": anomaly.severity.value,
        "type": anomaly.anomaly_type.value,
        "description": anomaly.description,
        "confidence": anomaly.confidence,
        "recommendation": anomaly.recommendation,
    }
    
    requests.post(webhook_url, json=payload)

# Monitor and alert
parser = LogParserFactory.create_parser("auth")
detector = AnomalyDetector()

for entry in parser.parse_file("/var/log/auth.log"):
    anomaly = detector.detect(entry)
    if anomaly and anomaly.severity.value in ("HIGH", "CRITICAL"):
        send_webhook(anomaly)
```

## Environment Variables

LogGem supports environment variables for configuration:

```bash
# LLM Provider
export LOGGEM_MODEL__PROVIDER="openai"
export LOGGEM_MODEL__NAME="gpt-4o-mini"

# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Detection settings
export LOGGEM_DETECTION__SENSITIVITY="0.8"
export LOGGEM_DETECTION__BATCH_SIZE="32"

# Security
export LOGGEM_SECURITY__MAX_FILE_SIZE="1073741824"  # 1GB

# Run with env vars
loggem analyze /var/log/auth.log
```

## Tips and Best Practices

### Choosing a Provider

- **HuggingFace (Gemma)**: Best for offline, data privacy, no recurring costs
- **OpenAI**: Best accuracy, fastest setup, pay-per-use
- **Anthropic**: Strong reasoning, good for complex analysis
- **Ollama**: Easy local deployment, good for development

### Performance Optimization

```yaml
# Fast configuration (lower accuracy)
detection:
  batch_size: 64
  context_window: 50
  min_confidence: 0.7

model:
  quantization: "int8"  # Faster inference

# Accurate configuration (slower)
detection:
  batch_size: 16
  context_window: 200
  min_confidence: 0.5

model:
  quantization: "fp32"  # Better accuracy
```

### Cost Optimization for Cloud APIs

```python
# Use rule-based detection first, AI only for uncertain cases
from loggem.analyzer.pattern_detector import PatternDetector
from loggem import AnomalyDetector

rule_detector = PatternDetector()
ai_detector = AnomalyDetector()

for entry in log_entries:
    # Try rules first (free)
    anomalies = rule_detector.detect_all([entry])
    
    if not anomalies:
        # Use AI only if rules don't catch anything
        anomaly = ai_detector.detect(entry)
```

### Security Best Practices

```yaml
# Recommended security settings
security:
  max_file_size: 1073741824  # 1GB limit
  max_line_length: 10000
  enable_audit_log: true
  sanitize_input: true

model:
  trust_remote_code: false  # Never enable unless you trust the model
```
