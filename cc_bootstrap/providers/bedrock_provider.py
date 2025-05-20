"""
Bedrock provider module for interacting with AWS Bedrock.
"""

import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from cc_bootstrap.providers.base_provider import LLMProvider


class BedrockProvider(LLMProvider):
    """Provider for AWS Bedrock."""

    def __init__(
        self,
        model: str,
        region: Optional[str] = None,
        profile: Optional[str] = None,
        dry_run: bool = False,
    ):
        """
        Initialize the Bedrock provider.

        Args:
            model: The LLM model identifier to use (e.g., anthropic.claude-3-7-sonnet-20250219-v1:0).
            region: AWS region for Bedrock. If None, will use default.
            profile: AWS profile for Bedrock. If None, will use default.
            dry_run: If True, will simulate API calls instead of making them.
        """
        self.logger = logging.getLogger(__name__)
        self.model = model
        self.region = region
        self.profile = profile
        self.dry_run = dry_run
        self.client = None

    def initialize(self) -> None:
        """Initialize the Bedrock client."""
        if not self.dry_run:
            try:
                session_args = {}
                if self.profile:
                    session_args["profile_name"] = self.profile
                if self.region:
                    session_args["region_name"] = self.region

                session = boto3.Session(**session_args)
                config = Config(read_timeout=3600)
                client_args = {}
                client_args["config"] = config
                if self.region:
                    client_args["region_name"] = self.region

                self.client = session.client("bedrock-runtime", **client_args)
                self.logger.debug(
                    f"Initialized Bedrock client with model: {self.model} in region: {self.client.meta.region_name}"
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize Bedrock client: {e}")
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
        Generate content using AWS Bedrock for Anthropic Claude 3.7 Sonnet (Messages API).

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
                f"DRY RUN: Would send prompt to AWS Bedrock with model {self.model}"
            )
            return f"[Dry run response for AWS Bedrock with model {self.model}]"

        try:
            self.logger.debug(
                f"Sending prompt to AWS Bedrock with model {self.model}, max_tokens: {max_tokens}"
            )

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
            }

            if enable_thinking and thinking_budget > 0:
                request_body["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                }
                request_body["temperature"] = 1.0

                self.logger.debug(
                    f"Bedrock thinking enabled with budget: {thinking_budget}, temp: {request_body['temperature']}"
                )
            else:
                request_body["temperature"] = temperature

            response = self.client.invoke_model(
                modelId=self.model,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))

            text_content = ""

            if "content" in response_body and isinstance(
                response_body["content"], list
            ):
                for block in response_body["content"]:
                    if block.get("type") == "text":
                        text_content = block.get("text", "")
                        break
                if not text_content:
                    self.logger.warning(
                        f"No 'text' content block found in Bedrock response. Full response: {response_body}"
                    )
            elif "completion" in response_body:
                self.logger.warning(
                    f"Bedrock response has 'completion' field, expected 'content' array for model {self.model}. Using 'completion'."
                )
                text_content = response_body["completion"]
            else:
                self.logger.error(
                    f"Unexpected Bedrock response format. 'content' array not found. Full response: {response_body}"
                )

            self.logger.debug("Received response from AWS Bedrock")
            return text_content

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error(f"AWS Bedrock error ({error_code}): {error_message}")

            self.logger.debug(f"Full Bedrock error response: {e.response}")
            return f"ERROR: AWS Bedrock error ({error_code}): {error_message}"
        except Exception as e:
            self.logger.error(f"Error generating content with Bedrock: {e}")
            import traceback

            self.logger.debug(traceback.format_exc())
            return f"ERROR: Failed to generate content with Bedrock: {e}"

    def get_model_id(self) -> str:
        """Get the model ID."""
        return self.model
