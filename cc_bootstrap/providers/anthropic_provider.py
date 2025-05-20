"""
Anthropic provider module for interacting with Anthropic's Claude API.
"""

import logging
from typing import Optional

import anthropic
from anthropic import Anthropic

from cc_bootstrap.providers.base_provider import LLMProvider


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic's Claude API."""

    def __init__(
        self, model: str, api_key: Optional[str] = None, dry_run: bool = False
    ):
        """
        Initialize the Anthropic provider.

        Args:
            model: The LLM model identifier to use.
            api_key: Anthropic API key. If None, will try to load from environment.
            dry_run: If True, will simulate API calls instead of making them.
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.api_key = api_key
        self.dry_run = dry_run
        self.client = None

    def initialize(self) -> None:
        """Initialize the Anthropic client."""
        if not self.dry_run:
            try:
                self.client = Anthropic(
                    api_key=self.api_key,
                    timeout=60000.0,
                )
                self.logger.debug(
                    f"Initialized Anthropic client with model: {self.model}"
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic client: {e}")
                raise

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
        Generate content using the Anthropic API.

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
        if self.dry_run:
            self.logger.info(
                f"DRY RUN: Would send prompt to Anthropic API with model {self.model}"
            )
            return f"[Dry run response for Anthropic API with model {self.model}]"

        try:
            self.logger.debug(
                f"Sending prompt to Anthropic API with model {self.model}, max_tokens: {max_tokens}"
            )

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            }

            extra_headers = None
            if enable_thinking:
                kwargs["temperature"] = 1.0
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                }

                extra_headers = {"anthropic-beta": "output-128k-2025-02-19"}
                self.logger.debug(
                    f"Anthropic thinking enabled with budget: {thinking_budget}, temp: {kwargs['temperature']}, extra_headers: {extra_headers}"
                )

            response = self.client.messages.create(
                **kwargs, extra_headers=extra_headers
            )

            content = ""
            if response.content and isinstance(response.content, list):
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text

            if not content:
                self.logger.warning(
                    f"No text content found in Anthropic response. Full response: {response}"
                )

            self.logger.debug("Received response from Anthropic API")
            return content

        except anthropic.RateLimitError:
            self.logger.error("API rate limit exceeded. Please try again later.")
            return "ERROR: API rate limit exceeded. Please try again later."
        except anthropic.APIError as e:
            self.logger.error(f"API error: {e}")
            return f"ERROR: API error occurred: {e}"
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            return f"ERROR: Failed to generate content: {e}"

    def get_model_id(self) -> str:
        """Get the model ID."""
        return self.model
