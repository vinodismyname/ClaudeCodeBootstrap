"""
Directory analyzer module for extracting project structure.
"""

import os
from pathlib import Path
from typing import Dict, Any, List

from cc_bootstrap.config import IGNORE_DIRS


class DirectoryAnalyzer:
    """Analyzes project directory structure."""

    def __init__(self, project_path: str):
        """
        Initialize the directory analyzer.

        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze project directory structure.

        Returns:
            Dictionary containing directory structure with metadata
        """
        return {
            "structure": self._extract_directory_structure(),
            "file_count": self._count_files(),
            "dir_count": self._count_directories(),
            "top_level_dirs": self._get_top_level_directories(),
        }

    def _extract_directory_structure(self) -> Dict[str, Any]:
        """Extract hierarchical directory structure with file metadata."""
        import logging

        logger = logging.getLogger(__name__)
        structure = {}

        try:
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

                try:
                    rel_path = os.path.relpath(root, self.project_path)
                    if rel_path == ".":
                        rel_path = ""

                    current_level = structure
                    if rel_path:
                        path_parts = rel_path.split(os.sep)
                        for part in path_parts:
                            if part not in current_level:
                                current_level[part] = {}
                            current_level = current_level[part]

                    file_metadata = []
                    for f in files:
                        try:
                            file_path = os.path.join(root, f)
                            file_size = os.path.getsize(file_path) // 1024
                            file_metadata.append(
                                {
                                    "name": f,
                                    "ext": os.path.splitext(f)[1],
                                    "size": file_size,
                                }
                            )
                        except PermissionError:
                            logger.warning(
                                f"Permission denied when accessing file: {os.path.join(root, f)}"
                            )
                        except FileNotFoundError:
                            logger.warning(
                                f"File not found (may have been deleted during analysis): {os.path.join(root, f)}"
                            )
                        except OSError as e:
                            logger.warning(
                                f"OS error when accessing file {os.path.join(root, f)}: {e}"
                            )

                    current_level["__files__"] = file_metadata

                except PermissionError:
                    logger.warning(
                        f"Permission denied when accessing directory: {root}"
                    )
                except OSError as e:
                    logger.warning(f"OS error when processing directory {root}: {e}")

        except PermissionError:
            logger.error(
                f"Permission denied when accessing project path: {self.project_path}"
            )
            return {"error": "Permission denied when accessing project path"}
        except FileNotFoundError:
            logger.error(f"Project path not found: {self.project_path}")
            return {"error": "Project path not found"}
        except OSError as e:
            logger.error(f"OS error when walking project directory: {e}")
            return {"error": f"Error analyzing project directory: {e}"}

        return structure

    def _count_files(self) -> int:
        """Count total number of files in project."""
        import logging

        logger = logging.getLogger(__name__)
        count = 0

        try:
            for _, _, files in os.walk(self.project_path):
                count += len(files)
            return count
        except PermissionError:
            logger.error(
                f"Permission denied when counting files in: {self.project_path}"
            )
            return -1
        except FileNotFoundError:
            logger.error(
                f"Project path not found when counting files: {self.project_path}"
            )
            return -1
        except OSError as e:
            logger.error(f"OS error when counting files: {e}")
            return -1

    def _count_directories(self) -> int:
        """Count total number of directories in project."""
        import logging

        logger = logging.getLogger(__name__)
        count = 0

        try:
            for _, dirs, _ in os.walk(self.project_path):
                count += len(dirs)
            return count
        except PermissionError:
            logger.error(
                f"Permission denied when counting directories in: {self.project_path}"
            )
            return -1
        except FileNotFoundError:
            logger.error(
                f"Project path not found when counting directories: {self.project_path}"
            )
            return -1
        except OSError as e:
            logger.error(f"OS error when counting directories: {e}")
            return -1

    def _get_top_level_directories(self) -> List[str]:
        """Get list of top-level directories."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            return [
                d.name
                for d in self.project_path.iterdir()
                if d.is_dir() and d.name not in IGNORE_DIRS
            ]
        except PermissionError:
            logger.error(
                f"Permission denied when accessing top-level directories in: {self.project_path}"
            )
            return []
        except FileNotFoundError:
            logger.error(
                f"Project path not found when getting top-level directories: {self.project_path}"
            )
            return []
        except OSError as e:
            logger.error(f"OS error when getting top-level directories: {e}")
            return []
