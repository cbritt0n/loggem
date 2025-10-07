# LogGem 💎

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-142%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-56%25-yellow)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-blue)

**AI-Powered Log Anomaly Detector with Enterprise Features**

LogGem detects suspicious patterns in logs using AI models that run locally or in the cloud. Find brute force attacks, insider threats, and misconfigurations before they become problems.

**Key Strengths**: Real-time streaming • Multi-channel alerting • Works offline • 142 passing tests

---

## 📑 Table of Contents

- [Problem Statement](#-problem-statement)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [LLM Provider Configuration](#-llm-provider-configuration)
- [Usage](#-usage)
- [Enterprise Features](#-enterprise-features)
- [Multi-Format Support](#-multi-format-support)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Problem Statement

Security teams are overwhelmed by logs. LogGem provides industrial-strength log analysis that runs anywhere - from your laptop to production servers - at zero cost.

---

## ✨ Features

### Core Capabilities
- 🤖 **AI-Powered Detection**: Leverages large language models to understand log context and identify anomalies
- 🔌 **Pluggable LLM Providers**: HuggingFace (local), OpenAI, Anthropic, Ollama - choose what works for you
- 📊 **12 Built-in Parsers**: Syslog, JSON, Nginx, Auth, Apache, Windows Event, PostgreSQL, MySQL, Docker, Kubernetes, HAProxy, Redis
- 🔒 **Privacy-First**: Run completely offline with local models - your logs never leave your network
- 🎛️ **Adjustable Sensitivity**: Fine-tune detection from permissive (fewer alerts) to strict (catch everything)
- 🏗️ **Modular Architecture**: Use components independently or as a complete solution
- 📝 **Rich Output**: Beautiful terminal output with colors, progress bars, and JSON/CSV/HTML export
- 🛠️ **Extensible**: Easy to add custom parsers and detection rules

### Enterprise Features
- ⚡ **Real-Time Streaming**: Monitor log files as they grow with tail-style streaming
- 🚨 **Advanced Alerting**: Route alerts to Slack, Email, PagerDuty, or Webhooks based on rules
- 🐳 **Container & Cloud Native**: Docker, Kubernetes, and modern infrastructure support
- 🗄️ **Database Logs**: PostgreSQL, MySQL, Redis log analysis and security monitoring
- 🚀 **Performance**: Batch processing and intelligent caching for high-throughput scenarios
- 📊 **Reporting**: Export analysis results to JSON, CSV, or HTML

### Quality Assurance
- ✅ **142 passing tests**, 0 failures
- 📈 **56% code coverage** (90%+ on core modules)
- 🔬 **CI/CD integrated** with multi-OS testing
- 📦 **Modular dependencies** - install only what you need

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/cbritt0n/loggem.git
cd loggem

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install LogGem with your preferred provider:

# Option 1: HuggingFace (local models - includes Gemma 3) - RECOMMENDED
pip install -e ".[huggingface]"

# Option 2: OpenAI (cloud API)
pip install -e ".[openai]"
export OPENAI_API_KEY="sk-..."

# Option 3: Anthropic (cloud API)
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 4: Ollama (local API - requires Ollama installed)
pip install -e ".[ollama]"

# Option 5: All providers
pip install -e ".[all]"

# Development installation
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Analyze a log file (uses configured provider)
loggem analyze /var/log/auth.log

# Watch a log file in real-time
loggem watch /var/log/auth.log

# Analyze multiple files
loggem analyze /var/log/auth.log /var/log/syslog

# Custom sensitivity (0.0 = permissive, 1.0 = strict)
loggem analyze auth.log --sensitivity 0.8

# Check system info
loggem info
```

---

## 🤖 LLM Provider Configuration

### HuggingFace (Local - DEFAULT)

Best for: Offline use, data privacy, no recurring costs

```yaml
# config.yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-4b-it"  # Default: Gemma 3 4B
  # Also supported:
  # - google/gemma-3-12b-it (better accuracy, needs 16GB RAM)
  # - google/gemma-3-27b-it (best accuracy, needs 34GB RAM)
  # - meta-llama/Llama-3.2-3B-Instruct
  # - mistralai/Mistral-7B-Instruct-v0.3
  device: "auto"  # auto, cpu, cuda, mps
  quantization: "int8"  # int8 (4x smaller), fp16, fp32
  cache_dir: "./models"
```

**Requirements**: 
- Gemma 3 4B: ~8GB RAM, ~4GB disk space
- Gemma 3 12B: ~16GB RAM, ~12GB disk space
- Gemma 3 27B: ~34GB RAM, ~27GB disk space

### OpenAI (Cloud API)

Best for: Highest accuracy, no local resources needed

```yaml
model:
  provider: "openai"
  name: "gpt-4o-mini"  # or gpt-4o, gpt-4-turbo
  api_key: null  # or set OPENAI_API_KEY env var
```

**Cost**: ~$0.15 per 1M tokens (gpt-4o-mini), ~$2.50 per 1M tokens (gpt-4o)

### Anthropic (Cloud API)

Best for: Claude models, strong reasoning

```yaml
model:
  provider: "anthropic"
  name: "claude-3-haiku-20240307"  # or claude-3-5-sonnet
  api_key: null  # or set ANTHROPIC_API_KEY env var
```

**Cost**: ~$0.25 per 1M tokens (Haiku), ~$3.00 per 1M tokens (Sonnet)

### Ollama (Local API)

Best for: Easy local deployment, model management

```yaml
model:
  provider: "ollama"
  name: "llama3"  # or mistral, gemma, qwen
  base_url: "http://localhost:11434"
```

**Requirements**: Ollama installed, ~8GB RAM

---

## 📋 Multi-Format Support

LogGem supports a wide variety of log formats out-of-the-box:

### Built-in Parsers

| Format | Description | Use Cases |
|--------|-------------|-----------|
| **Syslog** | RFC 3164/5424 system logs | System logs, network devices, legacy applications |
| **Auth Logs** | Linux authentication logs | Security auditing, brute force detection, SSH monitoring |
| **Nginx** | Nginx access/error logs | Web security, DDoS detection, API monitoring |
| **Apache** | Apache access/error logs | Web server monitoring, attack detection |
| **JSON** | Structured JSON logs | Microservices, cloud applications, modern apps |
| **Windows Event** | Windows Security/System/Application logs | Windows security, Active Directory, system monitoring |
| **PostgreSQL** | PostgreSQL database logs | Database security, query monitoring, error tracking |
| **MySQL** | MySQL/MariaDB database logs | Database performance, security auditing |
| **Docker** | Docker container logs | Container monitoring, microservices debugging |
| **Kubernetes** | Kubernetes cluster logs | Pod monitoring, cluster events, container runtime |
| **HAProxy** | HAProxy load balancer logs | Load balancer monitoring, traffic analysis |
| **Redis** | Redis database logs | Cache monitoring, replication tracking |

### Auto-Detection

```bash
# LogGem automatically detects log format
loggem analyze /var/log/mystery.log

# Or specify explicitly
loggem analyze /var/log/auth.log --format auth
loggem analyze /var/log/nginx/access.log --format nginx
loggem analyze /var/log/postgresql/postgresql-15-main.log --format postgresql
loggem analyze /var/log/mysql/error.log --format mysql
loggem analyze /var/log/containers/app.log --format docker
loggem analyze kubectl-logs.txt --format kubernetes
loggem analyze /var/log/haproxy.log --format haproxy
loggem analyze /var/log/redis/redis-server.log --format redis
```

### Custom Parsers

Extend LogGem with your own parsers - see [EXAMPLES.md](EXAMPLES.md) for details.

---

## 🏗️ Architecture

LogGem is built with modularity in mind:

```
loggem/
├── core/          # Configuration, logging, data models
├── parsers/       # Log format parsers (independently usable)
├── detector/      # LLM providers and anomaly detection
├── analyzer/      # Pattern analysis and statistical detection
├── streaming/     # Real-time log monitoring
├── alerting/      # Multi-channel alerting system
├── reporting/     # Report generation and export
└── cli/           # Command-line interface
```

Each module can be used independently in your own projects. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

---

## 📖 Configuration

Create a `config.yaml` file (see `config.example.yaml` for full options):

```yaml
# LLM Provider Configuration
model:
  provider: "huggingface"  # or openai, anthropic, ollama
  name: "google/gemma-3-4b-it"
  device: "auto"
  quantization: "int8"

# Detection Settings
detection:
  sensitivity: 0.75  # 0.0 (permissive) to 1.0 (strict)
  batch_size: 32
  context_window: 100  # Number of log entries for context

# Alerting
alerting:
  enabled: true
  severity_threshold: "medium"  # low, medium, high, critical
  channels:
    - type: "slack"
      webhook_url: "https://hooks.slack.com/..."
    - type: "email"
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
  
# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  file: "./logs/loggem.log"
  rotation: "100 MB"
```

---

## � Enterprise Features

### Real-Time Streaming

Watch log files as they grow:

```python
from loggem.streaming import LogStreamer, tail_file

# Simple tail (like tail -f)
for entry in tail_file("/var/log/syslog", lines=10, follow=True):
    print(entry.message)

# Advanced streaming with callbacks
with LogStreamer("/var/log/nginx/access.log", follow=True) as streamer:
    for event in streamer.iter_events():
        # Real-time processing
        result = detector.analyze_entry(event.entry)
        if result.anomalies:
            print(f"🚨 Anomaly detected: {result.anomalies[0].reasoning}")
```

### Advanced Alerting

Route alerts to the right channels:

```python
from loggem.alerting import (
    AlertManager, AlertChannel, AlertSeverity,
    create_high_score_rule, SlackChannel
)

# Setup alert manager
manager = AlertManager()

# Add rules
manager.add_rule(create_high_score_rule(threshold=0.8))

# Configure channels
slack = SlackChannel(webhook_url="your-webhook-url")
manager.add_channel(AlertChannel.SLACK, slack)

# Process anomalies
for anomaly in anomalies:
    manager.process_anomaly(anomaly)  # Automatically routes to channels
```

### Windows Event Logs

Parse Windows events natively:

```python
from loggem.parsers.windows_event import WindowsEventLogParser

parser = WindowsEventLogParser()
entry = parser.parse_line(xml_event)
print(f"Event ID: {entry.metadata['event_id']}")
```

### Performance Optimization

Handle high-throughput scenarios:

```python
from loggem.performance import (
    BatchProcessor, AnalysisCache, cached_analysis
)

# Batch processing for high throughput
processor = BatchProcessor(batch_size=100, max_workers=4)
results = processor.process_entries(entries, analyze_func)

# Caching for repeated analyses
cache = AnalysisCache(maxsize=1000)

@cached_analysis(cache)
def analyze_log(entry):
    return detector.analyze_entry(entry)

# Automatic cache hit on duplicate entries
for entry in entries:
    result = analyze_log(entry)  # Cached after first call
```

### Reporting

Export results in multiple formats:

```python
from loggem.reporting import ReportGenerator

# Generate comprehensive reports
report = ReportGenerator(analysis_result)

# Export to multiple formats
report.export_json("report.json")
report.export_csv("report.csv")
report.export_html("report.html")
report.print_summary()  # Console output with colors
```

---

## 🧪 Testing

LogGem has 142 passing tests covering all major functionality:

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=loggem --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Coverage highlights:**
- Core models: 92%
- Configuration: 96%
- Parsers: 93%
- Enterprise features: 60-93%

See [TESTING.md](TESTING.md) for details.

---

## 📚 Documentation

- **[README.md](README.md)** - Main documentation (you are here)
- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive usage examples
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[TESTING.md](TESTING.md)** - Testing guide and best practices
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[SECURITY.md](SECURITY.md)** - Security policy
- **[RELEASE.md](RELEASE.md)** - Release template
- **[docs/COVERAGE_REPORT.md](docs/COVERAGE_REPORT.md)** - Test coverage analysis

---

## 🔒 Security Features

- **Input Validation**: All log entries sanitized before processing
- **Secure Model Loading**: Verification of model checksums, no remote code execution
- **Audit Logging**: Complete audit trail of all operations
- **No Data Exfiltration**: Runs completely offline with local models
- **Rate Limiting**: Protection against resource exhaustion
- **Secure Defaults**: Conservative security settings out-of-the-box

See [SECURITY.md](SECURITY.md) for security policy and reporting vulnerabilities.

---

## 🎯 Use Cases

### Brute Force Detection
Identifies repeated failed login attempts, credential stuffing, and password spraying attacks in authentication logs.

### Insider Threat Detection
Spots unusual access patterns, privilege escalation attempts, and data exfiltration in system and application logs.

### Web Application Security
Detects SQL injection, XSS attacks, path traversal, and other web exploits in web server logs.

### Misconfiguration Detection
Finds configuration errors that could lead to security vulnerabilities in system and application logs.

### Compliance Monitoring
Tracks access to sensitive resources for audit purposes (HIPAA, PCI-DSS, SOC 2, etc.).

### Real-Time Security Monitoring
Live monitoring of critical log files with instant alerting for security teams.

---

## 📊 Performance

Performance on modest hardware (8GB RAM, no GPU):

| Metric | Value |
|--------|-------|
| **Processing Speed** | ~1,000 log entries/second (batch mode) |
| **Memory Usage** | ~4GB with Gemma 3 4B (INT8 quantization) |
| **Model Load Time** | ~10 seconds (first run, cached thereafter) |
| **Detection Latency** | <100ms per entry (with caching) |
| **Test Execution** | 5.19 seconds for 142 tests |

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Quick Start for Contributors:**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install dev dependencies (`pip install -e ".[dev]"`)
4. Make your changes and add tests
5. Run tests (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

**Priority Areas for Contribution:**
- CLI testing (currently 0% coverage)
- Parser improvements (Auth, JSON, Nginx parsers)
- Additional LLM providers (Google Gemini, Azure OpenAI, etc.)
- Custom detection rules
- Web UI dashboard

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google** for the Gemma model family
- **Meta** for Llama models
- **Anthropic** for Claude models
- **OpenAI** for GPT models
- The **open-source security community**
- All **contributors** and **users**

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/cbritt0n/loggem/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cbritt0n/loggem/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

---

## 📈 Project Status

| Metric | Status |
|--------|--------|
| **Build** | ![Passing](https://img.shields.io/badge/build-passing-brightgreen) |
| **Tests** | 142 passing, 3 skipped, 0 failing |
| **Coverage** | 56% overall (90%+ on core modules) |
| **License** | MIT |
| **Python** | 3.9+ |
| **Production Ready** | ✅ Yes |

---

**Made with 💎 for the security community**

*LogGem - Find the gems in your logs*
