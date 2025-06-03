"""
LLM Interface module for interacting with LLM APIs.

This module handles all communication with LLM APIs, including
prompt construction, response parsing, and error handling.
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader

from cc_bootstrap.config import (
    ENV_ANTHROPIC_API_KEY,
    ENV_AWS_REGION,
    ENV_AWS_PROFILE,
    LLM_PROVIDERS,
    MAX_TOKENS_THINKING_ENABLED,
    MAX_TOKENS_THINKING_DISABLED,
    DEFAULT_LLM_MODEL as GENERIC_DEFAULT_LLM_MODEL,
)
from cc_bootstrap.providers.provider_factory import LLMProviderFactory


class LLMInterface:
    """Interface for interacting with LLM APIs."""

    def __init__(
        self,
        model: str,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_profile: Optional[str] = None,
        dry_run: bool = False,
        enable_thinking: bool = False,
        thinking_budget: int = 0,
        verbose: bool = False,
        project_path: Optional[str] = None,
    ):
        """
        Initialize the LLM interface.

        Args:
            model: The LLM model identifier to use. Can be a generic placeholder.
            provider: The LLM provider to use (anthropic or bedrock).
            api_key: Anthropic API key. If None, will try to load from environment.
            aws_region: AWS region for Bedrock. If None, will try to load from environment.
            aws_profile: AWS profile for Bedrock. If None, will use default profile.
            dry_run: If True, will simulate API calls instead of making them.
            enable_thinking: If True, will enable extended thinking/reasoning.
            thinking_budget: Token budget for thinking (if enabled).
            verbose: If True, will save prompts to markdown files.
            project_path: Path to the project directory (used for saving prompts).
        """
        self.logger = logging.getLogger(__name__)
        self.provider_type = provider
        self.dry_run = dry_run
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
        self.verbose = verbose
        self.project_path = project_path or os.getcwd()
        self.prompt_counter = 0
        self.prompt_session_dir = None
        
        if self.verbose:
            self._setup_prompt_directory()

        if (
            model == GENERIC_DEFAULT_LLM_MODEL
            or not model
            or provider not in LLM_PROVIDERS
        ):
            self.model = LLM_PROVIDERS[self.provider_type]["default_model"]
            self.logger.info(
                f"Using default model for {self.provider_type}: {self.model}"
            )
        elif self.provider_type == "bedrock" and not model.startswith("anthropic."):
            self.model = LLM_PROVIDERS[self.provider_type]["default_model"]
            self.logger.warning(
                f"Provided model '{model}' for Bedrock does not look like a fully qualified ID. Using default: {self.model}"
            )
        else:
            self.model = model

        self.logger.info(
            f"LLMInterface initialized with provider: {self.provider_type}, model: {self.model}"
        )

        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.template_env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )

        provider_kwargs = {}

        if provider == "anthropic":
            provider_kwargs["api_key"] = api_key or os.environ.get(
                ENV_ANTHROPIC_API_KEY
            )

            if not provider_kwargs["api_key"] and not dry_run:
                self.logger.error(
                    f"Anthropic API key not found. Set {ENV_ANTHROPIC_API_KEY} environment variable or use --api-key."
                )
                sys.exit(1)

        elif provider == "bedrock":
            provider_kwargs["region"] = (
                aws_region
                or os.environ.get(ENV_AWS_REGION)
                or LLM_PROVIDERS["bedrock"]["default_region"]
            )

            provider_kwargs["profile"] = aws_profile or os.environ.get(ENV_AWS_PROFILE)

        else:
            self.logger.error(f"Unknown provider: {provider}")
            sys.exit(1)

        provider_kwargs["dry_run"] = dry_run

        try:
            self.provider = LLMProviderFactory.create_provider(
                provider, self.model, **provider_kwargs
            )
            self.logger.debug(
                f"Initialized {provider} provider with model: {self.model}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize {provider} provider: {e}")
            sys.exit(1)

    def _setup_prompt_directory(self):
        """Create directory for saving prompts in verbose mode."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.prompt_session_dir = os.path.join(
            self.project_path, 
            ".cc-bootstrap-prompts", 
            timestamp
        )
        os.makedirs(self.prompt_session_dir, exist_ok=True)
        self.logger.debug(f"Created prompt directory: {self.prompt_session_dir}")

    def _save_prompt_to_file(self, prompt_template: str, prompt: str, 
                            system_prompt: str, context: Dict):
        """Save prompt to markdown file in verbose mode."""
        if not self.verbose or not self.prompt_session_dir:
            return
        
        self.prompt_counter += 1
        template_name = os.path.basename(prompt_template).replace('.j2', '')
        filename = f"{self.prompt_counter:03d}_{template_name}.md"
        filepath = os.path.join(self.prompt_session_dir, filename)
        
        # Create markdown content
        content = f"""# LLM Prompt: {template_name}

Generated at: {datetime.now().isoformat()}
Template: {prompt_template}
Model: {self.model}
Provider: {self.provider_type}

## System Prompt

{system_prompt}

## User Prompt

{prompt}

## Context Keys

{json.dumps(list(context.keys()), indent=2)}
"""
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        self.logger.debug(f"Saved prompt to: {filepath}")
        
        # Also save metadata file
        metadata_path = os.path.join(self.prompt_session_dir, "metadata.json")
        metadata = {
            "session_start": self.prompt_session_dir.split('/')[-1],
            "project_path": self.project_path,
            "model": self.model,
            "provider": self.provider_type,
            "total_prompts": self.prompt_counter,
            "enable_thinking": self.enable_thinking,
            "thinking_budget": self.thinking_budget
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _render_template(self, template_path: str, context: Dict) -> str:
        """
        Render a template with the given context.

        Args:
            template_path: Path to the template file, relative to templates directory.
            context: Dictionary of variables to render in the template.

        Returns:
            Rendered template as a string.
        """
        try:
            template = self.template_env.get_template(template_path)
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"Error rendering template {template_path}: {e}")
            raise

    def generate_content(self, prompt_template: str, context: Dict) -> str:
        """
        Generate content using the LLM API with a prompt template and context.

        Args:
            prompt_template: Path to the prompt template file.
            context: Dictionary of variables to render in the template.

        Returns:
            Generated content as a string.
        """

        prompt = self._render_template(prompt_template, context)

        prompt_length = len(prompt)
        self.logger.debug(f"Prompt length (characters): {prompt_length}")

        if prompt_length > 75000 * 3:
            self.logger.warning(
                f"Prompt is very long ({prompt_length} chars). Consider reducing input size."
            )

        # Define system prompt early so it can be saved in verbose mode
        system_prompt = "You are an expert software developer tasked with creating configuration files for Anthropic's Claude Code. Claude Code is an AI coding assistant that runs in the terminal. Generate professional, well-structured, and comprehensive content for the requested configuration file."

        # Display the prompt in verbose mode
        self.logger.debug("=" * 50)
        self.logger.debug("=== PROMPT TEMPLATE ===")
        self.logger.debug(f"{prompt_template}")
        self.logger.debug("=== RENDERED PROMPT ===")
        self.logger.debug(f"{prompt}")
        self.logger.debug("=== SYSTEM PROMPT ===")
        self.logger.debug(f"{system_prompt}")
        
        # Save prompt to file if in verbose mode (even in dry run)
        self._save_prompt_to_file(prompt_template, prompt, system_prompt, context)

        if self.dry_run:
            self.logger.info("DRY RUN: Would send the following prompt to LLM API:")
            self.logger.info(f"Template: {prompt_template}")
            self.logger.info(f"Context keys: {list(context.keys())}")
            self.logger.info(f"Estimated prompt size: {prompt_length} characters")

            return f"[This is a placeholder response for dry run. Would generate content based on {prompt_template}]"

        try:
            self.logger.debug(
                f"Sending prompt to {self.model} via {self.provider_type}..."
            )

            if self.enable_thinking:
                max_tokens_to_use = MAX_TOKENS_THINKING_ENABLED
            else:
                max_tokens_to_use = MAX_TOKENS_THINKING_DISABLED

            self.logger.debug(
                f"Using max_tokens: {max_tokens_to_use} (thinking_enabled: {self.enable_thinking})"
            )

            content = self.provider.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens_to_use,
                temperature=0.3,
                enable_thinking=self.enable_thinking,
                thinking_budget=self.thinking_budget,
            )

            self.logger.debug("Received response from LLM API")
            self.logger.debug("=" * 50)
            return content

        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            return f"ERROR: Failed to generate content: {e}"
