"""
Dynamic config generator module for creating configuration files.
"""

import json
import logging
import os
from typing import Dict, Any

from cc_bootstrap.config import MCP_JSON_PATH, CLAUDE_DIR_PATH, SETTINGS_JSON_PATH
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.llm_interface import LLMInterface


class ConfigGenerator:
    """Generator for configuration files based on project context."""

    def __init__(
        self, llm: LLMInterface, fs_utils: FileSystemUtils, context: Dict[str, Any]
    ):
        """
        Initialize the config generator.

        Args:
            llm: LLM interface for generating content
            fs_utils: File system utilities for file operations
            context: Project context
        """
        self.logger = logging.getLogger(__name__)
        self.llm = llm
        self.fs_utils = fs_utils
        self.context = context

    def generate_mcp_config(self) -> str:
        """
        Generate the .mcp.json file based on raw project context.

        Following the LLM-led inference strategy, this method passes raw context
        (user_plan_content and project_file_samples) to the LLM, which is responsible
        for inferring project characteristics and suggesting appropriate MCP tools.

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        if (
            self.fs_utils.file_exists(MCP_JSON_PATH)
            and not self.fs_utils.force_overwrite
        ):
            self.logger.info(
                f"{MCP_JSON_PATH} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        user_mcp_tools = self.context.get("user_mcp_tools_input", [])

        if not user_mcp_tools:
            user_mcp_tools = [{"name": "web_search"}, {"name": "github"}]
            self.logger.info("No user-specified MCP tools found, using defaults.")
        else:
            self.logger.info(f"Using user-specified MCP tools: {user_mcp_tools}")

        try:
            self.logger.info("Using LLM to suggest and configure MCP tools...")

            llm_context = {
                "user_plan_content": self.context.get("user_plan_content", ""),
                "project_file_samples": self.context.get("project_file_samples", {}),
                "user_mcp_tools_input": user_mcp_tools,
                "research_results": self.context.get("research_results", {}),
            }

            prompt_template = "prompts/mcp_config.j2"
            content = self.llm.generate_content(prompt_template, llm_context)

            if content.startswith("ERROR:"):
                self.logger.error(f"Error generating MCP tool configs: {content}")
                return content

            try:
                tool_configs = json.loads(content)

                mcp_config = {"servers": tool_configs}

                success = self.fs_utils.write_file(
                    MCP_JSON_PATH, json.dumps(mcp_config, indent=2)
                )
                if success:
                    self.logger.info(f"Successfully generated {MCP_JSON_PATH}")
                    return "Success"
                else:
                    self.logger.error(f"Failed to write {MCP_JSON_PATH}")
                    return f"Failed to write {MCP_JSON_PATH}"

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse MCP tool configs: {e}")
                return f"Error parsing MCP tool configs: {e}"

        except Exception as e:
            self.logger.exception(f"Error generating {MCP_JSON_PATH}: {e}")
            return f"Error: {str(e)}"

    def generate_settings(self) -> str:
        """
        Generate the .claude/settings.json file.

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        if (
            self.fs_utils.file_exists(SETTINGS_JSON_PATH)
            and not self.fs_utils.force_overwrite
        ):
            self.logger.info(
                f"{SETTINGS_JSON_PATH} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        try:
            if not self.fs_utils.ensure_directory(CLAUDE_DIR_PATH):
                return f"Failed to create directory {CLAUDE_DIR_PATH}"

            template_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "templates",
                "defaults",
                "settings.json",
            )

            if os.path.exists(template_path):
                with open(template_path, "r") as f:
                    settings_content = f.read()
            else:
                self.logger.warning(
                    f"Default settings template not found at {template_path}, using hardcoded defaults."
                )
                default_settings = {
                    "theme": "dark",
                    "allowedTools": ["Read", "LS", "Grep"],
                    "autoApproveTools": ["Read", "LS", "Grep"],
                    "defaultAllowedBranches": ["main"],
                    "showPrompt": False,
                    "telemetry": {"disabled": False},
                }
                settings_content = json.dumps(default_settings, indent=2)

            try:
                settings_data = json.loads(settings_content)
            except json.JSONDecodeError:
                self.logger.error(
                    "Failed to parse default settings content. Using hardcoded base."
                )
                settings_data = {
                    "theme": "dark",
                    "allowedTools": ["Read", "LS", "Grep"],
                    "autoApproveTools": ["Read", "LS", "Grep"],
                    "defaultAllowedBranches": ["main"],
                    "showPrompt": False,
                    "telemetry": {"disabled": False},
                }

            if "allowedTools" not in settings_data or not isinstance(
                settings_data["allowedTools"], list
            ):
                settings_data["allowedTools"] = [
                    "Read",
                    "LS",
                    "Grep",
                ]

            mcp_config_content = self.fs_utils.read_file(MCP_JSON_PATH)
            if mcp_config_content:
                try:
                    mcp_data = json.loads(mcp_config_content)
                    if (
                        mcp_data
                        and "servers" in mcp_data
                        and isinstance(mcp_data["servers"], dict)
                    ):
                        for server_key in mcp_data["servers"].keys():
                            permission_string = f"mcp__{server_key}__*"
                            if permission_string not in settings_data["allowedTools"]:
                                settings_data["allowedTools"].append(permission_string)
                                self.logger.info(
                                    f"Added MCP tool permission: {permission_string}"
                                )
                except json.JSONDecodeError:
                    self.logger.warning(
                        f"Could not parse {MCP_JSON_PATH} to update allowedTools in settings.json."
                    )

            settings_content = json.dumps(settings_data, indent=2)

            success = self.fs_utils.write_file(SETTINGS_JSON_PATH, settings_content)
            if success:
                self.logger.info(f"Successfully generated {SETTINGS_JSON_PATH}")
                return "Success"
            else:
                self.logger.error(f"Failed to write {SETTINGS_JSON_PATH}")
                return f"Failed to write {SETTINGS_JSON_PATH}"

        except Exception as e:
            self.logger.exception(f"Error generating {SETTINGS_JSON_PATH}: {e}")
            return f"Error: {str(e)}"
