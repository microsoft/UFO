# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
GalaxySession - DAG-based Task Orchestration Session

This module provides the GalaxySession class that extends BaseSession to support
DAG-based task orchestration using the Galaxy framework. The session manages
the lifecycle of constellation execution and coordinates between Constellation
and TaskConstellationOrchestrator.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from ufo.module.basic import BaseSession, BaseRound
from ufo.module.context import Context

from ..agents.constellation_agent import ConstellationAgent
from ..constellation import TaskConstellationOrchestrator, TaskConstellation
from ..constellation.enums import ConstellationState
from ..client.constellation_client import ConstellationClient
from ..core.events import get_event_bus
from .observers import (
    ConstellationProgressObserver,
    SessionMetricsObserver,
    DAGVisualizationObserver,
)


class GalaxyRound(BaseRound):
    """
    A round in GalaxySession that manages constellation execution.
    """

    def __init__(
        self,
        request: str,
        agent: ConstellationAgent,
        context: Context,
        should_evaluate: bool,
        id: int,
        orchestrator: TaskConstellationOrchestrator,
    ):
        """
        Initialize GalaxyRound with orchestrator support.

        :param request: User request string
        :param agent: ConstellationAgent instance
        :param context: Context object for the round
        :param should_evaluate: Whether to evaluate the round
        :param id: Round identifier
        :param orchestrator: TaskConstellationOrchestrator for task execution
        """
        super().__init__(request, agent, context, should_evaluate, id)
        self._orchestrator = orchestrator
        self._constellation: Optional[TaskConstellation] = None
        self._task_results: Dict[str, Any] = {}
        self._execution_start_time: Optional[float] = None

        # Event system
        self._event_bus = get_event_bus()
        self._observers = []
        self._agent = agent

        # Set up observers
        self._setup_observers()

    def _setup_observers(self) -> None:
        """
        Set up event observers for this round.

        Initializes progress, metrics, and visualization observers
        and subscribes them to the event bus.
        """
        # Progress observer for task updates
        progress_observer = ConstellationProgressObserver(
            agent=self._agent, context=self._context
        )
        self._observers.append(progress_observer)

        # Metrics observer for performance tracking
        metrics_observer = SessionMetricsObserver(
            session_id=f"galaxy_round_{self._id}", logger=self.logger
        )
        self._observers.append(metrics_observer)

        # DAG visualization observer for constellation visualization
        visualization_observer = DAGVisualizationObserver(enable_visualization=True)
        self._observers.append(visualization_observer)

        # Subscribe observers to event bus
        for observer in self._observers:
            self._event_bus.subscribe(observer)

    async def run(self) -> None:
        """
        Run the round using agent state machine.

        Executes the agent state machine until completion,
        managing state transitions and error handling.
        """
        try:
            self.logger.info(
                f"Starting GalaxyRound {self._id} with request: {self._request[:100]}..."
            )

            # Set up agent with current request and orchestrator
            self._agent.current_request = self._request
            self._agent.orchestrator = self._orchestrator

            # Initialize agent in START state
            from ..agents.constellation_agent_states import StartConstellationAgentState

            self._agent.set_state(StartConstellationAgentState())

            # Run agent state machine until completion
            while not self._agent.state.is_round_end():
                # Execute current state
                await self._agent.handle(self._context)

                # Transition to next state
                next_state = self._agent.state.next_state(self._agent)
                next_agent = self._agent.state.next_agent(self._agent)

                # Update agent state
                self._agent.set_state(next_state)
                self._agent = next_agent

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.01)

            # Get final constellation for context update
            if self._agent.current_constellation:
                self._constellation = self._agent.current_constellation

                self.logger.info(
                    f"GalaxyRound {self._id} completed with status: {self._agent._status}"
                )

        except Exception as e:
            self.logger.error(f"Error in GalaxyRound execution: {e}")
            import traceback

            traceback.print_exc()

    async def _check_for_new_tasks(self) -> None:
        """
        Check if new tasks were added and schedule them for execution.

        Identifies ready tasks that haven't been executed yet
        and logs them for orchestrator pickup.
        """
        if not self._constellation:
            return

        # Get ready tasks that haven't been executed yet
        ready_tasks = self._constellation.get_ready_tasks()

        for task in ready_tasks:
            if task.task_id not in self._task_results:
                self.logger.info(f"New ready task detected: {task.task_id}")
                # The orchestrator will pick up new ready tasks automatically

    @property
    def constellation(self) -> Optional[TaskConstellation]:
        """
        Get the current constellation.

        :return: TaskConstellation instance if available, None otherwise
        """
        return self._constellation

    @property
    def task_results(self) -> Dict[str, Any]:
        """
        Get all task results.

        :return: Dictionary mapping task IDs to their results
        """
        return self._task_results


class GalaxySession(BaseSession):
    """
    Galaxy Session for DAG-based task orchestrator.

    This session extends BaseSession to support constellation-based task execution
    using Constellation for DAG management and TaskConstellationOrchestrator for execution.
    """

    def __init__(
        self,
        task: str,
        should_evaluate: bool,
        id: str,
        agent: Optional[ConstellationAgent] = None,
        client: Optional[ConstellationClient] = None,
        initial_request: str = "",
    ):
        """
        Initialize GalaxySession.

        :param task: Task name/description
        :param should_evaluate: Whether to evaluate the session
        :param id: Session ID
        :param agent: ConstellationAgent instance (creates MockConstellationAgent if None)
        :param client: ConstellationClient for device management
        :param initial_request: Initial user request
        """
        super().__init__(task, should_evaluate, id)

        # Import config
        from ufo.config import Config

        self._config = Config.get_instance().config_data

        # Set up agent
        if agent is None:
            from ..agents.constellation_agent import MockConstellation

            self._weaver_agent = MockConstellation()
        else:
            self._weaver_agent = agent

        # Set up client and orchestrator
        self._client = client
        self._orchestrator = TaskConstellationOrchestrator(
            device_manager=client.device_manager, enable_logging=True
        )

        # Session state
        self._initial_request = initial_request
        self._current_constellation: Optional[TaskConstellation] = None
        self._session_start_time: Optional[float] = None
        self._session_results: Dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)

    async def run(self) -> None:
        """
        Run the Galaxy session with constellation orchestrator.

        Executes the session using the base session logic with
        constellation support and tracks performance metrics.
        """
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

        Override base implementation to handle Galaxy-specific logic
        by checking weaver agent status and constellation state.

        :return: True if session is in error state, False otherwise
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

        Override base implementation to handle Galaxy-specific logic
        by checking completion conditions, error states, and constellation status.

        :return: True if session is finished, False otherwise
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
        """
        Create a new GalaxyRound.

        :return: GalaxyRound instance if request is available, None otherwise
        """
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
            orchestrator=self._orchestrator,
        )

        self.add_round(round_id, galaxy_round)
        return galaxy_round

    def next_request(self) -> str:
        """
        Get the next request for the session.

        :return: Request string for the next round, empty string if no more requests
        """
        # For now, only process one request per session
        if len(self._rounds) == 0:
            return self._initial_request or self.task
        return ""  # No more requests

    def request_to_evaluate(self) -> str:
        """
        Get the request for evaluation.

        :return: Request string to be used for evaluation
        """
        return self._initial_request or self.task

    def set_client(self, client: ConstellationClient) -> None:
        """
        Set the modular constellation client.

        :param client: ConstellationClient instance for device management
        """
        self._client = client
        self._orchestrator.set_client(client)

    def set_weaver_agent(self, agent: ConstellationAgent) -> None:
        """
        Set the weaver agent.

        :param agent: ConstellationAgent instance for task orchestration
        """
        self._weaver_agent = agent

    async def get_session_status(self) -> Dict[str, Any]:
        """
        Get comprehensive session status.

        :return: Dictionary containing session status information
        """
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
        """
        Force finish the session.

        :param reason: Reason for forcing the finish (default: "Manual termination")
        """
        self.logger.info(f"Force finishing session: {reason}")
        self._finish = True
        self._weaver_agent.agent_status = "finished"
        self._session_results["finish_reason"] = reason

    @property
    def current_constellation(self) -> Optional[TaskConstellation]:
        """
        Get the current constellation.

        :return: TaskConstellation instance from weaver agent if available
        """
        return self._weaver_agent.current_constellation

    @property
    def weaver_agent(self) -> ConstellationAgent:
        """
        Get the weaver agent.

        :return: ConstellationAgent instance for task orchestration
        """
        return self._weaver_agent

    @property
    def orchestrator(self) -> TaskConstellationOrchestrator:
        """
        Get the task orchestrator.

        :return: TaskConstellationOrchestrator instance for execution management
        """
        return self._orchestrator

    @property
    def session_results(self) -> Dict[str, Any]:
        """
        Get session results.

        :return: Dictionary containing session execution results and metrics
        """
        return self._session_results


# Convenience functions for easy session creation
async def create_galaxy_session(
    request: str,
    task_name: str = "galaxy_task",
    session_id: Optional[str] = None,
    agent: Optional[ConstellationAgent] = None,
    client: Optional[ConstellationClient] = None,
    should_evaluate: bool = False,
) -> GalaxySession:
    """
    Create a GalaxySession with default configuration.

    :param request: User request string
    :param task_name: Task name (default: "galaxy_task")
    :param session_id: Optional session ID (auto-generated if None)
    :param agent: Optional ConstellationAgent instance
    :param client: Optional ConstellationClient instance
    :param should_evaluate: Whether to evaluate the session (default: False)
    :return: Configured GalaxySession instance
    """
    if session_id is None:
        import uuid

        session_id = f"galaxy_{uuid.uuid4().hex[:8]}"

    # Create default modular client if not provided
    if client is None:
        from ..client.config_loader import ConstellationConfig

        config = ConstellationConfig()
        client = ConstellationClient(config)

    session = GalaxySession(
        task=task_name,
        should_evaluate=should_evaluate,
        id=session_id,
        agent=agent,
        client=client,
        initial_request=request,
    )

    return session


async def run_simple_galaxy_request(
    request: str,
    timeout: float = 300.0,
) -> Dict[str, Any]:
    """
    Run a simple Galaxy request with default configuration.

    :param request: User request string
    :param timeout: Execution timeout in seconds (default: 300.0)
    :return: Dictionary containing session results and status
    """
    session = await create_galaxy_session(request)

    # Run with timeout
    try:
        await asyncio.wait_for(session.run(), timeout=timeout)
    except asyncio.TimeoutError:
        await session.force_finish("Timeout")

    return await session.get_session_status()
