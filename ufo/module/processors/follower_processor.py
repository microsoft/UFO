# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from .processor import AppAgentProcessor, HostAgentProcessor
from ...config.config import Config
from ...agent.agent import FollowerAgent
import json



configs = Config.get_instance().config_data



class FollowerHostAgentProcessor(HostAgentProcessor):

    def create_sub_agent(self) -> FollowerAgent:
        """
        Create the app agent.
        :return: The app agent.
        """

        app_info_prompt = configs.get("APP_INFO_PROMPT", None)

        agent_name = "FollowerAgent/{root}/{process}".format(root=self.app_root, process=self._control_text)

        app_agent = self.host_agent.create_subagent("follower", agent_name, self._control_text, self.app_root, configs["APP_AGENT"]["VISUAL_MODE"], 
                                     configs["FOLLOWERAHENT_PROMPT"], configs["APPAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"], app_info_prompt)
        
        # Create the COM receiver for the app agent.
        if configs.get("USE_APIS", False):
            app_agent.Puppeteer.receiver_manager.create_com_receiver(self.app_root, self._control_text)
            
        self.app_agent_context_provision(app_agent)

        return app_agent



class FollowerAppAgentProcessor(AppAgentProcessor):
    
    def get_prompt_message(self) -> None:
            """
            Get the prompt message for the AppAgent.
            """

            if configs["RAG_EXPERIENCE"]:
                experience_examples, experience_tips = self.app_agent.rag_experience_retrieve(self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"])
            else:
                experience_examples = []
                experience_tips = []
                
            if configs["RAG_DEMONSTRATION"]:
                demonstration_examples, demonstration_tips = self.app_agent.rag_demonstration_retrieve(self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"])
            else:
                demonstration_examples = []
                demonstration_tips = []
            
            examples = experience_examples + demonstration_examples
            tips = experience_tips + demonstration_tips

            external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(self.request, configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"], configs["RAG_ONLINE_RETRIEVED_TOPK"])


            HostAgent = self.app_agent.get_host()

            action_history = HostAgent.get_global_action_memory().to_json()
            request_history = HostAgent.get_request_history_memory().to_json()

            current_state = {}
            state_diff = {}

            self._prompt_message = self.app_agent.message_constructor(examples, tips, external_knowledge_prompt, self._image_url, request_history, action_history, 
                                                                                self.filtered_control_info, self.prev_plan, self.request, current_state, state_diff, configs["INCLUDE_LAST_SCREENSHOT"])
            
            log = json.dumps({"step": self.global_step, "prompt": self._prompt_message, "control_items": self._control_info, 
                              "filted_control_items": self.filtered_control_info, "status": ""})
            self.request_logger.debug(log)