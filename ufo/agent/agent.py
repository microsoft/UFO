# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

import time
from typing import Dict, List

from .. import utils
from ..automator import puppeteer
from ..automator.ui_control import openfile
from ..automator.ui_control import utils as control
from ..config.config import Config
from ..prompter.agent_prompter import (AppAgentPrompter, FollowerAgentPrompter,
                                       HostAgentPrompter)
from .basic import BasicAgent, Memory, MemoryItem

configs = Config.get_instance().config_data

class AgentFactory:  
    """  
    Factory class to create agents.  
    """  
  
    @staticmethod  
    def create_agent(agent_type: str, *args, **kwargs) -> BasicAgent:  
        """  
        Create an agent based on the given type.  
        :param agent_type: The type of agent to create.  
        :return: The created agent.  
        """  
        if agent_type == "host":  
            return HostAgent(*args, **kwargs)  
        elif agent_type == "app":  
            return AppAgent(*args, **kwargs)
        elif agent_type == "follower":
            return FollowerAgent(*args, **kwargs)
        else:  
            raise ValueError("Invalid agent type: {}".format(agent_type))  



class AppAgent(BasicAgent):
    """
    The AppAgent class that manages the interaction with the application.
    """

    def __init__(self, name: str, process_name: str, app_root_name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str, skip_prompter:bool=False) -> None:
        """
        Initialize the AppAgent.
        :name: The name of the agent.
        :param process_name: The process name of the selected application.
        :param app_root_name: The root name of the selected application.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        """

        super().__init__(name=name)
        if not skip_prompter:
            self.prompter = self.get_prompter(is_visual, main_prompt, example_prompt, api_prompt, app_root_name)
        self._process_name = process_name
        self._app_root_name = app_root_name
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None
        self.Puppeteer = self.create_puppteer_interface()
        self.host = None


    def get_prompter(self, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str, app_root_name) -> AppAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return AppAgentPrompter(is_visual, main_prompt, example_prompt, api_prompt, app_root_name)
    

    def message_constructor(self, dynamic_examples: str, dynamic_tips: str, dynamic_knowledge: str, image_list: List,
                             request_history: str, action_history: str, control_info: str, plan: str, request: str, include_last_screenshot: bool) -> list:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_tips: The dynamic tips retrieved from the self-demonstration and human demonstration.
        :param dynamic_knowledge: The dynamic knowledge retrieved from the external knowledge base.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param control_info: The control information.
        :param plan: The plan.
        :param request: The request.
        :param include_last_screenshot: The flag indicating whether to include the last screenshot.
        :return: The prompt message.
        """
        appagent_prompt_system_message = self.prompter.system_prompt_construction(dynamic_examples, dynamic_tips)
        appagent_prompt_user_message = self.prompter.user_content_construction(image_list, request_history, action_history, 
                                                                                                        control_info, plan, request, dynamic_knowledge, include_last_screenshot)
        
        appagent_prompt_message = self.prompter.prompt_construction(appagent_prompt_system_message, appagent_prompt_user_message)

        return appagent_prompt_message
    


    def print_response(self, response_dict: Dict) -> None:
        """
        Print the response.
        :param response: The response dictionary.
        """
        
        control_text = response_dict.get("ControlText")
        control_label = response_dict.get("ControlLabel")
        if not control_text:
            control_text = "[No control selected.]"
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        plan = response_dict.get("Plan")
        status = response_dict.get("Status")
        comment = response_dict.get("Comment")
        function_call = response_dict.get("Function")
        args = utils.revise_line_breaks(response_dict.get("Args"))

        # Generate the function call string
        action = self.Puppeteer.get_command_string(function_call, args)

        utils.print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        utils.print_with_color("Selected item🕹️: {control_text}, Label: {label}".format(control_text=control_text, label=control_label), "yellow")
        utils.print_with_color("Action applied⚒️: {action}".format(action=action), "blue")
        utils.print_with_color("Status📊: {status}".format(status=status), "blue")
        utils.print_with_color("Next Plan📚: {plan}".format(plan=str(plan).replace("\\n", "\n")), "cyan")
        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")



    def external_knowledge_prompt_helper(self, request: str, offline_top_k: int, online_top_k: int) -> str:
        """
        Retrieve the external knowledge and construct the prompt.
        :param request: The request.
        :param offline_top_k: The number of offline documents to retrieve.
        :param online_top_k: The number of online documents to retrieve.
        :return: The prompt message for the external_knowledge.
        """

        retrieved_docs = ""

        # Retrieve offline documents and construct the prompt
        if self.offline_doc_retriever:
            offline_docs = self.offline_doc_retriever.retrieve("How to {query} for {app}".format(query=request, app=self._process_name), offline_top_k, filter=None)
            offline_docs_prompt = self.prompter.retrived_documents_prompt_helper("Help Documents", "Document", [doc.metadata["text"] for doc in offline_docs])
            retrieved_docs += offline_docs_prompt

        # Retrieve online documents and construct the prompt
        if self.online_doc_retriever:
            online_search_docs = self.online_doc_retriever.retrieve(request, online_top_k, filter=None)
            online_docs_prompt = self.prompter.retrived_documents_prompt_helper("Online Search Results", "Search Result", [doc.page_content for doc in online_search_docs])
            retrieved_docs += online_docs_prompt

        return retrieved_docs
    

    def rag_experience_retrieve(self, request: str, experience_top_k: int) -> str:
        """
        Retrieving experience examples for the user request.
        :param request: The user request.
        :param experience_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips string.
        """
        
        # Retrieve experience examples. Only retrieve the examples that are related to the current application.
        experience_docs = self.experience_retriever.retrieve(request, experience_top_k,
                                                                filter=lambda x: self._app_root_name.lower() in [app.lower() for app in x["app_list"]])
        
        if experience_docs:
            examples = [doc.metadata.get("example", {}) for doc in experience_docs]
            tips = [doc.metadata.get("Tips", "") for doc in experience_docs]
        else:
            examples = []
            tips = []

        return examples, tips
    
    
    def rag_demonstration_retrieve(self, request:str, demonstration_top_k: int) -> str:
        """
        Retrieving demonstration examples for the user request.
        :param request: The user request.
        :param demonstration_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips string.
        """
        
        # Retrieve demonstration examples.
        demonstration_docs = self.human_demonstration_retriever.retrieve(request, demonstration_top_k)
        
        if demonstration_docs:
            examples = [doc.metadata.get("example", {}) for doc in demonstration_docs]
            tips = [doc.metadata.get("Tips", "") for doc in demonstration_docs]
        else:
            examples = []
            tips = []

        return examples, tips
    

    def create_puppteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the Puppeteer interface to automate the app.
        :return: The Puppeteer interface.
        """
        return puppeteer.AppPuppeteer(self._process_name, self._app_root_name)
    

    def set_host(self, host: HostAgent) -> None:
        """
        Set the host agent.
        :param host: The host agent.
        """
        self.host = host


    def get_host(self) -> HostAgent:
        """
        Get the host agent that manages the AppAgent.
        :return: The host agent.
        """
        return self.host



    def build_offline_docs_retriever(self) -> None:
        """
        Build the offline docs retriever.
        """
        self.offline_doc_retriever = self.retriever_factory.create_retriever("offline", self._process_name)
        


    def build_online_search_retriever(self, request: str, top_k: int) -> None:
        """
        Build the online search retriever.
        :param request: The request for online Bing search.
        :param top_k: The number of documents to retrieve.
        """
        self.online_doc_retriever = self.retriever_factory.create_retriever("online", request, top_k)

    
    def build_experience_retriever(self, db_path: str) -> None:
        """
        Build the experience retriever.
        :param db_path: The path to the experience database.
        :return: The experience retriever.
        """
        self.experience_retriever = self.retriever_factory.create_retriever("experience", db_path)
        


    def build_human_demonstration_retriever(self, db_path: str) -> None:
        """
        Build the human demonstration retriever.
        :param db_path: The path to the human demonstration database.
        :return: The human demonstration retriever.
        """
        self.human_demonstration_retriever = self.retriever_factory.create_retriever("demonstration", db_path)


class HostAgent(BasicAgent):
    """
    The HostAgent class the manager of AppAgents.
    """

    def __init__(self, name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str, allow_openapp = False) -> None:
        """
        Initialize the HostAgent.
        :name: The name of the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param allow_openapp: The flag indicating whether to allow the agent to open an application process.
        """
        super().__init__(name=name)
        self.prompter = self.get_prompter(is_visual, main_prompt, example_prompt, api_prompt, allow_openapp)
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None
        self.agent_factory = AgentFactory()
        self.appagent_dict = {}
        self._global_action_memory = Memory()
        self._reqest_history_memory = Memory()
        self._active_appagent = None



    def get_prompter(self, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str, allow_openapp = False) -> HostAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return HostAgentPrompter(is_visual, main_prompt, example_prompt, api_prompt, allow_openapp)
    

    def create_subagent(self, agent_type: str, agent_name: str, process_name: str, app_root_name: str, is_visual: bool, main_prompt: str, 
                        example_prompt: str, api_prompt: str, *args, **kwargs) -> BasicAgent:
        """
        Create an SubAgent hosted by the HostAgent.
        :param agent_type: The type of the agent to create.
        :param agent_name: The name of the SubAgent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The created SubAgent.  
        """
        app_agent = self.agent_factory.create_agent(agent_type, agent_name, process_name, app_root_name, is_visual, main_prompt, example_prompt, api_prompt, *args, **kwargs)
        self.appagent_dict[agent_name] = app_agent
        app_agent.set_host(self)
        self._active_appagent = app_agent

        return app_agent
    

    def get_active_appagent(self) -> AppAgent:
        """
        Get the active app agent.
        :return: The active app agent.
        """
        return self._active_appagent
    

    def get_round(self) -> int:
        """
        Get the round number.
        :return: The round number.
        """
        return self._reqest_history_memory.length
    

    def message_constructor(self, image_list: List, request_history: str, action_history: str, os_info: str, plan: str, request: str) -> list:
        """
        Construct the message.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param os_info: The OS information.
        :param plan: The plan.
        :param request: The request.
        :return: The message.
        """
        hostagent_prompt_system_message = self.prompter.system_prompt_construction()
        hostagent_prompt_user_message = self.prompter.user_content_construction(image_list, request_history, action_history, 
                                                                                                  os_info, plan, request)
        
        hostagent_prompt_message = self.prompter.prompt_construction(hostagent_prompt_system_message, hostagent_prompt_user_message)
        
        return hostagent_prompt_message
    
    
    def app_file_manager(self, app_file_info: dict):
        '''
        Open the application or file for the user.
        :param app_file_info: The information of the application or file. {'APP': name of app, 'file_path': path}
        :return: The window of the application.
        '''

        utils.print_with_color("Opening the required application or file...", "yellow")
        file_manager = openfile.FileController()
        results = file_manager.execute_code(app_file_info)
        time.sleep(configs.get("SLEEP_TIME", 5))
        desktop_windows_dict, _ = control.get_desktop_app_info_dict()
        if not results:
            self.status = "ERROR in openning the application or file."
            return None
        app_window = file_manager.find_window_by_app_name(desktop_windows_dict)
        app_name = app_window.window_text()

        utils.print_with_color(f"The application {app_name} has been opened successfully.", "green")
        
        return app_window
    

    def print_response(self, response_dict: Dict):
        """
        Print the response.
        :param response: The response.
        """
        
        application = response_dict.get("ControlText")
        if not application:
            application = "[The required application needs to be opened.]"
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        plan = response_dict.get("Plan")
        status = response_dict.get("Status")
        comment = response_dict.get("Comment")

        utils.print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        utils.print_with_color("Selected application📲: {application}".format(application=application), "yellow")
        utils.print_with_color("Status📊: {status}".format(status=status), "blue")
        utils.print_with_color("Next Plan📚: {plan}".format(plan=str(plan).replace("\\n", "\n")), "cyan")
        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")


    def add_global_action_memory(self, action: dict) -> None:
        """
        Add the action to the memory.
        :param action: The action.
        """

        action_memory_item = MemoryItem()
        action_memory_item.set_values_from_dict(action)
        self._global_action_memory.add_memory_item(action_memory_item)



    def add_request_memory(self, request: str) -> None:
        """
        Add the request to the memory.
        :param request: The request.
        """
        request_length = self._reqest_history_memory.length
        request_memory_item = MemoryItem()
        request_memory_item.set_values_from_dict({f"old request {request_length}": request})
        self._reqest_history_memory.add_memory_item(request_memory_item)


    def get_global_action_memory(self) -> Memory:
        """
        Get the global action memory.
        :return: The global action memory.
        """
        return self._global_action_memory
    

    def get_request_history_memory(self) -> Memory:
        """
        Get the request history.
        :return: The request history.
        """
        return self._reqest_history_memory