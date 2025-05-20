"""
Progress indicators module for enhanced CLI feedback.

This module provides utility functions for creating progress bars, spinners,
and other progress indicators using the Rich library.
"""

from typing import Any, Callable, Iterable, List, Optional, TypeVar

from rich.console import Console, Group
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.live import Live
from rich.status import Status
from rich.panel import Panel


console = Console()


T = TypeVar("T")


def create_spinner(message: str) -> Status:
    """
    Create a spinner with a message.

    Args:
        message: The message to display alongside the spinner.

    Returns:
        A Status object that can be used in a context manager.
    """
    return Status(message, spinner="dots")


def create_progress_bar(
    total: Optional[int] = None,
    description: str = "Processing",
    transient: bool = False,
) -> Progress:
    """
    Create a progress bar.

    Args:
        total: The total number of steps.
        description: The description of the progress bar.
        transient: Whether to remove the progress bar after completion.

    Returns:
        A Progress object that can be used to track progress.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        MofNCompleteColumn(),
        transient=transient,
        console=console,
    )


def track_progress(
    sequence: Iterable[T],
    description: str = "Processing",
    total: Optional[int] = None,
    transient: bool = False,
) -> Iterable[T]:
    """
    Track progress through an iterable.

    Args:
        sequence: The iterable to track progress through.
        description: The description of the progress.
        total: The total number of items (calculated from sequence if not provided).
        transient: Whether to remove the progress bar after completion.

    Returns:
        An iterable that yields the items from the input sequence.
    """
    progress = create_progress_bar(total=total, transient=transient)

    with progress:
        task_id = progress.add_task(description, total=total)
        for item in sequence:
            yield item
            progress.update(task_id, advance=1)


def execute_with_spinner(
    func: Callable[..., T], message: str, *args: Any, **kwargs: Any
) -> T:
    """
    Execute a function with a spinner.

    Args:
        func: The function to execute.
        message: The message to display alongside the spinner.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call.
    """
    with create_spinner(message) as status:
        result = func(*args, **kwargs)
        status.update(f"{message} [bold green]Done![/bold green]")
        return result


def create_simple_progress_bar(transient: bool = False) -> Progress:
    """
    Create a simplified progress bar with minimal columns.

    Args:
        transient: Whether to remove the progress bar after completion.

    Returns:
        A Progress object with minimal columns.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        transient=transient,
        console=console,
        expand=True,
        refresh_per_second=10,
    )


def execute_with_progress(
    items: List[Any],
    process_func: Callable[[Any, Progress, int], T],
    description: str = "Processing items",
    transient: bool = False,
) -> List[T]:
    """
    Execute a function on each item with progress tracking.

    Args:
        items: The list of items to process.
        process_func: The function to execute on each item. Takes item, progress, and task_id.
        description: The description of the progress.
        transient: Whether to remove the progress bar after completion.

    Returns:
        A list of results from processing each item.
    """
    results = []
    progress = create_progress_bar(total=len(items), transient=transient)

    with progress:
        task_id = progress.add_task(description, total=len(items))
        for item in items:
            result = process_func(item, progress, task_id)
            results.append(result)
            progress.update(task_id, advance=1)

    return results


def create_live_display(max_status_lines: int = 10) -> tuple[Live, Progress, List[str]]:
    """
    Create a live display with a progress bar and status panel.

    Args:
        max_status_lines: Maximum number of status lines to display in the panel.

    Returns:
        A tuple containing:
        - Live display object
        - Progress bar object
        - Status messages list (append to this to update the display)
    """

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        expand=True,
    )

    status_messages = []

    def get_status_panel():
        display_messages = (
            status_messages[-max_status_lines:] if status_messages else ["Starting..."]
        )
        status_text = "\n".join(display_messages)
        return Panel(status_text, title="Status", border_style="blue")

    def get_renderable():
        return Group(progress, get_status_panel())

    live = Live(get_renderable(), refresh_per_second=4, console=console)

    return live, progress, status_messages


def create_status_updater(live: Live, status_messages: List[str]) -> Callable:
    """
    Create a status updater callback function for the DynamicWorkflow.

    Args:
        live: The Live display object.
        status_messages: The list of status messages to update.

    Returns:
        A callback function that can be passed to DynamicWorkflow.execute().
    """

    def status_updater(
        step_description: str, status: str, current_step: int, total_steps: int
    ) -> None:
        """
        Update the status display with the current step information.

        Args:
            step_description: Description of the current step.
            status: Status of the step (e.g., "Starting", "In progress", "Completed").
            current_step: Current step number (1-based).
            total_steps: Total number of steps.
        """

        message = f"[Step {current_step}/{total_steps}] {step_description}: {status}"

        if status == "Completed":
            message = f"[green]{message}[/green]"
        elif status == "In progress":
            message = f"[yellow]{message}[/yellow]"
        elif status == "Skipped":
            message = f"[blue]{message}[/blue]"

        status_messages.append(message)

        live.refresh()

    return status_updater
