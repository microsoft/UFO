# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
GalaxySession - DAG-based Task Orchestration Session

This module provides the GalaxySession class that extends BaseSession to support
DAG-based task orchestration using the Galaxy framework. The session manages
the lifecycle of constellation execution and coordinates between WeaverAgent
and TaskOrchestration.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Callable

from ufo.module.basic import BaseSession, BaseRound
from ufo.module.context import Context, ContextNames

from ..agents.weaver_agent import WeaverAgent
from ..constellation import TaskOrchestration, TaskConstellation, TaskStatus
from ..constellation.enums import ConstellationState
from ..client.constellation_client_modular import ModularConstellationClient


class GalaxyRound(BaseRound):
    """
    A round in GalaxySession that manages constellation execution.
    """

    def __init__(
        self,
        request: str,
        agent: WeaverAgent,
        context: Context,
        should_evaluate: bool,
        id: int,
        orchestration: TaskOrchestration,
    ):
        """Initialize GalaxyRound with orchestration support."""
        super().__init__(request, agent, context, should_evaluate, id)
        self._orchestration = orchestration
        self._constellation: Optional[TaskConstellation] = None
        self._task_results: Dict[str, Any] = {}
        self._execution_start_time: Optional[float] = None

    async def run(self) -> None:
        """Run the round with constellation orchestration."""
        try:
            self.logger.info(
                f"Starting GalaxyRound {self._id} with request: {self._request[:100]}..."
            )

            # Step 1: Generate initial constellation from request
            self._constellation = await self._agent.process_initial_request(
                self._request, self._context
            )

            if not self._constellation:
                self.logger.error("Failed to generate constellation from request")
                return

            self.logger.info(
                f"Generated constellation with {self._constellation.task_count} tasks"
            )

            # Display the newly created constellation DAG
            try:
                self._constellation.display_dag("overview", force=True)
            except Exception as e:
                self.logger.warning(f"Failed to display DAG visualization: {e}")

            # Step 2: Set up orchestration and start execution
            self._execution_start_time = time.time()

            # Assign devices automatically
            await self._orchestration.assign_devices_automatically(self._constellation)

            # Execute constellation with progress callback
            result = await self._orchestration.orchestrate_constellation(
                self._constellation, progress_callback=self._sync_progress_callback
            )

            execution_time = time.time() - self._execution_start_time
            self.logger.info(
                f"Constellation execution completed in {execution_time:.2f}s"
            )

            # Process any remaining progress updates asynchronously
            await self._process_progress_queue()

            # Update context with results - use existing SUBTASK context
            self._context.set(
                ContextNames.SUBTASK,
                f"Constellation execution result: {result.get('status', 'completed')}",
            )

        except Exception as e:
            self.logger.error(f"Error in GalaxyRound execution: {e}")
            import traceback

            traceback.print_exc()

    def _sync_progress_callback(
        self, task_id: str, status: TaskStatus, result: Any = None
    ) -> None:
        """
        Synchronous wrapper for async progress callback.

        This method handles task progress updates from the orchestration system.
        It provides a synchronous interface to avoid async conflicts while
        storing progress data for later async processing.

        Args:
            task_id: ID of the task being updated
            status: Current task status
            result: Task result if completed
        """
        try:
            # Log progress synchronously to avoid async issues
            self.logger.info(f"Task progress: {task_id} -> {status.value}")

            # Initialize progress queue if it doesn't exist
            if not hasattr(self, "_task_progress_queue"):
                self._task_progress_queue = []

            # Store progress for later async processing
            progress_entry = {
                "task_id": task_id,
                "status": status,
                "result": result,
                "timestamp": time.time(),
            }
            self._task_progress_queue.append(progress_entry)

            # Store in task results for immediate access
            self._task_results[task_id] = progress_entry

        except Exception as e:
            self.logger.error(f"Error in progress callback for task {task_id}: {e}")

    async def _process_progress_queue(self) -> None:
        """
        Process the progress queue asynchronously.

        This method handles any queued progress updates that require
        async processing, such as updating constellation state or
        triggering agent actions.
        """
        if not hasattr(self, "_task_progress_queue"):
            return

        while self._task_progress_queue:
            progress_entry = self._task_progress_queue.pop(0)
            try:
                await self._on_task_progress(
                    progress_entry["task_id"],
                    progress_entry["status"],
                    progress_entry.get("result"),
                )
            except Exception as e:
                self.logger.error(f"Error processing progress queue: {e}")

    async def _on_task_progress(
        self, task_id: str, status: TaskStatus, result: Any = None
    ) -> None:
        """
        Handle task progress updates and trigger agent updates.

        Args:
            task_id: ID of the task
            status: Current task status
            result: Task result if completed
        """
        try:
            self.logger.info(f"Task progress: {task_id} -> {status.value}")

            # Store result for later processing
            self._task_results[task_id] = {
                "task_id": task_id,
                "status": status.value,
                "result": result,
                "timestamp": time.time(),
            }

            # If task completed or failed, update constellation via agent
            if status in [TaskStatus.completed, TaskStatus.failed]:
                if isinstance(self._agent, WeaverAgent):
                    updated_constellation = (
                        await self._agent.update_constellation_with_lock(
                            self._task_results[task_id], self._context
                        )
                    )

                    # Update our local reference
                    self._constellation = updated_constellation

                    # Check if we need to add new tasks to orchestration
                    await self._check_for_new_tasks()

        except Exception as e:
            self.logger.error(f"Error handling task progress: {e}")

    async def _check_for_new_tasks(self) -> None:
        """Check if new tasks were added and schedule them for execution."""
        if not self._constellation:
            return

        # Get ready tasks that haven't been executed yet
        ready_tasks = self._constellation.get_ready_tasks()

        for task in ready_tasks:
            if task.task_id not in self._task_results:
                self.logger.info(f"New ready task detected: {task.task_id}")
                # The orchestration will pick up new ready tasks automatically

    @property
    def constellation(self) -> Optional[TaskConstellation]:
        """Get the current constellation."""
        return self._constellation

    @property
    def task_results(self) -> Dict[str, Any]:
        """Get all task results."""
        return self._task_results


class GalaxySession(BaseSession):
    """
    Galaxy Session for DAG-based task orchestration.

    This session extends BaseSession to support constellation-based task execution
    using WeaverAgent for DAG management and TaskOrchestration for execution.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: str,
        agent: Optional[WeaverAgent] = None,
        modular_client: Optional[ModularConstellationClient] = None,
        initial_request: str = "",
    ):
        """
        Initialize GalaxySession.

        Args:
            task: Task name/description
            should_evaluate: Whether to evaluate the session
            id: Session ID
            agent: WeaverAgent instance (creates MockWeaverAgent if None)
            modular_client: ModularConstellationClient for device management
            initial_request: Initial user request
        """
        super().__init__(task, should_evaluate, id)

        # Import config
        from ufo.config import Config

        self._config = Config.get_instance().config_data

        # Set up agent
        if agent is None:
            from ..agents.weaver_agent import MockWeaverAgent

            self._weaver_agent = MockWeaverAgent()
        else:
            self._weaver_agent = agent

        # Set up client and orchestration
        self._modular_client = modular_client
        self._orchestration = TaskOrchestration(
            modular_client=modular_client, enable_logging=True
        )

        # Session state
        self._initial_request = initial_request
        self._current_constellation: Optional[TaskConstellation] = None
        self._session_start_time: Optional[float] = None
        self._session_results: Dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        """Run the Galaxy session with constellation orchestration."""
        try:
            self.logger.info(f"Starting GalaxySession: {self.task}")
            self._session_start_time = time.time()

            # Run base session logic with constellation support
            await super().run()

            # Calculate total session time
            if self._session_start_time:
                total_time = time.time() - self._session_start_time
                self.logger.info(f"GalaxySession completed in {total_time:.2f}s")
                self._session_results["total_execution_time"] = total_time

            # Final constellation status
            if self._current_constellation:
                self._session_results["final_constellation_stats"] = (
                    self._current_constellation.get_statistics()
                )
                self._session_results["agent_status"] = self._weaver_agent.agent_status

        except Exception as e:
            self.logger.error(f"Error in GalaxySession: {e}")
            import traceback

            traceback.print_exc()

    def is_error(self) -> bool:
        """
        Check if the session is in error state.
        Override base implementation to handle Galaxy-specific logic.
        """
        # Check if weaver agent indicates error
        if self._weaver_agent and hasattr(self._weaver_agent, "_status"):
            return self._weaver_agent._status == "failed"

        # Check if current constellation failed
        if self._current_constellation:
            return self._current_constellation.state == ConstellationState.FAILED

        # Fall back to checking rounds if they exist
        if (
            self.current_round is not None
            and hasattr(self.current_round, "state")
            and self.current_round.state is not None
        ):
            try:
                from ufo.agents.states.basic import AgentStatus

                return self.current_round.state.name() == AgentStatus.ERROR.value
            except (AttributeError, ImportError):
                pass

        return False

    def is_finished(self) -> bool:
        """
        Check if the session is finished.
        Override base implementation to handle Galaxy-specific logic.
        """
        # Check standard completion conditions
        if (
            self._finish
            or self.step >= self._config.get("MAX_STEP", 100)
            or self.total_rounds >= self._config.get("MAX_ROUND", 10)
        ):
            return True

        # Check if in error state
        if self.is_error():
            return True

        # Check if weaver agent indicates completion
        if self._weaver_agent and hasattr(self._weaver_agent, "_status"):
            return self._weaver_agent._status in ["finished", "failed"]

        # Check if constellation is completed
        if self._current_constellation:
            return self._current_constellation.state in [
                ConstellationState.COMPLETED,
                ConstellationState.FAILED,
                ConstellationState.PARTIALLY_FAILED,
            ]

        return False

    def create_new_round(self) -> Optional[GalaxyRound]:
        """Create a new GalaxyRound."""
        request = self.next_request()
        if not request:
            return None

        round_id = len(self._rounds)

        galaxy_round = GalaxyRound(
            request=request,
            agent=self._weaver_agent,
            context=self._context,
            should_evaluate=self._should_evaluate,
            id=round_id,
            orchestration=self._orchestration,
        )

        self.add_round(round_id, galaxy_round)
        return galaxy_round

    def next_request(self) -> str:
        """Get the next request for the session."""
        # For now, only process one request per session
        if len(self._rounds) == 0:
            return self._initial_request or self.task
        return ""  # No more requests

    def request_to_evaluate(self) -> str:
        """Get the request for evaluation."""
        return self._initial_request or self.task

    def set_modular_client(self, client: ModularConstellationClient) -> None:
        """Set the modular constellation client."""
        self._modular_client = client
        self._orchestration.set_modular_client(client)

    def set_weaver_agent(self, agent: WeaverAgent) -> None:
        """Set the weaver agent."""
        self._weaver_agent = agent

    async def get_session_status(self) -> Dict[str, Any]:
        """Get comprehensive session status."""
        status = {
            "session_id": self._id,
            "task": self.task,
            "rounds_completed": len(self._rounds),
            "agent_status": self._weaver_agent.agent_status,
            "session_results": self._session_results,
        }

        if self._weaver_agent.current_constellation:
            status["constellation_stats"] = (
                self._weaver_agent.get_constellation_statistics()
            )

        return status

    async def force_finish(self, reason: str = "Manual termination") -> None:
        """Force finish the session."""
        self.logger.info(f"Force finishing session: {reason}")
        self._finish = True
        self._weaver_agent.agent_status = "finished"
        self._session_results["finish_reason"] = reason

    @property
    def current_constellation(self) -> Optional[TaskConstellation]:
        """Get the current constellation."""
        return self._weaver_agent.current_constellation

    @property
    def weaver_agent(self) -> WeaverAgent:
        """Get the weaver agent."""
        return self._weaver_agent

    @property
    def orchestration(self) -> TaskOrchestration:
        """Get the task orchestration."""
        return self._orchestration

    @property
    def session_results(self) -> Dict[str, Any]:
        """Get session results."""
        return self._session_results


# Convenience functions for easy session creation
async def create_galaxy_session(
    request: str,
    task_name: str = "galaxy_task",
    session_id: Optional[str] = None,
    agent: Optional[WeaverAgent] = None,
    modular_client: Optional[ModularConstellationClient] = None,
    should_evaluate: bool = False,
) -> GalaxySession:
    """
    Create a GalaxySession with default configuration.

    Args:
        request: User request string
        task_name: Task name
        session_id: Optional session ID
        agent: Optional WeaverAgent
        modular_client: Optional ModularConstellationClient
        should_evaluate: Whether to evaluate the session

    Returns:
        Configured GalaxySession
    """
    if session_id is None:
        import uuid

        session_id = f"galaxy_{uuid.uuid4().hex[:8]}"

    # Create default modular client if not provided
    if modular_client is None:
        from ..client.config_loader import ConstellationConfig

        config = ConstellationConfig()
        modular_client = ModularConstellationClient(config)

    session = GalaxySession(
        task=task_name,
        should_evaluate=should_evaluate,
        id=session_id,
        agent=agent,
        modular_client=modular_client,
        initial_request=request,
    )

    return session


async def run_simple_galaxy_request(
    request: str,
    timeout: float = 300.0,
) -> Dict[str, Any]:
    """
    Run a simple Galaxy request with default configuration.

    Args:
        request: User request string
        timeout: Execution timeout in seconds

    Returns:
        Session results
    """
    session = await create_galaxy_session(request)

    # Run with timeout
    try:
        await asyncio.wait_for(session.run(), timeout=timeout)
    except asyncio.TimeoutError:
        await session.force_finish("Timeout")

    return await session.get_session_status()
