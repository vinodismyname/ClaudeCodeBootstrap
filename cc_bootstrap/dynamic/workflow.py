"""
Dynamic workflow orchestration module.
"""

import logging
from typing import Dict, List, Any, Optional

from cc_bootstrap.analyzers.context_builder import ContextBuilder
from cc_bootstrap.research.perplexity_client import PerplexityClient
from cc_bootstrap.research.question_generator import QuestionGenerator
from cc_bootstrap.dynamic.command_generator import CommandGenerator
from cc_bootstrap.dynamic.config_generator import ConfigGenerator
from cc_bootstrap.dynamic.doc_generator import DocGenerator
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.llm_interface import LLMInterface


class DynamicWorkflow:
    """Orchestrates the dynamic workflow for project configuration."""

    def __init__(
        self,
        project_path: str,
        llm: LLMInterface,
        fs_utils: FileSystemUtils,
        plan_file: Optional[str] = None,
        use_perplexity: bool = False,
        perplexity_api_key: Optional[str] = None,
        use_claude_squad: bool = False,
        smithery_server_names: Optional[List[str]] = None,
        smithery_api_key: Optional[str] = None,
    ):
        """
        Initialize the dynamic workflow.

        Args:
            project_path: Path to the project directory
            llm: LLM interface
            fs_utils: File system utilities
            plan_file: Path to the user's plan file (optional)
            use_perplexity: Whether to use Perplexity API for research
            perplexity_api_key: Perplexity API key (required if use_perplexity is True)
            use_claude_squad: Whether to generate Claude Squad assets
            smithery_server_names: List of Smithery qualified server names (optional)
            smithery_api_key: Smithery API key (required if smithery_server_names is provided)
        """
        self.logger = logging.getLogger(__name__)
        self.project_path = project_path
        self.llm = llm
        self.fs_utils = fs_utils
        self.plan_file = plan_file
        self.use_perplexity = use_perplexity
        self.perplexity_api_key = perplexity_api_key
        self.use_claude_squad = use_claude_squad
        self.smithery_server_names = smithery_server_names or []
        self.smithery_api_key = smithery_api_key

    def get_workflow_steps(self) -> List[str]:
        """
        Get a list of workflow steps based on the current configuration.

        Returns:
            List of step descriptions
        """

        steps = ["Building project context"]

        if self.smithery_server_names and self.smithery_api_key:
            steps.append("Fetching MCP server details from Smithery Registry")

        if self.use_perplexity and self.perplexity_api_key:
            steps.append("Performing research (Perplexity API)")

        steps.append("Generating CLAUDE.md")

        if not self.fs_utils.skip_commands:
            steps.append("Generating custom commands")
        else:
            steps.append("Skipping custom commands")

        if not self.fs_utils.skip_mcp_config:
            steps.append("Generating MCP config")
        else:
            steps.append("Skipping MCP config")

        steps.append("Generating settings.json")

        action_plan_type = (
            "Squad Action Plan" if self.use_claude_squad else "Action Plan"
        )
        steps.append(f"Generating {action_plan_type}")

        return steps

    def execute(self, progress=None, status_updater_callback=None) -> Dict[str, str]:
        """
        Execute the dynamic workflow.

        Args:
            progress: Optional progress bar for tracking execution steps
            status_updater_callback: Optional callback function for status updates
                with signature (step_description: str, status: str, current_step: int, total_steps: int)

        Returns:
            Dictionary containing results for each generated asset
        """
        self.logger.info("Executing dynamic workflow")

        steps = self.get_workflow_steps()
        total_steps = len(steps)
        current_step_num = 0

        def update_status(step_description: str, status: str):
            nonlocal current_step_num
            if status_updater_callback:
                status_updater_callback(
                    step_description=step_description,
                    status=status,
                    current_step=current_step_num + 1,
                    total_steps=total_steps,
                )
            if progress:
                progress.update(
                    task_id,
                    description=step_description,
                    advance=0 if status != "Completed" else 1,
                )

        if progress:
            task_id = progress.add_task("Initializing...", total=total_steps)

        step_desc = steps[current_step_num]
        update_status(step_desc, "Starting")
        self.logger.info(step_desc)
        context_builder = ContextBuilder(self.project_path, self.plan_file)
        context = context_builder.build_context()
        context["use_claude_squad"] = self.use_claude_squad
        update_status(step_desc, "Completed")
        current_step_num += 1

        # Fetch Smithery MCP server configurations if provided
        fetched_smithery_configs = {}
        if self.smithery_server_names and self.smithery_api_key:
            step_desc = steps[current_step_num]
            update_status(step_desc, "Starting")
            self.logger.info(f"{step_desc} for: {self.smithery_server_names}")
            try:
                from cc_bootstrap.smithery_client import (
                    get_all_mcp_server_configs,
                    parse_config_schema_for_basic_info,
                )

                # Get all server configs from Smithery
                raw_fetched_data = get_all_mcp_server_configs(
                    self.smithery_server_names, self.smithery_api_key
                )

                for q_name, server_details in raw_fetched_data.items():
                    if server_details:
                        # Check if this was a matched result from a search
                        if server_details.get("matched_from_query"):
                            original_query = server_details.get(
                                "original_query", q_name
                            )
                            matched_to = server_details.get("matched_to", "unknown")
                            self.logger.info(
                                f"Query '{original_query}' matched to server '{matched_to}'"
                            )

                        if server_details.get("config_schema") is not None:
                            # Parse the schema for easier use in prompts
                            parsed_schema = parse_config_schema_for_basic_info(
                                server_details["config_schema"]
                            )
                            fetched_smithery_configs[q_name] = {
                                **server_details,  # includes qualified_name, display_name, description, icon_url, config_schema, tools
                                "parsed_schema_info": parsed_schema,
                            }
                            self.logger.info(
                                f"Successfully fetched and parsed Smithery config for {q_name}"
                            )
                        else:
                            self.logger.warning(
                                f"No config_schema for Smithery server: {q_name}"
                            )
                            fetched_smithery_configs[q_name] = None
                    else:
                        self.logger.warning(
                            f"Failed to fetch Smithery server: {q_name}"
                        )
                        fetched_smithery_configs[q_name] = None

                context["fetched_smithery_mcp_configs"] = fetched_smithery_configs
                update_status(step_desc, "Completed")
            except ImportError:
                self.logger.error(
                    "Smithery client module not found. Skipping Smithery integration."
                )
                context["fetched_smithery_mcp_configs"] = {}
                update_status(step_desc, "Failed (ImportError)")
            except Exception as e:
                self.logger.error(f"Error fetching Smithery MCP configs: {e}")
                context["fetched_smithery_mcp_configs"] = {}  # Ensure key exists
                update_status(step_desc, f"Failed ({type(e).__name__})")
            current_step_num += 1
        else:
            if self.smithery_server_names and not self.smithery_api_key:
                self.logger.warning(
                    "Smithery server names provided, but no API key. Skipping Smithery fetch."
                )
            context["fetched_smithery_mcp_configs"] = {}  # Ensure key exists

        research_results = None
        if self.use_perplexity and self.perplexity_api_key:
            step_desc = steps[current_step_num]
            update_status(step_desc, "Starting")
            self.logger.info(step_desc)
            research_results = self._perform_research(context)

            if research_results:
                formatted_research_insights_list = []
                for question, p_response in research_results.items():
                    answer_text = f"Error fetching answer: {p_response.get('error', 'Unknown error')}"
                    if "error" not in p_response:
                        try:
                            answer_text = (
                                p_response.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content", "Could not extract answer.")
                            )
                            if answer_text == "Could not extract answer.":
                                self.logger.warning(
                                    f"Could not parse Perplexity response for question: {question}. Response: {p_response}"
                                )
                        except (KeyError, IndexError, TypeError, AttributeError) as e:
                            answer_text = f"Error parsing Perplexity response: {e}"
                            self.logger.warning(
                                f"Error parsing Perplexity response for question: {question}. Response: {p_response}, Error: {e}"
                            )

                    formatted_research_insights_list.append(
                        f"Research Question: {question}\nResearch Finding:\n{answer_text}\n---\n"
                    )
                context["formatted_research_insights"] = "\n".join(
                    formatted_research_insights_list
                )
                context["raw_research_results"] = research_results
            else:
                context["formatted_research_insights"] = None
                context["raw_research_results"] = None

            context["research_results"] = research_results

            update_status(step_desc, "Completed")
            current_step_num += 1

        results: Dict[str, str] = {}

        step_desc = steps[current_step_num]
        update_status(step_desc, "In progress")
        self.logger.info(step_desc)
        doc_generator = DocGenerator(self.llm, self.fs_utils, context)
        results["claude_md"] = doc_generator.generate_claude_md()
        update_status(
            step_desc,
            "Completed" if not results["claude_md"].startswith("ERROR:") else "Failed",
        )
        current_step_num += 1

        step_desc = steps[current_step_num]
        if not self.fs_utils.skip_commands:
            update_status(step_desc, "In progress")
            self.logger.info(step_desc)
            command_generator = CommandGenerator(self.llm, self.fs_utils, context)
            results["commands"] = command_generator.generate_commands()
            update_status(
                step_desc,
                "Completed"
                if not results["commands"].startswith("Error")
                else "Failed",
            )
        else:
            self.logger.info(step_desc)
            results["commands"] = "Skipped"
            update_status(step_desc, "Skipped")
        current_step_num += 1

        step_desc = steps[current_step_num]
        if not self.fs_utils.skip_mcp_config:
            update_status(step_desc, "In progress")
            self.logger.info(step_desc)
            config_generator = ConfigGenerator(self.llm, self.fs_utils, context)
            results["mcp_config"] = config_generator.generate_mcp_config()
            update_status(
                step_desc,
                "Completed"
                if not results["mcp_config"].startswith("Error")
                else "Failed",
            )
        else:
            self.logger.info(step_desc)
            results["mcp_config"] = "Skipped"
            update_status(step_desc, "Skipped")
        current_step_num += 1

        step_desc = steps[current_step_num]
        update_status(step_desc, "In progress")
        self.logger.info(step_desc)
        if "config_generator" not in locals():
            config_generator = ConfigGenerator(self.llm, self.fs_utils, context)
        results["settings"] = config_generator.generate_settings()
        update_status(
            step_desc,
            "Completed" if not results["settings"].startswith("Error") else "Failed",
        )
        current_step_num += 1

        step_desc = steps[current_step_num]
        update_status(step_desc, "In progress")
        self.logger.info(step_desc)

        results["action_plan"] = doc_generator.generate_action_plan()
        update_status(
            step_desc,
            "Completed"
            if not results["action_plan"].startswith("ERROR:")
            else "Failed",
        )
        current_step_num += 1

        if progress:
            progress.update(
                task_id, completed=total_steps, description="All steps completed."
            )

        self.logger.info("Dynamic workflow execution completed")
        return results

    def _perform_research(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Perform research using Perplexity API with LLM-generated questions.

        Args:
            context: Raw project context.

        Returns:
            Dictionary of research results, or None if research is skipped or fails.
        """
        if not self.use_perplexity or not self.perplexity_api_key:
            self.logger.info(
                "Skipping Perplexity research (not enabled or API key missing)."
            )
            return None

        self.logger.info(
            "Generating research questions for Perplexity API using LLM..."
        )

        question_generator = QuestionGenerator(context, self.llm)

        questions_list = question_generator.generate_questions()

        if not questions_list:
            self.logger.info("No research questions generated by LLM.")
            return None

        self.logger.info(
            f"Querying Perplexity API with {len(questions_list)} LLM-generated questions..."
        )
        try:
            perplexity_client = PerplexityClient(self.perplexity_api_key)
        except Exception as e:
            self.logger.error(f"Failed to initialize PerplexityClient: {e}")
            return None

        research_results: Dict[str, Any] = {}
        for i, question_str in enumerate(questions_list):
            self.logger.info(
                f"Perplexity query {i + 1}/{len(questions_list)}: '{question_str[:100]}...'"
            )
            try:
                result = perplexity_client.query(question_str, focus=None)
                research_results[question_str] = result
            except Exception as e:
                self.logger.warning(
                    f"Perplexity API query failed for question '{question_str[:50]}...': {e}"
                )
                research_results[question_str] = {"error": str(e)}

        self.logger.info(
            f"Completed Perplexity API queries. Got results for {sum(1 for r in research_results.values() if 'error' not in r)} questions."
        )
        return research_results
