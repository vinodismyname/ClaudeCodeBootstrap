"""
Main entry point for the cc-bootstrap tool.

This module serves as the entry point for the CLI tool, now using Typer
for command-line argument parsing and handling.
"""

from cc_bootstrap.cli.app import app


def main():
    """Main entry point for the cc-bootstrap CLI."""
    import sys
    import os

    if "--debug" in sys.argv:
        os.environ["CC_BOOTSTRAP_DEBUG"] = "1"
        sys.argv.remove("--debug")
        print("Debug mode enabled")
        print(f"Command line arguments: {sys.argv}")

    try:
        app()
    except Exception as e:
        print(f"Error in Typer app: {e}")
        if os.environ.get("CC_BOOTSTRAP_DEBUG"):
            import traceback

            print(traceback.format_exc())


if __name__ == "__main__":
    main()
