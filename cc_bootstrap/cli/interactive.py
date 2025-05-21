"""
Interactive CLI components module.

This module provides utility functions for creating interactive CLI components
such as prompts, confirmations, and selection menus using the Rich library.
"""

from typing import Any, Dict, List, Optional
import os

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

from cc_bootstrap.config import (
    ENV_ANTHROPIC_API_KEY,
    ENV_PERPLEXITY_API_KEY,
    ENV_SMITHERY_API_KEY,
    ENV_AWS_REGION,
    ENV_AWS_PROFILE,
    LLM_PROVIDERS,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_THINKING_ENABLED,
    DEFAULT_THINKING_BUDGET,
)


console = Console()


def prompt_input(
    message: str,
    default: Optional[str] = None,
    password: bool = False,
    sensitive: bool = False,
) -> str:
    """
    Prompt the user for input.

    Args:
        message: The prompt message.
        default: The default value if the user doesn't provide input.
        password: Whether to hide the input (for passwords).
        sensitive: Whether the input is sensitive (like API keys) and should not be displayed.

    Returns:
        The user's input.
    """

    if sensitive and default:
        display_default = "********"
        result = Prompt.ask(
            f"[bold cyan]{message}[/bold cyan]",
            default=display_default,
            password=password,
        )

        if result == display_default:
            return default
        return result
    else:
        return Prompt.ask(
            f"[bold cyan]{message}[/bold cyan]", default=default, password=password
        )


def prompt_yes_no(message: str, default: bool = False) -> bool:
    """
    Prompt the user for a yes/no response.

    Args:
        message: The prompt message.
        default: The default value if the user doesn't provide input.

    Returns:
        True for yes, False for no.
    """
    return Confirm.ask(f"[bold cyan]{message}[/bold cyan]", default=default)


def prompt_choice(
    message: str,
    choices: List[str],
    default: Optional[int] = None,
) -> str:
    """
    Prompt the user to select from a list of choices.

    Args:
        message: The prompt message.
        choices: The list of choices.
        default: The default choice index (1-based) if the user doesn't provide input.

    Returns:
        The selected choice.
    """
    console.print(f"[bold cyan]{message}[/bold cyan]")

    for i, choice_text in enumerate(choices, 1):
        console.print(f"  {i}. {choice_text}")

    default_str = str(default) if default is not None else None

    choice_prompt_text = (
        f"[bold cyan]Enter your choice (number 1-{len(choices)})[/bold cyan]"
    )

    while True:
        choice_idx_str = Prompt.ask(choice_prompt_text, default=default_str)
        try:
            choice_idx = int(choice_idx_str)
            if 1 <= choice_idx <= len(choices):
                return choices[choice_idx - 1]
        except ValueError:
            pass

        console.print("[bold red]Invalid choice. Please try again.[/bold red]")


def confirm_action(
    action: str, consequences: Optional[str] = None, default: bool = False
) -> bool:
    """
    Ask for confirmation before performing a potentially destructive action.

    Args:
        action: The action to confirm.
        consequences: Optional description of the consequences.
        default: The default value if the user doesn't provide input.

    Returns:
        True if confirmed, False otherwise.
    """
    message = f"[bold yellow]Are you sure you want to {action}?[/bold yellow]"

    if consequences:
        console.print(
            Panel(f"[bold red]Warning:[/bold red] {consequences}", border_style="red")
        )

    return Confirm.ask(message, default=default)


def prompt_skip_options(
    current_cli_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, bool]:
    """
    Prompt for skip options in a grouped manner.
    Uses current_cli_params to suggest defaults if available.

    Args:
        current_cli_params: Dictionary of current CLI parameters.

    Returns:
        Dictionary with skip configuration options.
    """
    skip_options = {}

    default_skip_commands = (
        current_cli_params.get("skip_commands", False) if current_cli_params else False
    )
    default_skip_mcp = (
        current_cli_params.get("skip_mcp_config", False)
        if current_cli_params
        else False
    )

    default_input_str = ""
    if default_skip_commands:
        default_input_str += "c"
    if default_skip_mcp:
        default_input_str += "m"

    console.print("[bold cyan]Skip generation options:[/bold cyan]")
    skip_input = prompt_input(
        "Skip generation for: \\[c]ommands, \\[m]cp config? (enter letters or leave empty, e.g., cm)",
        default=default_input_str,
    ).lower()

    skip_options["skip_commands"] = "c" in skip_input
    skip_options["skip_mcp_config"] = "m" in skip_input

    if any(skip_options.values()):
        selected = []
        if skip_options["skip_commands"]:
            selected.append("commands")
        if skip_options["skip_mcp_config"]:
            selected.append("MCP config")
        if selected:
            console.print(
                f"[yellow]Will skip generating: {', '.join(selected)}[/yellow]"
            )

    return skip_options


def prompt_for_project_config(
    current_cli_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Interactive prompt for project configuration.

    Args:
        current_cli_params: Dictionary of current CLI parameters, used for defaults.

    Returns:
        Dictionary with project configuration choices made by the user.
    """
    console.print(
        Panel.fit("[bold blue]Project Configuration[/bold blue]", border_style="blue")
    )

    interactive_choices: Dict[str, Any] = {}

    def get_prompt_default(key: str, fallback_if_none_from_cli: Any) -> Any:
        if current_cli_params:
            val_from_cli = current_cli_params.get(key)

            if val_from_cli is not None:
                return val_from_cli
        return fallback_if_none_from_cli

    setup_mode = prompt_choice(
        "Choose setup mode:",
        [
            "Quick Setup (minimal questions, sensible defaults)",
            "Advanced Setup (all configuration options)",
        ],
        default=1,
    )
    is_quick_setup = "Quick" in setup_mode

    interactive_choices["project_path"] = prompt_input(
        "Enter the path to the target project folder",
        default=str(get_prompt_default("project_path", ".")),
    )

    interactive_choices["project_plan_file"] = prompt_input(
        "Enter the path to the project specification/plan file (e.g., plan.md)",
        default=str(get_prompt_default("project_plan_file", "")),
    )

    if is_quick_setup:
        console.print(
            "[bold green]Using Quick Setup with the following configuration (CLI args override defaults):[/bold green]"
        )

        interactive_choices["use_claude_squad"] = get_prompt_default(
            "use_claude_squad", False
        )
        interactive_choices["smithery_mcp_servers"] = get_prompt_default(
            "smithery_mcp_servers", ""
        )
        interactive_choices["smithery_api_key"] = get_prompt_default(
            "smithery_api_key", os.environ.get(ENV_SMITHERY_API_KEY, "")
        )
        interactive_choices["use_perplexity"] = get_prompt_default(
            "use_perplexity", False
        )

        if interactive_choices["use_perplexity"]:
            interactive_choices["perplexity_api_key"] = get_prompt_default(
                "perplexity_api_key", None
            )
        else:
            interactive_choices["perplexity_api_key"] = None

        quick_llm_provider = get_prompt_default("llm_provider", DEFAULT_LLM_PROVIDER)
        interactive_choices["llm_provider"] = quick_llm_provider

        provider_config_qs = LLM_PROVIDERS[quick_llm_provider]
        cli_llm_model = get_prompt_default("llm_model", None)
        interactive_choices["llm_model"] = (
            cli_llm_model if cli_llm_model else provider_config_qs["default_model"]
        )

        if interactive_choices["llm_provider"] == "anthropic":
            interactive_choices["api_key"] = get_prompt_default(
                "api_key", os.environ.get(ENV_ANTHROPIC_API_KEY, "")
            )
        else:
            default_bedrock_region = provider_config_qs.get(
                "default_region", "us-west-2"
            )
            interactive_choices["aws_region"] = get_prompt_default(
                "aws_region", os.environ.get(ENV_AWS_REGION, default_bedrock_region)
            )
            interactive_choices["aws_profile"] = get_prompt_default(
                "aws_profile", os.environ.get(ENV_AWS_PROFILE, "")
            )

        interactive_choices["enable_thinking"] = get_prompt_default(
            "enable_thinking",
            provider_config_qs.get(
                "default_thinking_enabled", DEFAULT_THINKING_ENABLED
            ),
        )
        interactive_choices["thinking_budget"] = get_prompt_default(
            "thinking_budget",
            provider_config_qs.get("default_thinking_budget", DEFAULT_THINKING_BUDGET),
        )

        interactive_choices["skip_commands"] = get_prompt_default(
            "skip_commands", False
        )
        interactive_choices["skip_mcp_config"] = get_prompt_default(
            "skip_mcp_config", False
        )
        interactive_choices["force_overwrite"] = get_prompt_default(
            "force_overwrite", False
        )
        interactive_choices["dry_run"] = get_prompt_default("dry_run", False)
        interactive_choices["verbose"] = get_prompt_default("verbose", False)

        console.print(
            f"- [cyan]Project Path:[/cyan] {interactive_choices['project_path']}"
        )
        console.print(
            f"- [cyan]Project Plan File:[/cyan] {interactive_choices['project_plan_file']}"
        )
        console.print(
            f"- [cyan]LLM Provider:[/cyan] {LLM_PROVIDERS[interactive_choices['llm_provider']]['name']}"
        )
        console.print(f"- [cyan]LLM Model:[/cyan] {interactive_choices['llm_model']}")
        thinking_status = (
            "Enabled" if interactive_choices["enable_thinking"] else "Disabled"
        )
        if interactive_choices["enable_thinking"]:
            thinking_status += f" (Budget: {interactive_choices['thinking_budget']})"
        console.print(f"- [cyan]Extended Thinking:[/cyan] {thinking_status}")
        console.print(
            f"- [cyan]Claude Squad:[/cyan] {'Enabled' if interactive_choices['use_claude_squad'] else 'Disabled'}"
        )
        mcp_display = (
            interactive_choices["smithery_mcp_servers"]
            if interactive_choices["smithery_mcp_servers"]
            else "Default tools only"
        )
        console.print(f"- [cyan]Smithery MCP Servers:[/cyan] {mcp_display}")
        console.print(
            f"- [cyan]Perplexity API:[/cyan] {'Enabled' if interactive_choices['use_perplexity'] else 'Disabled'}"
        )
        skip_display_parts = []
        if interactive_choices["skip_commands"]:
            skip_display_parts.append("commands")
        if interactive_choices["skip_mcp_config"]:
            skip_display_parts.append("MCP config")
        skip_display = (
            ", ".join(skip_display_parts)
            if skip_display_parts
            else "Generate all assets"
        )
        console.print(f"- [cyan]Skip Options:[/cyan] {skip_display}")
        console.print(
            f"- [cyan]Force Overwrite:[/cyan] {'Yes' if interactive_choices['force_overwrite'] else 'No'}"
        )
        console.print(
            f"- [cyan]Dry Run:[/cyan] {'Yes' if interactive_choices['dry_run'] else 'No'}"
        )
        console.print(
            f"- [cyan]Verbose Output:[/cyan] {'Yes' if interactive_choices['verbose'] else 'No'}"
        )

        if not prompt_yes_no("Continue with this configuration?", default=True):
            console.print("[yellow]Switching to Advanced Setup...[/yellow]")
            is_quick_setup = False

    if not is_quick_setup:
        console.print("\n[bold cyan]Feature options:[/bold cyan]")
        interactive_choices["use_claude_squad"] = prompt_yes_no(
            "Generate assets for Claude Squad (parallel work planning)?",
            default=get_prompt_default("use_claude_squad", False),
        )
        interactive_choices["smithery_mcp_servers"] = prompt_input(
            "Enter Smithery MCP server names or search terms (comma-separated, e.g., 'owner/repo,exa,search term')",
            default=get_prompt_default("smithery_mcp_servers", ""),
        )
        if interactive_choices["smithery_mcp_servers"]:
            default_smithery_key = get_prompt_default(
                "smithery_api_key", os.environ.get(ENV_SMITHERY_API_KEY, "")
            )
            interactive_choices["smithery_api_key"] = prompt_input(
                "Enter your Smithery API key (press Enter to use env var if set, needed for Smithery servers)",
                default=default_smithery_key,
                password=True,
                sensitive=True,
            )
            if not interactive_choices["smithery_api_key"]:
                console.print(
                    "[yellow]Smithery API key not provided. Will not be able to fetch server details from Smithery.[/yellow]"
                )
        interactive_choices["use_perplexity"] = prompt_yes_no(
            "Use Perplexity API for research?",
            default=get_prompt_default("use_perplexity", False),
        )
        if interactive_choices["use_perplexity"]:
            default_key = get_prompt_default(
                "perplexity_api_key", os.environ.get(ENV_PERPLEXITY_API_KEY, "")
            )
            interactive_choices["perplexity_api_key"] = prompt_input(
                "Enter your Perplexity API key (press Enter to use env var if set)",
                default=default_key,
                password=True,
                sensitive=True,
            )
            if not interactive_choices["perplexity_api_key"]:
                console.print(
                    "[yellow]Perplexity API key not provided. Disabling Perplexity research.[/yellow]"
                )
                interactive_choices["use_perplexity"] = False

        provider_choices_map = {
            data["name"]: key for key, data in LLM_PROVIDERS.items()
        }
        provider_display_choices = list(provider_choices_map.keys())

        cli_provider_key = get_prompt_default("llm_provider", DEFAULT_LLM_PROVIDER)
        cli_provider_name = LLM_PROVIDERS[cli_provider_key]["name"]
        default_provider_idx = (
            provider_display_choices.index(cli_provider_name) + 1
            if cli_provider_name in provider_display_choices
            else 1
        )

        selected_provider_name = prompt_choice(
            "Select LLM provider:",
            provider_display_choices,
            default=default_provider_idx,
        )
        interactive_choices["llm_provider"] = provider_choices_map[
            selected_provider_name
        ]

        provider_config_adv = LLM_PROVIDERS[interactive_choices["llm_provider"]]

        cli_llm_model_adv = get_prompt_default("llm_model", None)
        prompt_default_llm_model = provider_config_adv["default_model"]
        if (
            cli_llm_model_adv
            and interactive_choices["llm_provider"] == cli_provider_key
        ):
            prompt_default_llm_model = cli_llm_model_adv

        interactive_choices["llm_model"] = prompt_input(
            f"Enter LLM model ID for {provider_config_adv['name']} (default: {provider_config_adv['default_model']})",
            default=prompt_default_llm_model,
        )

        if interactive_choices["llm_provider"] == "anthropic":
            default_anthropic_key = get_prompt_default(
                "api_key", os.environ.get(ENV_ANTHROPIC_API_KEY, "")
            )
            interactive_choices["api_key"] = prompt_input(
                "Enter your Anthropic API key (press Enter to use env var if set)",
                default=default_anthropic_key,
                password=True,
                sensitive=True,
            )
            if not interactive_choices["api_key"]:
                console.print(
                    f"[bold red]Anthropic API key is required for {provider_config_adv['name']}. Please set {ENV_ANTHROPIC_API_KEY} or provide it.[/bold red]"
                )
        else:
            default_aws_region = get_prompt_default(
                "aws_region",
                os.environ.get(
                    ENV_AWS_REGION,
                    provider_config_adv.get("default_region", "us-west-2"),
                ),
            )
            interactive_choices["aws_region"] = prompt_input(
                "Enter AWS region for Bedrock:", default=default_aws_region
            )
            default_aws_profile = get_prompt_default(
                "aws_profile", os.environ.get(ENV_AWS_PROFILE, "")
            )
            interactive_choices["aws_profile"] = prompt_input(
                "Enter AWS profile name for Bedrock (leave empty for default profile/credentials chain):",
                default=default_aws_profile,
            )

        interactive_choices["enable_thinking"] = prompt_yes_no(
            "Enable extended thinking/reasoning for the LLM?",
            default=get_prompt_default(
                "enable_thinking",
                provider_config_adv.get(
                    "default_thinking_enabled", DEFAULT_THINKING_ENABLED
                ),
            ),
        )
        if interactive_choices["enable_thinking"]:
            default_thinking_budget = get_prompt_default(
                "thinking_budget",
                provider_config_adv.get(
                    "default_thinking_budget", DEFAULT_THINKING_BUDGET
                ),
            )
            interactive_choices["thinking_budget"] = int(
                prompt_input(
                    "Enter token budget for thinking:",
                    default=str(default_thinking_budget),
                )
            )
        else:
            interactive_choices["thinking_budget"] = 0

        skip_opts_adv = prompt_skip_options(current_cli_params)
        interactive_choices["skip_commands"] = skip_opts_adv.get(
            "skip_commands", get_prompt_default("skip_commands", False)
        )
        interactive_choices["skip_mcp_config"] = skip_opts_adv.get(
            "skip_mcp_config", get_prompt_default("skip_mcp_config", False)
        )

        console.print("\n[bold cyan]Execution options:[/bold cyan]")
        interactive_choices["force_overwrite"] = prompt_yes_no(
            "Force overwrite existing files?",
            default=get_prompt_default("force_overwrite", False),
        )
        interactive_choices["dry_run"] = prompt_yes_no(
            "Perform a dry run (no files will be written)?",
            default=get_prompt_default("dry_run", False),
        )
        interactive_choices["verbose"] = prompt_yes_no(
            "Enable verbose output?", default=get_prompt_default("verbose", False)
        )

    return interactive_choices


def display_help_menu() -> None:
    """Display the help menu with common commands and examples."""
    console.print(
        Panel.fit(
            "[bold blue]CC-Bootstrap Help[/bold blue]\n"
            "[italic]A tool for bootstrapping Claude Code configuration files[/italic]",
            border_style="blue",
        )
    )

    console.print("\n[bold cyan]Common Usage Examples:[/bold cyan]")
    console.print(
        "  cc-bootstrap bootstrap --project-path ./my-project --project-plan-file ./plan.md"
    )
    console.print(
        "  cc-bootstrap bootstrap -p ./my-proj -project-plan-file ./plan.md --mcp-tools-config jira,postgres,web_search"
    )
    console.print(
        "  cc-bootstrap bootstrap -p ./my-proj -project-plan-file ./plan.md --skip-commands"
    )
    console.print(
        "  cc-bootstrap bootstrap -p ./my-proj -project-plan-file ./plan.md --llm-provider bedrock --aws-region us-west-2"
    )
    console.print(
        "  cc-bootstrap bootstrap -p ./my-proj -project-plan-file ./plan.md --enable-thinking --thinking-budget 10000"
    )
    console.print(
        "  cc-bootstrap bootstrap -p ./my-proj -project-plan-file ./plan.md --llm-model anthropic.claude-3-opus-20240229-v1:0 --llm-provider bedrock"
    )

    console.print("\n[bold cyan]Interactive Mode:[/bold cyan]")
    console.print("  cc-bootstrap --interactive  (or cc-bootstrap -i)")

    console.print("\n[bold cyan]Other Commands:[/bold cyan]")
    console.print("  cc-bootstrap show-examples")

    console.print("\n[bold cyan]For more information:[/bold cyan]")
    console.print("  cc-bootstrap --help")
    console.print("  cc-bootstrap bootstrap --help")
    console.print("  cc-bootstrap --version")
