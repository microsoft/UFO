# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
import logging
import os
from abc import ABC, abstractmethod
from logging import Logger
from typing import Type

from .. import utils
from ..agent.agent import AgentFactory, HostAgent
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from ..experience.summarizer import ExperienceSummarizer
from . import interactor
from .state import StatusToStateMapper

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    """
    The base processor for the session.
    """

    def __init__(self, index: int, log_path: str, photographer: PhotographerFacade, request: str, request_logger: Logger, logger: Logger, 
                 round_step: int, global_step: int, prev_status: str, app_window:Type) -> None:
        """
        Initialize the processor.
        :param log_path: The log path.
        :param photographer: The photographer facade to process the screenshots.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param global_step: The global step of the session.
        :param prev_status: The previous status of the session.
        """

        self.log_path = log_path
        self.photographer = photographer
        self.request = request
        self.request_logger = request_logger
        self.logger = logger
        self._app_window = app_window
        
        self.global_step = global_step
        self.round_step = round_step
        self.prev_status = prev_status
        self.index = index
        
        self._step = 0
        self._status = prev_status
        self._prompt_message = None  
        self._response = None  
        self._cost = 0
        self._control_label = None
        self._control_text = None
        self._response_json = None
        self._results = None
        self.app_root = None

        
    def process(self):
        """
        Process the session.
        The process includes the following steps:
        1. Print the step information.
        2. Capture the screenshot.
        3. Get the control information.
        4. Get the prompt message.
        5. Get the response.
        6. Parse the response.
        7. Execute the action.
        8. Update the memory.
        9. Create the app agent if necessary.
        10. Update the step and status.
        """

        self.print_step_info()
        self.capture_screenshot()
        self.get_control_info()
        self.get_prompt_message()
        self.get_response()

        if self.is_error():
            return
        self.parse_response()

        if self.is_error():
            return
        
        self.execute_action()
        self.update_memory()

        if self.should_create_appagent():
            self.create_app_agent()
        self.update_step_and_status()
        
    
    @abstractmethod
    def print_step_info(self):
        """
        Print the step information.
        """
        pass
    
    @abstractmethod 
    def capture_screenshot(self):
        """
        Capture the screenshot.
        """
        pass
    
    @abstractmethod 
    def get_control_info(self): 
        """
        Get the control information.
        """
        pass
  

    @abstractmethod  
    def get_prompt_message(self):
        """
        Get the prompt message.
        """
        pass  
  
    @abstractmethod  
    def get_response(self):  
        """
        Get the response from the LLM.
        """
        pass  
  
    @abstractmethod  
    def parse_response(self):
        """
        Parse the response.
        """
        pass  

    @abstractmethod  
    def execute_action(self):
        """
        Execute the action.
        """
        pass  

    @abstractmethod
    def update_memory(self):
        """
        Update the memory of the Agent.
        """
        pass


    @abstractmethod  
    def update_status(self):
        """
        Update the status of the session.
        """
        pass

    
    def create_app_agent(self):
        """
        Create the app agent.
        """
        pass


    def update_step_and_status(self):
        """
        Update the step and status of the process.
        """
        self._step += 1  
        self.update_status()


    def get_active_window(self):
        """
        Get the active window.
        :return: The active window.
        """
        return self._app_window
    
    
    def get_active_control_text(self):
        """
        Get the active application.
        :return: The active application.
        """
        return self._control_text
    

    def get_process_status(self):
        """
        Get the process status.
        :return: The process status.
        """
        return self._status
    
    
    def get_process_step(self):
        """
        Get the process step.
        :return: The process step.
        """
        return self._step
    
    
    def get_process_cost(self):
        """
        Get the process cost.
        :return: The process cost.
        """
        return self._cost
    

    def is_error(self):
        """
        Check if the process is in error.
        :return: The boolean value indicating if the process is in error.
        """

        return self._status == "ERROR"
    

    def should_create_appagent(self):
        """
        Check if the app agent should be created.
        :return: The boolean value indicating if the app agent should be created.
        """

        return False


    def log(self, response_json: dict) -> dict:
        """
        Set the result of the session, and log the result.
        result: The result of the session.
        response_json: The response json.
        return: The response json.
        """

        self.logger.info(json.dumps(response_json))


    def error_log(self, response_str: str, error: str) -> None:
        """
        Error handler for the session.
        """
        log = json.dumps({"step": self._step, "status": "ERROR", "response": response_str, "error": error})
        self.logger.info(log)
        


    def get_current_action_memory(self):
        """
        Get the current action memory.
        :return: The current action memory.
        """
        pass



class BaseRound(object):
    """
    A round of a session in UFO.
    """

    def __init__(self, task: str, logger: Logger, request_logger: Logger, photographer: PhotographerFacade, HostAgent: HostAgent, request: str) -> None: 
        """
        Initialize a session.
        :param task: The name of current task.
        :param gpt_key: GPT key.
        """

        self._step = 0

        self.log_path = f"logs/{task}/"

        self.logger = logger
        self.request_logger = request_logger

        self.HostAgent = HostAgent
        self.AppAgent = None

        self.photographer = photographer

        self._status = "APP_SELECTION"

        self.application = ""
        self.app_root = ""
        self.app_window = None

        self._cost = 0.0
        self.control_reannotate = []

        self.request = request

        self.index = None
        self.global_step = None


    def process_application_selection(self) -> None:

        """
        Select an application to interact with.
        """

        pass


    def process_action_selection(self) -> None:
        """
        Select an action with the application.
        """

        pass


    def get_status(self) -> str:
        """
        Get the status of the session.
        return: The status of the session.
        """
        return self._status



    def get_step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self._step


    def get_cost(self) -> float:
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self._cost


    def print_cost(self) -> None:
        # Print the total cost 

        total_cost = self.get_cost()  
        if isinstance(total_cost, float):  
            formatted_cost = '${:.2f}'.format(total_cost)  
            utils.print_with_color(f"Request total cost for current round is {formatted_cost}", "yellow")


    def get_results(self) -> str:
        """
        Get the results of the session.
        return: The results of the session.
        """

        action_history = self.HostAgent.get_global_action_memory().content

        if len(action_history) > 0:
            result = action_history[-1].to_dict().get("Results")
        else:
            result = ""
        return result


    def set_index(self, index: int) -> None:
        """
        Set the index of the session.
        """
        self.index = index


    def set_global_step(self, global_step: int) -> None:
        """
        Set the global step of the session.
        """
        self.global_step = global_step


    def get_application_window(self) -> object:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window


    def update_cost(self, cost: float) -> None:
        """
        Update the cost of the session.
        """
        if isinstance(cost, float) and isinstance(self._cost, float):
            self._cost += cost
        else:
            self._cost = None



class BaseSession(object):
    """
    A session for UFO.
    """
    
    def __init__(self, task):
        """
        Initialize a session.
        :param task: The name of current task.
        :param gpt_key: GPT key.
        """
        
        self.task = task
        self._step = 0
        self._round = 0

        self.log_path = f"logs/{self.task}/"
        utils.create_folder(self.log_path)
        self.logger = self.initialize_logger(self.log_path, "response.log")
        self.request_logger = self.initialize_logger(self.log_path, "request.log")

        self.HostAgent = AgentFactory.create_agent("host", "HostAgent", configs["HOST_AGENT"]["VISUAL_MODE"], configs["HOSTAGENT_PROMPT"], 
                                                   configs["HOSTAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"], configs["ALLOW_OPENAPP"])
    
        self.AppAgent = None

        self.photographer = PhotographerFacade()

        self._status = "APP_SELECTION"
        self._state = StatusToStateMapper().get_appropriate_state(self._status)
        self.application = ""
        self.app_root = ""
        self.app_window = None
        

        self._cost = 0.0
        self.control_reannotate = []

        utils.print_with_color(interactor.WELCOME_TEXT, "cyan")
        
        self.request = interactor.first_request()
        
        self.round_list = []
        self._current_round = self.create_round()


    @abstractmethod
    def create_round(self):
        """
        Create a new round.
        """

        pass
    
        
  
    def experience_saver(self) -> None:
        """
        Save the current trajectory as agent experience.
        """
        utils.print_with_color("Summarizing and saving the execution flow as experience...", "yellow")

        summarizer = ExperienceSummarizer(configs["APP_AGENT"]["VISUAL_MODE"], configs["EXPERIENCE_PROMPT"], configs["APPAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
        experience = summarizer.read_logs(self.log_path)
        summaries, total_cost = summarizer.get_summary_list(experience)

        experience_path = configs["EXPERIENCE_SAVED_PATH"]
        utils.create_folder(experience_path)
        summarizer.create_or_update_yaml(summaries, os.path.join(experience_path, "experience.yaml"))
        summarizer.create_or_update_vector_db(summaries, os.path.join(experience_path, "experience_db"))
        
        self.update_cost(cost=total_cost)
        utils.print_with_color("The experience has been saved.", "magenta")



    def start_new_round(self) -> None:
        """
        Start a new round.
        """

        self.HostAgent.add_request_memory(self.request)
        self._round += 1
        
        self.request = interactor.new_request()

        if self.request.upper() == "N":
            self._status = "COMPLETE"
            return
        else:
            self._current_round = self.create_round()
            self._status = "APP_SELECTION"
            return
        
        
    @abstractmethod
    def round_hostagent_execution(self) -> None:
        """
        Execute the host agent in the current round.
        """

        pass

    @abstractmethod
    def round_appagent_execution(self) -> None:
        """
        Execute the app agent in the current round.
        """
        
        pass
    
    
    def get_current_round(self):
        """
        Get the current round.
        return: The current round.
        """
        return self._current_round


    def get_round_num(self) -> int:
        """
        Get the round of the session.
        return: The round of the session.
        """
        return self._round
    

    def get_status(self) -> str:
        """
        Get the status of the session.
        return: The status of the session.
        """
        return self._status
    

    def get_state(self) -> object:
        """
        Get the state of the session.
        return: The state of the session.
        """
        return self._state
    
    
    def get_step(self) -> int:
        """
        Get the step of the session.
        return: The step of the session.
        """
        return self._step
    

    def get_cost(self) -> float:
        """
        Get the cost of the session.
        return: The cost of the session.
        """
        return self._cost
    
    
    def print_cost(self) -> None:
        """
        Print the total cost.
        """ 

        total_cost = self.get_cost()  
        if isinstance(total_cost, float):  
            formatted_cost = '${:.2f}'.format(total_cost)  
            utils.print_with_color(f"Request total cost is {formatted_cost}", "yellow")
        

    def get_results(self) -> str:
        """
        Get the results of the session.
        return: The results of the session.
        """

        action_history = self.HostAgent.get_global_action_memory().content

        if len(action_history) > 0:
            result = action_history[-1].to_dict().get("Results")
        else:
            result = ""
        return result
    
    
    
    def get_application_window(self) -> object:
        """
        Get the application of the session.
        return: The application of the session.
        """
        return self.app_window
    

    def update_cost(self, cost: float) -> None:
        """
        Update the cost of the session.
        """
        if isinstance(cost, float) and isinstance(self._cost, float):
            self._cost += cost
        else:
            self._cost = None



    def set_state(self, state) -> None:
        """
        Set the state of the session.
        """
        self._state = state


    def handle(self) -> None:
        """
        Handle the session.
        """
        self._state.handle(self)



    @staticmethod
    def initialize_logger(log_path: str, log_filename: str) -> logging.Logger:
        """
        Initialize logging.
        log_path: The path of the log file.
        log_filename: The name of the log file.
        return: The logger.
        """
        # Code for initializing logging
        logger = logging.Logger(log_filename)

        if not configs["PRINT_LOG"]:
            # Remove existing handlers if PRINT_LOG is False
            logger.handlers = []


        log_file_path = os.path.join(log_path, log_filename)
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.setLevel(configs["LOG_LEVEL"])

        return logger