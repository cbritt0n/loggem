"""
LLM Provider abstraction layer.

Supports multiple LLM backends including HuggingFace, OpenAI, Anthropic, and custom providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loggem.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the LLM provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.is_initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider (load model, connect to API, etc.)."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources (unload model, close connections, etc.)."""
        pass

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Get information about the provider and model."""
        pass


class HuggingFaceProvider(LLMProvider):
    """HuggingFace Transformers provider for local models."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize HuggingFace provider.

        Config keys:
            - model_name: HuggingFace model name (required)
            - device: Device to run on (auto, cpu, cuda, mps)
            - quantization: Quantization level (int8, fp16, fp32)
            - cache_dir: Directory to cache models
            - trust_remote_code: Whether to trust remote code (default: False)
        """
        super().__init__(config)
        self.model_name = config.get("model_name")
        if not self.model_name:
            raise ValueError("model_name is required for HuggingFace provider")

        self.device = config.get("device", "auto")
        self.quantization = config.get("quantization", "int8")
        self.cache_dir = config.get("cache_dir", "./models")
        self.trust_remote_code = config.get("trust_remote_code", False)

        self.model: Any | None = None
        self.tokenizer: Any | None = None

    def initialize(self) -> None:
        """Load the HuggingFace model and tokenizer."""
        if self.is_initialized:
            logger.info("huggingface_provider_already_initialized")
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        logger.info(
            "initializing_huggingface_provider",
            model=self.model_name,
            device=self.device,
        )

        # Determine device
        if self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            trust_remote_code=self.trust_remote_code,
        )

        # Configure model loading
        model_kwargs = {
            "cache_dir": self.cache_dir,
            "trust_remote_code": self.trust_remote_code,
            "low_cpu_mem_usage": True,
        }

        # Apply quantization
        if self.quantization == "int8" and self.device in ("cuda", "auto"):
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0,
            )
            model_kwargs["quantization_config"] = quantization_config
            model_kwargs["device_map"] = "auto"
        elif self.quantization == "fp16":
            model_kwargs["torch_dtype"] = torch.float16
            if self.device != "cpu":
                model_kwargs["device_map"] = "auto"
        else:  # fp32
            model_kwargs["torch_dtype"] = torch.float32

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **model_kwargs,
        )

        # Move to device if not using device_map
        if "device_map" not in model_kwargs:
            self.model = self.model.to(self.device)

        self.model.eval()
        self.is_initialized = True
        logger.info("huggingface_provider_initialized")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """Generate response using HuggingFace model."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        import torch

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.get("max_length", 2048),
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                **kwargs,
            )

        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Remove prompt from response
        if response.startswith(prompt):
            response = response[len(prompt) :].strip()

        return response

    def cleanup(self) -> None:
        """Cleanup HuggingFace resources."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None

        # Clear CUDA cache
        if self.device == "cuda":
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        self.is_initialized = False
        logger.info("huggingface_provider_cleaned_up")

    def get_info(self) -> dict[str, Any]:
        """Get HuggingFace provider info."""
        info = {
            "provider": "huggingface",
            "model_name": self.model_name,
            "device": self.device,
            "quantization": self.quantization,
            "initialized": self.is_initialized,
        }

        if self.is_initialized and self.model is not None:
            param_count = sum(p.numel() for p in self.model.parameters())
            info["parameters"] = param_count

        return info


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize OpenAI provider.

        Config keys:
            - api_key: OpenAI API key (required, or set OPENAI_API_KEY env var)
            - model: Model name (default: gpt-4o-mini)
            - base_url: Custom API base URL (optional)
            - organization: Organization ID (optional)
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-4o-mini")
        self.base_url = config.get("base_url")
        self.organization = config.get("organization")
        self.client: Any | None = None

    def initialize(self) -> None:
        """Initialize OpenAI client."""
        if self.is_initialized:
            return

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI provider requires 'openai' package. Install with: pip install openai"
            )

        logger.info("initializing_openai_provider", model=self.model)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            organization=self.organization,
        )
        self.is_initialized = True
        logger.info("openai_provider_initialized")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """Generate response using OpenAI API."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

        return response.choices[0].message.content or ""

    def cleanup(self) -> None:
        """Cleanup OpenAI resources."""
        self.client = None
        self.is_initialized = False
        logger.info("openai_provider_cleaned_up")

    def get_info(self) -> dict[str, Any]:
        """Get OpenAI provider info."""
        return {
            "provider": "openai",
            "model": self.model,
            "initialized": self.is_initialized,
        }


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize Anthropic provider.

        Config keys:
            - api_key: Anthropic API key (required, or set ANTHROPIC_API_KEY env var)
            - model: Model name (default: claude-3-haiku-20240307)
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "claude-3-haiku-20240307")
        self.client: Any | None = None

    def initialize(self) -> None:
        """Initialize Anthropic client."""
        if self.is_initialized:
            return

        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic provider requires 'anthropic' package. "
                "Install with: pip install anthropic"
            )

        logger.info("initializing_anthropic_provider", model=self.model)

        self.client = Anthropic(api_key=self.api_key)
        self.is_initialized = True
        logger.info("anthropic_provider_initialized")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """Generate response using Anthropic API."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

        return response.content[0].text

    def cleanup(self) -> None:
        """Cleanup Anthropic resources."""
        self.client = None
        self.is_initialized = False
        logger.info("anthropic_provider_cleaned_up")

    def get_info(self) -> dict[str, Any]:
        """Get Anthropic provider info."""
        return {
            "provider": "anthropic",
            "model": self.model,
            "initialized": self.is_initialized,
        }


class OllamaProvider(LLMProvider):
    """Ollama local API provider."""

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize Ollama provider.

        Config keys:
            - model: Model name (required, e.g., "llama3", "mistral")
            - base_url: Ollama API URL (default: http://localhost:11434)
        """
        super().__init__(config)
        self.model = config.get("model")
        if not self.model:
            raise ValueError("model is required for Ollama provider")

        self.base_url = config.get("base_url", "http://localhost:11434")
        self.client: Any | None = None

    def initialize(self) -> None:
        """Initialize Ollama client."""
        if self.is_initialized:
            return

        try:
            import requests
        except ImportError:
            raise ImportError(
                "Ollama provider requires 'requests' package. Install with: pip install requests"
            )

        logger.info(
            "initializing_ollama_provider",
            model=self.model,
            base_url=self.base_url,
        )

        # Test connection
        import requests

        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Ollama at {self.base_url}: {e}")

        self.is_initialized = True
        logger.info("ollama_provider_initialized")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        **kwargs: Any,
    ) -> str:
        """Generate response using Ollama API."""
        if not self.is_initialized:
            raise RuntimeError("Provider not initialized. Call initialize() first.")

        import requests

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()

        return response.json()["response"]

    def cleanup(self) -> None:
        """Cleanup Ollama resources."""
        self.is_initialized = False
        logger.info("ollama_provider_cleaned_up")

    def get_info(self) -> dict[str, Any]:
        """Get Ollama provider info."""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "initialized": self.is_initialized,
        }


# Provider registry
PROVIDERS = {
    "huggingface": HuggingFaceProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def create_provider(provider_type: str, config: dict[str, Any]) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider_type: Type of provider (huggingface, openai, anthropic, ollama)
        config: Provider-specific configuration

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider_type is not recognized
    """
    if provider_type not in PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_type}. Available providers: {', '.join(PROVIDERS.keys())}"
        )

    provider_class = PROVIDERS[provider_type]
    return provider_class(config)
