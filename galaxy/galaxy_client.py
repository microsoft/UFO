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

import asyncio
import json
import logging
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

from config.config_loader import get_galaxy_config
from galaxy.client.config_loader import ConstellationConfig
from ufo.logging.setup import setup_logger

from .client.constellation_client import ConstellationClient
from .session.galaxy_session import GalaxySession
from .visualization.client_display import ClientDisplay

tracemalloc.start()

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
        task_name: Optional[str] = None,
        max_rounds: int = 10,
        log_level: str = "WARNING",
        output_dir: Optional[str] = None,
    ):
        """
        Initialize Galaxy client.

        :param session_name: Name for the Galaxy session (auto-generated if None)
        :param task_name: Name for the task (auto-generated if None)
        :param max_rounds: Maximum number of rounds per session (default: 10)
        :param log_level: Logging level (default: "WARNING")
        :param output_dir: Output directory for logs and results (default: None, uses session log path)
        """
        self.session_name = (
            session_name or f"galaxy_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        # Generate task_name with timestamp if not provided
        self.task_name = (
            task_name or f"request_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.max_rounds = max_rounds
        self.output_dir = Path(output_dir) if output_dir else None

        # Setup logging only if not already configured
        # (galaxy.py already calls setup_logger before importing GalaxyClient)
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            setup_logger(log_level)
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._client: Optional[ConstellationClient] = None
        self._session: Optional[GalaxySession] = None
        self._current_request_task: Optional[asyncio.Task] = None
        self._is_shutting_down: bool = False

        # Load device configuration from new config system
        galaxy_config = get_galaxy_config()
        device_info_path = galaxy_config.constellation.DEVICE_INFO
        self._device_config = ConstellationConfig.from_yaml(device_info_path)

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
                self._client = ConstellationClient(
                    config=self._device_config, task_name=self.task_name
                )
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

    async def process_request(self, request: str) -> Dict[str, Any]:
        """
        Process a single user request.

        :param request: User request text to process
        :return: Dictionary containing processing result with execution details
        :raises RuntimeError: If Galaxy client is not initialized
        """
        if not self._client:
            raise RuntimeError(
                "Galaxy client not initialized. Call initialize() first."
            )

        # Save current task reference for cancellation support
        self._current_request_task = asyncio.current_task()

        try:
            self.display.print_info(
                f"[bold yellow]📝 Processing request:[/bold yellow] [white]{request[:100]}{'...' if len(request) > 100 else ''}[/white]"
            )
            self.logger.info(f"📝 Processing request: {request[:100]}...")

            # Quick check: count devices in connected states (CONNECTED, IDLE, or BUSY)
            from galaxy.client.components.types import DeviceStatus

            all_devices = self._client.device_manager.device_registry.get_all_devices()
            connected_devices_count = sum(
                1
                for device in all_devices.values()
                if device.status
                in [DeviceStatus.CONNECTED, DeviceStatus.IDLE, DeviceStatus.BUSY]
            )
            total_devices_count = len(all_devices)

            if connected_devices_count < total_devices_count:
                self.logger.info(
                    f"🔌 Detected {total_devices_count - connected_devices_count} disconnected devices, attempting reconnection..."
                )
                self.display.print_info(
                    "[cyan]🔌 Reconnecting disconnected devices...[/cyan]"
                )
                connection_results = await self._client.ensure_devices_connected()
                connected_count = sum(
                    1 for connected in connection_results.values() if connected
                )

                if connected_count < total_devices_count:
                    self.display.print_warning(
                        f"⚠️  Only {connected_count}/{total_devices_count} devices connected"
                    )
                    self.logger.warning(
                        f"⚠️  Only {connected_count}/{total_devices_count} devices connected"
                    )
                else:
                    self.display.print_success(
                        f"✅ All {connected_count} devices reconnected"
                    )
                    self.logger.info(f"✅ All devices reconnected")

                # DEBUG: Log device registry state after reconnection
                all_devices_after = (
                    self._client.device_manager.device_registry.get_all_devices()
                )
                self.logger.info(
                    f"🔍 DEBUG: After reconnection, device registry contains {len(all_devices_after)} devices: {list(all_devices_after.keys())}"
                )

            # Use the task_name set during initialization or updated externally
            task_name = self.task_name

            # Clean up old session observers before creating new session
            if self._session:
                self.logger.info("🧹 Cleaning up observers from previous session...")
                self._session._cleanup_observers()
                self.logger.info("✅ Previous session observers cleaned up")

            # Create a new session for this request
            session_id = f"{self.session_name}_{task_name}"
            self._session = GalaxySession(
                task=task_name,
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

            # Collect results - check if session is still valid
            if not self._session:
                self.logger.warning("Session was terminated during execution")
                return {
                    "session_name": self.session_name,
                    "request": request,
                    "task_name": task_name,
                    "status": "stopped",
                    "execution_time": execution_time,
                    "message": "Task was stopped by user",
                    "timestamp": datetime.now().isoformat(),
                }

            result = {
                "session_name": self.session_name,
                "request": request,
                "task_name": task_name,
                "status": "completed",
                "execution_time": execution_time,
                "rounds": len(self._session._rounds) if self._session._rounds else 0,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "trajectory_path": (
                    self._session.log_path
                    if hasattr(self._session, "log_path")
                    else None
                ),
                "session_results": (
                    self._session.session_results
                    if hasattr(self._session, "session_results")
                    else None
                ),
            }

            # Add constellation info if available
            if self._session and self._session.current_constellation:
                constellation = self._session.current_constellation
                result["constellation"] = {
                    "id": constellation.constellation_id,
                    "name": constellation.name,
                    "task_count": len(constellation.tasks),
                    "dependency_count": len(constellation.dependencies),
                    "state": (constellation.state.value),
                }

            self.display.print_success(
                f"✅ Request processed successfully in {execution_time:.2f}s"
            )
            self.logger.info(
                f"✅ Request processed successfully in {execution_time:.2f}s"
            )

            # Save result to file
            self._save_result(result)

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
        finally:
            # Clear task reference
            self._current_request_task = None

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

                # Temporarily set task_name for this request
                original_task_name = self.task_name
                self.task_name = f"interactive_task_{request_count}"

                result = await self.process_request(user_input)

                # Restore original task_name
                self.task_name = original_task_name

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

    def _save_result(self, result: Dict[str, Any]) -> None:
        """
        Save result to JSON file.

        If output_dir is specified, saves to output_dir.
        Otherwise, saves to the session's log_path.

        :param result: Result dictionary to save
        """
        try:
            # Determine output path
            if self.output_dir:
                output_path = self.output_dir / f"{self.session_name}_result.json"
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Save to session log path
                if self._session and self._session.log_path:
                    output_path = Path(self._session.log_path) / "result.json"
                else:
                    # Fallback to default logs directory
                    output_path = Path("./logs") / f"{self.session_name}_result.json"
                    output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save result to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            self.display.print_info(
                f"[bold cyan]📁 Result saved to:[/bold cyan] [green]{output_path}[/green]"
            )
            self.logger.info(f"📁 Result saved to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save result: {e}", exc_info=True)
            self.display.print_warning(f"⚠️ Failed to save result: {e}")

    async def reset_session(self) -> Dict[str, Any]:
        """
        Reset the current session, clearing all state.

        Clears the current session's constellation, tasks, and execution history
        while keeping the same session instance and configuration.

        :return: Dictionary with reset status information
        """
        try:
            self.logger.info("🔄 Resetting current session...")

            if self._session:
                # Reset session state
                self._session.reset()
                self.logger.info("✅ Session state reset")

                return {
                    "status": "success",
                    "message": "Session reset successfully",
                    "session_name": self.session_name,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                self.logger.warning("⚠️ No active session to reset")
                return {
                    "status": "warning",
                    "message": "No active session to reset",
                    "session_name": self.session_name,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            self.logger.error(f"Failed to reset session: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to reset session: {str(e)}",
                "session_name": self.session_name,
                "timestamp": datetime.now().isoformat(),
            }

    async def create_next_session(self) -> Dict[str, Any]:
        """
        Create a new session, replacing the current one.

        Properly cleans up the current session and creates a fresh session
        with a new session ID and timestamp.

        :return: Dictionary with new session information
        """
        try:
            self.logger.info("🔄 Creating next session...")

            # Clean up current session if exists
            if self._session:
                await self._session.force_finish("Starting next session")
                old_session_name = self.session_name
                self.logger.info(f"✅ Previous session {old_session_name} finished")

            # Ensure all devices are connected for the new session
            if self._client:
                self.display.print_info(
                    "[cyan]🔌 Checking device connections for new session...[/cyan]"
                )
                self.logger.info("🔌 Ensuring devices connected for new session...")
                connection_results = await self._client.ensure_devices_connected()
                connected_count = sum(
                    1 for connected in connection_results.values() if connected
                )
                total_count = len(connection_results)

                if connected_count < total_count:
                    self.display.print_warning(
                        f"⚠️  Only {connected_count}/{total_count} devices connected for new session"
                    )
                    self.logger.warning(
                        f"⚠️  Only {connected_count}/{total_count} devices connected"
                    )
                else:
                    self.display.print_success(
                        f"✅ All {connected_count} devices ready for new session"
                    )
                    self.logger.info(f"✅ All {connected_count} devices connected")

            # Generate new session name with timestamp
            self.session_name = (
                f"galaxy_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.task_name = f"request_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Clear session reference (new one will be created on next request)
            self._session = None

            self.logger.info(f"✅ Next session ready: {self.session_name}")

            return {
                "status": "success",
                "message": "Next session created successfully",
                "session_name": self.session_name,
                "task_name": self.task_name,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to create next session: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to create next session: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    async def shutdown(self, force: bool = False) -> None:
        """
        Shutdown the Galaxy client.

        Properly closes all components including the constellation client
        and session, ensuring clean resource cleanup.

        :param force: If True, forcefully cancel any running tasks before shutdown.
                     This is useful for WebUI Stop button to immediately halt execution.
                     If False (default), assumes tasks have completed normally.
        """
        # Prevent multiple concurrent shutdowns
        if self._is_shutting_down:
            self.logger.warning("Shutdown already in progress, skipping duplicate call")
            return

        self._is_shutting_down = True

        try:
            self.display.print_warning("🛑 Shutting down Galaxy client...")
            self.logger.info("🛑 Shutting down Galaxy client...")

            # If force=True, cancel any running request task
            if force and self._current_request_task:
                task = self._current_request_task
                if task and not task.done():
                    self.logger.info("🛑 Forcefully cancelling running request task...")
                    task.cancel()
                    try:
                        # Wait for cancellation to complete with timeout
                        await asyncio.wait_for(task, timeout=2.0)
                        self.logger.info("✅ Task cancelled successfully")
                    except asyncio.CancelledError:
                        self.logger.info("✅ Task cancellation completed")
                    except asyncio.TimeoutError:
                        self.logger.warning(
                            "⚠️ Task cancellation timed out, proceeding anyway"
                        )
                    except Exception as e:
                        self.logger.error(f"Error during task cancellation: {e}")

            # Force finish session if it exists
            if self._session:
                if force:
                    # Use request_cancellation for immediate stop with orchestrator cancellation
                    await self._session.request_cancellation()
                else:
                    await self._session.force_finish("Client shutdown")
                # Clear session reference to prevent access to stale session
                self._session = None

            # Shutdown constellation client
            if self._client:
                await self._client.shutdown()

            self.display.print_success("✅ Galaxy client shutdown complete")
            self.logger.info("✅ Galaxy client shutdown complete")

        except Exception as e:
            self.display.print_error(f"Error during shutdown: {e}")
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            self._is_shutting_down = False


# Note: This file now serves as a client library.
# For command-line usage, use galaxy.py as the main entry point.
