"""
Base provider module for LLM providers.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider client."""
        pass

    @abstractmethod
    def generate_content(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 8000,
        temperature: float = 0.3,
        enable_thinking: bool = False,
        thinking_budget: int = 0,
    ) -> str:
        """
        Generate content using the LLM provider.

        Args:
            prompt: The prompt to send to the LLM.
            system_prompt: The system prompt to use.
            max_tokens: Maximum number of tokens to generate.
            temperature: Temperature for generation.
            enable_thinking: Whether to enable extended thinking/reasoning.
            thinking_budget: Token budget for thinking (if enabled).

        Returns:
            Generated content as a string.
        """
        pass

    @abstractmethod
    def get_model_id(self) -> str:
        """Get the model ID for this provider."""
        pass
