"""
Configuration settings for the cc-bootstrap tool.
"""

from typing import Dict, Set, Any


DEFAULT_LLM_MODEL = "provider-specific-default"


ENV_ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
ENV_PERPLEXITY_API_KEY = "PERPLEXITY_API_KEY"
ENV_SMITHERY_API_KEY = "SMITHERY_API_KEY"


ENV_AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
ENV_AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
ENV_AWS_SESSION_TOKEN = "AWS_SESSION_TOKEN"
ENV_AWS_REGION = "AWS_REGION"
ENV_AWS_PROFILE = "AWS_PROFILE"


LLM_PROVIDERS = {
    "anthropic": {
        "name": "Anthropic API",
        "default_model": "claude-3-7-sonnet-20250219",
        "env_api_key": ENV_ANTHROPIC_API_KEY,
        "default_thinking_enabled": True,
        "default_thinking_budget": 6000,
    },
    "bedrock": {
        "name": "AWS Bedrock",
        "default_model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "env_region": ENV_AWS_REGION,
        "env_profile": ENV_AWS_PROFILE,
        "default_region": "us-west-2",
        "default_thinking_enabled": True,
        "default_thinking_budget": 6000,
    },
}


DEFAULT_LLM_PROVIDER = "anthropic"


DEFAULT_THINKING_ENABLED = True
DEFAULT_THINKING_BUDGET = 6000


SMITHERY_API_BASE_URL = "https://registry.smithery.ai"


MAX_TOKENS_THINKING_ENABLED = 100000
MAX_TOKENS_THINKING_DISABLED = 8000


CLAUDE_MD_PATH = "CLAUDE.md"
CLAUDE_DIR_PATH = ".claude"
COMMANDS_DIR_PATH = f"{CLAUDE_DIR_PATH}/commands"
SETTINGS_JSON_PATH = f"{CLAUDE_DIR_PATH}/settings.json"
MCP_JSON_PATH = ".mcp.json"
ACTION_PLAN_PATH = "ACTION_PLAN.md"


COMMAND_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "code-review": {
        "description": "Commands for reviewing code and pull requests",
        "commands": {
            "review-file": {
                "description": "Review a specific file in the codebase for issues and improvements"
            },
            "review-pr": {
                "description": "Review a pull request and provide comprehensive feedback"
            },
        },
    },
    "test-generation": {
        "description": "Commands for generating different types of tests",
        "commands": {
            "generate-unit-tests": {
                "description": "Generate comprehensive unit tests for a specific file or function"
            },
            "generate-integration-tests": {
                "description": "Generate integration tests to verify interactions between components"
            },
        },
    },
    "git-workflow": {
        "description": "Commands for Git-related tasks and workflows",
        "commands": {
            "prepare-commit": {
                "description": "Prepare a well-formatted Git commit message for your changes"
            },
            "create-pr": {
                "description": "Create a well-structured pull request with a comprehensive description"
            },
        },
    },
    "refactoring": {
        "description": "Commands for improving code structure and quality",
        "commands": {
            "refactor-file": {
                "description": "Improve the structure and readability of a file while preserving functionality"
            },
            "extract-function": {
                "description": "Extract a section of code into a separate, reusable function"
            },
        },
    },
    "documentation": {
        "description": "Commands for generating and improving documentation",
        "commands": {
            "document-code": {
                "description": "Add or improve documentation for code files, functions, or classes"
            },
            "generate-readme": {
                "description": "Generate a comprehensive README file for the project"
            },
        },
    },
}


IGNORE_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    ".cache",
    ".next",
    ".nuxt",
    ".output",
    "target",
    "out",
    "coverage",
    ".nyc_output",
    ".DS_Store",
    ".idea",
    ".vscode",
    ".gradle",
    ".dart_tool",
    ".pub",
    ".angular",
    ".svelte-kit",
    ".parcel-cache",
    "vendor",
    "bower_components",
    ".bundle",
    "tmp",
    "temp",
    "logs",
    ".yarn",
    ".pnp",
}


CODE_FILE_EXTENSIONS: Set[str] = {
    ".py",
    ".pyw",
    ".pyx",
    ".pxd",
    ".pxi",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".rb",
    ".rake",
    ".gemspec",
    ".java",
    ".class",
    ".jar",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".h",
    ".hpp",
    ".hxx",
    ".cs",
    ".csx",
    ".go",
    ".rs",
    ".php",
    ".phtml",
    ".php5",
    ".php7",
    ".phps",
    ".swift",
    ".kt",
    ".kts",
    ".md",
    ".txt",
    ".rst",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
    ".sql",
    "Dockerfile",
    ".dockerfile",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".env",
    ".ini",
    ".toml",
    ".cfg",
    ".conf",
    ".lock",
}


IMPORTANT_FILES: Set[str] = {
    "README.md",
    "package.json",
    "requirements.txt",
    "setup.py",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".gitignore",
    ".env.example",
    "tsconfig.json",
    "webpack.config.js",
    "vite.config.js",
    "rollup.config.js",
    "next.config.js",
    "nuxt.config.js",
    "angular.json",
    "svelte.config.js",
    "tauri.conf.json",
    "capacitor.config.json",
    "android/app/build.gradle",
    "ios/Podfile",
    "pubspec.yaml",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    ".gitlab-ci.yml",
    ".github/workflows/main.yml",
    "Jenkinsfile",
    "bitbucket-pipelines.yml",
    "azure-pipelines.yml",
    "travis.yml",
    "sonar-project.properties",
    "manifest.json",
    "composer.json",
    "Gemfile",
    "tox.ini",
    "pytest.ini",
    "phpunit.xml",
    "karma.conf.js",
    "jest.config.js",
    "cypress.json",
    "playwright.config.js",
    "nginx.conf",
    "apache2.conf",
    "serverless.yml",
    "netlify.toml",
    "vercel.json",
    "fly.toml",
    "heroku.yml",
    "app.yaml",
    "chart.yaml",
    "values.yaml",
    "kustomization.yaml",
    "terraform.tf",
    "main.tf",
    "buildspec.yml",
    "appspec.yml",
    "cloudbuild.yaml",
    "lerna.json",
    "rush.json",
    "nx.json",
    "deno.json",
    "bun.lockb",
}


MAX_LINES_PER_FILE = 500


MAX_CHARS_PER_FILE = 5000


MAX_FILES_IN_CONTEXT = 20


MAX_CONTEXT_TOKENS = 100000


ENTRY_POINTS: Set[str] = {
    "main.py",
    "index.js",
    "app.py",
    "server.js",
    "app.js",
}

CONFIG_EXTENSIONS: Set[str] = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".config",
}
