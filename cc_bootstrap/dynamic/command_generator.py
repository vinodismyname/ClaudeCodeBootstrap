"""
Dynamic command generator module for creating custom commands.
"""

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

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        try:
            if not self.fs_utils.ensure_directory(COMMANDS_DIR_PATH):
                return f"Failed to create directory {COMMANDS_DIR_PATH}"

            commands_generated = 0
            commands_skipped = 0
            errors = []

            for category, commands in COMMAND_CATEGORIES.items():
                category_dir = f"{COMMANDS_DIR_PATH}/{category}"
                if not self.fs_utils.ensure_directory(category_dir):
                    errors.append(f"Failed to create directory {category_dir}")
                    continue

                for command_name, command_info in commands["commands"].items():
                    file_path = f"{category_dir}/{command_name}.md"

                    if (
                        self.fs_utils.file_exists(file_path)
                        and not self.fs_utils.force_overwrite
                    ):
                        self.logger.info(f"{file_path} already exists, skipping.")
                        commands_skipped += 1
                        continue

                    llm_context = {
                        "command_name": command_name,
                        "command_description": command_info.get("description", ""),
                        "category": category,
                        "category_description": commands.get("description", ""),
                        "user_plan_content": self.context.get("user_plan_content", ""),
                        "project_file_samples": self.context.get(
                            "project_file_samples", {}
                        ),
                        "research_results": self.context.get("research_results", {}),
                        "mcp_tools": self.context.get("user_mcp_tools_input", []),
                    }

                    prompt_template = "prompts/custom_command.j2"
                    content = self.llm.generate_content(prompt_template, llm_context)

                    if content.startswith("ERROR:"):
                        self.logger.error(f"Error generating {file_path}: {content}")
                        errors.append(f"Error generating {file_path}: {content}")
                        continue

                    success = self.fs_utils.write_file(file_path, content)
                    if success:
                        self.logger.info(f"Successfully generated {file_path}")
                        commands_generated += 1
                    else:
                        self.logger.error(f"Failed to write {file_path}")
                        errors.append(f"Failed to write {file_path}")

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
