"""
Dynamic command generator module for creating custom commands.
"""

import json
import logging
from typing import Dict, Any

from cc_bootstrap.config import COMMAND_CATEGORIES, COMMANDS_DIR_PATH
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.llm_interface import LLMInterface


class CommandGenerator:
    """Generator for custom commands based on project context."""

    def __init__(
        self, llm: LLMInterface, fs_utils: FileSystemUtils, context: Dict[str, Any]
    ):
        """
        Initialize the command generator.

        Args:
            llm: LLM interface for generating content
            fs_utils: File system utilities for file operations
            context: Project context
        """
        self.logger = logging.getLogger(__name__)
        self.llm = llm
        self.fs_utils = fs_utils
        self.context = context

    def generate_commands(self) -> str:
        """
        Generate custom command files based on project context.

        Uses a single LLM call to generate all commands as a JSON object,
        then parses the JSON and writes each command to its respective file.

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        try:
            if not self.fs_utils.ensure_directory(COMMANDS_DIR_PATH):
                return f"Failed to create directory {COMMANDS_DIR_PATH}"

            commands_generated = 0
            commands_skipped = 0
            errors = []

            llm_context = {
                "command_definitions": COMMAND_CATEGORIES,
                "user_plan_content": self.context.get("user_plan_content", ""),
                "project_file_samples": self.context.get("project_file_samples", {}),
                "research_results": self.context.get("research_results", {}),
                "fetched_smithery_mcp_configs": self.context.get(
                    "fetched_smithery_mcp_configs", {}
                ),
            }

            self.logger.info("Generating all custom commands via a single LLM call...")
            prompt_template = "prompts/all_custom_commands.j2"
            raw_json_response = self.llm.generate_content(prompt_template, llm_context)

            if raw_json_response.startswith("ERROR:"):
                self.logger.error(
                    f"LLM failed to generate commands JSON: {raw_json_response}"
                )
                return f"LLM Error: {raw_json_response}"

            try:
                commands_json = json.loads(raw_json_response)
                self.logger.debug(
                    f"Successfully parsed JSON response with {len(commands_json)} categories"
                )
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                self.logger.debug(f"Raw response: {raw_json_response}")
                return f"Error: Failed to parse JSON response: {e}"

            for category in commands_json:
                if category not in COMMAND_CATEGORIES:
                    self.logger.warning(
                        f"Unknown category '{category}' in LLM response, skipping"
                    )
                    continue

                category_dir = f"{COMMANDS_DIR_PATH}/{category}"
                if not self.fs_utils.ensure_directory(category_dir):
                    errors.append(f"Failed to create directory {category_dir}")
                    continue

                for command_name, command_content in commands_json[category].items():
                    if command_name not in COMMAND_CATEGORIES[category]["commands"]:
                        self.logger.warning(
                            f"Unknown command '{command_name}' in category '{category}', skipping"
                        )
                        continue

                    file_path = f"{category_dir}/{command_name}.md"

                    if (
                        self.fs_utils.file_exists(file_path)
                        and not self.fs_utils.force_overwrite
                    ):
                        self.logger.info(f"{file_path} already exists, skipping.")
                        commands_skipped += 1
                        continue

                    success = self.fs_utils.write_file(file_path, command_content)
                    if success:
                        self.logger.info(f"Successfully generated {file_path}")
                        commands_generated += 1
                    else:
                        self.logger.error(f"Failed to write {file_path}")
                        errors.append(f"Failed to write {file_path}")

            for category, category_data in COMMAND_CATEGORIES.items():
                if category not in commands_json:
                    self.logger.warning(
                        f"Category '{category}' missing from LLM response"
                    )
                    continue

                for command_name in category_data["commands"]:
                    if command_name not in commands_json[category]:
                        self.logger.warning(
                            f"Command '{command_name}' in category '{category}' missing from LLM response"
                        )

            if errors:
                return f"Partial success ({commands_generated} generated, {commands_skipped} skipped, {len(errors)} errors)"
            elif commands_generated == 0 and commands_skipped > 0:
                return "Skipped (all files already exist)"
            elif commands_generated > 0:
                return f"Success ({commands_generated} generated, {commands_skipped} skipped)"
            else:
                return "No commands generated"

        except Exception as e:
            self.logger.exception(f"Error generating commands: {e}")
            return f"Error: {str(e)}"
