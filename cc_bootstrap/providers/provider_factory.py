"""
Provider factory module for creating LLM providers.
"""

from typing import Dict, Type

from cc_bootstrap.providers.base_provider import LLMProvider
from cc_bootstrap.providers.anthropic_provider import AnthropicProvider
from cc_bootstrap.providers.bedrock_provider import BedrockProvider


class LLMProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create_provider(provider_type: str, model: str, **kwargs) -> LLMProvider:
        """
        Create a provider instance based on type.

        Args:
            provider_type: The type of provider to create (anthropic or bedrock).
            model: The LLM model identifier to use.
            **kwargs: Additional arguments to pass to the provider constructor.

        Returns:
            An initialized LLM provider.

        Raises:
            ValueError: If the provider type is unknown.
        """
        providers: Dict[str, Type[LLMProvider]] = {
            "anthropic": AnthropicProvider,
            "bedrock": BedrockProvider,
        }

        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider_class = providers[provider_type]
        provider = provider_class(model, **kwargs)
        provider.initialize()
        return provider
