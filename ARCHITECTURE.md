# LogGem Architecture

Complete overview of the LogGem architecture and design patterns.

## Directory Structure

```
loggem/
├── src/loggem/              # Main source code
│   ├── __init__.py          # Package initialization
│   ├── py.typed             # PEP 561 marker
│   │
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── models.py        # Data models (LogEntry, Anomaly, etc.)
│   │   ├── config.py        # Configuration management
│   │   └── logging.py       # Structured logging setup
│   │
│   ├── parsers/             # Log format parsers
│   │   ├── __init__.py
│   │   ├── base.py          # Base parser interface
│   │   ├── factory.py       # Parser factory with auto-detection
│   │   ├── syslog.py        # Syslog parser (RFC 3164/5424)
│   │   ├── json_parser.py   # JSON log parser
│   │   ├── nginx.py         # Nginx access/error logs
│   │   ├── apache.py        # Apache/httpd access/error logs
│   │   ├── auth.py          # Auth log parser (SSH, sudo)
│   │   ├── windows_event.py # Windows Event Log parser
│   │   ├── postgresql.py    # PostgreSQL database logs
│   │   ├── mysql.py         # MySQL/MariaDB database logs
│   │   ├── docker.py        # Docker container logs
│   │   ├── kubernetes.py    # Kubernetes cluster logs
│   │   ├── haproxy.py       # HAProxy load balancer logs
│   │   └── redis.py         # Redis database logs
│   │
│   ├── detector/            # Anomaly detection
│   │   ├── __init__.py
│   │   ├── llm_provider.py  # LLM provider abstraction
│   │   ├── model_manager.py # Model lifecycle management
│   │   └── anomaly_detector.py # AI-powered detection
│   │
│   ├── analyzer/            # Analysis and patterns
│   │   ├── __init__.py
│   │   ├── log_analyzer.py  # Statistical analysis
│   │   └── pattern_detector.py # Rule-based detection
│   │
│   ├── streaming/           # Real-time monitoring
│   │   ├── __init__.py
│   │   ├── streamer.py      # Log file streaming
│   │   └── tail.py          # Tail-like functionality
│   │
│   ├── alerting/            # Multi-channel alerting
│   │   ├── __init__.py
│   │   ├── manager.py       # Alert manager
│   │   ├── channels.py      # Alert channels (Slack, Email, etc.)
│   │   └── rules.py         # Alert rules engine
│   │
│   ├── performance/         # Performance optimization
│   │   ├── __init__.py
│   │   ├── batch.py         # Batch processing
│   │   └── cache.py         # LRU caching
│   │
│   ├── reporting/           # Report generation
│   │   ├── __init__.py
│   │   └── generator.py     # Report generator (JSON, CSV, HTML)
│   │
│   └── cli.py               # Command-line interface
│
├── tests/                   # Comprehensive test suite (142 tests, 56% coverage)
│   ├── __init__.py
│   ├── test_config.py       # Configuration tests (41 tests)
│   ├── test_models.py       # Core model tests (8 tests)
│   ├── test_parsers.py      # Parser tests (5 tests)
│   ├── test_llm_provider.py # LLM provider tests (22 tests)
│   ├── test_model_manager.py # Model manager tests (20 tests)
│   ├── test_analyzers.py    # Analyzer tests (15 tests)
│   ├── enterprise/          # Enterprise feature tests (31 tests)
│   │   ├── test_alerting.py # Alerting system tests
│   │   ├── test_streaming.py # Streaming tests
│   │   ├── test_performance.py # Performance optimization tests
│   │   └── test_windows_event.py # Windows Event Log tests
│   └── conftest.py          # Shared test fixtures
│
├── examples/                # Example files
│   ├── sample_auth.log      # Example auth logs
│   ├── sample_nginx.log     # Example nginx logs
│   ├── sample_json.log      # Example JSON logs
│   ├── basic_usage.py       # Basic usage example
│   └── custom_parser.py     # Custom parser example
│
├── docs/                    # Additional documentation
│   └── COVERAGE_REPORT.md   # Detailed coverage analysis
│
├── pyproject.toml           # Project metadata & dependencies
├── config.example.yaml      # Example configuration
├── .gitignore               # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks
├── Makefile                 # Development commands
│
├── README.md                # Main documentation
├── EXAMPLES.md              # Usage examples
├── ARCHITECTURE.md          # This file
├── TESTING.md               # Testing guide
├── CONTRIBUTING.md          # Contribution guidelines
├── DEPLOYMENT.md            # Deployment guide
├── SECURITY.md              # Security policy
├── RELEASE.md               # Release template
├── LICENSE                  # MIT License
├── install.sh               # Installation script
└── quickstart.py            # Interactive setup
```

## Module Descriptions

### Core (`src/loggem/core/`)

**Purpose**: Foundation of LogGem with data models, configuration, and logging.

**Files**:
- `models.py`: Defines `LogEntry`, `Anomaly`, `AnalysisResult`, and enums
- `config.py`: Configuration management with Pydantic settings
- `logging.py`: Structured logging with audit trail

**Key Classes**:
- `LogEntry`: Standardized log entry representation with validation
- `Anomaly`: Detected anomaly with severity, type, and recommendations
- `Settings`: Application configuration with nested sections
- `AuditLogger`: Security event logging
- `Anomaly`: Detected anomaly with metadata
- `Severity`: Enum for severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- `AnomalyType`: Enum for anomaly types (BRUTE_FORCE, etc.)
- `Settings`: Application configuration

### Parsers (`src/loggem/parsers/`)

**Purpose**: Convert various log formats into standardized LogEntry objects.

**Files**:
- `base.py`: Abstract base class for all parsers
- `factory.py`: Factory pattern for parser creation with auto-detection
- `syslog.py`: RFC 3164 and RFC 5424 syslog formats
- `json_parser.py`: JSON-structured logs
- `nginx.py`: Nginx access and error logs
- `apache.py`: Apache/httpd access and error logs
- `auth.py`: Linux authentication logs (SSH, sudo, su)
- `windows_event.py`: Windows Event Logs (Security, System, Application)
- `postgresql.py`: PostgreSQL database logs
- `mysql.py`: MySQL/MariaDB database logs
- `docker.py`: Docker container logs (JSON, compose, CLI formats)
- `kubernetes.py`: Kubernetes cluster logs (kubectl, events, container runtime)
- `haproxy.py`: HAProxy load balancer logs (HTTP/TCP)
- `redis.py`: Redis database logs

**Key Classes**:
- `BaseParser`: Abstract base with common functionality
- `LogParserFactory`: Creates appropriate parser for log format with auto-detection
- Format-specific parsers: `SyslogParser`, `JSONParser`, `PostgreSQLParser`, etc.

**Supported Formats**: 12 built-in parsers covering system logs, web servers, databases, containers, and load balancers

### Detector (`src/loggem/detector/`)

**Purpose**: AI-powered anomaly detection with pluggable LLM providers.

**Files**:
- `llm_provider.py`: Abstract LLM provider interface and implementations
- `model_manager.py`: Model lifecycle management with provider abstraction
- `anomaly_detector.py`: Main detection engine with AI integration

**Key Classes**:
- `LLMProvider`: Abstract base for all providers
- `HuggingFaceProvider`: Local models (Gemma 3, Llama, Mistral, etc.)
- `OpenAIProvider`: OpenAI API integration (GPT-4o, GPT-4o-mini, etc.)
- `AnthropicProvider`: Anthropic API integration (Claude 3+)
- `OllamaProvider`: Ollama local API integration
- `ModelManager`: Provider-agnostic model lifecycle management
- `AnomalyDetector`: Analyzes logs using configured LLM provider

**Features**:
- Multiple LLM provider support (HuggingFace, OpenAI, Anthropic, Ollama)
- Model quantization for HuggingFace (INT8, FP16, FP32)
- Automatic device selection (CUDA, MPS, CPU)
- Context-aware detection
- Configurable sensitivity
- Extensible provider system
- Batch processing for efficiency
- Performance optimization with caching

**Supported Models**:
- **HuggingFace**: google/gemma-3-4b-it, google/gemma-3-12b-it, Llama 3, Mistral, Qwen
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3-haiku, claude-3-5-sonnet, claude-3-opus
- **Ollama**: llama3, mistral, gemma, qwen, and any Ollama model

### Analyzer (`src/loggem/analyzer/`)

**Purpose**: Statistical analysis and rule-based pattern detection.

- `log_analyzer.py`: Generates statistics and insights
- `pattern_detector.py`: Rule-based anomaly detection

**Key Classes**:
- `LogAnalyzer`: Statistical analysis of logs and anomalies
- `PatternDetector`: Detects common attack patterns

**Detection Rules**:
- Brute force authentication attempts
- Privilege escalation
- Suspicious web requests (SQL injection, XSS)
- Rate limit violations

### CLI (`src/loggem/cli.py`)

**Purpose**: Command-line interface using Typer and Rich.

**Commands**:
- `analyze`: Analyze log files
- `watch`: Real-time monitoring
- `info`: System information
- `version`: Version info

**Features**:
- Rich terminal output with colors
- Progress indicators
- JSON export
- Multiple file support

### Streaming (`src/loggem/streaming/`)

**Purpose**: Real-time log file monitoring and streaming.

**Files**:
- `streamer.py`: LogStreamer class for advanced streaming
- `tail.py`: Simple tail-like functionality

**Key Classes**:
- `LogStreamer`: Advanced streaming with callbacks
- `tail_file()`: Simple tail -f functionality

**Features**:
- Real-time file monitoring with watchdog
- Multi-file streaming support
- Async streaming capabilities
- Position tracking for resumable streaming
- Event-based callbacks

### Alerting (`src/loggem/alerting/`)

**Purpose**: Multi-channel alerting system with intelligent routing.

**Files**:
- `manager.py`: AlertManager orchestrates alert processing
- `channels.py`: Alert channel implementations
- `rules.py`: Alert rule engine

**Key Classes**:
- `AlertManager`: Main alert orchestrator
- `AlertChannel`: Base class for alert channels
- `SlackChannel`, `EmailChannel`, `WebhookChannel`: Channel implementations
- `AlertRule`: Rule-based alert filtering

**Features**:
- Multi-channel support (Console, Email, Webhook, Slack)
- Intelligent rule engine for alert conditions
- Rate limiting and deduplication
- Alert aggregation and batching
- Severity-based routing

### Performance (`src/loggem/performance/`)

**Purpose**: Performance optimization for high-throughput analysis.

**Files**:
- `batch.py`: Batch processing implementation
- `cache.py`: LRU caching for duplicate detection

**Key Classes**:
- `BatchProcessor`: Batch processing for high throughput
- `AnalysisCache`: LRU cache for duplicate entry detection
- `@cached_analysis`: Decorator for automatic caching

**Features**:
- Adaptive batching based on system resources
- Memory-efficient processing
- LRU caching for duplicate detection
- Configurable batch sizes
- Async processing support

### Reporting (`src/loggem/reporting/`)

**Purpose**: Comprehensive report generation and export.

**Files**:
- `generator.py`: ReportGenerator class

**Key Classes**:
- `ReportGenerator`: Generate reports from analysis results

**Features**:
- JSON, CSV, HTML export formats
- Detailed statistics and metrics
- Severity breakdowns
- Top anomalies highlighting
- Timeline visualization
- Configurable report templates

## Data Flow

```
1. Log Files
   ↓
2. Parser (converts to LogEntry objects)
   ↓
3. Pattern Detector (rule-based anomalies)
   ↓
4. AI Detector (AI-based anomalies)
   ↓
5. Analyzer (statistics and insights)
   ↓
6. Output (terminal, JSON file)
```

## Key Design Patterns

### Factory Pattern
- `LogParserFactory` creates appropriate parser based on format

### Strategy Pattern
- Different parsers implement same `BaseParser` interface

### Builder Pattern
- `LogEntry` and `Anomaly` use Pydantic for validation

### Singleton Pattern
- Global `Settings` instance via `get_settings()`

### Template Method
- `BaseParser` defines parsing workflow, subclasses implement specifics

## Dependencies

### Core
- **pydantic**: Data validation and settings
- **transformers**: AI model loading
- **torch**: Neural network operations

### CLI
- **typer**: CLI framework
- **rich**: Terminal formatting

### Utilities
- **structlog**: Structured logging
- **watchdog**: File monitoring
- **cryptography**: Security features

### Development
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking

## Extension Points

### Adding New Parsers
1. Inherit from `BaseParser`
2. Implement `parse_line()` method
3. Register with `LogParserFactory`

### Adding New Detectors
1. Add method to `PatternDetector`
2. Return list of `Anomaly` objects
3. Follow naming: `detect_[pattern_name]`

### Custom Configuration
1. Extend `Settings` class in `config.py`
2. Add to `config.yaml`
3. Access via `get_settings()`

## Performance Considerations

### Memory
- Generator-based file parsing
- Model quantization (INT8 saves 4x memory)
- Configurable batch sizes

### Speed
- Rule-based detection runs first (fast)
- AI detection optional (slower but accurate)
- Batch processing for efficiency

### Scalability
- Process files sequentially or in parallel
- Streaming support for large files
- Context window limits memory usage

## Security Features

### Input Validation
- All inputs sanitized in `LogEntry`
- Maximum line length enforced
- Control characters removed

### Model Security
- No remote code execution (`trust_remote_code=False`)
- Model checksums verified
- Secure defaults throughout

### Audit Trail
- All operations logged
- Separate audit log file
- Security events tracked

## Testing Strategy

### Current Status
- **111 passing tests** across all modules
- **50% overall code coverage**
- **3 skipped tests** (require complex integration)
- **0 failing tests** - production ready!

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (LLM providers, file I/O)
- Fast execution (completes in <3 seconds)
- Covers configuration, models, parsers, analyzers

### Integration Tests
- Test component interaction and data flow
- Use sample log files for realistic scenarios
- Verify end-to-end parsing → detection → analysis flow
- Test provider factory patterns

### Test Organization
- `test_config.py`: All configuration classes and validation (41 tests)
- `test_models.py`: Core data models and validation (8 tests)
- `test_parsers.py`: Log format parsing (5 tests)
- `test_llm_provider.py`: LLM provider abstraction (22 tests)
- `test_model_manager.py`: Model lifecycle management (20 tests)
- `test_analyzers.py`: Statistical analysis and pattern detection (15 tests)

### Coverage Highlights
- **High coverage** (90%+): Core models, config, model manager, parsers
- **Medium coverage** (50-90%): Analyzers, pattern detectors
- **Low coverage** (<50%): CLI (0%), some parsers (16-32%), anomaly detector (19%)

### Running Tests
```bash
# All tests with coverage
pytest tests/ -v --cov=loggem --cov-report=html

# Specific module
pytest tests/test_config.py -v

# With markers
pytest tests/ -v -m "not slow"

# Generate coverage report
pytest tests/ --cov=loggem --cov-report=term-missing
```

### CI/CD Integration
- GitHub Actions workflow configured
- Multi-OS testing (Ubuntu, macOS, Windows)
- Multi-Python versions (3.9, 3.10, 3.11, 3.12)
- Automated linting (ruff, black)
- Security scanning (bandit, safety)
- Coverage reporting to Codecov

## CI/CD Pipeline

### GitHub Actions Workflow

Location: `.github/workflows/ci.yml`

**Test Job** (Matrix strategy):
- **Operating Systems**: Ubuntu 22.04, macOS 13, Windows 2022
- **Python Versions**: 3.9, 3.10, 3.11, 3.12
- **Steps**:
  1. Checkout code
  2. Set up Python
  3. Install dependencies
  4. Run pytest with coverage
  5. Upload coverage to Codecov

**Lint Job**:
- Code formatting check with `black`
- Linting with `ruff`
- Runs on Python 3.11

**Security Job**:
- Security scanning with `bandit`
- Dependency vulnerability check with `safety`
- Generates security report

**Docs Job**:
- Markdown linting with `markdownlint-cli`
- Link checking with `markdown-link-check`
- Ensures documentation quality

### Pre-commit Hooks

`.pre-commit-config.yaml` includes:
- Code formatting (black, isort)
- Linting (ruff)
- Type checking (mypy)
- Security checks (bandit)
- YAML/JSON validation
- Trailing whitespace removal

### Quality Gates

- All tests must pass
- No linting errors allowed
- Security vulnerabilities flagged
- Documentation links verified
- Code coverage tracked

---

**Test Status**: 142 passing, 3 skipped, 0 failing  
**Coverage**: 56% overall (90%+ on core modules)
