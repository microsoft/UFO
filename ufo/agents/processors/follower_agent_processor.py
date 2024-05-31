# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json

from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.config.config import Config

configs = Config.get_instance().config_data


class FollowerAppAgentProcessor(AppAgentProcessor):
    """
    The processor for the AppAgent in the follower mode.
    """

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
            examples,
            tips,
            external_knowledge_prompt,
            self._image_url,
            self.filtered_control_info,
            self.prev_plan,
            self.request,
            current_state,
            state_diff,
            configs["INCLUDE_LAST_SCREENSHOT"],
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
