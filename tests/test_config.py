"""
Comprehensive test suite for LogGem core configuration.

Tests configuration loading, validation, and provider settings.
"""

import os
import tempfile
from pathlib import Path

import pytest

from loggem.core.config import (
    AlertingConfig,
    DetectionConfig,
    LoggingConfig,
    ModelConfig,
    SecurityConfig,
    Settings,
    get_settings,
    reset_settings,
)


class TestModelConfig:
    """Test ModelConfig validation and defaults."""

    def test_default_provider(self):
        """Test default provider is huggingface."""
        config = ModelConfig()
        assert config.provider == "huggingface"

    def test_default_model_name(self):
        """Test default model is Gemma 3 2B."""
        config = ModelConfig()
        assert config.name == "google/gemma-3-4b-it"

    def test_default_device(self):
        """Test default device is auto."""
        config = ModelConfig()
        assert config.device == "auto"

    def test_default_quantization(self):
        """Test default quantization is int8."""
        config = ModelConfig()
        assert config.quantization == "int8"

    def test_default_max_length(self):
        """Test default max_length is 2048."""
        config = ModelConfig()
        assert config.max_length == 2048

    def test_custom_provider(self):
        """Test setting custom provider."""
        config = ModelConfig(provider="openai")
        assert config.provider == "openai"

    def test_custom_model_name(self):
        """Test setting custom model name."""
        config = ModelConfig(name="gpt-4o-mini")
        assert config.name == "gpt-4o-mini"

    def test_invalid_provider(self):
        """Test invalid provider raises validation error."""
        with pytest.raises(Exception):
            ModelConfig(provider="invalid")

    def test_invalid_device(self):
        """Test invalid device raises validation error."""
        with pytest.raises(Exception):
            ModelConfig(device="invalid")

    def test_max_length_validation(self):
        """Test max_length bounds validation."""
        # Too small
        with pytest.raises(Exception):
            ModelConfig(max_length=50)

        # Too large
        with pytest.raises(Exception):
            ModelConfig(max_length=10000)

        # Valid
        config = ModelConfig(max_length=1024)
        assert config.max_length == 1024


class TestDetectionConfig:
    """Test DetectionConfig validation and defaults."""

    def test_default_sensitivity(self):
        """Test default sensitivity is 0.75."""
        config = DetectionConfig()
        assert config.sensitivity == 0.75

    def test_default_batch_size(self):
        """Test default batch_size is 32."""
        config = DetectionConfig()
        assert config.batch_size == 32

    def test_default_context_window(self):
        """Test default context_window is 100."""
        config = DetectionConfig()
        assert config.context_window == 100

    def test_default_min_confidence(self):
        """Test default min_confidence is 0.6."""
        config = DetectionConfig()
        assert config.min_confidence == 0.6

    def test_sensitivity_bounds(self):
        """Test sensitivity validation bounds."""
        # Too low
        with pytest.raises(Exception):
            DetectionConfig(sensitivity=-0.1)

        # Too high
        with pytest.raises(Exception):
            DetectionConfig(sensitivity=1.5)

        # Valid bounds
        config = DetectionConfig(sensitivity=0.0)
        assert config.sensitivity == 0.0

        config = DetectionConfig(sensitivity=1.0)
        assert config.sensitivity == 1.0

    def test_batch_size_validation(self):
        """Test batch_size validation."""
        # Too small
        with pytest.raises(Exception):
            DetectionConfig(batch_size=0)

        # Too large
        with pytest.raises(Exception):
            DetectionConfig(batch_size=1000)

        # Valid
        config = DetectionConfig(batch_size=16)
        assert config.batch_size == 16


class TestAlertingConfig:
    """Test AlertingConfig validation and defaults."""

    def test_default_enabled(self):
        """Test default enabled is True."""
        config = AlertingConfig()
        assert config.enabled is True

    def test_default_severity_threshold(self):
        """Test default severity_threshold is medium."""
        config = AlertingConfig()
        assert config.severity_threshold == "medium"

    def test_default_max_alerts(self):
        """Test default max_alerts_per_hour is 100."""
        config = AlertingConfig()
        assert config.max_alerts_per_hour == 100

    def test_custom_severity_threshold(self):
        """Test setting custom severity threshold."""
        config = AlertingConfig(severity_threshold="high")
        assert config.severity_threshold == "high"

    def test_invalid_severity_threshold(self):
        """Test invalid severity threshold raises error."""
        with pytest.raises(Exception):
            AlertingConfig(severity_threshold="invalid")


class TestLoggingConfig:
    """Test LoggingConfig validation and defaults."""

    def test_default_level(self):
        """Test default level is INFO."""
        config = LoggingConfig()
        assert config.level == "INFO"

    def test_default_file(self):
        """Test default log file path."""
        config = LoggingConfig()
        assert config.file == Path("./logs/loggem.log")

    def test_default_rotation(self):
        """Test default rotation is 100 MB."""
        config = LoggingConfig()
        assert config.rotation == "100 MB"

    def test_default_retention(self):
        """Test default retention is 7 days."""
        config = LoggingConfig()
        assert config.retention == 7

    def test_custom_level(self):
        """Test setting custom log level."""
        config = LoggingConfig(level="DEBUG")
        assert config.level == "DEBUG"

    def test_invalid_level(self):
        """Test invalid log level raises error."""
        with pytest.raises(Exception):
            LoggingConfig(level="INVALID")


class TestSecurityConfig:
    """Test SecurityConfig validation and defaults."""

    def test_default_max_file_size(self):
        """Test default max_file_size is 1GB."""
        config = SecurityConfig()
        assert config.max_file_size == 1024 * 1024 * 1024

    def test_default_max_line_length(self):
        """Test default max_line_length is 10000."""
        config = SecurityConfig()
        assert config.max_line_length == 10000

    def test_default_enable_audit_log(self):
        """Test default enable_audit_log is True."""
        config = SecurityConfig()
        assert config.enable_audit_log is True

    def test_default_sanitize_input(self):
        """Test default sanitize_input is True."""
        config = SecurityConfig()
        assert config.sanitize_input is True

    def test_custom_max_file_size(self):
        """Test setting custom max_file_size."""
        config = SecurityConfig(max_file_size=1024 * 1024)  # 1MB
        assert config.max_file_size == 1024 * 1024


class TestSettings:
    """Test Settings integration and loading."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()

    def teardown_method(self):
        """Reset settings after each test."""
        reset_settings()

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        assert settings.model.provider == "huggingface"
        assert settings.model.name == "google/gemma-3-4b-it"
        assert settings.detection.sensitivity == 0.75
        assert settings.alerting.enabled is True
        assert settings.logging.level == "INFO"
        assert settings.security.enable_audit_log is True

    def test_settings_from_dict(self):
        """Test creating settings from dictionary."""
        data = {
            "model": {
                "provider": "openai",
                "name": "gpt-4o-mini",
            },
            "detection": {
                "sensitivity": 0.9,
            },
        }
        settings = Settings(**data)
        assert settings.model.provider == "openai"
        assert settings.model.name == "gpt-4o-mini"
        assert settings.detection.sensitivity == 0.9

    def test_settings_from_yaml(self):
        """Test loading settings from YAML file."""
        yaml_content = """
model:
  provider: anthropic
  name: claude-3-haiku-20240307

detection:
  sensitivity: 0.8
  batch_size: 16
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = Path(f.name)

        try:
            settings = Settings.from_yaml(yaml_path)
            assert settings.model.provider == "anthropic"
            assert settings.model.name == "claude-3-haiku-20240307"
            assert settings.detection.sensitivity == 0.8
            assert settings.detection.batch_size == 16
        finally:
            yaml_path.unlink()

    def test_settings_from_nonexistent_yaml(self):
        """Test loading from nonexistent file returns defaults."""
        settings = Settings.from_yaml(Path("/nonexistent/file.yaml"))
        assert settings.model.provider == "huggingface"

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_reset_settings(self):
        """Test reset_settings clears singleton."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        assert settings1 is not settings2

    def test_environment_variables(self):
        """Test environment variable override."""
        os.environ["LOGGEM_MODEL__PROVIDER"] = "openai"
        os.environ["LOGGEM_MODEL__NAME"] = "gpt-4o"

        try:
            reset_settings()
            settings = get_settings()
            assert settings.model.provider == "openai"
            assert settings.model.name == "gpt-4o"
        finally:
            os.environ.pop("LOGGEM_MODEL__PROVIDER", None)
            os.environ.pop("LOGGEM_MODEL__NAME", None)
            reset_settings()

    def test_directory_creation(self):
        """Test that data directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            temp_dir = Path(tmpdir) / "temp"

            Settings(
                data_dir=data_dir,
                temp_dir=temp_dir,
            )

            assert data_dir.exists()
            assert temp_dir.exists()

    def test_max_workers_validation(self):
        """Test max_workers validation."""
        # Too small
        with pytest.raises(Exception):
            Settings(max_workers=0)

        # Too large
        with pytest.raises(Exception):
            Settings(max_workers=100)

        # Valid
        settings = Settings(max_workers=8)
        assert settings.max_workers == 8
