"""
CLI components for the cc-bootstrap tool.

This package contains modules for enhanced CLI functionality using the Rich library
and Typer for command-line argument parsing.
"""

from cc_bootstrap.cli.formatters import (
    format_header,
    format_section,
    format_success,
    format_warning,
    format_error,
    format_info,
    format_summary,
)
from cc_bootstrap.cli.interactive import (
    confirm_action,
    prompt_input,
    prompt_choice,
    prompt_yes_no,
)
from cc_bootstrap.cli.progress import (
    create_spinner,
    create_progress_bar,
    create_simple_progress_bar,
    track_progress,
)
from cc_bootstrap.cli.app import app

__all__ = [
    "format_header",
    "format_section",
    "format_success",
    "format_warning",
    "format_error",
    "format_info",
    "format_summary",
    "confirm_action",
    "prompt_input",
    "prompt_choice",
    "prompt_yes_no",
    "create_spinner",
    "create_progress_bar",
    "create_simple_progress_bar",
    "track_progress",
    "app",
]
