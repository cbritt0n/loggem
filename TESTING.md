# LogGem Testing Guide

Here's my complete guide to testing LogGem, understanding test coverage, and contributing tests.

## Test Status

**Current Status**: ✅ **Production Ready**

- **142 passing tests** (0 failures)
- **3 skipped tests** (require complex integration)
- **56% overall code coverage**
- **Multi-OS tested**: Ubuntu, macOS, Windows
- **Multi-Python tested**: 3.9, 3.10, 3.11, 3.12

## Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=loggem --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## Test Organization

### Test Files

```
tests/
├── __init__.py
├── test_config.py         # 41 tests - Configuration & settings
├── test_models.py         # 8 tests - Core data models
├── test_parsers.py        # 5 tests - Log format parsers
├── test_llm_provider.py   # 22 tests - LLM provider abstraction
├── test_model_manager.py  # 20 tests - Model lifecycle
├── test_analyzers.py      # 15 tests - Analysis & detection
└── enterprise/            # 31 tests - Enterprise features
    ├── test_alerting.py       # Alerting system tests
    ├── test_streaming.py      # Streaming tests
    ├── test_performance.py    # Performance optimization tests
    └── test_windows_event.py  # Windows Event Log tests
```

### Coverage by Module

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| `core/config.py` | 96% | 41 | ✅ Excellent |
| `detector/model_manager.py` | 97% | 20 | ✅ Excellent |
| `parsers/syslog.py` | 94% | 5 | ✅ Excellent |
| `parsers/windows_event.py` | 93% | 31 | ✅ Excellent |
| `analyzer/pattern_detector.py` | 94% | 15 | ✅ Excellent |
| `core/models.py` | 92% | 8 | ✅ Excellent |
| `analyzer/log_analyzer.py` | 88% | 15 | ✅ Good |
| `performance/` | 83% | 31 | ✅ Good |
| `alerting/` | 68% | 31 | ⚠️ Good |
| `streaming/` | 60% | 31 | ⚠️ Acceptable |
| `core/logging.py` | 58% | - | ⚠️ Needs tests |
| `detector/llm_provider.py` | 41% | 22 | ⚠️ Needs integration tests |
| `parsers/base.py` | 32% | - | ⚠️ Needs tests |
| `parsers/nginx.py` | 20% | - | ❌ Needs tests |
| `parsers/json_parser.py` | 21% | - | ❌ Needs tests |
| `detector/anomaly_detector.py` | 19% | - | ❌ Needs tests |
| `parsers/auth.py` | 16% | - | ❌ Needs tests |
| `cli.py` | 0% | - | ❌ Needs tests |

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_config.py

# Run specific test class
pytest tests/test_config.py::TestModelConfig

# Run specific test
pytest tests/test_config.py::TestModelConfig::test_default_provider

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

### Coverage Commands

```bash
# Generate coverage report
pytest tests/ --cov=loggem

# HTML coverage report
pytest tests/ --cov=loggem --cov-report=html

# Show missing lines
pytest tests/ --cov=loggem --cov-report=term-missing

# Coverage for specific module
pytest tests/ --cov=loggem.core --cov-report=term

# Minimum coverage threshold
pytest tests/ --cov=loggem --cov-fail-under=50
```

### Test Markers

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto
```

### Debugging Tests

```bash
# Debug mode with PDB
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l

# Full traceback
pytest tests/ --tb=long

# Only last failed tests
pytest tests/ --lf

# Stop after N failures
pytest tests/ --maxfail=3
```

## Test Structure

### Configuration Tests (`test_config.py`)

Tests all configuration classes:

```python
class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_default_provider(self):
        """Test default provider is huggingface."""
        config = ModelConfig()
        assert config.provider == "huggingface"
    
    def test_default_model_name(self):
        """Test default model is Gemma 3."""
        config = ModelConfig()
        assert config.name == "google/gemma-3-4b-it"
```

**Coverage**: 41 tests covering:
- Default values
- Custom configurations
- Validation rules
- Environment variables
- YAML file loading
- Singleton pattern

### Model Tests (`test_models.py`)

Tests core data models:

```python
class TestLogEntry:
    """Test LogEntry model."""
    
    def test_create_basic_entry(self):
        """Test creating a basic log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            source="test",
            message="Test message",
            raw="raw log line"
        )
        assert entry.level == "INFO"
        assert entry.source == "test"
```

**Coverage**: 8 tests covering:
- LogEntry creation and validation
- Anomaly model
- AnalysisResult aggregation
- Field validation
- Sanitization

### Parser Tests (`test_parsers.py`)

Tests log format parsers:

```python
class TestSyslogParser:
    """Test syslog parser."""
    
    def test_parse_rfc3164_basic(self):
        """Test parsing RFC 3164 syslog."""
        parser = SyslogParser()
        line = "Jan 15 10:30:00 hostname sshd[1234]: Failed password"
        entry = parser.parse_line(line)
        assert entry.source == "sshd"
```

**Coverage**: 5 tests covering:
- RFC 3164 parsing
- RFC 5424 parsing
- Priority handling
- Malformed input
- Edge cases

### LLM Provider Tests (`test_llm_provider.py`)

Tests provider abstraction:

```python
class TestHuggingFaceProvider:
    """Test HuggingFace provider."""
    
    def test_initialization_with_valid_config(self):
        """Test initialization with valid config."""
        config = {
            "model_name": "google/gemma-3-4b-it",
            "device": "cpu",
        }
        provider = HuggingFaceProvider(config)
        assert provider.model_name == "google/gemma-3-4b-it"
```

**Coverage**: 22 tests covering:
- Provider initialization
- Configuration validation
- Factory pattern
- Default values
- Error handling

### Model Manager Tests (`test_model_manager.py`)

Tests model lifecycle:

```python
class TestModelManager:
    """Test ModelManager class."""
    
    def test_load_model_creates_provider(self):
        """Test loading model creates provider."""
        manager = ModelManager()
        manager.load_model()
        assert manager.is_loaded()
```

**Coverage**: 20 tests covering:
- Model loading/unloading
- Provider configuration
- Response generation
- Error handling
- Resource cleanup

### Analyzer Tests (`test_analyzers.py`)

Tests analysis and detection:

```python
class TestPatternDetector:
    """Test pattern detector."""
    
    def test_detect_brute_force_attack(self):
        """Test brute force detection."""
        detector = PatternDetector()
        logs = [...]  # Multiple failed auth attempts
        anomalies = detector.detect_brute_force(logs)
        assert len(anomalies) > 0
```

**Coverage**: 15 tests covering:
- Statistical analysis
- Pattern detection
- Brute force detection
- Time-based patterns
- Edge cases

### Enterprise Tests (`tests/enterprise/`)

Tests for enterprise features:

```python
class TestAlertManager:
    """Test alert manager."""
    
    def test_process_anomaly_triggers_alert(self):
        """Test anomaly triggers alert."""
        manager = AlertManager()
        manager.add_rule(create_high_score_rule(threshold=0.8))
        anomaly = create_test_anomaly(score=0.9)
        alerts = manager.process_anomaly(anomaly)
        assert len(alerts) > 0
```

**Coverage**: 31 tests covering:
- Real-time streaming functionality
- Multi-channel alerting
- Windows Event Log parsing
- Batch processing
- LRU caching
- Report generation

## Writing Tests

### Test Template

```python
"""
Tests for new_module.

Description of what's being tested.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from loggem.module import ClassName


class TestClassName:
    """Test ClassName functionality."""
    
    def test_basic_functionality(self):
        """Test basic use case."""
        obj = ClassName()
        result = obj.method()
        assert result == expected
    
    def test_edge_case(self):
        """Test edge case handling."""
        obj = ClassName()
        with pytest.raises(ValueError):
            obj.method(invalid_input)
    
    @patch('loggem.module.dependency')
    def test_with_mock(self, mock_dep):
        """Test with mocked dependency."""
        mock_dep.return_value = "mocked"
        obj = ClassName()
        result = obj.method()
        assert result == "expected"
```

### Test Best Practices

Here are the testing practices I follow:

1. **Descriptive Names**: Use clear, descriptive test names
   ```python
   # Good
   def test_parse_rfc3164_with_priority(self):
   
   # Bad
   def test_parse(self):
   ```

2. **One Assertion Per Test**: Focus on one behavior
   ```python
   # Good
   def test_default_provider(self):
       config = ModelConfig()
       assert config.provider == "huggingface"
   
   def test_default_model_name(self):
       config = ModelConfig()
       assert config.name == "google/gemma-3-4b-it"
   
   # Bad
   def test_defaults(self):
       config = ModelConfig()
       assert config.provider == "huggingface"
       assert config.name == "google/gemma-3-4b-it"
       assert config.device == "auto"
   ```

3. **Use Fixtures**: Share setup code
   ```python
   @pytest.fixture
   def sample_logs():
       """Create sample log entries."""
       return [
           LogEntry(timestamp=datetime.now(), message="test1", ...),
           LogEntry(timestamp=datetime.now(), message="test2", ...),
       ]
   
   def test_analyze(sample_logs):
       analyzer = LogAnalyzer()
       result = analyzer.analyze(sample_logs)
       assert result.total_entries == 2
   ```

4. **Mock External Dependencies**: Don't call real APIs
   ```python
   @patch('loggem.detector.llm_provider.OpenAI')
   def test_openai_provider(self, mock_openai):
       mock_openai.return_value.chat.completions.create.return_value = Mock()
       provider = OpenAIProvider({"api_key": "test"})
       # ... test without real API call
   ```

5. **Test Error Cases**: Don't just test happy path
   ```python
   def test_invalid_config_raises_error(self):
       with pytest.raises(ValueError, match="Invalid provider"):
           ModelConfig(provider="invalid")
   ```

## CI/CD Integration

### GitHub Actions Workflow

Location: `.github/workflows/ci.yml`

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov=loggem
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Configuration in `.pre-commit-config.yaml`:
- Black (formatting)
- Ruff (linting)
- Mypy (type checking)
- Bandit (security)

## Contributing Tests

### Adding New Tests

I'd love your help adding more tests! Here's how:

1. **Identify untested code**:
   ```bash
   pytest tests/ --cov=loggem --cov-report=term-missing
   ```

2. **Create test file** (if needed):
   ```bash
   touch tests/test_new_module.py
   ```

3. **Write tests** following templates above

4. **Run tests**:
   ```bash
   pytest tests/test_new_module.py -v
   ```

5. **Check coverage**:
   ```bash
   pytest tests/ --cov=loggem.new_module
   ```

### Priority Areas for Testing

Based on current coverage, these are the areas where I could use help:

1. **CLI** (0% coverage) - Priority: HIGH
   - Command-line interface
   - Argument parsing
   - Output formatting
   - Error handling

2. **Parsers** (16-32% coverage) - Priority: HIGH
   - Auth log parser
   - JSON parser
   - Nginx parser
   - Edge cases and malformed input

3. **Anomaly Detector** (19% coverage) - Priority: MEDIUM
   - AI-based detection
   - Batch processing
   - Error handling

4. **Logging** (58% coverage) - Priority: MEDIUM
   - Log setup
   - Audit logging
   - Error logging

## Troubleshooting

### Tests Fail Locally

```bash
# Clean cache
pytest --cache-clear

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# Check Python version
python --version  # Should be 3.9+
```

### Coverage Reports Not Generated

```bash
# Install coverage tools
pip install pytest-cov coverage

# Run with explicit coverage
pytest tests/ --cov=loggem --cov-report=html --cov-report=term
```

### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
```

### Mock Failures

```python
# Use proper patch path (where it's used, not defined)
# Bad
@patch('openai.OpenAI')

# Good
@patch('loggem.detector.llm_provider.OpenAI')
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Test Status**: 142 passing, 3 skipped, 0 failing  
**Coverage**: 56% overall (90%+ on core modules)
