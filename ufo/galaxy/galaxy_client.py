#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UFO3 Framework Client

Main entry point for the Galaxy Framework, providing a command-line interface
for starting Galaxy sessions, executing DAG-based workflows, and managing
constellation orchestration.

Usage:
    python galaxy_client.py --request "Your task description"
    python galaxy_client.py --interactive  # Interactive mode
    python galaxy_client.py --session-name "my_session" --request "Task"
"""

import argparse
import asyncio
import logging
import sys
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich import print as rprint
from rich.markdown import Markdown

from ufo.config import Config
from ufo.logging.setup import setup_logger
from ufo.module.context import Context, ContextNames

from .session.galaxy_session import GalaxySession
from .agents.galaxy_agent import GalaxyWeaverAgent, MockGalaxyWeaverAgent
from .constellation import TaskOrchestration
from .client.constellation_client import ConstellationClient
from .core.types import ProcessingContext

tracemalloc.start()
CONFIGS = Config.get_instance().config_data

# Initialize rich console
console = Console()


class GalaxyClient:
    """
    Main Galaxy Framework client for command-line interaction.

    Provides capabilities for:
    - Starting Galaxy sessions
    - Processing user requests into DAG workflows
    - Managing constellation execution
    - Interactive and batch modes
    """

    def __init__(
        self,
        session_name: Optional[str] = None,
        use_mock_agent: bool = False,
        max_rounds: int = 10,
        log_level: str = "INFO",
        output_dir: Optional[str] = None,
    ):
        """
        Initialize Galaxy client.

        Args:
            session_name: Name for the Galaxy session
            use_mock_agent: Whether to use mock agent for testing
            max_rounds: Maximum number of rounds per session
            log_level: Logging level
            output_dir: Output directory for logs and results
        """
        self.session_name = (
            session_name or f"galaxy_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.use_mock_agent = use_mock_agent
        self.max_rounds = max_rounds
        self.output_dir = Path(output_dir) if output_dir else Path("./logs")

        # Setup logging
        setup_logger(log_level)
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._agent: Optional[GalaxyWeaverAgent] = None
        self._orchestration: Optional[TaskOrchestration] = None
        self._client: Optional[ConstellationClient] = None
        self._session: Optional[GalaxySession] = None

        # Rich console for this instance
        self.console = Console()

        # Display initialization
        self._show_galaxy_banner()
        self.console.print(
            f"[bold cyan]🌌 Galaxy Client initialized:[/bold cyan] [green]{self.session_name}[/green]"
        )
        self.logger.info(f"🌌 Galaxy Client initialized: {self.session_name}")

    def _show_galaxy_banner(self) -> None:
        """Show the Galaxy Framework banner."""
        banner = """╔══════════════════════════════════════╗
║           🌌 UFO3 FRAMEWORK          ║
║      DAG-based Task Orchestration    ║
╚══════════════════════════════════════╝"""
        self.console.print(Panel(banner, style="bold blue", expand=False))

    async def initialize(self) -> None:
        """Initialize all Galaxy framework components."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Initializing UFO3 Framework...", total=None
                )

                self.logger.info("🚀 Initializing UFO3 Framework components...")

                # Initialize agent
                progress.update(task, description="[cyan]Setting up Agent...")
                if self.use_mock_agent:
                    self._agent = MockGalaxyWeaverAgent("galaxy_mock_agent")
                    self.console.print(
                        "[green]✅ Mock GalaxyWeaverAgent initialized[/green]"
                    )
                    self.logger.info("✅ Mock GalaxyWeaverAgent initialized")
                else:
                    self._agent = GalaxyWeaverAgent("galaxy_weaver_agent")
                    self.console.print(
                        "[green]✅ GalaxyWeaverAgent initialized[/green]"
                    )
                    self.logger.info("✅ GalaxyWeaverAgent initialized")

                # Initialize constellation client
                progress.update(
                    task, description="[cyan]Setting up Constellation Client..."
                )
                self._client = ConstellationClient()
                await self._client.initialize()
                self.console.print("[green]✅ ConstellationClient initialized[/green]")
                self.logger.info("✅ ConstellationClient initialized")

                # Initialize orchestration
                progress.update(
                    task, description="[cyan]Setting up Task Orchestration..."
                )
                self._orchestration = TaskOrchestration(
                    device_manager=self._client.device_manager, enable_logging=True
                )
                self.console.print("[green]✅ TaskOrchestration initialized[/green]")
                self.logger.info("✅ TaskOrchestration initialized")

                # Initialize context
                progress.update(task, description="[cyan]Setting up Session Context...")
                context = Context()
                context.set(ContextNames.ID, self.session_name)
                context.set(ContextNames.LOG_PATH, str(self.output_dir))

                # Initialize Galaxy session
                progress.update(task, description="[cyan]Creating Galaxy Session...")
                self._session = GalaxySession(
                    task=self.session_name,
                    should_evaluate=False,
                    id=self.session_name,
                    agent=self._agent,
                    client=self._client,
                )
                self.console.print("[green]✅ GalaxySession initialized[/green]")
                self.logger.info("✅ GalaxySession initialized")

            self.console.print(
                "\n[bold green]🌟 UFO3 Framework initialization complete![/bold green]\n"
            )
            self.logger.info("🌟 UFO3 Framework initialization complete!")

        except Exception as e:
            self.console.print(
                f"[bold red]❌ Failed to initialize UFO3 Framework: {e}[/bold red]"
            )
            self.logger.error(
                f"❌ Failed to initialize UFO3 Framework: {e}", exc_info=True
            )
            raise

    async def process_request(
        self, request: str, task_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single user request.

        Args:
            request: User request text
            task_name: Optional task name

        Returns:
            Processing result with execution details
        """
        if not self._session:
            raise RuntimeError(
                "Galaxy client not initialized. Call initialize() first."
            )

        try:
            self.console.print(
                f"[bold yellow]📝 Processing request:[/bold yellow] [white]{request[:100]}{'...' if len(request) > 100 else ''}[/white]"
            )
            self.logger.info(f"📝 Processing request: {request[:100]}...")

            # Update session task if provided
            if task_name:
                self._session._task = task_name

            # Execute the session with progress
            start_time = datetime.now()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task_id = progress.add_task(
                    "[cyan]Executing Galaxy session...", total=None
                )
                await self._session.run()

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Collect results
            result = {
                "session_name": self.session_name,
                "request": request,
                "task_name": task_name,
                "status": "completed",
                "execution_time": execution_time,
                "rounds": len(self._session._rounds),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "trajectory_path": getattr(self._session, "_trajectory_path", None),
            }

            # Add constellation info if available
            if (
                hasattr(self._session, "_current_constellation")
                and self._session._current_constellation
            ):
                constellation = self._session._current_constellation
                result["constellation"] = {
                    "id": constellation.constellation_id,
                    "name": constellation.name,
                    "task_count": len(constellation.tasks),
                    "dependency_count": len(constellation.dependencies),
                    "state": (
                        constellation.state.value
                        if hasattr(constellation.state, "value")
                        else str(constellation.state)
                    ),
                }

            self.console.print(
                f"[bold green]✅ Request processed successfully in {execution_time:.2f}s[/bold green]"
            )
            self.logger.info(
                f"✅ Request processed successfully in {execution_time:.2f}s"
            )
            return result

        except Exception as e:
            self.console.print(
                f"[bold red]❌ Failed to process request: {e}[/bold red]"
            )
            self.logger.error(f"❌ Failed to process request: {e}", exc_info=True)
            return {
                "session_name": self.session_name,
                "request": request,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def interactive_mode(self) -> None:
        """Run in interactive mode, accepting user input."""
        self.logger.info("🎯 Starting interactive mode. Type 'quit' or 'exit' to stop.")

        # Display interactive banner
        banner = Panel.fit(
            "[bold cyan]🌌 UFO3 Framework - Interactive Mode[/bold cyan]\n\n"
            "[white]Enter your requests below. Galaxy will convert them into DAG workflows.[/white]\n"
            "[dim]Commands: [bold]help[/bold], [bold]status[/bold], [bold]clear[/bold], [bold]quit[/bold][/dim]",
            border_style="blue",
        )
        self.console.print(banner)

        request_count = 0

        while True:
            try:
                # Get user input with rich prompt
                user_input = Prompt.ask(
                    f"[bold blue]Galaxy[{request_count}][/bold blue]",
                    console=self.console,
                ).strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    self.console.print("[bold yellow]👋 Goodbye![/bold yellow]")
                    break
                elif user_input.lower() in ["help", "h"]:
                    self._show_help()
                    continue
                elif user_input.lower() in ["status", "s"]:
                    self._show_status()
                    continue
                elif user_input.lower() in ["clear", "c"]:
                    self.console.clear()
                    continue

                # Process the request
                with self.console.status("[bold cyan]🚀 Processing your request..."):
                    result = await self.process_request(
                        user_input, f"interactive_task_{request_count}"
                    )

                # Display result
                self._display_result(result)
                request_count += 1

            except KeyboardInterrupt:
                self.console.print(
                    "\n[bold yellow]👋 Interrupted. Goodbye![/bold yellow]"
                )
                break
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}", exc_info=True)
                self.console.print(f"[bold red]❌ Error: {e}[/bold red]")

    def _show_help(self) -> None:
        """Show help information."""
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
            "• Use [bold]--mock-agent[/bold] for testing without real execution",
            title="Usage Tips",
            border_style="yellow",
        )
        self.console.print(tips_panel)

    def _show_status(self) -> None:
        """Show current session status."""
        status_table = Table(title="[bold cyan]📊 Galaxy Session Status[/bold cyan]")
        status_table.add_column("Property", style="cyan", no_wrap=True)
        status_table.add_column("Value", style="white")

        status_table.add_row("Session Name", self.session_name)
        status_table.add_row("Agent Type", "Mock" if self.use_mock_agent else "Real")
        status_table.add_row("Max Rounds", str(self.max_rounds))
        status_table.add_row("Output Directory", str(self.output_dir))

        if self._session:
            status_table.add_row("Current Rounds", str(len(self._session._rounds)))
            status_table.add_row("Session State", "[green]Initialized[/green]")
        else:
            status_table.add_row("Session State", "[red]Not initialized[/red]")

        self.console.print(status_table)

    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display execution result with rich formatting."""
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

    async def shutdown(self) -> None:
        """Shutdown the Galaxy client."""
        try:
            self.console.print(
                "[bold yellow]🛑 Shutting down Galaxy client...[/bold yellow]"
            )
            self.logger.info("🛑 Shutting down Galaxy client...")

            if self._client:
                await self._client.shutdown()

            if self._session:
                # Force finish session if needed
                await self._session.force_finish("Client shutdown")

            self.console.print(
                "[bold green]✅ Galaxy client shutdown complete[/bold green]"
            )
            self.logger.info("✅ Galaxy client shutdown complete")

        except Exception as e:
            self.console.print(f"[bold red]Error during shutdown: {e}[/bold red]")
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)


async def main():
    """Main entry point for Galaxy client."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="UFO3 Framework Client")

    parser.add_argument(
        "--session-name",
        dest="session_name",
        default=None,
        help="Name for the Galaxy session",
    )

    parser.add_argument(
        "--request",
        dest="request_text",
        default=None,
        help="The task request text",
    )

    parser.add_argument(
        "--task-name",
        dest="task_name",
        default=None,
        help="The name of the task",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )

    parser.add_argument(
        "--mock-agent",
        action="store_true",
        help="Use mock agent for testing",
    )

    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        dest="max_rounds",
        help="Maximum rounds per session (default: 10)",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL, OFF) (default: INFO)",
    )

    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default="./logs",
        help="Output directory for logs and results (default: ./logs)",
    )

    args = parser.parse_args()

    # Create Galaxy client
    client = GalaxyClient(
        session_name=args.session_name,
        use_mock_agent=args.mock_agent,
        max_rounds=args.max_rounds,
        log_level=args.log_level,
        output_dir=args.output_dir,
    )

    try:
        # Initialize the client
        await client.initialize()

        # Run based on mode
        if args.interactive:
            # Interactive mode
            await client.interactive_mode()
        elif args.request_text:
            # Single request mode
            result = await client.process_request(args.request_text, args.task_name)

            # Display result
            console.print(
                "\n[bold green]🎯 UFO3 Framework Execution Complete![/bold green]"
            )
            console.print("=" * 50)
            client._display_result(result)

            # Save result if needed
            if args.output_dir:
                output_path = (
                    Path(args.output_dir) / f"{client.session_name}_result.json"
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)

                import json

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                console.print(
                    f"[bold cyan]📁 Result saved to:[/bold cyan] [green]{output_path}[/green]"
                )
        else:
            # No arguments provided, show help
            parser.print_help()
            console.print("\n[bold yellow]💡 Examples:[/bold yellow]")
            console.print(
                "  [cyan]python galaxy_client.py --request 'Create a data analysis pipeline'[/cyan]"
            )
            console.print("  [cyan]python galaxy_client.py --interactive[/cyan]")
            console.print(
                "  [cyan]python galaxy_client.py --mock-agent --request 'Test workflow'[/cyan]"
            )

    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Galaxy client error: {e}[/bold red]")
        logging.error(f"Galaxy client error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
