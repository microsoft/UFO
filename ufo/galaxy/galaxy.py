#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Quick Start

Quick entry point for Galaxy Framework with simplified interface.
This script provides an easy way to start Galaxy sessions.

Usage:
    python galaxy.py "Create a machine learning pipeline"
    python galaxy.py --interactive
    python galaxy.py --demo
"""

import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel


# Add UFO2 to path to enable imports
UFO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(UFO_ROOT))

from ufo.galaxy.galaxy_client import GalaxyClient

# Initialize rich console
console = Console()


async def run_demo():
    """
    Run a demo showcasing Galaxy framework capabilities.

    Demonstrates the Galaxy Framework's DAG-based task orchestration
    with predefined demo requests and mock execution.
    """
    demo_panel = Panel(
        "[bold cyan]🌟 Galaxy Framework Demo[/bold cyan]\n\n"
        "[white]This demo showcases the Galaxy Framework's DAG-based task orchestration capabilities.[/white]\n"
        "[dim]Watch as complex requests are broken down into executable workflows![/dim]",
        border_style="cyan",
    )
    console.print(demo_panel)

    client = GalaxyClient(
        session_name="galaxy_demo", use_mock_agent=True, log_level="INFO"
    )

    await client.initialize()

    demo_requests = [
        "Create a data analysis pipeline with parallel processing",
        "Build a machine learning workflow with training and evaluation",
        "Design a web scraping system with data validation",
    ]

    for i, request in enumerate(demo_requests, 1):
        console.print(
            f"\n[bold yellow]🎯 Demo {i}:[/bold yellow] [white]{request}[/white]"
        )

        with console.status(f"[bold cyan]Processing demo {i}..."):
            result = await client.process_request(request, f"demo_task_{i}")

        client._display_result(result)

    await client.shutdown()

    success_panel = Panel(
        "[bold green]✨ Demo complete![/bold green]\n\n"
        "[white]All demo workflows have been processed successfully.[/white]\n"
        "[dim]Try running your own requests with --interactive or --request flags![/dim]",
        border_style="green",
    )
    console.print(success_panel)


async def galaxy_quick_start(
    request: str, session_name: str = "galaxy_quick", use_mock: bool = True
):
    """
    Quick start function for single requests.

    :param request: User request text to process
    :param session_name: Name for the Galaxy session (default: "galaxy_quick")
    :param use_mock: Whether to use mock agent for testing (default: True)
    :return: Processing result dictionary
    """
    client = GalaxyClient(
        session_name=session_name, use_mock_agent=use_mock, log_level="INFO"
    )

    await client.initialize()
    result = await client.process_request(request)
    await client.shutdown()

    return result


async def galaxy_interactive(
    session_name: str = "galaxy_interactive", use_mock: bool = True
):
    """
    Interactive function for command-line interaction.

    :param session_name: Name for the Galaxy session (default: "galaxy_interactive")
    :param use_mock: Whether to use mock agent for testing (default: True)
    """
    client = GalaxyClient(
        session_name=session_name, use_mock_agent=use_mock, log_level="INFO"
    )

    await client.initialize()
    await client.interactive_mode()
    await client.shutdown()


async def main():
    """
    Main entry point.

    Handles command-line arguments and routes to appropriate
    execution mode (demo, interactive, or single request).
    """
    if len(sys.argv) == 1:
        welcome_panel = Panel(
            "[bold cyan]🌌 Galaxy Framework Quick Start[/bold cyan]\n\n"
            "[white]Welcome to the Galaxy Framework![/white]\n\n"
            "[bold yellow]Usage Examples:[/bold yellow]\n"
            "  [cyan]python galaxy.py 'Your request here'[/cyan]\n"
            "  [cyan]python galaxy.py --interactive[/cyan]\n"
            "  [cyan]python galaxy.py --demo[/cyan]\n\n"
            "[dim]Add --mock flag for testing without real execution[/dim]",
            border_style="blue",
        )
        console.print(welcome_panel)
        return

    if "--demo" in sys.argv:
        await run_demo()
        return

    if "--interactive" in sys.argv:
        await galaxy_interactive(use_mock="--mock" in sys.argv)
        return

    # Single request mode
    request = " ".join(arg for arg in sys.argv[1:] if not arg.startswith("--"))

    if request:
        console.print(
            f"[bold cyan]🚀 Processing request:[/bold cyan] [white]{request}[/white]"
        )
        result = await galaxy_quick_start(request, use_mock="--mock" in sys.argv)

        # Simple result display for quick start
        if result.get("status") == "completed":
            console.print(
                f"[bold green]✅ Request completed successfully in {result.get('execution_time', 0):.2f}s[/bold green]"
            )
        else:
            console.print(
                f"[bold red]❌ Request failed: {result.get('error', 'Unknown error')}[/bold red]"
            )
    else:
        console.print("[bold red]❌ No request provided![/bold red]")
        console.print("[dim]Example: python galaxy.py 'Create a data pipeline'[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
