# Makefile for LogGem development

.PHONY: help install install-dev test test-cov lint format clean run-example docs

help:
	@echo "LogGem Development Commands:"
	@echo "  make install       - Install LogGem in development mode"
	@echo "  make install-dev   - Install with development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters (ruff, mypy)"
	@echo "  make format        - Format code with black"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make run-example   - Run example analysis"
	@echo "  make quickstart    - Run quick start setup"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest

test-cov:
	pytest --cov=loggem --cov-report=html --cov-report=term-missing

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/ examples/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-example:
	python examples/basic_usage.py

quickstart:
	python quickstart.py

# Development workflow
dev: install-dev format lint test

# CI/CD simulation
ci: format lint test-cov
