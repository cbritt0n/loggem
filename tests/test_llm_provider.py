"""
Test suite for LLM Provider abstraction and implementations.

Note: Initialization tests are skipped because they require mocking dynamic imports.
Integration tests should test actual provider initialization.
"""

import pytest
from unittest.mock import Mock, patch

from loggem.detector.llm_provider import (
    LLMProvider,
    HuggingFaceProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    create_provider,
    PROVIDERS,
)


class TestLLMProviderBase:
    """Test LLMProvider base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider({})


class TestHuggingFaceProvider:
    """Test HuggingFaceProvider implementation."""

    def test_initialization_requires_model_name(self):
        """Test that model_name is required."""
        with pytest.raises(ValueError):
            HuggingFaceProvider({})

    def test_initialization_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "model_name": "google/gemma-3-4b-it",
            "device": "cpu",
            "quantization": "int8",
        }
        provider = HuggingFaceProvider(config)
        
        assert provider.model_name == "google/gemma-3-4b-it"
        assert provider.device == "cpu"
        assert provider.quantization == "int8"
        assert provider.is_initialized is False

    def test_default_values(self):
        """Test default configuration values."""
        config = {"model_name": "test-model"}
        provider = HuggingFaceProvider(config)
        
        assert provider.device == "auto"
        assert provider.quantization == "int8"
        assert provider.cache_dir == "./models"
        assert provider.trust_remote_code is False

    def test_get_info_not_initialized(self):
        """Test get_info when not initialized."""
        config = {"model_name": "test-model"}
        provider = HuggingFaceProvider(config)
        
        info = provider.get_info()
        assert info["provider"] == "huggingface"
        assert info["model_name"] == "test-model"
        assert info["initialized"] is False


class TestOpenAIProvider:
    """Test OpenAIProvider implementation."""

    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        config = {
            "api_key": "test-key",
            "model": "gpt-4o-mini",
        }
        provider = OpenAIProvider(config)
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o-mini"
        assert provider.is_initialized is False

    def test_default_model(self):
        """Test default model is gpt-4o-mini."""
        config = {}
        provider = OpenAIProvider(config)
        assert provider.model == "gpt-4o-mini"

    def test_get_info(self):
        """Test get_info method."""
        config = {"model": "gpt-4o"}
        provider = OpenAIProvider(config)
        
        info = provider.get_info()
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4o"
        assert info["initialized"] is False


class TestAnthropicProvider:
    """Test AnthropicProvider implementation."""

    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        config = {
            "api_key": "test-key",
            "model": "claude-3-5-sonnet-20241022",
        }
        provider = AnthropicProvider(config)
        
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-5-sonnet-20241022"
        assert provider.is_initialized is False

    def test_default_model(self):
        """Test default model."""
        config = {}
        provider = AnthropicProvider(config)
        assert provider.model == "claude-3-haiku-20240307"

    def test_get_info(self):
        """Test get_info method."""
        config = {"model": "claude-3-opus-20240229"}
        provider = AnthropicProvider(config)
        
        info = provider.get_info()
        assert info["provider"] == "anthropic"
        assert info["model"] == "claude-3-opus-20240229"
        assert info["initialized"] is False


class TestOllamaProvider:
    """Test OllamaProvider implementation."""

    def test_initialization_requires_model(self):
        """Test that model_name is required."""
        with pytest.raises(ValueError):
            OllamaProvider({})

    def test_initialization_with_config(self):
        """Test initialization with configuration."""
        config = {
            "model": "llama2",
            "base_url": "http://custom:11434",
        }
        provider = OllamaProvider(config)
        
        assert provider.model == "llama2"
        assert provider.base_url == "http://custom:11434"
        assert provider.is_initialized is False

    def test_default_base_url(self):
        """Test default base URL."""
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        assert provider.base_url == "http://localhost:11434"

    def test_get_info(self):
        """Test get_info method."""
        config = {"model": "llama2"}
        provider = OllamaProvider(config)
        
        info = provider.get_info()
        assert info["provider"] == "ollama"
        assert info["model"] == "llama2"
        assert info["initialized"] is False


class TestProviderFactory:
    """Test provider factory functions."""

    def test_provider_registry_contains_all_providers(self):
        """Test that PROVIDERS registry contains all provider types."""
        assert "huggingface" in PROVIDERS
        assert "openai" in PROVIDERS
        assert "anthropic" in PROVIDERS
        assert "ollama" in PROVIDERS

    def test_create_huggingface_provider(self):
        """Test creating HuggingFace provider via factory."""
        config = {"provider": "huggingface", "model_name": "test-model"}
        provider = create_provider(config["provider"], config)
        
        assert isinstance(provider, HuggingFaceProvider)
        assert provider.model_name == "test-model"

    def test_create_openai_provider(self):
        """Test creating OpenAI provider via factory."""
        config = {"provider": "openai", "api_key": "test-key"}
        provider = create_provider(config["provider"], config)
        
        assert isinstance(provider, OpenAIProvider)

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider via factory."""
        config = {"provider": "anthropic", "api_key": "test-key"}
        provider = create_provider(config["provider"], config)
        
        assert isinstance(provider, AnthropicProvider)

    def test_create_ollama_provider(self):
        """Test creating Ollama provider via factory."""
        config = {"provider": "ollama", "model": "llama2"}
        provider = create_provider(config["provider"], config)
        
        assert isinstance(provider, OllamaProvider)

    def test_create_provider_invalid_type(self):
        """Test that invalid provider type raises ValueError."""
        config = {"provider": "invalid"}
        
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider("invalid", config)

    def test_provider_registry_keys(self):
        """Test that provider registry has expected keys."""
        expected_providers = {"huggingface", "openai", "anthropic", "ollama"}
        assert set(PROVIDERS.keys()) == expected_providers
