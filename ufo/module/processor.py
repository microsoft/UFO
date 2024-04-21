# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from abc import ABC, abstractmethod
from .. import utils
from ..automator.ui_control import utils as control
import json
import os
import time
import traceback
from pywinauto.uia_defines import NoPatternInterfaceError
from ..agent.basic import MemoryItem
from ..config.config import Config

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    def __init__(self, log_path, photographer, request, request_logger, logger):
        self.log_path = log_path
        self.photographer = photographer
        self.request = request
        self.request_logger = request_logger
        self.logger = logger
        
        self._step = 0
        self._status = ""  
        self._prompt_message = None  
        self._response = None  
        self._parsed_response = None
        self._cost = 0
        self._control_label = None
        self._memorized_action = None
        self._app_window = None

        
    def process(self):
        self.print_step_info()  
        self.capture_screenshot()
        self.get_control_info()
        self.get_prompt_message()  
        self.get_response()
        if self._status == "ERROR":
            return "ERROR", self._step, self._cost, self.action_history
        self.parse_response()  
        self.execute_action()

        if isinstance(self, HostAgentProcessor):
            self.create_app_agent()
        self.update_step_and_status()
        return self._status, self._step, self._cost, self._memorized_action
        
    def print_step_info(self):  
        pass  
  
    def capture_screenshot(self):  
        pass

    def get_control_info(self):  
        pass
  
    @abstractmethod  
    def get_prompt_message(self):  
        pass  
  
    @abstractmethod  
    def get_response(self):  
        pass  
  
    @abstractmethod  
    def parse_response(self):  
        pass  

    @abstractmethod
    def update_memory(self):
        pass

    @abstractmethod  
    def execute_action(self):  
        pass  
  
    def update_step_and_status(self):  
        self._step += 1  
        self.update_status()


    def get_active_window(self):
        """
        Get the active window.
        :return: The active window.
        """
        return self._app_window
  
    @abstractmethod  
    def update_status(self):  
        pass


    def log(self, response_json: dict) -> dict:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))
        


    def get_current_action_memory(self):
        """
        Get the current action memory.
        :return: The current action memory.
        """
        pass




class HostAgentProcessor(BaseProcessor):

    def __init__(self, host_agent):  
        super().__init__()  
        self.HostAgent = host_agent  

        self._desktop_screen_url = None
        self._desktop_windows_dict = None
        self._desktop_windows_info = None
        
        

    def print_step_info(self):  
        utils.print_with_color("Step {step}: Selecting an application.".format(step=self._step), "magenta")

    def capture_screenshot(self):

        desktop_save_path = self.log_path + f"action_step{self._step}.png"
        self.photographer.capture_desktop_screen_screenshot(all_screens=True, save_path=desktop_save_path)
        self._desktop_screen_url = utils.encode_image_from_path(desktop_save_path)


    def get_control_info(self):  
        self._desktop_windows_dict, self._desktop_windows_info = control.get_desktop_app_info_dict()


    def get_prompt_message(self):

        request_history = self.HostAgent.get_request_history_memory().to_json()
        action_history = self.HostAgent.get_global_action_memory().to_json()

        agent_memory = self.HostAgent.memory
        if agent_memory.length > 0:
            plan = agent_memory.get_latest_item().to_dict()["Plan"]

        self._prompt_message = self.HostAgent.message_constructor([self._desktop_screen_url], request_history, action_history, 
                                                                                                  self._desktop_windows_info, plan, self.request)
        self.request_logger.debug(json.dumps({"step": self._step, "prompt": self._prompt_message, "status": ""}))
        return self._prompt_message
    
    
    def get_response(self):

        try:
            self._response, self._cost = self.HostAgent.get_response(self._prompt_message, "HOSTAGENT", use_backup_engine=True)
        except Exception as e:
            log = json.dumps({"step": self._step, "status": str(e), "prompt": self._prompt_message})
            utils.print_with_color("Error occurs when calling LLM: {e}".format(e=str(e)), "red")
            self.request_logger.info(log)
            self._status = "ERROR"
        

    def parse_response(self):  
        try:
            response_json = self.HostAgent.response_to_dict(self._response)
            self.control_label = response_json["ControlLabel"]
            self.application = response_json["ControlText"]
            self.plan = response_json["Plan"]
            self._status = response_json["Status"]
            return response_json

        except Exception:
            error_trace = traceback.format_exc()
            utils.print_with_color("Error Occurs at application selection.", "red")
            utils.print_with_color(str(error_trace), "red")
            utils.print_with_color(self._response, "red")
            self.error_logger(self._response, str(error_trace))
            self._status = "ERROR"


    def update_memory(self):

        host_agent_step_memory = MemoryItem()
        additional_memory = {"Step": self._step, "AgentStep": self.HostAgent.get_step(), "Round": self._round, "ControlLabel": self.application, "Action": "set_focus()", 
                                "Request": self.request, "Agent": "HostAgent", "AgentName": self.HostAgent.name, "Application": self.app_root, "Cost": self._cost, "Results": ""}
        host_agent_step_memory.set_values_from_dict(self.response_json)
        host_agent_step_memory.set_values_from_dict(additional_memory)
        self.HostAgent.add_memory(host_agent_step_memory)
        
        self.log(host_agent_step_memory.to_dict())
        memorized_action = {key: host_agent_step_memory.to_dict()[key] for key in configs["HISTORY_KEYS"]}
        self.HostAgent.add_global_action_memory(memorized_action)


    def execute_action(self):

         # Get the application window
        self._app_window = self._desktop_windows_dict.get(self.control_label)

        # Get the application name
        self.app_root = control.get_application_name(self.app_window)

        try:
            self._app_window.is_normal()

        # Handle the case when the window interface is not available
        except NoPatternInterfaceError as e:
            utils.print_with_color("Window interface {title} not available for the visual element.".format(title=self.application), "red")
            self._status = "ERROR"
            return
        
        self._status = "CONTINUE"
        self._app_window.set_focus()
        

    def update_status(self):  
        self._step += 1
        self.HostAgent.update_step()
        self.HostAgent.update_status(self._status)

        time.sleep(configs["SLEEP_TIME"])


    def create_app_agent(self):
        """
        Create the app agent.
        :return: The app agent.
        """
        appagent = self.HostAgent.create_appagent("AppAgent/{root}/{process}".format(root=self.app_root, process=self.application), self.application, self.app_root, configs["APP_AGENT"]["VISUAL_MODE"], 
                                     configs["APPAGENT_PROMPT"], configs["APPAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
            
        # Load the retrievers for APP_AGENT.
        if configs["RAG_OFFLINE_DOCS"]:
            utils.print_with_color("Loading offline document indexer for {app}...".format(app=self.application), "magenta")
            appagent.build_offline_docs_retriever()
        if configs["RAG_ONLINE_SEARCH"]:
            utils.print_with_color("Creating a Bing search indexer...", "magenta")
            appagent.build_online_search_retriever(self.request, configs["RAG_ONLINE_SEARCH_TOPK"])
        if configs["RAG_EXPERIENCE"]:
            utils.print_with_color("Creating an experience indexer...", "magenta")
            experience_path = configs["EXPERIENCE_SAVED_PATH"]
            db_path = os.path.join(experience_path, "experience_db")
            appagent.build_experience_retriever(db_path)
        if configs["RAG_DEMONSTRATION"]:
            utils.print_with_color("Creating an demonstration indexer...", "magenta")
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            db_path = os.path.join(demonstration_path, "demonstration_db")
            appagent.build_human_demonstration_retriever(db_path)

        return appagent