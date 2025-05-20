![Banner](assets/banner.png)
# **cc-bootstrap**: *Claude Code Project Bootstrapper*

[![PyPI version](https://img.shields.io/pypi/v/cc-bootstrap.svg)](https://pypi.org/project/cc-bootstrap/)
[![Python Versions](https://img.shields.io/pypi/pyversions/cc-bootstrap.svg)](https://pypi.org/project/cc-bootstrap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

`cc-bootstrap` is a Python command-line tool designed to automate and accelerate the setup of [Anthropic's Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), an agentic coding assistant that operates in your terminal. It intelligently generates essential configuration files for Claude Code by leveraging Large Language Models (LLMs) to analyze user-provided project plans and, optionally, existing project structures.

The idea behind `cc-bootstrap` is an **LLM-led inference approach**. You provide a high-level project plan and point the tool to your project directory. `cc-bootstrap` then uses an LLM (such as Claude Sonnet via Anthropic API or AWS Bedrock) to:
1.  Analyze your project plan and sample project files.
2.  Infer key characteristics like project purpose, technology stack, architecture, and common development patterns.
3.  Generate tailored configuration files specifically for Claude Code, imbuing it with relevant context from the start.

This significantly speeds up the onboarding process for Claude Code, ensuring it has a solid foundation of understanding about your project, leading to more effective and context-aware assistance.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Command Structure](#command-structure)
  - [Core Arguments](#core-arguments)
  - [Interactive Mode](#interactive-mode)
  - [Key CLI Options (Bootstrap Command)](#key-cli-options-bootstrap-command)
  - [Global Options](#global-options)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [The Project Plan File](#the-project-plan-file)
  - [Generated Files Overview](#generated-files-overview)
  - [Configuring MCP Tools](#configuring-mcp-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

✨ **Automated Configuration Generation**: Creates a comprehensive set of starting configuration files for Claude Code, including:
*   `CLAUDE.md`: For persistent project context, coding standards, and operational guidance.
*   `ACTION_PLAN.md`: A detailed, actionable plan for project implementation, adaptable for single Claude instances or [Claude Squads](https://docs.anthropic.com/en/docs/claude-code/tutorials/claude-squad).
*   `.claude/commands/`: A suite of categorized custom Markdown commands to automate common development tasks within Claude Code.
*   `.mcp.json`: Configuration for Model Context Protocol (MCP) servers, enabling Claude Code to interact with external tools and services. `cc-bootstrap` suggests relevant tools based on your project.
*   `.claude/settings.json`: Claude Code settings, including dynamically generated permissions for the configured MCP tools.

🧠 **LLM-Powered Analysis**: Utilizes powerful LLMs (Anthropic API, AWS Bedrock) to understand your project's nuances from a plan file and code samples.

🤖 **Interactive Mode**: Offers a user-friendly, guided CLI experience (`-i`) for easy configuration of generation parameters.

☁️ **Multiple LLM Provider Support**:
*   Anthropic API (default model: `claude-3-7-sonnet-20250219`)
*   AWS Bedrock (default model: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`)

🔍 **External Research Integration**: Optionally leverages the Perplexity API (`--use-perplexity`) to:
1.  Generate research questions based on your project plan.
2.  Query Perplexity for insights.
3.  Incorporate these findings into the generated assets (e.g., `CLAUDE.md`, `ACTION_PLAN.md`).

🤝 **Claude Squad Compatibility**: Can generate an `ACTION_PLAN.md` specifically structured for parallel development using Claude Squads (`--use-claude-squad`).

🤔 **Extended LLM Reasoning**: Supports enabling an LLM's "thinking" mode with a configurable token budget (`--enable-thinking`, `--thinking-budget`) for more sophisticated and nuanced content generation.

🛠️ **Customizable Output**:
*   `--force-overwrite`: Overwrite existing Claude Code configuration files.
*   `--skip-commands`, `--skip-mcp-config`: Selectively skip generating certain assets.
*   `--dry-run`: Preview intended actions and generated content without writing any files.

🔧 **MCP Tool Integration**: Allows specification of MCP tools to integrate via a comma-separated list or a JSON/YAML configuration file (`--mcp-tools-config`).

💻 **Modern CLI**: Built with Typer for a robust command-line interface and Rich for enhanced, user-friendly output and progress indicators.

📜 **Open Source**: Distributed under the MIT License.

## Installation

### Prerequisites

*   Python 3.11 or higher.

### Virtual Environment (Recommended)

It's highly recommended to install `cc-bootstrap` within a Python virtual environment to avoid conflicts with other projects or system-wide packages.

1.  Create a virtual environment (e.g., named `.venv`):
    ```bash
    python3 -m venv .venv
    ```

2.  Activate the virtual environment:
    *   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

### Installing `cc-bootstrap`

Install `cc-bootstrap` using pip:

```bash
pip install cc-bootstrap
```

### Post-Installation: API Keys

`cc-bootstrap` requires API keys for the LLM providers and optional research tools you intend to use. These are typically configured via environment variables. See the [Environment Variables](#environment-variables) section for details.

## Usage

### Command Structure

The primary command for `cc-bootstrap` is `bootstrap`:

```bash
cc-bootstrap bootstrap [OPTIONS]
```

### Core Arguments

*   `-p, --project-path DIRECTORY`: Path to the target project folder where Claude Code configurations will be generated. (Required unless in interactive mode).
*   `--project-plan-file FILE`: Path to your project specification or plan file (typically Markdown). This file is crucial for the LLM to understand your project. (Required unless in interactive mode).

### Interactive Mode

For a guided experience, you can run `cc-bootstrap` in interactive mode. It will prompt you for all necessary information and options.

```bash
cc-bootstrap -i
# or
cc-bootstrap bootstrap -i
```

If you run `cc-bootstrap -i` without specifying the `bootstrap` command, it will automatically invoke `bootstrap` in interactive mode.

### Key CLI Options (Bootstrap Command)

Here are some ofika the key options available for the `bootstrap` command:

*   **LLM Configuration**:
    *   `--llm-provider TEXT`: LLM provider to use (e.g., `anthropic`, `bedrock`). Default: `anthropic`.
    *   `--llm-model TEXT`: Specific LLM model ID to use. If not set, uses the provider's default.
    *   `--api-key TEXT`: Anthropic API key. Can also be set via `ANTHROPIC_API_KEY` environment variable.
    *   `--aws-region TEXT`: AWS region for Bedrock. Can also be set via `AWS_REGION` environment variable or AWS configuration.
    *   `--aws-profile TEXT`: AWS profile for Bedrock. Can also be set via `AWS_PROFILE` environment variable or AWS configuration.

*   **Feature Flags**:
    *   `--use-claude-squad / --no-use-claude-squad`: If set, generated assets (especially `ACTION_PLAN.md`) will include guidance for Claude Squad. Default: `no-use-claude-squad`.
    *   `--use-perplexity / --no-use-perplexity`: Use Perplexity API for research. Requires API key. Default: `no-use-perplexity`.
    *   `--perplexity-api-key TEXT`: Perplexity API key. Can also be set via `PERPLEXITY_API_KEY` environment variable.

*   **LLM Behavior**:
    *   `--enable-thinking / --disable-thinking`: Enable/disable extended thinking/reasoning for the LLM. Default: enabled (provider-specific).
    *   `--thinking-budget INTEGER`: Token budget for LLM thinking (if enabled). Default: `6000` (provider-specific).

*   **Output Control**:
    *   `--force-overwrite / --no-force-overwrite`: If set, existing Claude Code configuration files will be overwritten. Default: no overwrite.
    *   `--skip-commands / --generate-commands`: Skip generating custom commands. Default: generate commands.
    *   `--skip-mcp-config / --generate-mcp-config`: Skip generating MCP configuration. Default: generate MCP config.
    *   `--dry-run / --execute-run`: If set, prints intended actions and generated content without writing files. Default: execute run.

*   **MCP Tools**:
    *   `--mcp-tools-config TEXT`: Path to a JSON/YAML file defining MCP tools to integrate, or a comma-separated string of tool names (e.g., `web_search,github`). If empty, LLM will suggest default tools.

*   **Other**:
    *   `-v, --verbose`: Increase output verbosity for more detailed logging.
    *   `-i, --interactive`: Run bootstrap in interactive mode (overrides global interactive flag if set).

### Global Options

These options can be used with `cc-bootstrap` before specifying a command:

*   `-i, --interactive`: Run in interactive mode globally. If no command is specified, `bootstrap` will be run interactively.
*   `-v, --verbose`: Increase output verbosity globally.
*   `--version / -V`: Show `cc-bootstrap` version and exit.
*   `--help`: Show the main help message and exit. Use `cc-bootstrap bootstrap --help` for command-specific help.

## Configuration

### Environment Variables

`cc-bootstrap` uses environment variables for sensitive information like API keys and cloud configurations:

*   `ANTHROPIC_API_KEY`: Your Anthropic API key. Required if using the `anthropic` LLM provider and not passing via `--api-key`.
*   `PERPLEXITY_API_KEY`: Your Perplexity API key. Required if using `--use-perplexity` and not passing via `--perplexity-api-key`.
*   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`: Standard AWS credentials. Used by AWS Bedrock if specific profile/region settings don't resolve credentials.
*   `AWS_REGION`: Default AWS region for Bedrock. Can be overridden by `--aws-region`.
*   `AWS_PROFILE`: Default AWS profile for Bedrock. Can be overridden by `--aws-profile`.

It's recommended to use a `.env` file in your project or export these variables in your shell environment. `cc-bootstrap` uses `python-dotenv` to load `.env` files.

### The Project Plan File

The quality and detail of your `--project-plan-file` (e.g., `plan.md`) are **critical** to `cc-bootstrap`'s effectiveness. Due to its "LLM-led inference" approach, the tool relies heavily on this document to understand your project's context, goals, and technical requirements.

**Tips for Writing an Effective Project Plan File:**

1.  **Be Specific About Project Goals and Purpose**:
    *   Clearly state what the project aims to accomplish.
    *   Describe the problem it solves or the value it provides.
2.  **Include Technical Details**:
    *   Mention programming languages, frameworks, and key libraries.
    *   Describe the intended architecture or design patterns.
    *   List any external services, APIs, or databases the project will interact with.
3.  **Outline Project Structure**:
    *   Describe major components, modules, or directories.
    *   Explain how different parts of the system are expected to interact.
4.  **Specify Development Practices**:
    *   Note any coding standards, conventions, or style guides.
    *   Mention testing approaches (e.g., TDD, specific frameworks), CI/CD requirements.
5.  **Define Key Features**:
    *   List the main features or user stories you want Claude Code to help with.

**Example Project Plan Structure (Markdown):**

```markdown
# Project Plan: MyAwesomeApp

## 1. Project Overview
A web application for tracking personal fitness goals. Users can log workouts, set goals, and view progress.
The primary goal is to provide an intuitive and motivating platform for fitness enthusiasts.

## 2. Technical Stack
- **Frontend**: React 18 with TypeScript, Tailwind CSS, Zustand for state management.
- **Backend**: Node.js with Express.js, PostgreSQL database.
- **Authentication**: JWT-based authentication, OAuth2 for Google/GitHub login.
- **Deployment**: Dockerized application, planned deployment on AWS ECS.

## 3. Architecture
- Single-Page Application (SPA) frontend.
- RESTful API backend.
- Modular backend services: User Service, Workout Service, Goal Service.
- Database schema will include tables for users, workouts, goals, etc.

## 4. Key Features to Implement
- User registration and login (email/password and OAuth).
- Workout logging (type, duration, intensity, notes).
- Goal setting and tracking (e.g., run 5km, workout 3 times a week).
- Dashboard displaying progress and stats.

## 5. Development Practices
- **Testing**: Jest and React Testing Library for frontend; Mocha/Chai for backend. Aim for >80% test coverage.
- **Linting**: ESLint and Prettier with provided configurations.
- **Version Control**: Git with GitFlow branching model. Commit messages should follow Conventional Commits.
- **CI/CD**: GitHub Actions for automated testing and deployment.

## 6. External Services & APIs
- (Potentially) Strava API for workout import.
- (Potentially) OpenWeatherMap API for weather context during outdoor workouts.
```

The more detailed and clear your plan, the better `cc-bootstrap` and subsequently Claude Code will understand your project.

### Generated Files Overview

`cc-bootstrap` generates the following files to configure Claude Code for your project:

*   **`CLAUDE.md`** (in project root)
    *   **Purpose**: Serves as the primary persistent context for Claude Code. It contains project overview, tech stack, key files, common commands, coding standards, and specific instructions for how Claude should behave within this project.
    *   **Generation**: Content is LLM-generated based on your project plan and file samples, aiming to be concise yet comprehensive.

*   **`ACTION_PLAN.md`** (in project root)
    *   **Purpose**: Provides a detailed, step-by-step actionable plan for implementing the project or a specific feature outlined in your project plan.
    *   **Generation**: LLM-generated. If `--use-claude-squad` is enabled, the plan is structured for parallel work by multiple Claude instances.

*   **`.claude/commands/`** (directory in project root)
    *   **Purpose**: Contains custom commands (as Markdown files) that you can invoke within Claude Code (e.g., `/project:code-review:review-file`). These automate common tasks or complex prompts.
    *   **Generation**: `cc-bootstrap` generates a set of useful starter commands categorized into subdirectories (e.g., `code-review`, `test-generation`, `git-workflow`). The content of each command is LLM-generated to be relevant to your project.

*   **`.mcp.json`** (in project root)
    *   **Purpose**: Configures Model Context Protocol (MCP) servers. MCP allows Claude Code to extend its capabilities by interacting with external tools, databases, APIs (e.g., web search, database query, GitHub interaction).
    *   **Generation**: LLM-generated based on your project plan and any tools specified via `--mcp-tools-config`. It suggests and configures relevant MCP servers.

*   **`.claude/settings.json`** (in project root)
    *   **Purpose**: Contains settings for Claude Code, such as theme, telemetry, and crucially, `allowedTools`.
    *   **Generation**: `cc-bootstrap` starts with default settings and dynamically adds permissions to `allowedTools` for any MCP servers configured in `.mcp.json` (e.g., `mcp__web_search__*`).

### Configuring MCP Tools

You can guide `cc-bootstrap` on which MCP tools to consider for your `.mcp.json` file using the `--mcp-tools-config` option. This option accepts:
*   A comma-separated string of tool names (e.g., `web_search,github,postgres`). `cc-bootstrap` will then ask the LLM to generate configurations for these.
*   A path to a JSON or YAML file containing more detailed MCP tool definitions. This allows for pre-defining specific