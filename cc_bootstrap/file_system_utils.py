"""
File System Utils module for handling file operations.

This module handles file system operations such as reading, writing,
creating directories, and checking if files exist.
"""

import logging
from pathlib import Path
from typing import List, Optional


class FileSystemUtils:
    """Utility class for file system operations."""

    def __init__(
        self, project_path: Path, force_overwrite: bool = False, dry_run: bool = False
    ):
        """
        Initialize the file system utilities.

        Args:
            project_path: Base path for the project.
            force_overwrite: Whether to force overwrite existing files.
            dry_run: If True, will simulate file operations without actually writing.
        """
        self.logger = logging.getLogger(__name__)
        self.project_path = project_path
        self.force_overwrite = force_overwrite
        self.dry_run = dry_run
        self.skip_commands = False
        self.skip_mcp_config = False

        self.logger.debug(
            f"Initialized FileSystemUtils with project_path={project_path}"
        )

    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path against the project path.

        Args:
            relative_path: Path relative to the project root.

        Returns:
            Absolute path.
        """
        return self.project_path / relative_path

    def ensure_directory(self, directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Directory path relative to project root.

        Returns:
            True if directory exists or was created, False otherwise.
        """
        dir_path = self.resolve_path(directory_path)

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would create directory: {dir_path}")
            return True

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {dir_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {dir_path}: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path: File path relative to project root.

        Returns:
            True if file exists, False otherwise.
        """
        path = self.resolve_path(file_path)
        return path.exists() and path.is_file()

    def read_file(self, file_path: str, default: str = "") -> str:
        """
        Read the contents of a file.

        Args:
            file_path: File path relative to project root.
            default: Default value to return if file doesn't exist.

        Returns:
            File contents as string, or default if file doesn't exist.
        """
        path = self.resolve_path(file_path)

        if not path.exists():
            self.logger.debug(f"File does not exist: {path}")
            return default

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.debug(f"Read file: {path}")
            return content
        except Exception as e:
            self.logger.error(f"Failed to read file {path}: {e}")
            return default

    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to a file.

        Args:
            file_path: File path relative to project root.
            content: Content to write to the file.

        Returns:
            True if successful, False otherwise.
        """
        path = self.resolve_path(file_path)

        if path.exists() and not self.force_overwrite:
            self.logger.info(
                f"File exists and force_overwrite is False, skipping: {path}"
            )
            return False

        parent_dir = path.parent
        if not self.ensure_directory(str(parent_dir.relative_to(self.project_path))):
            return False

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would write to file: {path}")
            self.logger.debug(f"Content preview (first 100 chars): {content[:100]}...")
            return True

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.logger.info(f"Wrote file: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to write file {path}: {e}")
            return False

    def list_files(
        self, directory_path: str, pattern: Optional[str] = None
    ) -> List[Path]:
        """
        List files in a directory, optionally matching a pattern.

        Args:
            directory_path: Directory path relative to project root.
            pattern: Optional glob pattern to filter files.

        Returns:
            List of Path objects for matching files.
        """
        dir_path = self.resolve_path(directory_path)

        if not dir_path.exists() or not dir_path.is_dir():
            self.logger.debug(f"Directory does not exist: {dir_path}")
            return []

        try:
            if pattern:
                files = list(dir_path.glob(pattern))
            else:
                files = [p for p in dir_path.iterdir() if p.is_file()]

            self.logger.debug(f"Listed {len(files)} files in {dir_path}")
            return files
        except Exception as e:
            self.logger.error(f"Failed to list files in {dir_path}: {e}")
            return []

    def set_skip_commands(self, skip: bool) -> None:
        """Set whether to skip generating custom commands."""
        self.skip_commands = skip
        self.logger.debug(f"Set skip_commands to {skip}")

    def set_skip_mcp_config(self, skip: bool) -> None:
        """Set whether to skip generating MCP config."""
        self.skip_mcp_config = skip
        self.logger.debug(f"Set skip_mcp_config to {skip}")
