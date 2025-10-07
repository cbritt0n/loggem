"""
Configuration management for LogGem.

Handles loading configuration from files, environment variables, and defaults.
Uses Pydantic for validation and type safety.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelConfig(BaseSettings):
    """Configuration for the AI model."""

    # Provider type: huggingface, openai, anthropic, ollama
    provider: Literal["huggingface", "openai", "anthropic", "ollama"] = Field(
        default="huggingface",
        description="LLM provider type",
    )

    # HuggingFace provider settings
    name: str = Field(
        default="google/gemma-3-4b-it",
        description="Model name (provider-specific)",
    )
    device: Literal["auto", "cpu", "cuda", "mps"] = Field(
        default="auto",
        description="Device to run model on (HuggingFace only)",
    )
    cache_dir: Path = Field(
        default=Path("./models"),
        description="Directory to cache models (HuggingFace only)",
    )
    quantization: Literal["int8", "fp16", "fp32"] = Field(
        default="int8",
        description="Model quantization level (HuggingFace only)",
    )
    max_length: int = Field(
        default=2048,
        ge=128,
        le=8192,
        description="Maximum token length",
    )

    # API provider settings (OpenAI, Anthropic)
    api_key: str | None = Field(
        default=None,
        description="API key for cloud providers (OpenAI, Anthropic)",
    )
    base_url: str | None = Field(
        default=None,
        description="Base URL for API providers (OpenAI, Ollama)",
    )
    organization: str | None = Field(
        default=None,
        description="Organization ID (OpenAI only)",
    )

    # Advanced settings
    trust_remote_code: bool = Field(
        default=False,
        description="Whether to trust remote code in models (HuggingFace only)",
    )


class DetectionConfig(BaseSettings):
    """Configuration for anomaly detection."""

    sensitivity: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Detection sensitivity (0=permissive, 1=strict)",
    )
    batch_size: int = Field(
        default=32,
        ge=1,
        le=256,
        description="Batch size for processing",
    )
    context_window: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Number of log entries for context",
    )
    min_confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to report anomaly",
    )


class AlertingConfig(BaseSettings):
    """Configuration for alerting."""

    enabled: bool = Field(default=True, description="Enable alerting")
    severity_threshold: Literal["low", "medium", "high", "critical"] = Field(
        default="medium",
        description="Minimum severity to alert on",
    )
    max_alerts_per_hour: int = Field(
        default=100,
        ge=1,
        description="Maximum alerts per hour",
    )


class LoggingConfig(BaseSettings):
    """Configuration for application logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    file: Path | None = Field(
        default=Path("./logs/loggem.log"),
        description="Log file path",
    )
    rotation: str = Field(
        default="100 MB",
        description="Log rotation size",
    )
    retention: int = Field(
        default=7,
        ge=1,
        description="Days to retain logs",
    )


class SecurityConfig(BaseSettings):
    """Configuration for security features."""

    max_file_size: int = Field(
        default=1024 * 1024 * 1024,  # 1 GB
        ge=1024,
        description="Maximum log file size in bytes",
    )
    max_line_length: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum length of a single log line",
    )
    enable_audit_log: bool = Field(
        default=True,
        description="Enable audit logging",
    )
    sanitize_input: bool = Field(
        default=True,
        description="Sanitize all input data",
    )


class Settings(BaseSettings):
    """
    Main settings for LogGem.

    Loads configuration from:
    1. Environment variables (prefixed with LOGGEM_)
    2. config.yaml file (if exists)
    3. Default values
    """

    model_config = SettingsConfigDict(
        env_prefix="LOGGEM_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Nested configurations
    model: ModelConfig = Field(default_factory=ModelConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    alerting: AlertingConfig = Field(default_factory=AlertingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # General settings
    data_dir: Path = Field(
        default=Path("./loggem_data"),
        description="Directory for storing data",
    )
    temp_dir: Path = Field(
        default=Path("/tmp/loggem"),
        description="Temporary directory",
    )
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum worker threads",
    )

    @field_validator("data_dir", "temp_dir")
    @classmethod
    def create_directories(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> Settings:
        """Load settings from a YAML file."""
        import yaml

        if not path.exists():
            return cls()

        with open(path) as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


# Global settings instance
_settings: Settings | None = None


def get_settings(config_file: Path | None = None) -> Settings:
    """
    Get the global settings instance.

    Args:
        config_file: Optional path to configuration file

    Returns:
        Settings instance
    """
    global _settings

    if _settings is None:
        if config_file and config_file.exists():
            _settings = Settings.from_yaml(config_file)
        else:
            # Try default locations
            default_paths = [
                Path("config.yaml"),
                Path("config.yml"),
                Path.home() / ".loggem" / "config.yaml",
            ]
            for path in default_paths:
                if path.exists():
                    _settings = Settings.from_yaml(path)
                    break
            else:
                _settings = Settings()

    return _settings


def reset_settings() -> None:
    """Reset the global settings instance. Useful for testing."""
    global _settings
    _settings = None
