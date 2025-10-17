#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UFO3 Framework Client Library

Galaxy Framework client class providing programmatic interface
for starting Galaxy sessions, executing DAG-based workflows, and managing
constellation orchestration.

This module provides the GalaxyClient class for integration into other applications.
For command-line usage, use galaxy.py as the main entry point.
"""

import logging
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from galaxy.client.config_loader import ConstellationConfig
from ufo.config import Config
from ufo.logging.setup import setup_logger

from .client.constellation_client import ConstellationClient
from .session.galaxy_session import GalaxySession
from .visualization.client_display import ClientDisplay

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
        max_rounds: int = 10,
        log_level: str = "INFO",
        output_dir: Optional[str] = None,
    ):
        """
        Initialize Galaxy client.

        :param session_name: Name for the Galaxy session (auto-generated if None)
        :param max_rounds: Maximum number of rounds per session (default: 10)
        :param log_level: Logging level (default: "INFO")
        :param output_dir: Output directory for logs and results (default: "./logs")
        """
        self.session_name = (
            session_name or f"galaxy_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.max_rounds = max_rounds
        self.output_dir = Path(output_dir) if output_dir else Path("./logs")

        # Setup logging
        setup_logger(log_level)
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._client: Optional[ConstellationClient] = None
        self._session: Optional[GalaxySession] = None
        self._device_config = ConstellationConfig.from_yaml(CONFIGS["DEVICE_INFO"])

        # Rich console and display manager
        self.console = Console()
        self.display = ClientDisplay(self.console)

        # Display initialization
        self.display.show_galaxy_banner()
        self.display.print_info(
            f"[bold cyan]🌌 Galaxy Client initialized:[/bold cyan] [green]{self.session_name}[/green]"
        )
        self.logger.info(f"🌌 Galaxy Client initialized: {self.session_name}")

    async def initialize(self) -> None:
        """
        Initialize all Galaxy framework components.

        Sets up agent, constellation client, orchestration, context,
        and Galaxy session with progress indication.
        """
        try:
            with self.display.show_initialization_progress() as progress:
                task = progress.add_task(
                    "[cyan]Initializing UFO3 Framework...", total=None
                )

                self.logger.info("🚀 Initializing UFO3 Framework components...")

                # Initialize constellation client
                progress.update(
                    task, description="[cyan]Setting up Constellation Client..."
                )
                self._client = ConstellationClient(config=self._device_config)
                await self._client.initialize()
                self.display.print_success("✅ ConstellationClient initialized")
                self.logger.info("✅ ConstellationClient initialized")

                # Galaxy session will be created per request
                progress.update(
                    task, description="[cyan]Framework ready for requests..."
                )
                self.display.print_success("✅ Framework initialized and ready")
                self.logger.info("✅ Framework initialized and ready")

            self.display.print_success("\n🌟 UFO3 Framework initialization complete!\n")
            self.logger.info("🌟 UFO3 Framework initialization complete!")

        except Exception as e:
            self.display.print_error(f"❌ Failed to initialize UFO3 Framework: {e}")
            self.logger.error(
                f"❌ Failed to initialize UFO3 Framework: {e}", exc_info=True
            )
            raise

    async def process_request(
        self, request: str, task_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single user request.

        :param request: User request text to process
        :param task_name: Optional task name for the request
        :return: Dictionary containing processing result with execution details
        :raises RuntimeError: If Galaxy client is not initialized
        """
        if not self._client:
            raise RuntimeError(
                "Galaxy client not initialized. Call initialize() first."
            )

        try:
            self.display.print_info(
                f"[bold yellow]📝 Processing request:[/bold yellow] [white]{request[:100]}{'...' if len(request) > 100 else ''}[/white]"
            )
            self.logger.info(f"📝 Processing request: {request[:100]}...")

            # Create a new session for this request
            session_id = f"{self.session_name}_{task_name or 'request'}"
            self._session = GalaxySession(
                task=task_name
                or f"request_{len(getattr(self, '_processed_requests', []))}",
                should_evaluate=False,
                id=session_id,
                client=self._client,
                initial_request=request,
            )

            # Execute the session with progress
            start_time = datetime.now()

            with self.display.show_initialization_progress() as progress:
                # progress.add_task("[cyan]Executing Galaxy session...", total=None)
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
                "trajectory_path": getattr(self._session, "log_path", None),
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

            self.display.print_success(
                f"✅ Request processed successfully in {execution_time:.2f}s"
            )
            self.logger.info(
                f"✅ Request processed successfully in {execution_time:.2f}s"
            )
            return result

        except Exception as e:
            self.display.print_error(f"❌ Failed to process request: {e}")
            self.logger.error(f"❌ Failed to process request: {e}", exc_info=True)
            return {
                "session_name": self.session_name,
                "request": request,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def interactive_mode(self) -> None:
        """
        Run in interactive mode, accepting user input.

        Starts an interactive command-line interface that accepts
        user requests and processes them through the Galaxy framework.
        """
        self.logger.info("🎯 Starting interactive mode. Type 'quit' or 'exit' to stop.")

        # Display interactive banner
        self.display.show_interactive_banner()

        request_count = 0

        while True:
            try:
                # Get user input with rich prompt
                user_input = self.display.get_user_input(
                    f"[bold blue]UFO[{request_count}][/bold blue]"
                )

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    self.display.print_warning("👋 Goodbye!")
                    break
                elif user_input.lower() in ["help", "h"]:
                    self.display.show_help()
                    continue
                elif user_input.lower() in ["status", "s"]:
                    self._show_status()
                    continue
                elif user_input.lower() in ["clear", "c"]:
                    self.display.clear_screen()
                    continue

                # Process the request
                self.display.show_processing_status("🚀 Processing your request...")
                result = await self.process_request(
                    user_input, f"interactive_task_{request_count}"
                )

                # Display result
                self.display.display_result(result)
                request_count += 1

            except KeyboardInterrupt:
                self.display.print_warning("\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                self.logger.error(f"Interactive mode error: {e}", exc_info=True)
                self.display.print_error(f"❌ Error: {e}")

    def _show_status(self) -> None:
        """
        Show current session status using the display manager.
        """
        session_info = {
            "client_initialized": self._client is not None,
            "last_session_rounds": len(self._session._rounds) if self._session else 0,
        }

        self.display.show_status(
            self.session_name, self.max_rounds, self.output_dir, session_info
        )

    async def shutdown(self) -> None:
        """
        Shutdown the Galaxy client.

        Properly closes all components including the constellation client
        and session, ensuring clean resource cleanup.
        """
        try:
            self.display.print_warning("🛑 Shutting down Galaxy client...")
            self.logger.info("🛑 Shutting down Galaxy client...")

            if self._client:
                await self._client.shutdown()

            if self._session:
                # Force finish session if needed
                await self._session.force_finish("Client shutdown")

            self.display.print_success("✅ Galaxy client shutdown complete")
            self.logger.info("✅ Galaxy client shutdown complete")

        except Exception as e:
            self.display.print_error(f"Error during shutdown: {e}")
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)


# Note: This file now serves as a client library.
# For command-line usage, use galaxy.py as the main entry point.
