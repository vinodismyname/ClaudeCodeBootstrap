"""
Smithery API client for fetching MCP server configurations.

This module provides functions to interact with the Smithery Registry API
to fetch MCP server configurations and schemas, as well as search for servers.
"""

import logging
import requests
from typing import Dict, List, Optional, Any

from cc_bootstrap.config import SMITHERY_API_BASE_URL


logger = logging.getLogger(__name__)


def get_mcp_server_config_schema(
    qualified_name: str, api_token: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch the configuration schema for an MCP server from Smithery Registry.

    Args:
        qualified_name: The qualified name of the MCP server (e.g., 'owner/repo')
        api_token: The Smithery API token

    Returns:
        A dictionary containing the server details including config schema, or None if not found
    """
    logger.info(f"Fetching MCP server config schema for: {qualified_name}")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    url = f"{SMITHERY_API_BASE_URL}/servers/{qualified_name}"

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        server_data = response.json()
        logger.debug(f"Received server data for {qualified_name}")

        http_conn = None
        connections = server_data.get("connections", [])
        for conn in connections:
            if conn.get("type") == "http":
                http_conn = conn
                break

        if http_conn:
            return {
                "qualified_name": server_data.get("name", qualified_name),
                "display_name": server_data.get("displayName", qualified_name),
                "description": server_data.get("description", ""),
                "icon_url": server_data.get("iconUrl", ""),
                "config_schema": http_conn.get("configSchema", {}),
                "tools": server_data.get("tools", []),
                "connections": server_data.get("connections", []),
                "raw_smithery_response": server_data,
            }
        else:
            logger.warning(f"No HTTP connection found for server {qualified_name}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching server config for {qualified_name}: {e}")
        return None


def get_all_mcp_server_configs(
    server_queries: List[str], api_token: str
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch configuration schemas for multiple MCP servers, using search when needed.

    Args:
        server_queries: List of server names or search queries
        api_token: The Smithery API token

    Returns:
        Dictionary mapping server names to their configuration schemas
    """
    logger.info(f"Processing {len(server_queries)} MCP server queries")

    results = {}
    for query in server_queries:
        best_match = find_best_server_match(query, api_token)

        if best_match:
            server_config = get_mcp_server_config_schema(best_match, api_token)
            if server_config:
                results[query] = server_config
                if best_match != query:
                    results[query]["matched_from_query"] = True
                    results[query]["original_query"] = query
                    results[query]["matched_to"] = best_match
            else:
                results[query] = None
        else:
            results[query] = None

    return results


def search_mcp_servers(
    query: str, api_token: str, page_size: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for MCP servers in Smithery Registry using a query string.

    Args:
        query: The search query string
        api_token: The Smithery API token
        page_size: Number of results to return (default: 5)

    Returns:
        List of server information dictionaries
    """
    logger.info(f"Searching for MCP servers with query: {query}")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }

    encoded_query = requests.utils.quote(query)
    url = (
        f"{SMITHERY_API_BASE_URL}/servers?q={encoded_query}&page=1&pageSize={page_size}"
    )

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        search_results = response.json()
        servers = search_results.get("servers", [])
        logger.info(f"Found {len(servers)} servers matching query: {query}")

        return servers
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for MCP servers with query '{query}': {e}")
        return []


def find_best_server_match(query: str, api_token: str) -> Optional[str]:
    """
    Find the best matching server for a given query.

    Args:
        query: The server name or search query
        api_token: The Smithery API token

    Returns:
        The qualified name of the best matching server, or None if no match found
    """
    direct_result = get_mcp_server_config_schema(query, api_token)
    if direct_result:
        logger.info(f"Found exact match for '{query}'")
        return query

    search_results = search_mcp_servers(query, api_token)

    if not search_results:
        logger.warning(f"No servers found matching '{query}'")
        return None

    best_match = search_results[0]
    qualified_name = best_match.get("qualifiedName")

    logger.info(f"Best match for '{query}' is '{qualified_name}'")
    return qualified_name


def parse_config_schema_for_basic_info(config_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a config schema to extract basic information about required parameters.

    Args:
        config_schema: The configuration schema from Smithery

    Returns:
        Dictionary with parsed schema information
    """
    if not config_schema:
        return {"required_params": [], "params": {}}

    result = {"required_params": config_schema.get("required", []), "params": {}}

    properties = config_schema.get("properties", {})
    for param_name, param_details in properties.items():
        result["params"][param_name] = {
            "type": param_details.get("type", "unknown"),
            "description": param_details.get("description", ""),
            "default": param_details.get("default", ""),
            "enum": param_details.get("enum", []),
        }

    return result
