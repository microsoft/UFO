# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json

from ufo.agent.agent import FollowerAgent
from ufo.config.config import Config
from ufo.module.processors.processor import AppAgentProcessor, HostAgentProcessor

configs = Config.get_instance().config_data


class FollowerHostAgentProcessor(HostAgentProcessor):
    """
    Follower host agent processor to handle the AppAgent in the follower mode.
    """

    def create_sub_agent(self) -> FollowerAgent:
        """
        Create a follower subagent for the host agent.
        :return: The created sub agent.
        """

        # Load additional app info prompt.
        app_info_prompt = configs.get("APP_INFO_PROMPT", None)

        agent_name = "FollowerAgent/{root}/{process}".format(
            root=self.app_root, process=self._control_text
        )

        # Create the app agent in the follower mode.
        app_agent = self.host_agent.create_subagent(
            "follower",
            agent_name,
            self._control_text,
            self.app_root,
            configs["APP_AGENT"]["VISUAL_MODE"],
            configs["FOLLOWERAHENT_PROMPT"],
            configs["APPAGENT_EXAMPLE_PROMPT"],
            configs["API_PROMPT"],
            app_info_prompt,
        )

        # Create the COM receiver for the app agent.
        if configs.get("USE_APIS", False):
            app_agent.Puppeteer.receiver_manager.create_com_receiver(
                self.app_root, self._control_text
            )

        self.app_agent_context_provision(app_agent)

        return app_agent


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

        host_agent = self.app_agent.get_host()

        action_history = host_agent.get_global_action_memory().to_json()
        request_history = host_agent.get_request_history_memory().to_json()

        # Get the current state of the application and the state difference between the current state and the previous state.
        current_state = {}
        state_diff = {}

        self._prompt_message = self.app_agent.message_constructor(
            examples,
            tips,
            external_knowledge_prompt,
            self._image_url,
            request_history,
            action_history,
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
