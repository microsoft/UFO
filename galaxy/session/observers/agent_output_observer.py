# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Observer for agent output events.

This observer handles AGENT_RESPONSE and AGENT_ACTION events,
delegating the actual printing logic to presenters.
"""

import logging
from typing import TYPE_CHECKING

from galaxy.core.events import AgentEvent, Event, EventType, IEventObserver
from galaxy.agents.schema import ConstellationAgentResponse
from ufo.agents.processors.schemas.actions import (
    ActionCommandInfo,
    ListActionCommandInfo,
)
from ufo.agents.presenters import PresenterFactory

if TYPE_CHECKING:
    from ufo.agents.presenters.base_presenter import BasePresenter


class AgentOutputObserver(IEventObserver):
    """
    Observer that handles agent output events and delegates to presenters.

    This observer listens for AGENT_RESPONSE and AGENT_ACTION events
    and uses the appropriate presenter to display the output.
    """

    def __init__(self, presenter_type: str = "rich"):
        """
        Initialize the agent output observer.

        :param presenter_type: Type of presenter to use ("rich", "text", etc.)
        """
        self.logger = logging.getLogger(__name__)
        self.presenter: "BasePresenter" = PresenterFactory.create_presenter(
            presenter_type
        )

    async def on_event(self, event: Event) -> None:
        """
        Handle agent output events.

        :param event: The event to handle
        """
        if not isinstance(event, AgentEvent):
            return

        try:
            if event.event_type == EventType.AGENT_RESPONSE:
                await self._handle_agent_response(event)
            elif event.event_type == EventType.AGENT_ACTION:
                await self._handle_agent_action(event)
        except Exception as e:
            self.logger.error(f"Error handling agent output event: {e}")

    async def _handle_agent_response(self, event: AgentEvent) -> None:
        """
        Handle agent response event.

        :param event: The agent response event
        """
        try:
            output_data = event.output_data

            # Check if this is a constellation agent response
            if event.agent_type == "constellation":
                # Reconstruct ConstellationAgentResponse from output data
                response = ConstellationAgentResponse.model_validate(output_data)
                print_action = output_data.get("print_action", False)

                # Use presenter to display the response
                self.presenter.present_constellation_agent_response(
                    response, print_action=print_action
                )
            else:
                # Handle other agent types if needed
                self.logger.debug(
                    f"Received response from {event.agent_type} agent: {event.agent_name}"
                )

        except Exception as e:
            self.logger.error(f"Error handling agent response: {e}")

    async def _handle_agent_action(self, event: AgentEvent) -> None:
        """
        Handle agent action event.

        :param event: The agent action event
        """
        try:
            output_data = event.output_data

            # Check if this is constellation editing actions
            if output_data.get("action_type") == "constellation_editing":
                # Reconstruct ActionCommandInfo objects from output data
                actions_data = output_data.get("actions", [])

                # Convert each action dict to ActionCommandInfo using Pydantic
                action_objects = []
                for action_dict in actions_data:
                    action_obj = ActionCommandInfo.model_validate(action_dict)
                    action_objects.append(action_obj)

                # Create ListActionCommandInfo with the reconstructed actions
                actions = ListActionCommandInfo(actions=action_objects)

                # Use presenter to display the actions
                self.presenter.present_constellation_editing_actions(actions)
            elif output_data.get("action_type") == "constellation_creation":
                # For creation mode, do nothing (as per original logic)
                pass
            else:
                # Handle other action types if needed
                self.logger.debug(
                    f"Received action from {event.agent_type} agent: {event.agent_name}"
                )

        except Exception as e:
            self.logger.error(f"Error handling agent action: {e}")
