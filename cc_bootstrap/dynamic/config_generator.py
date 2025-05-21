"""
Dynamic config generator module for creating configuration files.
"""

import json
import logging
import os
import re
import ast
from typing import Dict, Any, Optional

from cc_bootstrap.config import MCP_JSON_PATH, CLAUDE_DIR_PATH, SETTINGS_JSON_PATH
from cc_bootstrap.file_system_utils import FileSystemUtils
from cc_bootstrap.llm_interface import LLMInterface


class ConfigGenerator:
    """Generator for configuration files based on project context."""

    def __init__(
        self, llm: LLMInterface, fs_utils: FileSystemUtils, context: Dict[str, Any]
    ):
        """
        Initialize the config generator.

        Args:
            llm: LLM interface for generating content (used for settings, not MCP config)
            fs_utils: File system utilities for file operations
            context: Project context
        """
        self.logger = logging.getLogger(__name__)
        self.llm = llm
        self.fs_utils = fs_utils
        self.context = context

    def _parse_stdio_function(
        self, stdio_function_str: str, config_schema: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a JavaScript stdioFunction string into command, args, and env.
        """
        self.logger.debug(f"Attempting to parse stdioFunction: {stdio_function_str}")
        if not stdio_function_str:
            return None

        match = re.search(
            r"command:\s*['\"](?P<command>[^'\"]+)['\"],\s*"
            r"args:\s*(?P<args>\[.*?\])"
            r"(?:,\s*env:\s*(?P<env>\{.*?\})\s*)?",
            stdio_function_str,
            re.DOTALL,
        )

        if not match:
            self.logger.warning(
                f"Could not parse stdioFunction with main regex: {stdio_function_str}"
            )
            return None

        parsed_config: Dict[str, Any] = {}
        try:
            command_val = match.group("command")
            if command_val:
                parsed_config["command"] = command_val
                self.logger.debug(f"Parsed command: {command_val}")
            else:
                self.logger.warning("Command part not found or empty in stdioFunction.")

            args_str = match.group("args")
            self.logger.debug(f"Raw args string from regex: {args_str}")
            if args_str:
                temp_args_str_json = args_str
                if "'" in temp_args_str_json and '"' not in temp_args_str_json:
                    temp_args_str_json = temp_args_str_json.replace("'", '"')
                try:
                    parsed_args = json.loads(temp_args_str_json)
                    if isinstance(parsed_args, list) and all(
                        isinstance(arg, str) for arg in parsed_args
                    ):
                        parsed_config["args"] = parsed_args
                        self.logger.debug(f"Parsed args via json.loads: {parsed_args}")
                    else:
                        self.logger.warning(
                            f"Args parsed via json.loads but failed type check: {parsed_args}"
                        )
                except json.JSONDecodeError:
                    try:
                        parsed_args_ast = ast.literal_eval(args_str)
                        if isinstance(parsed_args_ast, list) and all(
                            isinstance(arg, str) for arg in parsed_args_ast
                        ):
                            parsed_config["args"] = parsed_args_ast
                            self.logger.debug(
                                f"Parsed args via ast.literal_eval: {parsed_args_ast}"
                            )
                        else:
                            self.logger.warning(
                                f"Args parsed via ast.literal_eval but failed type check: {parsed_args_ast}"
                            )
                    except (ValueError, SyntaxError, TypeError) as e_ast:
                        self.logger.error(
                            f"Failed to parse args string '{args_str}': {e_ast}"
                        )
            else:
                self.logger.warning("Args part not found or empty in stdioFunction.")

            env_str = match.group("env")
            self.logger.debug(f"Raw env string from regex: {env_str}")
            if env_str:
                parsed_env: Dict[str, Any] = {}
                pattern_env = (
                    r"'?(?P<key>\w+)'?\s*:\s*"
                    r"(?P<valueSource>config\.\w+|process\.env\.\w+|['\"].*?['\"]|[0-9.]+)"
                )
                for m in re.finditer(pattern_env, env_str):
                    key = m.group("key")
                    value_source_str = m.group("valueSource").strip()
                    placeholder = f"YOUR_{key.upper()}_HERE"
                    env_value_to_set: Any = placeholder

                    if value_source_str.startswith("config."):
                        config_var_name = value_source_str.split(".", 1)[1]
                        env_from_os = os.environ.get(key.upper()) or os.environ.get(
                            config_var_name.upper()
                        )
                        if env_from_os:
                            env_value_to_set = env_from_os
                            self.logger.info(
                                f"Found env var {key} from config.{config_var_name}"
                            )
                        elif (
                            config_schema
                            and "properties" in config_schema
                            and config_var_name in config_schema["properties"]
                        ):
                            env_value_to_set = (
                                f"YOUR_{config_var_name.upper()}_FROM_CONFIG_SCHEMA"
                            )
                            self.logger.info(
                                f"Using placeholder for env var {key} from config schema"
                            )
                        else:
                            self.logger.warning(
                                f"Config variable '{config_var_name}' for env key '{key}' not found in schema."
                            )
                    elif value_source_str.startswith("process.env."):
                        env_var_name = value_source_str.split("process.env.", 1)[1]
                        env_from_os = os.environ.get(env_var_name) or os.environ.get(
                            key.upper()
                        )
                        if env_from_os:
                            env_value_to_set = env_from_os
                            self.logger.info(
                                f"Found env var {env_var_name} from process.env"
                            )
                        else:
                            env_value_to_set = (
                                f"YOUR_{env_var_name.upper()}_FROM_PROCESS_ENV"
                            )
                            self.logger.info(
                                f"Using placeholder for process.env env var {env_var_name}"
                            )
                    elif (
                        value_source_str.startswith("'")
                        and value_source_str.endswith("'")
                    ) or (
                        value_source_str.startswith('"')
                        and value_source_str.endswith('"')
                    ):
                        env_value_to_set = value_source_str[1:-1]
                    else:
                        try:
                            env_value_to_set = json.loads(value_source_str)
                        except json.JSONDecodeError:
                            self.logger.warning(
                                f"Env value '{value_source_str}' not recognized; using literal"
                            )
                            env_value_to_set = value_source_str

                    parsed_env[key] = env_value_to_set

                if parsed_env:
                    parsed_config["env"] = parsed_env
                    self.logger.debug(f"Parsed env: {parsed_env}")

            self.logger.debug(
                f"Final parsed_config from stdioFunction: {parsed_config}"
            )
            return parsed_config

        except Exception as e:
            self.logger.error(f"Error parsing stdioFunction: {e}", exc_info=True)
            return None

    def generate_mcp_config(self) -> str:
        """
        Generate the .mcp.json file based on Smithery API data.
        Prioritizes stdio connections and attempts to parse stdioFunction.
        The top-level key in .mcp.json will be "mcpServers".
        """
        if (
            self.fs_utils.file_exists(MCP_JSON_PATH)
            and not self.fs_utils.force_overwrite
        ):
            self.logger.info(
                f"{MCP_JSON_PATH} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        mcp_server_configs = {}
        fetched_smithery_configs = self.context.get("fetched_smithery_mcp_configs", {})

        if fetched_smithery_configs:
            self.logger.info(
                f"Processing Smithery data for {len(fetched_smithery_configs)} specified servers to build .mcp.json"
            )
            for q_name, server_details in fetched_smithery_configs.items():
                if not server_details or not server_details.get(
                    "raw_smithery_response"
                ):
                    self.logger.warning(
                        f"No valid Smithery data found for '{q_name}'. Skipping for .mcp.json."
                    )
                    continue

                smithery_data = server_details["raw_smithery_response"]
                connections = smithery_data.get("connections", [])

                if not connections:
                    self.logger.warning(
                        f"No connections found for Smithery server '{q_name}'. Skipping for .mcp.json."
                    )
                    continue

                actual_qualified_name = smithery_data.get("qualifiedName", q_name)
                server_key = actual_qualified_name

                connection_configured = False

                stdio_conn_to_use = None
                for conn in connections:
                    if conn.get("type") == "stdio":
                        stdio_conn_to_use = conn
                        break

                if stdio_conn_to_use:
                    config_entry = {
                        "transport": "stdio",
                        "description": smithery_data.get(
                            "displayName", actual_qualified_name
                        ),
                        "startupTimeoutMillis": 10000,
                    }

                    if stdio_conn_to_use.get("command"):
                        config_entry["command"] = stdio_conn_to_use.get("command")
                    if stdio_conn_to_use.get("args"):
                        config_entry["args"] = stdio_conn_to_use.get("args")

                    if (
                        "command" not in config_entry or "args" not in config_entry
                    ) and stdio_conn_to_use.get("stdioFunction"):
                        self.logger.info(
                            f"Attempting to parse stdioFunction for {actual_qualified_name}"
                        )
                        parsed_stdio = self._parse_stdio_function(
                            stdio_conn_to_use.get("stdioFunction"),
                            stdio_conn_to_use.get("configSchema"),
                        )
                        if parsed_stdio:
                            self.logger.info(
                                f"Successfully parsed stdioFunction for {actual_qualified_name}: {parsed_stdio}"
                            )
                            if "command" in parsed_stdio:
                                config_entry["command"] = parsed_stdio["command"]
                            if "args" in parsed_stdio:
                                config_entry["args"] = parsed_stdio["args"]
                            if "env" in parsed_stdio:
                                config_entry["env"] = parsed_stdio["env"]
                        else:
                            self.logger.warning(
                                f"Failed to parse stdioFunction for {actual_qualified_name}"
                            )

                    if stdio_conn_to_use.get("cwd"):
                        config_entry["cwd"] = stdio_conn_to_use.get("cwd")

                    if "command" in config_entry and "args" in config_entry:
                        mcp_server_configs[server_key] = config_entry
                        self.logger.info(
                            f"Configured MCP server '{actual_qualified_name}' (key: {server_key}) in .mcp.json using stdio connection."
                        )
                        connection_configured = True
                    else:
                        self.logger.warning(
                            f"Stdio connection found for '{actual_qualified_name}' but could not determine command/args after attempting to parse stdioFunction. Skipping stdio."
                        )

                if not connection_configured:
                    http_conn_to_use = None
                    for conn in connections:
                        if conn.get("type") == "http":
                            http_url = conn.get("deploymentUrl") or conn.get("url")
                            if http_url:
                                http_conn_to_use = conn
                                break

                    if http_conn_to_use:
                        http_url = http_conn_to_use.get(
                            "deploymentUrl"
                        ) or http_conn_to_use.get("url")
                        mcp_server_configs[server_key] = {
                            "transport": "http",
                            "url": http_url,
                            "description": smithery_data.get(
                                "displayName", actual_qualified_name
                            ),
                            "startupTimeoutMillis": 10000,
                        }
                        self.logger.info(
                            f"Configured MCP server '{actual_qualified_name}' (key: {server_key}) in .mcp.json using HTTP connection: {http_url}"
                        )
                        connection_configured = True

                if not connection_configured:
                    self.logger.warning(
                        f"No usable stdio (with command/args) or HTTP (with url/deploymentUrl) connection found for '{q_name}' (resolved to '{actual_qualified_name}'). Skipping for .mcp.json configuration."
                    )
        else:
            self.logger.info(
                "No Smithery servers specified or found. .mcp.json will have no servers configured from Smithery."
            )

        mcp_config_final = {"mcpServers": mcp_server_configs}

        try:
            success = self.fs_utils.write_file(
                MCP_JSON_PATH, json.dumps(mcp_config_final, indent=4)
            )
            if success:
                self.logger.info(
                    f"Successfully generated {MCP_JSON_PATH} with {len(mcp_server_configs)} servers"
                )
                return "Success"
            else:
                self.logger.error(f"Failed to write {MCP_JSON_PATH}")
                return f"Failed to write {MCP_JSON_PATH}"
        except Exception as e:
            self.logger.exception(f"Error generating {MCP_JSON_PATH}: {e}")
            return f"Error: {str(e)}"

    def generate_settings(self) -> str:
        """
        Generate the .claude/settings.json file.
        Updates allowedTools based on servers configured in .mcp.json.
        """
        if (
            self.fs_utils.file_exists(SETTINGS_JSON_PATH)
            and not self.fs_utils.force_overwrite
        ):
            self.logger.info(
                f"{SETTINGS_JSON_PATH} already exists and force_overwrite is False, skipping."
            )
            return "Skipped"

        try:
            if not self.fs_utils.ensure_directory(CLAUDE_DIR_PATH):
                return f"Failed to create directory {CLAUDE_DIR_PATH}"

            template_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "templates",
                "defaults",
                "settings.json",
            )

            settings_data = {}
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    try:
                        settings_data = json.load(f)
                    except json.JSONDecodeError as e:
                        self.logger.error(
                            f"Error parsing default settings template {template_path}: {e}. Using hardcoded defaults."
                        )
            else:
                self.logger.warning(
                    f"Default settings template not found at {template_path}, using hardcoded defaults."
                )

            if not settings_data:
                settings_data = {
                    "theme": "dark",
                    "allowedTools": ["Read", "LS", "Grep"],
                    "autoApproveTools": ["Read", "LS", "Grep"],
                    "defaultAllowedBranches": ["main"],
                    "showPrompt": False,
                    "telemetry": {"disabled": False},
                }

            if "allowedTools" not in settings_data or not isinstance(
                settings_data["allowedTools"], list
            ):
                settings_data["allowedTools"] = ["Read", "LS", "Grep"]

            mcp_config_content = self.fs_utils.read_file(MCP_JSON_PATH)
            if mcp_config_content:
                try:
                    mcp_data = json.loads(mcp_config_content)
                    if (
                        mcp_data
                        and "mcpServers" in mcp_data
                        and isinstance(mcp_data["mcpServers"], dict)
                    ):
                        for server_key in mcp_data["mcpServers"].keys():
                            permission_key_segment = server_key.replace(
                                "/", "_"
                            ).replace("@", "")
                            permission_string = f"mcp__{permission_key_segment}__*"
                            if permission_string not in settings_data["allowedTools"]:
                                settings_data["allowedTools"].append(permission_string)
                                self.logger.info(
                                    f"Added MCP tool permission: {permission_string} (derived from server key: {server_key})"
                                )
                    else:
                        self.logger.warning(
                            f"'{MCP_JSON_PATH}' does not contain a 'mcpServers' dictionary. Cannot update allowedTools."
                        )
                except json.JSONDecodeError:
                    self.logger.warning(
                        f"Could not parse {MCP_JSON_PATH} to update allowedTools in settings.json."
                    )

            settings_content_final = json.dumps(settings_data, indent=2)

            success = self.fs_utils.write_file(
                SETTINGS_JSON_PATH, settings_content_final
            )
            if success:
                self.logger.info(f"Successfully generated {SETTINGS_JSON_PATH}")
                return "Success"
            else:
                self.logger.error(f"Failed to write {SETTINGS_JSON_PATH}")
                return f"Failed to write {SETTINGS_JSON_PATH}"

        except Exception as e:
            self.logger.exception(f"Error generating {SETTINGS_JSON_PATH}: {e}")
            return f"Error: {str(e)}"
