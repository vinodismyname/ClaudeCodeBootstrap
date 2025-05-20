import os
from pathlib import Path
from typing import Dict, List, Any

from cc_bootstrap.config import (
    MAX_FILES_IN_CONTEXT,
    MAX_LINES_PER_FILE,
    MAX_CHARS_PER_FILE,
    IMPORTANT_FILES,
    CODE_FILE_EXTENSIONS,
    ENTRY_POINTS,
    CONFIG_EXTENSIONS,
)


class FileSampler:
    """Samples key files from a project based on simple heuristics."""

    def __init__(self, project_path: str, directory_structure: Dict[str, Any]):
        """
        Initialize the file sampler.

        Args:
            project_path: Path to the project directory
            directory_structure: Directory structure from DirectoryAnalyzer
        """
        self.project_path = Path(project_path)
        self.directory_structure = directory_structure

    def sample(self, max_files: int = MAX_FILES_IN_CONTEXT) -> Dict[str, str]:
        """
        Sample key files based on simple importance heuristics.

        Args:
            max_files: Maximum number of files to sample

        Returns:
            Dictionary mapping file paths to file contents
        """

        all_files: List[tuple[str, Dict[str, Any]]] = []
        self._collect_files(self.directory_structure, all_files)

        scored_files = self._score_files(all_files)

        scored_files.sort(key=lambda x: x[1], reverse=True)
        top_files_paths = [path for path, _ in scored_files[:max_files]]

        file_contents: Dict[str, str] = {}
        for file_path_str in top_files_paths:
            try:
                full_path = self.project_path / file_path_str

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[:MAX_LINES_PER_FILE]
                    content = "".join(lines)

                    if len(content) > MAX_CHARS_PER_FILE:
                        content = (
                            content[:MAX_CHARS_PER_FILE]
                            + f"\n... (truncated, {len(content) - MAX_CHARS_PER_FILE} more characters)"
                        )

                    file_contents[file_path_str] = content
            except Exception as e:
                file_contents[file_path_str] = (
                    f"Error reading file {file_path_str}: {str(e)}"
                )

        return file_contents

    def _collect_files(
        self,
        structure: Dict[str, Any],
        result: List[tuple[str, Dict[str, Any]]],
        current_path_str: str = "",
    ):
        """Recursively collect all files from directory structure."""
        if "__files__" in structure and isinstance(structure["__files__"], list):
            for file_info in structure["__files__"]:
                if isinstance(file_info, dict) and "name" in file_info:
                    file_path_str = os.path.join(current_path_str, file_info["name"])
                    result.append((file_path_str, file_info))

        for key, value in structure.items():
            if key != "__files__" and isinstance(value, dict):
                new_path_str = os.path.join(current_path_str, key)
                self._collect_files(value, result, new_path_str)

    def _score_files(
        self, files: List[tuple[str, Dict[str, Any]]]
    ) -> List[tuple[str, int]]:
        """Score files by importance using simple heuristics."""

        scored_files: List[tuple[str, int]] = []
        for path_str, file_info in files:
            score = 0

            if not isinstance(file_info, dict):
                continue

            file_name = file_info.get("name", "")
            file_ext = file_info.get("ext", "")
            file_size_kb = file_info.get("size", float("inf"))

            if file_name in IMPORTANT_FILES:
                score += 10

            if file_name in ENTRY_POINTS:
                score += 5

            if file_ext in CONFIG_EXTENSIONS:
                score += 3

            if file_ext in CODE_FILE_EXTENSIONS:
                score += 2

            if file_size_kb < 10:
                score += 1

            scored_files.append((path_str, score))

        return scored_files
