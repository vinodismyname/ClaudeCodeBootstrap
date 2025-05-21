"""
Dynamic document generator module for creating documentation files.
"""

import logging

from typing import Dict, Any, Optional

from cc_bootstrap.config import CLAUDE_MD_PATH, ACTION_PLAN_PATH
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.llm_interface import LLMInterface


class DocGenerator:
    """Generator for documentation files based on project context."""

    def __init__(
        self,
        llm: LLMInterface,
        fs_utils: FileSystemUtils,
        context: Dict[str, Any],
        output_path: Optional[str] = None,
    ):
        """
        Initialize the document generator.

        Args:
            llm: LLM interface for generating content
            fs_utils: File system utilities for file operations
            context: Project context
            output_path: Optional custom output path for plan template
        """
        self.logger = logging.getLogger(__name__)
        self.llm = llm
        self.fs_utils = fs_utils
        self.context = context
        self.output_path = output_path

    def generate_claude_md(self) -> str:
        """
        Generate the CLAUDE.md file based on raw project context.

        Following the LLM-led inference strategy, this method passes raw context
        (user_plan_content and project_file_samples) to the LLM, which is responsible
        for inferring project characteristics and generating appropriate content.

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        if (
            self.fs_utils.file_exists(CLAUDE_MD_PATH)
            and not self.fs_utils.force_overwrite
        ):
            self.logger.info(
                f"{CLAUDE_MD_PATH} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        try:
            llm_context = {
                "user_plan_content": self.context.get("user_plan_content", ""),
                "project_file_samples": self.context.get("project_file_samples", {}),
                "use_claude_squad": self.context.get("use_claude_squad", False),
                "research_results": self.context.get("research_results", {}),
                "fetched_smithery_mcp_configs": self.context.get(
                    "fetched_smithery_mcp_configs", {}
                ),
                "formatted_research_insights": self.context.get(
                    "formatted_research_insights", ""
                ),
            }

            self.logger.info(f"Generating {CLAUDE_MD_PATH} content...")
            prompt_template = "prompts/claude_md.j2"

            content = self.llm.generate_content(prompt_template, llm_context)

            if content.startswith("ERROR:"):
                self.logger.error(f"Error generating {CLAUDE_MD_PATH}: {content}")
                return content

            success = self.fs_utils.write_file(CLAUDE_MD_PATH, content)
            if success:
                self.logger.info(f"Successfully generated {CLAUDE_MD_PATH}")
                return "Success"
            else:
                self.logger.error(f"Failed to write {CLAUDE_MD_PATH}")
                return f"Failed to write {CLAUDE_MD_PATH}"

        except Exception as e:
            self.logger.exception(f"Error generating {CLAUDE_MD_PATH}: {e}")
            return f"Error: {str(e)}"

    def generate_action_plan(self) -> str:
        """
        Generate an action plan document based on raw project context.

        This method conditionally selects the appropriate template based on whether
        Claude Squad is enabled, generating either a sequential plan for a single
        Claude instance or a parallel plan for multiple Claude instances.

        Returns:
            Status string ("Success", "Skipped", or error message)
        """
        output_path = self.output_path or ACTION_PLAN_PATH

        if self.fs_utils.file_exists(output_path) and not self.fs_utils.force_overwrite:
            self.logger.info(
                f"{output_path} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        try:
            llm_context = {
                "user_plan_content": self.context.get("user_plan_content", ""),
                "project_file_samples": self.context.get("project_file_samples", {}),
                "research_results": self.context.get("research_results", {}),
                "formatted_research_insights": self.context.get(
                    "formatted_research_insights", ""
                ),
                "task_description": self.context.get("task_description", ""),
                "feature_name": self.context.get("feature_name", ""),
                "fetched_smithery_mcp_configs": self.context.get(
                    "fetched_smithery_mcp_configs", {}
                ),
            }

            use_claude_squad = self.context.get("use_claude_squad", False)

            if use_claude_squad:
                self.logger.info(
                    "Claude Squad is enabled, using squad action plan template."
                )
                prompt_template = "prompts/action_plan_squad.j2"
            else:
                self.logger.info(
                    "Claude Squad is not enabled, using single action plan template."
                )
                prompt_template = "prompts/action_plan_single.j2"

            self.logger.info(f"Generating {output_path} content...")
            content = self.llm.generate_content(prompt_template, llm_context)

            if content.startswith("ERROR:"):
                self.logger.error(f"Error generating {output_path}: {content}")
                return content

            success = self.fs_utils.write_file(output_path, content)
            if success:
                self.logger.info(f"Successfully generated {output_path}")
                return "Success"
            else:
                self.logger.error(f"Failed to write {output_path}")
                return f"Failed to write {output_path}"

        except Exception as e:
            self.logger.exception(f"Error generating {output_path}: {e}")
            return f"Error: {str(e)}"
