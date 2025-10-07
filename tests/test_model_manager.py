"""
Comprehensive test suite for ModelManager.

Tests model manager initialization and provider integration.
"""

from unittest.mock import Mock, patch

import pytest

from loggem.core.config import reset_settings
from loggem.detector.model_manager import ModelManager


class TestModelManager:
    """Test ModelManager class."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()

    def teardown_method(self):
        """Reset settings after each test."""
        reset_settings()

    def test_default_initialization(self):
        """Test initialization with default settings."""
        manager = ModelManager()

        assert manager.provider_type == "huggingface"
        assert manager.provider is None

    def test_initialization_with_custom_provider(self):
        """Test initialization with custom provider type."""
        manager = ModelManager(provider_type="openai")

        assert manager.provider_type == "openai"

    def test_initialization_with_custom_config(self):
        """Test initialization with custom provider config."""
        custom_config = {
            "model_name": "custom-model",
            "device": "cpu",
        }

        manager = ModelManager(provider_type="huggingface", provider_config=custom_config)

        assert manager.provider_config["model_name"] == "custom-model"

    def test_build_provider_config_huggingface(self):
        """Test building config for HuggingFace provider."""
        manager = ModelManager(provider_type="huggingface")
        config = manager._build_provider_config()

        assert "model_name" in config
        assert config["model_name"] == "google/gemma-3-4b-it"
        assert "device" in config
        assert "quantization" in config
        assert "cache_dir" in config

    def test_build_provider_config_openai(self):
        """Test building config for OpenAI provider."""
        manager = ModelManager(provider_type="openai")
        config = manager._build_provider_config()

        assert "model" in config
        assert "api_key" in config

    def test_build_provider_config_anthropic(self):
        """Test building config for Anthropic provider."""
        manager = ModelManager(provider_type="anthropic")
        config = manager._build_provider_config()

        assert "model" in config
        assert "api_key" in config

    def test_build_provider_config_ollama(self):
        """Test building config for Ollama provider."""
        manager = ModelManager(provider_type="ollama")
        config = manager._build_provider_config()

        assert "model" in config
        assert "base_url" in config

    def test_sanitize_config_removes_api_key(self):
        """Test that sanitize_config masks API keys."""
        manager = ModelManager()
        config = {
            "api_key": "sk-secret123456",
            "model": "gpt-4o-mini",
        }

        sanitized = manager._sanitize_config(config)

        assert sanitized["api_key"] == "***"
        assert sanitized["model"] == "gpt-4o-mini"

    @patch("loggem.detector.model_manager.create_provider")
    def test_load_model_creates_provider(self, mock_create_provider):
        """Test that load_model creates and initializes provider."""
        mock_provider = Mock()
        mock_provider.is_initialized = False
        mock_create_provider.return_value = mock_provider

        manager = ModelManager(provider_type="huggingface")
        manager.load_model()

        mock_create_provider.assert_called_once()
        mock_provider.initialize.assert_called_once()
        assert manager.provider == mock_provider

    @patch("loggem.detector.model_manager.create_provider")
    def test_load_model_already_loaded(self, mock_create_provider):
        """Test that load_model skips if already loaded."""
        mock_provider = Mock()
        mock_provider.is_initialized = True

        manager = ModelManager()
        manager.provider = mock_provider
        manager.load_model()

        # Should not create new provider
        mock_create_provider.assert_not_called()

    @patch("loggem.detector.model_manager.create_provider")
    def test_load_model_handles_errors(self, mock_create_provider):
        """Test that load_model handles initialization errors."""
        mock_create_provider.side_effect = Exception("Failed to load")

        manager = ModelManager()

        with pytest.raises(RuntimeError, match="Failed to initialize"):
            manager.load_model()

    def test_unload_model(self):
        """Test unloading model."""
        mock_provider = Mock()

        manager = ModelManager()
        manager.provider = mock_provider
        manager.unload_model()

        mock_provider.cleanup.assert_called_once()
        assert manager.provider is None

    def test_unload_model_when_none(self):
        """Test unloading when no provider is loaded."""
        manager = ModelManager()
        manager.provider = None

        # Should not raise error
        manager.unload_model()

    def test_generate_response_not_loaded(self):
        """Test generate_response raises error when not loaded."""
        manager = ModelManager()

        with pytest.raises(RuntimeError, match="Provider not initialized"):
            manager.generate_response("test prompt")

    def test_generate_response_success(self):
        """Test successful response generation."""
        mock_provider = Mock()
        mock_provider.is_initialized = True
        mock_provider.generate.return_value = "Generated response"

        manager = ModelManager()
        manager.provider = mock_provider

        response = manager.generate_response("test prompt")

        assert response == "Generated response"
        mock_provider.generate.assert_called_once()

    def test_generate_response_with_parameters(self):
        """Test response generation with custom parameters."""
        mock_provider = Mock()
        mock_provider.is_initialized = True
        mock_provider.generate.return_value = "Response"

        manager = ModelManager()
        manager.provider = mock_provider

        manager.generate_response(
            prompt="test",
            max_tokens=256,
            temperature=0.8,
            top_p=0.95,
        )

        mock_provider.generate.assert_called_once_with(
            prompt="test",
            max_tokens=256,
            temperature=0.8,
            top_p=0.95,
        )

    def test_generate_response_handles_errors(self):
        """Test generate_response handles provider errors."""
        mock_provider = Mock()
        mock_provider.is_initialized = True
        mock_provider.generate.side_effect = Exception("Generation failed")

        manager = ModelManager()
        manager.provider = mock_provider

        with pytest.raises(RuntimeError, match="Failed to generate response"):
            manager.generate_response("test")

    def test_is_loaded_true(self):
        """Test is_loaded returns True when provider is initialized."""
        mock_provider = Mock()
        mock_provider.is_initialized = True

        manager = ModelManager()
        manager.provider = mock_provider

        assert manager.is_loaded() is True

    def test_is_loaded_false_no_provider(self):
        """Test is_loaded returns False when no provider."""
        manager = ModelManager()
        manager.provider = None

        assert manager.is_loaded() is False

    def test_is_loaded_false_not_initialized(self):
        """Test is_loaded returns False when provider not initialized."""
        mock_provider = Mock()
        mock_provider.is_initialized = False

        manager = ModelManager()
        manager.provider = mock_provider

        assert manager.is_loaded() is False

    def test_get_model_info_no_provider(self):
        """Test get_model_info when no provider is loaded."""
        manager = ModelManager(provider_type="openai")

        info = manager.get_model_info()

        assert info["provider"] == "openai"
        assert info["initialized"] is False

    def test_get_model_info_with_provider(self):
        """Test get_model_info when provider is loaded."""
        mock_provider = Mock()
        mock_provider.get_info.return_value = {
            "provider": "huggingface",
            "model_name": "test-model",
            "initialized": True,
        }

        manager = ModelManager()
        manager.provider = mock_provider

        info = manager.get_model_info()

        assert info["provider"] == "huggingface"
        assert info["model_name"] == "test-model"
        assert info["initialized"] is True
