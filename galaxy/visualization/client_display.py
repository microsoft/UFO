# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Client Display Module

This module provides rich console display utilities for the Galaxy client,
including banners, status tables, result displays, and help information.
"""

from pathlib import Path
from typing import Dict, Any, Optional


from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt


class ClientDisplay:
    """
    Rich console display manager for Galaxy client.

    Provides formatted output for banners, status information,
    execution results, and interactive help.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize client display.

        :param console: Rich console instance (creates new if None)
        """
        self.console = console or Console()

    def show_galaxy_banner(self) -> None:
        """
        Show the Galaxy Framework banner.

        Displays a formatted banner for the UFO3 Galaxy Framework.
        """
        banner = """╔══════════════════════════════════════╗
║           🌌 UFO3 FRAMEWORK          ║
║      DAG-based Task Orchestration    ║
╚══════════════════════════════════════╝"""
        self.console.print(Panel(banner, style="bold blue", expand=False))

    def show_welcome_with_usage(self) -> None:
        """
        Display welcome panel with usage instructions.

        Shows main welcome message and usage examples for new users.
        """
        welcome_panel = Panel(
            "[bold cyan]🌌 Galaxy Framework[/bold cyan]\n\n"
            "[white]AI-powered DAG workflow orchestration system[/white]\n\n"
            "[bold yellow]Quick Start:[/bold yellow]\n"
            "  [cyan]python -m galaxy 'Create a data pipeline'[/cyan]\n"
            "  [cyan]python -m galaxy --interactive[/cyan]\n"
            "  [cyan]python -m galaxy --demo[/cyan]\n\n"
            "[bold yellow]Advanced Usage:[/bold yellow]\n"
            "  [cyan]python -m galaxy --request 'Task' --session-name 'my_session'[/cyan]\n"
            "  [cyan]python -m galaxy --interactive --max-rounds 20[/cyan]\n\n"
            "[dim]Use --help for all options[/dim]",
            border_style="blue",
        )
        self.console.print(welcome_panel)

    def show_interactive_banner(self) -> None:
        """
        Display interactive mode banner.

        Shows welcome message and usage instructions for interactive mode.
        """
        banner = Panel.fit(
            "[bold cyan]🌌 UFO3 Framework - Interactive Mode[/bold cyan]\n\n"
            "[white]Enter your requests below. UFO will convert them into Constellation workflows.[/white]\n"
            "[dim]Commands: [bold]help[/bold], [bold]status[/bold], [bold]clear[/bold], [bold]quit[/bold][/dim]",
            border_style="blue",
        )
        self.console.print(banner)

    def show_help(self) -> None:
        """
        Show help information.

        Displays a formatted table of available commands and usage tips
        for the interactive mode.
        """
        help_table = Table(title="[bold cyan]📖 UFO3 Framework Commands[/bold cyan]")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")

        help_table.add_row("help, h", "Show this help message")
        help_table.add_row("status, s", "Show current session status")
        help_table.add_row("clear, c", "Clear screen")
        help_table.add_row("quit, exit, q", "Exit interactive mode")

        self.console.print(help_table)

        tips_panel = Panel(
            "[bold yellow]💡 Tips:[/bold yellow]\n"
            "• Enter any text to create a DAG-based workflow\n"
            "• Complex requests will be broken down into tasks\n"
            "• Tasks are executed in dependency order\n"
            "• Monitor execution progress with real-time updates",
            title="Usage Tips",
            border_style="yellow",
        )
        self.console.print(tips_panel)

    def show_status(
        self,
        session_name: str,
        max_rounds: int,
        output_dir: Path,
        session_info: Dict[str, Any] = None,
    ) -> None:
        """
        Show current session status.

        Displays a formatted table with current Galaxy session
        configuration and state information.

        :param session_name: Name of the current session
        :param max_rounds: Maximum rounds configuration
        :param output_dir: Output directory path
        :param session_info: Optional session state information
        """
        status_table = Table(title="[bold cyan]📊 Galaxy Session Status[/bold cyan]")
        status_table.add_column("Property", style="cyan", no_wrap=True)
        status_table.add_column("Value", style="white")

        status_table.add_row("Session Name", session_name)
        status_table.add_row("Max Rounds", str(max_rounds))
        status_table.add_row("Output Directory", str(output_dir))

        if session_info:
            status_table.add_row("Current Rounds", str(session_info.get("rounds", 0)))
            status_table.add_row(
                "Session State",
                (
                    "[green]Initialized[/green]"
                    if session_info.get("initialized")
                    else "[red]Not initialized[/red]"
                ),
            )
        else:
            status_table.add_row("Session State", "[red]Not initialized[/red]")

        self.console.print(status_table)

    def display_result(self, result: Dict[str, Any]) -> None:
        """
        Display execution result with rich formatting.

        :param result: Dictionary containing execution results and metadata
        """
        # Create main result panel
        status_color = "green" if result["status"] == "completed" else "red"
        status_icon = "✅" if result["status"] == "completed" else "❌"

        result_table = Table(
            title=f"[bold {status_color}]🎯 Execution Result[/bold {status_color}]"
        )
        result_table.add_column("Property", style="cyan", no_wrap=True)
        result_table.add_column("Value", style="white")

        result_table.add_row(
            "Status",
            f"[{status_color}]{status_icon} {result['status']}[/{status_color}]",
        )

        if result.get("execution_time"):
            result_table.add_row("Execution Time", f"{result['execution_time']:.2f}s")

        if result.get("rounds"):
            result_table.add_row("Rounds", str(result["rounds"]))

        if result.get("constellation"):
            constellation = result["constellation"]
            result_table.add_row(
                "Constellation",
                f"[bold]{constellation['name']}[/bold] ({constellation['task_count']} tasks)",
            )
            result_table.add_row("State", constellation.get("state", "Unknown"))

        if result.get("error"):
            result_table.add_row("Error", f"[red]{result['error']}[/red]")

        if result.get("trajectory_path"):
            result_table.add_row("Trajectory", str(result["trajectory_path"]))

        self.console.print(result_table)

        # Show constellation details if available
        if result.get("constellation"):
            constellation = result["constellation"]
            constellation_panel = Panel(
                f"[bold cyan]Constellation Details:[/bold cyan]\n"
                f"• ID: {constellation.get('id', 'N/A')}\n"
                f"• Tasks: {constellation.get('task_count', 0)}\n"
                f"• Dependencies: {constellation.get('dependency_count', 0)}\n"
                f"• State: {constellation.get('state', 'Unknown')}",
                title="DAG Information",
                border_style="cyan",
            )
            self.console.print(constellation_panel)

    def show_initialization_progress(self) -> Progress:
        """
        Create and return a progress indicator for initialization.

        :return: Rich Progress instance for showing initialization steps
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            refresh_per_second=1,
            transient=True,
        )

    def show_processing_request(self, request_text: str) -> None:
        """
        Show processing request message.

        :param request_text: Request text being processed
        """
        truncated_text = (
            f"{request_text[:100]}{'...' if len(request_text) > 100 else ''}"
        )
        self.console.print(
            f"[bold cyan]🚀 Processing request:[/bold cyan] [white]{truncated_text}[/white]"
        )

    def show_execution_complete(self) -> None:
        """
        Show execution completion banner.
        """
        self.console.print("\n" + "=" * 60)
        self.print_success("🎯 UFO Framework Execution Complete!")
        self.console.print("=" * 60)

    def show_demo_banner(self) -> None:
        """
        Show demo mode banner.
        """
        demo_panel = Panel(
            "[bold cyan]🌟 UFO3 Framework Demo[/bold cyan]\n\n"
            "[white]Showcasing AI-powered DAG workflow orchestration[/white]\n"
            "[dim]Watch complex requests transform into executable workflows![/dim]",
            border_style="cyan",
        )
        self.console.print(demo_panel)

    def show_demo_step(self, step_number: int, request: str) -> None:
        """
        Show demo step information.

        :param step_number: Demo step number
        :param request: Demo request text
        """
        self.console.print(
            f"\n[bold yellow]🎯 Demo {step_number}:[/bold yellow] [white]{request}[/white]"
        )

    def show_demo_complete(self) -> None:
        """
        Show demo completion panel.
        """
        success_panel = Panel(
            "[bold green]✨ Demo Complete![/bold green]\n\n"
            "[white]All demo workflows processed successfully![/white]\n"
            "[dim]Try your own requests with --interactive or --request flags![/dim]",
            border_style="green",
        )
        self.console.print(success_panel)

    def show_processing_status(self, message: str) -> None:
        """
        Show processing status message.

        :param message: Status message to display
        """
        self.console.status(f"[bold cyan]{message}")

    def print_info(self, message: str) -> None:
        """
        Print informational message.

        :param message: Information message to display
        """
        self.console.print(message)

    def print_success(self, message: str) -> None:
        """
        Print success message.

        :param message: Success message to display
        """
        self.console.print(f"[bold green]{message}[/bold green]")

    def print_error(self, message: str) -> None:
        """
        Print error message.

        :param message: Error message to display
        """
        self.console.print(f"[bold red]{message}[/bold red]")

    def print_warning(self, message: str) -> None:
        """
        Print warning message.

        :param message: Warning message to display
        """
        self.console.print(f"[bold yellow]{message}[/bold yellow]")

    def clear_screen(self) -> None:
        """Clear the console screen."""
        self.console.clear()

    def get_user_input(self, prompt_text: str) -> str:
        """
        Get user input with rich prompt.

        :param prompt_text: Prompt text to display
        :return: User input string
        """
        return Prompt.ask(prompt_text, console=self.console).strip()
