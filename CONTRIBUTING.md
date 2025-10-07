# Contributing to LogGem

Thank you for your interest in contributing to LogGem! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/loggem.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
5. Install development dependencies: `pip install -e ".[dev]"`
6. Create a feature branch: `git checkout -b feature/amazing-feature`

## Development Workflow

### Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting (100 character line length)
- **Ruff**: Linting and code analysis
- **mypy**: Type checking

Run before committing:
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Testing

LogGem has 142 passing tests with 56% code coverage. Write tests for all contributions:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=loggem --cov-report=html

# Run specific test file
pytest tests/test_parsers.py -v

# Run specific test
pytest tests/test_parsers.py::TestSyslogParser::test_parse_rfc3164_basic -v
```

**Test Guidelines:**
- Write unit tests for individual functions/classes
- Write integration tests for component interactions
- Aim for >80% coverage on contributions
- Use pytest fixtures for common setup
- Mock external dependencies (LLM providers, API calls)
- Test both success and error cases

**Test Organization:**
- `tests/test_config.py` - Configuration and settings
- `tests/test_models.py` - Data models and validation
- `tests/test_parsers.py` - Log format parsers
- `tests/test_llm_provider.py` - LLM provider implementations
- `tests/test_model_manager.py` - Model lifecycle management
- `tests/test_analyzers.py` - Analysis and pattern detection

### Pre-commit Hooks

Install pre-commit hooks to automatically check code before commits:

```bash
pre-commit install
```

## What to Contribute

### Good First Issues

Look for issues labeled `good first issue` for beginner-friendly tasks:

- Log format parsers
- Improving documentation
- Writing tests
- Fixing bugs

### Priority Areas

- **Parsers**: Apache, IIS, cloud service logs
- **Pattern Detectors**: More rule-based detection patterns
- **Performance**: Optimization for large log files
- **Documentation**: Examples, tutorials, use cases
- **Testing**: Increase test coverage

## Pull Request Process

1. **Update Documentation**: Add/update docstrings, README, and docs
2. **Add Tests**: Cover new functionality
3. **Update CHANGELOG**: Add entry describing your changes
4. **Run Tests**: Make sure all tests pass
5. **Commit Messages**: Use clear, descriptive commit messages
   - Format: `type(scope): description`
   - Example: `feat(parsers): add Apache log parser`
   - Types: feat, fix, docs, test, refactor, perf, chore

6. **Create Pull Request**:
   - Provide a clear description
   - Reference any related issues
   - Explain the motivation and context

7. **Code Review**: Respond to feedback and make requested changes

## Code Guidelines

### Python Style

- Follow PEP 8 (enforced by Black and Ruff)
- Use type hints for all function signatures
- Write docstrings for all public functions/classes (Google style)
- Keep functions focused and small
- Prefer composition over inheritance

### Security

- Validate all input data
- Sanitize user-provided strings
- Never execute arbitrary code
- Use secure defaults
- Document security considerations

### Performance

- Profile before optimizing
- Use generators for large datasets
- Cache expensive operations
- Minimize memory usage
- Document performance characteristics

## Adding Parsers

To add a log format parser:

1. Create `src/loggem/parsers/your_format.py`
2. Inherit from `BaseParser`
3. Implement `parse_line()` method
4. Add to `LogParserFactory` in `factory.py`
5. Write tests in `tests/test_your_format.py`
6. Update documentation

Example:
```python
from loggem.parsers.base import BaseParser
from loggem.core.models import LogEntry

class YourFormatParser(BaseParser):
    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        # Parse the line
        # Return LogEntry or None
        pass
```

## Adding Detection Patterns

To add rule-based detection patterns:

1. Add method to `PatternDetector` class
2. Follow naming convention: `detect_[pattern_name]`
3. Return list of `Anomaly` objects
4. Write tests
5. Update documentation

## Documentation

- Use Google-style docstrings
- Include examples in docstrings
- Update README.md for user-facing changes
- Add inline comments for complex logic

## Questions?

- Open an issue for questions
- Join discussions on GitHub
- Check existing issues and PRs

## Code of Conduct

Be respectful and professional. We're all here to make LogGem better!

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LogGem! 🙏
