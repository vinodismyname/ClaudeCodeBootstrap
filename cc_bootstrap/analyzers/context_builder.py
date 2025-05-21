"""
Context builder module for preparing raw context for LLM-led inference.
"""

from typing import Dict, Any, Optional

from cc_bootstrap.analyzers.directory_analyzer import DirectoryAnalyzer
from cc_bootstrap.analyzers.file_sampler import FileSampler


class ContextBuilder:
    """Builds raw context for LLM-led inference based on project analysis."""

    def __init__(self, project_path: str, plan_file: Optional[str] = None):
        """
        Initialize the context builder.

        Args:
            project_path: Path to the project directory
            plan_file: Path to the user's plan file (optional)
        """
        self.project_path = project_path
        self.plan_file = plan_file

    def build_context(self) -> Dict[str, Any]:
        """
        Build raw context for LLM-led inference based on project analysis.

        Following the LLM-led inference strategy, this method only provides raw data:
        - The content of the user's plan file
        - A sample of files from the project directory

        The LLM will be responsible for inferring project characteristics from this raw data.

        Returns:
            Dictionary containing raw project context
        """

        directory_analyzer = DirectoryAnalyzer(self.project_path)
        directory_analysis = directory_analyzer.analyze()

        file_sampler = FileSampler(self.project_path, directory_analysis["structure"])
        project_file_samples = file_sampler.sample()

        user_plan_content = None
        if self.plan_file:
            try:
                with open(self.plan_file, "r", encoding="utf-8") as f:
                    user_plan_content = f.read()
            except Exception as e:
                print(f"Warning: Could not read plan file: {e}")

        context = {
            "user_plan_content": user_plan_content,
            "project_file_samples": project_file_samples,
        }

        return context
