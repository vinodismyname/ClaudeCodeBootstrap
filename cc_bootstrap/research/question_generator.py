"""
Question generator module for generating research questions.

This module uses an LLM to generate specific research questions based on
raw project context (user plan content and file samples).
"""

import logging
import json
from typing import Dict, List, Any
from cc_bootstrap.llm_interface import LLMInterface


class QuestionGenerator:
    """Generates research questions using an LLM based on project context."""

    def __init__(self, context: Dict[str, Any], llm_interface: LLMInterface):
        """
        Initialize the question generator.

        Args:
            context: Raw project context containing user_plan_content and project_file_samples
            llm_interface: LLM interface for generating research questions
        """
        self.logger = logging.getLogger(__name__)
        self.context = context
        self.llm_interface = llm_interface

    def generate_questions(self) -> List[str]:
        """
        Generate research questions using an LLM.

        Returns:
            List of question strings.
        """
        self.logger.debug(
            "Generating research questions using LLM based on project context"
        )

        llm_context = {
            "user_plan_content": self.context.get("user_plan_content", ""),
            "project_file_samples": self.context.get("project_file_samples", {}),
        }

        prompt_template = "prompts/generate_research_questions.j2"

        try:
            raw_response = self.llm_interface.generate_content(
                prompt_template, llm_context
            )

            if raw_response.startswith("ERROR:"):
                self.logger.error(
                    f"LLM failed to generate research questions: {raw_response}"
                )
                return []

            if raw_response.strip().startswith("```json"):
                raw_response = raw_response.strip()[7:]
                if raw_response.strip().endswith("```"):
                    raw_response = raw_response.strip()[:-3]

            question_strings = json.loads(raw_response.strip())

            if not isinstance(question_strings, list) or not all(
                isinstance(q, str) for q in question_strings
            ):
                self.logger.error(
                    f"LLM response for research questions was not a valid JSON list of strings: {raw_response}"
                )
                return []

            self.logger.info(
                f"LLM generated {len(question_strings)} research questions."
            )
            return question_strings

        except json.JSONDecodeError:
            self.logger.error(
                f"Failed to parse LLM response for research questions as JSON: {raw_response}"
            )
            return []
        except Exception as e:
            self.logger.error(
                f"An unexpected error occurred during LLM question generation: {e}"
            )
            import traceback

            self.logger.debug(traceback.format_exc())
            return []
