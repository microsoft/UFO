# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Dict

from ufo.agents.processors.app_agent_processor import (
    AppAgentProcessor,
    AppAgentRequestLog,
)
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.agents.agent.follower_agent import FollowerAgent

configs = Config.get_instance().config_data


@dataclass
class FollowerAgentRequestLog(AppAgentRequestLog):
    """
    The request log data for the AppAgent.
    """

    current_state: Dict[str, Any]
    state_diff: Dict[str, Any]


class FollowerAppAgentProcessor(AppAgentProcessor):
    """
    The processor for the AppAgent in the follower mode.
    """

    def __init__(self, agent: "FollowerAgent", context: Context) -> None:
        """
        Initialize the FollowerAppAgentProcessor.
        :param app_agent: The AppAgent instance.
        """
        super().__init__(agent, context)
        self.subtask = self.context.get(ContextNames.REQUEST)

    @AppAgentProcessor.exception_capture
    @AppAgentProcessor.method_timer
    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent in the follower mode. It may accept additional prompts as input.
        """

        examples, tips = self.demonstration_prompt_helper()

        external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(
            self.request,
            configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"],
            configs["RAG_ONLINE_RETRIEVED_TOPK"],
        )

        if not self.app_agent.blackboard.is_empty():
            blackboard_prompt = self.app_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        # Get the current state of the application and the state difference between the current state and the previous state.
        current_state = {}
        state_diff = {}

        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=examples,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self._image_url,
            control_info=self.filtered_control_info,
            prev_subtask=[],
            plan=self.prev_plan,
            subtask=self.request,
            request=self.request,
            host_message=[],
            current_state=current_state,
            state_diff=state_diff,
            blackboard_prompt=blackboard_prompt,
            include_last_screenshot=configs["INCLUDE_LAST_SCREENSHOT"],
        )

        request_data = FollowerAgentRequestLog(
            step=self.session_step,
            dynamic_examples=examples,
            dynamic_knowledge=external_knowledge_prompt,
            image_list=self._image_url,
            prev_subtask=[],
            plan=self.prev_plan,
            request=self.request,
            control_info=self.filtered_control_info,
            subtask=self.request,
            host_message=[],
            blackboard_prompt=blackboard_prompt,
            include_last_screenshot=configs["INCLUDE_LAST_SCREENSHOT"],
            prompt=self._prompt_message,
        )

        request_log_str = json.dumps(asdict(request_data), indent=4, ensure_ascii=False)
        self.request_logger.debug(request_log_str)
