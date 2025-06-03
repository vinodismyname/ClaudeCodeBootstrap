"""
Typer-based CLI application for cc-bootstrap.

This module implements the CLI interface using Typer, providing a more
modern and feature-rich command-line experience compared to argparse.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Any

import typer
from rich.console import Console
from rich.logging import RichHandler

from cc_bootstrap import __version__
from cc_bootstrap.config import (
    DEFAULT_LLM_PROVIDER,
    DEFAULT_THINKING_ENABLED,
    DEFAULT_THINKING_BUDGET,
    ENV_ANTHROPIC_API_KEY,
    ENV_PERPLEXITY_API_KEY,
    ENV_SMITHERY_API_KEY,
    ENV_AWS_REGION,
    ENV_AWS_PROFILE,
    LLM_PROVIDERS,
)
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.dynamic.workflow import DynamicWorkflow
from cc_bootstrap.llm_interface import LLMInterface
from cc_bootstrap.cli import (
    format_header,
    format_section,
    format_success,
    format_warning,
    format_error,
    format_info,
    format_summary,
    prompt_yes_no,
    create_spinner,
)

console = Console()

app = typer.Typer(
    help="Bootstrap Claude Code configuration for a project",
    add_completion=True,
    invoke_without_command=True,
)


_app_logger = logging.getLogger("cc_bootstrap")


def setup_logging(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.ERROR

    for h in _app_logger.handlers[:]:
        _app_logger.removeHandler(h)
        h.close()

    new_handler = RichHandler(
        level=level,
        rich_tracebacks=True,
        markup=True,
        show_path=verbose,
        log_time_format="[%X]",
    )

    _app_logger.addHandler(new_handler)
    _app_logger.setLevel(level)
    _app_logger.propagate = False

    return _app_logger


def validate_path(
    path: Path,
    is_file: bool = True,
    must_exist: bool = True,
    check_writable: bool = False,
    create_if_missing: bool = False,
    prompt_message: Optional[str] = None,
) -> Path:
    logger = logging.getLogger("cc_bootstrap")
    try:
        if not path.exists():
            if must_exist and not create_if_missing:
                type_str = "file" if is_file else "directory"
                format_error(f"{type_str.capitalize()} not found: {path}")
                raise typer.Exit(code=1)

            if create_if_missing:
                if prompt_message is None:
                    type_str = "file" if is_file else "directory"
                    prompt_message = f"The {type_str} {path} does not exist. Would you like to create it?"

                if prompt_yes_no(prompt_message, default=True):
                    try:
                        if is_file:
                            path.parent.mkdir(parents=True, exist_ok=True)
                            with open(path, "w", encoding="utf-8"):
                                pass
                            format_success(f"Created empty file at {path}")
                        else:
                            path.mkdir(parents=True, exist_ok=True)
                            format_success(f"Created directory at {path}")
                    except PermissionError:
                        type_str = "file" if is_file else "directory"
                        format_error(
                            f"Permission denied when creating {type_str}: {path}. Please check your permissions and try again."
                        )
                        raise typer.Exit(code=1)
                    except Exception as e:
                        type_str = "file" if is_file else "directory"
                        format_error(f"Failed to create {type_str}: {e}")
                        raise typer.Exit(code=1)
                else:
                    format_info("Path creation aborted by user.")
                    raise typer.Exit(code=1)
        else:
            if is_file and not path.is_file():
                format_error(f"Path exists but is not a file: {path}")
                raise typer.Exit(code=1)
            elif not is_file and not path.is_dir():
                format_error(f"Path exists but is not a directory: {path}")
                raise typer.Exit(code=1)

            try:
                if is_file:
                    with open(path, "r", encoding="utf-8"):
                        pass
                else:
                    os.listdir(path)
            except PermissionError:
                type_str = "file" if is_file else "directory"
                format_error(
                    f"Permission denied when reading {type_str}: {path}. Please check your permissions and try again."
                )
                raise typer.Exit(code=1)
            except Exception as e:
                type_str = "file" if is_file else "directory"
                format_error(f"Failed to read {type_str}: {e}")
                raise typer.Exit(code=1)

            if check_writable:
                check_path = path if path.is_dir() else path.parent
                if not os.access(check_path, os.W_OK):
                    if path.is_dir():
                        format_error(
                            f"Permission denied: Directory {check_path} is not writable. Please check your permissions and try again."
                        )
                    else:
                        format_error(
                            f"Permission denied: Location {check_path} (for file {path}) is not writable. Please check your permissions and try again."
                        )
                    raise typer.Exit(code=1)

        return path.resolve()
    except typer.Exit:
        raise
    except Exception as e:
        if not isinstance(e, typer.Exit):
            format_error(f"Unexpected error validating path {path}: {e}")
            if logger.isEnabledFor(logging.DEBUG):
                format_error(traceback.format_exc())
            raise typer.Exit(code=1)
        else:
            raise


def parse_smithery_server_names(names_input: Optional[str]) -> List[str]:
    """
    Parse a comma-separated string of Smithery server names or search queries.

    Args:
        names_input: Comma-separated string of Smithery qualified names or search terms

    Returns:
        List of Smithery server names or search queries
    """
    if not names_input:
        return []
    return [name.strip() for name in names_input.split(",") if name.strip()]


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit.", is_eager=True
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive mode. If no command is specified, 'bootstrap' will be run interactively.",
    ),
    verbose_global: bool = typer.Option(
        False, "--verbose", "-v", help="Increase output verbosity (global)."
    ),
):
    logger = setup_logging(verbose_global)

    if version:
        console.print(f"cc-bootstrap {__version__}")
        raise typer.Exit(0)

    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["interactive_global"] = interactive
    ctx.obj["verbose_global"] = verbose_global

    if not (interactive and ctx.invoked_subcommand is None):
        format_header(
            f"Claude Code Bootstrapper v{__version__}",
            "A tool for bootstrapping Claude Code configuration files",
        )

    if ctx.invoked_subcommand is None:
        if interactive:
            console.print(
                "\nGlobal interactive mode detected. Invoking 'bootstrap' command interactively...\n"
            )

            bootstrap_command_obj = ctx.command.get_command(ctx, "bootstrap")
            if bootstrap_command_obj is None:
                logger.error(
                    "Fatal: 'bootstrap' command not found internally. This indicates a problem with command registration."
                )
                raise typer.Exit(code=2)

            ctx.invoke(bootstrap_command_obj, project_path=None, project_plan_file=None)
        else:
            console.print(ctx.get_help())
            raise typer.Exit(0)


@app.command("show-examples")
def show_examples():
    from cc_bootstrap.cli.interactive import display_help_menu

    display_help_menu()


@app.command()
def bootstrap(
    ctx: typer.Context,
    project_path: Optional[Path] = typer.Option(
        None,
        "--project-path",
        "-p",
        help="Path to the target project folder.",
        dir_okay=True,
        file_okay=False,
        resolve_path=True,
    ),
    project_plan_file: Optional[Path] = typer.Option(
        None,
        "--project-plan-file",
        help="Path to the user's project specification/plan file.",
        exists=False,
        readable=True,
        resolve_path=True,
    ),
    smithery_mcp_servers: Optional[str] = typer.Option(
        None,
        "--smithery-mcp-servers",
        help="Comma-separated list of Smithery server names or search queries. Exact matches will be used directly, otherwise the best search match will be used (e.g., 'owner/repo,exa,search term').",
    ),
    smithery_api_key: Optional[str] = typer.Option(
        None,
        "--smithery-api-key",
        help=f"Smithery API key (or use {ENV_SMITHERY_API_KEY} env var).",
        envvar=ENV_SMITHERY_API_KEY,
    ),
    use_claude_squad: bool = typer.Option(
        False,
        "--use-claude-squad/--no-use-claude-squad",
        help="Enable Claude Squad guidance.",
    ),
    use_perplexity: bool = typer.Option(
        False,
        "--use-perplexity/--no-use-perplexity",
        help="Use Perplexity API for research.",
    ),
    perplexity_api_key: Optional[str] = typer.Option(
        None,
        "--perplexity-api-key",
        help=f"Perplexity API key (or use {ENV_PERPLEXITY_API_KEY} env var).",
        envvar=ENV_PERPLEXITY_API_KEY,
    ),
    llm_provider: str = typer.Option(
        DEFAULT_LLM_PROVIDER,
        "--llm-provider",
        help=f"LLM provider ({', '.join(LLM_PROVIDERS.keys())}).",
        case_sensitive=False,
    ),
    llm_model: Optional[str] = typer.Option(
        None, "--llm-model", help="LLM model ID (uses provider's default if not set)."
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help=f"Anthropic API key (or use {ENV_ANTHROPIC_API_KEY} env var).",
        envvar=ENV_ANTHROPIC_API_KEY,
    ),
    aws_region: Optional[str] = typer.Option(
        None,
        "--aws-region",
        help=f"AWS region for Bedrock (or use {ENV_AWS_REGION} env var).",
        envvar=ENV_AWS_REGION,
    ),
    aws_profile: Optional[str] = typer.Option(
        None,
        "--aws-profile",
        help=f"AWS profile for Bedrock (or use {ENV_AWS_PROFILE} env var).",
        envvar=ENV_AWS_PROFILE,
    ),
    enable_thinking: bool = typer.Option(
        DEFAULT_THINKING_ENABLED,
        "--enable-thinking/--disable-thinking",
        help="Enable/disable extended LLM thinking.",
    ),
    thinking_budget: int = typer.Option(
        DEFAULT_THINKING_BUDGET,
        "--thinking-budget",
        min=0,
        help="Token budget for thinking.",
    ),
    force_overwrite: bool = typer.Option(
        False,
        "--force-overwrite/--no-force-overwrite",
        help="Overwrite existing files.",
    ),
    skip_commands: bool = typer.Option(
        False,
        "--skip-commands/--generate-commands",
        help="Skip custom commands generation.",
    ),
    skip_mcp_config: bool = typer.Option(
        False,
        "--skip-mcp-config/--generate-mcp-config",
        help="Skip MCP config generation.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run/--execute-run", help="Simulate run without writing files."
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Increase output verbosity (uses global setting).",
        hidden=True,
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Run in interactive mode (uses global setting).",
        hidden=True,
    ),
):
    is_interactive = interactive or ctx.obj.get("interactive_global", False)

    final_verbose = verbose or ctx.obj.get("verbose_global", False)

    logger = setup_logging(final_verbose)

    cli_params: Dict[str, Any] = {
        "project_path": project_path,
        "project_plan_file": project_plan_file,
        "smithery_mcp_servers": smithery_mcp_servers,
        "smithery_api_key": smithery_api_key,
        "use_claude_squad": use_claude_squad,
        "use_perplexity": use_perplexity,
        "perplexity_api_key": perplexity_api_key,
        "llm_provider": llm_provider.lower(),
        "llm_model": llm_model,
        "api_key": api_key,
        "aws_region": aws_region,
        "aws_profile": aws_profile,
        "enable_thinking": enable_thinking,
        "thinking_budget": thinking_budget,
        "force_overwrite": force_overwrite,
        "skip_commands": skip_commands,
        "skip_mcp_config": skip_mcp_config,
        "dry_run": dry_run,
        "verbose": final_verbose,
    }

    if is_interactive:
        from cc_bootstrap.cli.interactive import prompt_for_project_config

        interactive_config = prompt_for_project_config(cli_params)
        for key, value in interactive_config.items():
            if value is not None:
                if key in ["project_path", "project_plan_file"] and isinstance(
                    value, str
                ):
                    cli_params[key] = Path(value)
                elif key == "llm_provider" and isinstance(value, str):
                    cli_params[key] = value.lower()
                else:
                    cli_params[key] = value

        if cli_params["verbose"] != final_verbose:
            logger = setup_logging(cli_params["verbose"])
            logger.info(f"Verbosity updated to: {cli_params['verbose']}")
    else:
        if cli_params.get("project_path") is None:
            format_error("--project-path is required in non-interactive mode.")
            raise typer.Exit(code=1)
        if cli_params.get("project_plan_file") is None:
            format_error("--project-plan-file is required in non-interactive mode.")
            raise typer.Exit(code=1)

    try:
        format_section("Project Setup")
        cli_params["project_path"] = validate_path(
            Path(cli_params["project_path"]),
            is_file=False,
            must_exist=False,
            check_writable=True,
            create_if_missing=True,
        )
        logger.info(f"Using project directory: {cli_params['project_path']}")
        cli_params["project_plan_file"] = validate_path(
            Path(cli_params["project_plan_file"]),
            is_file=True,
            must_exist=False,
            check_writable=True,
            create_if_missing=True,
        )
        logger.info(f"Using project plan file: {cli_params['project_plan_file']}")

        if cli_params["project_plan_file"].stat().st_size == 0:
            try:
                with open(cli_params["project_plan_file"], "w", encoding="utf-8") as f:
                    f.write("# Project Plan\n\nAdd your project details here.\n")
                format_success(
                    f"Created and initialized empty plan file at {cli_params['project_plan_file']}"
                )
            except Exception as e:
                format_error(
                    f"Failed to write to new plan file {cli_params['project_plan_file']}: {e}"
                )
                raise typer.Exit(code=1)

        fs_utils = FileSystemUtils(
            cli_params["project_path"],
            cli_params["force_overwrite"],
            cli_params["dry_run"],
        )
        fs_utils.set_skip_commands(cli_params["skip_commands"])
        fs_utils.set_skip_mcp_config(cli_params["skip_mcp_config"])
        logger.info(
            f"FileSystemUtils initialized (overwrite: {cli_params['force_overwrite']}, dry_run: {cli_params['dry_run']})"
        )
        if cli_params["skip_commands"]:
            logger.info("Custom commands generation will be skipped.")
        if cli_params["skip_mcp_config"]:
            logger.info("MCP configuration generation will be skipped.")

        actual_llm_model = cli_params["llm_model"]
        current_llm_provider = cli_params["llm_provider"]
        if not actual_llm_model:
            if current_llm_provider not in LLM_PROVIDERS:
                format_error(
                    f"Unknown LLM provider: {current_llm_provider}. Available: {', '.join(LLM_PROVIDERS.keys())}"
                )
                raise typer.Exit(code=1)
            actual_llm_model = LLM_PROVIDERS[current_llm_provider]["default_model"]
            logger.info(
                f"No LLM model specified, using default for {current_llm_provider}: {actual_llm_model}"
            )

        with create_spinner("Initializing LLM interface..."):
            llm = LLMInterface(
                actual_llm_model,
                current_llm_provider,
                cli_params["api_key"],
                cli_params["aws_region"],
                cli_params["aws_profile"],
                cli_params["dry_run"],
                cli_params["enable_thinking"],
                cli_params["thinking_budget"],
                cli_params["verbose"],
                str(cli_params["project_path"]),
            )
        format_success(
            f"LLM interface initialized: Provider={llm.provider_type}, Model={llm.model}"
        )

        project_plan_content = ""
        with create_spinner(
            f"Reading project plan from {cli_params['project_plan_file']}..."
        ):
            try:
                with open(cli_params["project_plan_file"], "r", encoding="utf-8") as f:
                    project_plan_content = f.read()
            except Exception as e:
                format_error(
                    f"Failed to read project plan file {cli_params['project_plan_file']}: {e}"
                )
                raise typer.Exit(code=1)

        if len(project_plan_content.strip()) < 10:
            format_warning("Project plan file seems very short or empty!")
            if not cli_params["dry_run"] and is_interactive:
                if prompt_yes_no("Continue with this plan file?", default=False):
                    pass
                elif prompt_yes_no(
                    "Would you like to edit the plan file now?", default=True
                ):
                    editor = os.environ.get(
                        "EDITOR", "nano" if sys.platform != "win32" else "notepad"
                    )
                    try:
                        import subprocess

                        subprocess.run(
                            [editor, str(cli_params["project_plan_file"])], check=True
                        )
                        with open(
                            cli_params["project_plan_file"], "r", encoding="utf-8"
                        ) as f:
                            project_plan_content = f.read()
                        format_success("Project plan updated and reloaded.")
                    except Exception as e:
                        format_error(f"Failed to open editor for plan file: {e}")
                else:
                    format_info(
                        "Proceeding with the current short plan file (as per user choice or if editing failed)."
                    )
        else:
            format_success("Project plan loaded successfully.")

        parsed_names = []
        if cli_params["smithery_mcp_servers"]:
            with create_spinner("Parsing Smithery MCP server names..."):
                parsed_names = parse_smithery_server_names(
                    cli_params["smithery_mcp_servers"]
                )
            if not parsed_names:
                format_warning("No valid Smithery MCP server names found.")
                if is_interactive and not prompt_yes_no(
                    "Continue without Smithery MCP servers?", default=True
                ):
                    raise typer.Exit(code=1)
            else:
                format_success(
                    f"Smithery MCP server names parsed: Found {len(parsed_names)} server(s)."
                )

        format_section("Asset Generation")
        if cli_params["use_perplexity"] and not cli_params["perplexity_api_key"]:
            format_warning(
                f"Perplexity API usage is enabled, but key not found. Set {ENV_PERPLEXITY_API_KEY} or use --perplexity-api-key."
            )
            if is_interactive:
                if prompt_yes_no("Enter Perplexity API key now?", default=False):
                    from cc_bootstrap.cli.interactive import prompt_input

                    cli_params["perplexity_api_key"] = prompt_input(
                        "Perplexity API key:", password=True
                    )
                elif not prompt_yes_no(
                    "Continue without Perplexity research?", default=True
                ):
                    raise typer.Exit(code=1)
                else:
                    cli_params["use_perplexity"] = False
            else:
                cli_params["use_perplexity"] = False

        if cli_params["use_perplexity"] and not cli_params["perplexity_api_key"]:
            format_warning(
                "Proceeding without Perplexity research (API key still missing)."
            )
            cli_params["use_perplexity"] = False

        results: Dict[str, str] = {}
        from cc_bootstrap.cli.progress import create_live_display, create_status_updater

        live, progress_bar, status_messages = create_live_display(max_status_lines=15)
        status_updater = create_status_updater(live, status_messages)

        with live:
            try:
                dynamic_workflow = DynamicWorkflow(
                    str(cli_params["project_path"]),
                    llm,
                    fs_utils,
                    str(cli_params["project_plan_file"]),
                    cli_params["use_perplexity"],
                    cli_params["perplexity_api_key"],
                    cli_params["use_claude_squad"],
                    smithery_server_names=parsed_names,
                    smithery_api_key=cli_params["smithery_api_key"],
                )
                results = dynamic_workflow.execute(progress_bar, status_updater)
            except Exception as e:
                format_error(f"Error during dynamic workflow execution: {e}")
                if cli_params["verbose"]:
                    format_error(traceback.format_exc())
                live.stop()
                raise typer.Exit(code=1)

        format_section("Generation Summary")
        summary_items = {
            "CLAUDE.md": results.get("claude_md", "Not Run / Skipped"),
            "Custom commands": results.get("commands", "Not Run / Skipped"),
            "MCP config": results.get("mcp_config", "Not Run / Skipped"),
            "Settings": results.get("settings", "Not Run / Skipped"),
            "Action Plan": results.get("action_plan", "Not Run / Skipped"),
        }
        format_summary("Generated Assets", summary_items)

        if cli_params["dry_run"]:
            format_warning("Dry run: No files were written.")
        format_section("Next Steps")
        format_info("1. Review generated files in your project directory.")
        format_info("2. Customize CLAUDE.md and other configuration files as needed.")
        format_info(
            f'3. Run Claude Code: `cd "{cli_params["project_path"]}" && claude` (or your claude-code alias)'
        )
        if not cli_params["dry_run"]:
            format_success("\nBootstrap complete!")

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        format_error(f"File not found: {e.filename}")
        if cli_params.get("verbose", False):
            format_error(traceback.format_exc())
        raise typer.Exit(code=1)
    except PermissionError as e:
        format_error(
            f"Permission denied: {e.filename if hasattr(e, 'filename') else str(e)}"
        )
        if cli_params.get("verbose", False):
            format_error(traceback.format_exc())
        raise typer.Exit(code=1)
    except ValueError as e:
        format_error(f"Invalid value or configuration: {e}")
        if cli_params.get("verbose", False):
            format_error(traceback.format_exc())
        raise typer.Exit(code=1)
    except Exception as e:
        format_error(f"An unexpected error occurred: {e}")
        if cli_params.get("verbose", False):
            format_error(traceback.format_exc())
        else:
            format_info("Run with --verbose for more detailed error information.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
