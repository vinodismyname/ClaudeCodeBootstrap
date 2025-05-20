"""
Formatters module for enhanced CLI output.

This module provides utility functions for formatting CLI output using the Rich library.
"""

from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box


console = Console()


def format_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Format and print a header with an optional subtitle.

    Args:
        title: The main title text.
        subtitle: Optional subtitle text.
    """
    console.print()
    console.print(
        Panel.fit(
            f"[bold blue]{title}[/bold blue]"
            + (f"\n[italic]{subtitle}[/italic]" if subtitle else ""),
            border_style="blue",
        )
    )
    console.print()


def format_section(title: str) -> None:
    """
    Format and print a section title.

    Args:
        title: The section title text.
    """
    console.print(f"\n[bold cyan]== {title} ==[/bold cyan]")


def format_success(message: str) -> None:
    """
    Format and print a success message.

    Args:
        message: The success message text.
    """
    console.print(f"[bold green]✓ {message}[/bold green]")


def format_warning(message: str) -> None:
    """
    Format and print a warning message.

    Args:
        message: The warning message text.
    """
    console.print(f"[bold yellow]⚠ {message}[/bold yellow]")


def format_error(message: str) -> None:
    """
    Format and print an error message.

    Args:
        message: The error message text.
    """
    console.print(f"[bold red]✗ {message}[/bold red]")


def format_info(message: str) -> None:
    """
    Format and print an informational message.

    Args:
        message: The informational message text.
    """
    console.print(f"[blue]ℹ {message}[/blue]")


def format_summary(title: str, items: Dict[str, str]) -> None:
    """
    Format and print a summary table.

    Args:
        title: The summary title.
        items: Dictionary of items to display in the summary.
    """
    table = Table(title=title, show_header=False, box=box.SIMPLE)
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="white")

    for item, status in items.items():
        status_style = ""
        if status.lower() in ["success", "completed", "done"]:
            status_style = "green"
        elif status.lower() in ["skipped", "ignored"]:
            status_style = "yellow"
        elif status.lower() in ["failed", "error"]:
            status_style = "red"

        table.add_row(
            item,
            f"[{status_style}]{status}[/{status_style}]" if status_style else status,
        )

    console.print()
    console.print(table)
    console.print()


def format_code(code: str, language: str = "python") -> None:
    """
    Format and print code with syntax highlighting.

    Args:
        code: The code to display.
        language: The programming language for syntax highlighting.
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def format_markdown(markdown_text: str) -> None:
    """
    Format and print Markdown text.

    Args:
        markdown_text: The Markdown text to display.
    """
    md = Markdown(markdown_text)
    console.print(md)


def format_file_list(files: List[str], title: str = "Files") -> None:
    """
    Format and print a list of files.

    Args:
        files: List of file paths to display.
        title: The title for the file list.
    """
    if not files:
        return

    table = Table(title=title, show_header=False, box=box.SIMPLE)
    table.add_column("File", style="cyan")

    for file in files:
        table.add_row(file)

    console.print(table)


def clear_screen() -> None:
    """Clear the console screen."""
    console.clear()
