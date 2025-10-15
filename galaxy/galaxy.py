#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Main Entry Point

Primary command-line interface for Galaxy Framework with comprehensive functionality.
This script provides both simple and advanced interfaces for Galaxy sessions.

Simple Usage:
    python -m galaxy "Create a machine learning pipeline"
    python -m galaxy --interactive
    python -m galaxy --demo

Advanced Usage:
    python -m galaxy --request "Task description" --session-name "my_session"
    python -m galaxy --request "Task" --output-dir "./results" --log-level DEBUG
    python -m galaxy --interactive --max-rounds 20
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add UFO2 to path to enable imports
UFO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(UFO_ROOT))

from rich.console import Console
from ufo.logging.setup import setup_logger


def parse_args():
    """Parse command-line arguments with support for both simple and advanced usage."""
    parser = argparse.ArgumentParser(
        description="Galaxy Framework - AI-powered DAG workflow orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Simple Usage:
    python -m galaxy "Create a data analysis pipeline"
    python -m galaxy --demo
    python -m galaxy --interactive

  Advanced Usage:
    python -m galaxy --request "Build ML pipeline" --session-name "ml_session"
    python -m galaxy --interactive --max-rounds 20 --log-level DEBUG
    python -m galaxy --request "Task" --output-dir "./results" --mock
        """,
    )

    # Core functionality
    parser.add_argument(
        "simple_request",
        nargs="*",
        help="Simple request text (alternative to --request)",
    )

    parser.add_argument(
        "--request", dest="request_text", help="Task request text to process"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive command-line mode",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demonstration mode with sample workflows",
    )

    # Session configuration
    parser.add_argument(
        "--session-name", dest="session_name", help="Custom name for the Galaxy session"
    )

    parser.add_argument(
        "--task-name", dest="task_name", help="Custom name for the specific task"
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="Maximum rounds per session (default: 10)",
    )

    # Output and logging
    parser.add_argument(
        "--output-dir",
        default="./logs",
        help="Output directory for logs and results (default: ./logs)",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    # Testing and development
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock agent for testing (no real LLM calls)",
    )

    return parser.parse_args()


args = parse_args()
setup_logger(args.log_level)

from galaxy.galaxy_client import GalaxyClient

# Initialize rich console
console = Console()


# Utility functions for backward compatibility and convenience


async def galaxy_quick_start(
    request: str,
    session_name: str = "galaxy_quick",
    log_level: str = "INFO",
    output_dir: str = "./logs",
):
    """
    Quick start function for single requests (programmatic API).

    :param request: User request text to process
    :param session_name: Name for the Galaxy session (default: "galaxy_quick")
    :param log_level: Logging level (default: "INFO")
    :param output_dir: Output directory for results (default: "./logs")
    :return: Processing result dictionary
    """
    client = GalaxyClient(
        session_name=session_name, log_level=log_level, output_dir=output_dir
    )

    await client.initialize()
    result = await client.process_request(request)
    await client.shutdown()

    return result


async def galaxy_interactive(
    session_name: str = "galaxy_interactive",
    log_level: str = "INFO",
    max_rounds: int = 10,
    output_dir: str = "./logs",
):
    """
    Interactive function for programmatic use.

    :param session_name: Name for the Galaxy session (default: "galaxy_interactive")
    :param log_level: Logging level (default: "INFO")
    :param max_rounds: Maximum rounds per session (default: 10)
    :param output_dir: Output directory for results (default: "./logs")
    """
    client = GalaxyClient(
        session_name=session_name,
        log_level=log_level,
        max_rounds=max_rounds,
        output_dir=output_dir,
    )

    await client.initialize()
    await client.interactive_mode()
    await client.shutdown()


async def main():
    """
    Main entry point with unified simple and advanced CLI support.

    Supports both simple usage (direct arguments) and advanced usage (flags).
    Routes to appropriate execution mode based on arguments provided.
    """

    # Handle no arguments case
    if not any([args.simple_request, args.request_text, args.interactive, args.demo]):
        from galaxy.visualization.client_display import ClientDisplay

        display = ClientDisplay(console)
        display.show_welcome_with_usage()
        return

    # Initialize client with provided configuration
    client = GalaxyClient(
        session_name=args.session_name,
        max_rounds=args.max_rounds,
        log_level=args.log_level,
        output_dir=args.output_dir,
    )

    try:
        await client.initialize()

        # Demo mode
        if args.demo:
            await run_demo_with_client(client)

        # Interactive mode
        elif args.interactive:
            await client.interactive_mode()

        # Request processing mode
        elif args.request_text or args.simple_request:
            # Determine request text
            request_text = args.request_text or " ".join(args.simple_request)

            # client.display.show_processing_request(request_text)

            # Process request
            result = await client.process_request(request_text, args.task_name)

            # Display results
            client.display.show_execution_complete()
            client.display.display_result(result)

            # Save results if output directory specified
            if args.output_dir:
                output_path = (
                    Path(args.output_dir) / f"{client.session_name}_result.json"
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

                client.display.print_info(
                    f"[bold cyan]📁 Result saved to:[/bold cyan] [green]{output_path}[/green]"
                )

    except KeyboardInterrupt:
        if "client" in locals():
            client.display.print_warning("\n👋 Interrupted by user")
        else:
            # Fallback display for when client is not yet initialized
            from galaxy.visualization.client_display import ClientDisplay

            display = ClientDisplay(console=console)
            display.print_warning("\n👋 Interrupted by user")
    except Exception as e:
        if "client" in locals():
            client.display.print_error(f"❌ Galaxy Framework error: {e}")
        else:
            # Fallback display for when client is not yet initialized
            from galaxy.visualization.client_display import ClientDisplay

            display = ClientDisplay(console=console)
            display.print_error(f"❌ Galaxy Framework error: {e}")
        logging.error(f"Galaxy Framework error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await client.shutdown()


async def run_demo_with_client(client: GalaxyClient):
    """
    Run demo mode with initialized client.

    :param client: Initialized GalaxyClient instance
    """
    client.display.show_demo_banner()

    demo_requests = [
        "Create a data analysis pipeline with parallel processing",
        "Build a machine learning workflow with training and evaluation",
        "Design a web scraping system with data validation and storage",
    ]

    for i, request in enumerate(demo_requests, 1):
        client.display.show_demo_step(i, request)

        with client.display.console.status(f"[bold cyan]Processing demo {i}..."):
            result = await client.process_request(request, f"demo_task_{i}")

        client.display.display_result(result)

    client.display.show_demo_complete()


if __name__ == "__main__":
    asyncio.run(main())
