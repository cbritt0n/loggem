"""
Model manager for loading and managing AI models.

Supports multiple LLM providers: HuggingFace, OpenAI, Anthropic, Ollama, and custom providers.
"""

from __future__ import annotations

from typing import Any

from loggem.core.config import get_settings
from loggem.core.logging import get_audit_logger, get_logger
from loggem.detector.llm_provider import LLMProvider, create_provider

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class ModelManager:
    """
    Manages AI model lifecycle: loading, caching, and inference.

    Supports multiple LLM providers with a unified interface.
    """

    def __init__(
        self,
        provider_type: str | None = None,
        provider_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize model manager.

        Args:
            provider_type: LLM provider type (huggingface, openai, anthropic, ollama)
            provider_config: Provider-specific configuration (overrides settings)
        """
        self.settings = get_settings()

        # Determine provider type
        self.provider_type = provider_type or self.settings.model.provider

        # Build provider config from settings
        if provider_config is None:
            provider_config = self._build_provider_config()

        self.provider_config = provider_config

        # Create provider instance
        self.provider: LLMProvider | None = None

        logger.info(
            "model_manager_initialized",
            provider=self.provider_type,
            config=self._sanitize_config(provider_config),
        )

    def _build_provider_config(self) -> dict[str, Any]:
        """Build provider configuration from settings."""
        config: dict[str, Any] = {
            "model_name": self.settings.model.name,
            "max_length": self.settings.model.max_length,
        }

        if self.provider_type == "huggingface":
            config.update(
                {
                    "device": self.settings.model.device,
                    "cache_dir": str(self.settings.model.cache_dir),
                    "quantization": self.settings.model.quantization,
                    "trust_remote_code": self.settings.model.trust_remote_code,
                }
            )
        elif self.provider_type in ("openai", "anthropic"):
            config.update(
                {
                    "api_key": self.settings.model.api_key,
                    "model": self.settings.model.name,
                }
            )
            if self.settings.model.base_url:
                config["base_url"] = self.settings.model.base_url
            if self.provider_type == "openai" and self.settings.model.organization:
                config["organization"] = self.settings.model.organization
        elif self.provider_type == "ollama":
            config.update(
                {
                    "model": self.settings.model.name,
                    "base_url": self.settings.model.base_url or "http://localhost:11434",
                }
            )

        return config

    def _sanitize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Sanitize config for logging (remove sensitive data)."""
        sanitized = config.copy()
        if "api_key" in sanitized:
            sanitized["api_key"] = "***"
        return sanitized

    def load_model(self) -> None:
        """
        Initialize the LLM provider.

        Raises:
            RuntimeError: If provider initialization fails
        """
        if self.provider is not None and self.provider.is_initialized:
            logger.info("provider_already_initialized")
            return

        logger.info("initializing_provider", provider=self.provider_type)

        try:
            # Create and initialize provider
            self.provider = create_provider(self.provider_type, self.provider_config)
            self.provider.initialize()

            logger.info("provider_initialized_successfully")
            audit_logger.log_model_load(
                self.provider_config.get("model_name")
                or self.provider_config.get("model", "unknown"),
                self.provider_type,
            )

        except Exception as e:
            logger.error("provider_initialization_failed", error=str(e))
            raise RuntimeError(f"Failed to initialize {self.provider_type} provider: {e}") from e

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        if self.provider is not None:
            self.provider.cleanup()
            self.provider = None

        logger.info("provider_unloaded")

    def generate_response(
        self,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (higher = more random)
            top_p: Nucleus sampling parameter

        Returns:
            Generated text response

        Raises:
            RuntimeError: If provider is not initialized
        """
        if self.provider is None or not self.provider.is_initialized:
            raise RuntimeError("Provider not initialized. Call load_model() first.")

        if max_tokens is None:
            max_tokens = 512

        logger.debug("generating_response", prompt_length=len(prompt))

        try:
            response = self.provider.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )

            logger.debug("response_generated", response_length=len(response))
            return response

        except Exception as e:
            logger.error("generation_failed", error=str(e))
            raise RuntimeError(f"Failed to generate response: {e}") from e

    def is_loaded(self) -> bool:
        """Check if provider is initialized."""
        return self.provider is not None and self.provider.is_initialized

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the provider and model."""
        if self.provider is None:
            return {
                "provider": self.provider_type,
                "initialized": False,
            }

        return self.provider.get_info()
