# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json

from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.config.config import Config
from typing import TYPE_CHECKING
from ufo.module.context import Context, ContextNames

if TYPE_CHECKING:
    from ufo.agents.agent.follower_agent import FollowerAgent

configs = Config.get_instance().config_data


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

        # Get the current state of the application and the state difference between the current state and the previous state.
        current_state = {}
        state_diff = {}

        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=examples,
            dynamic_tips=tips,
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
            include_last_screenshot=configs["INCLUDE_LAST_SCREENSHOT"],
        )

        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "control_items": self._control_info,
                "filted_control_items": self.filtered_control_info,
                "status": "",
            }
        )
        self.request_logger.debug(log)
