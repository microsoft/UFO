# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


"""
This module contains the basic classes of Round and Session for the UFO system.

A round of a session in UFO manages a single user request and consists of multiple steps. 

A session may consists of multiple rounds of interactions.

The session is the core class of UFO. It manages the state transition and handles the different states, using the state pattern.

For more details definition of the state pattern, please refer to the state.py module.
"""

import logging
import os
from abc import ABC, abstractmethod
from logging import Logger


from .. import utils
from ..agent.agent import AgentFactory, HostAgent
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from ..experience.summarizer import ExperienceSummarizer
from . import interactor
from .state import StatusToStateMapper

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]



class BaseRound(ABC):
    """
    A round of a session in UFO. 
    A round manages a single user request and consists of multiple steps. A session may consists of multiple rounds of interactions.
    """

    def __init__(self, task: str, logger: Logger, request_logger: Logger, photographer: PhotographerFacade, HostAgent: HostAgent, request: str) -> None: 
        """
        Initialize a round.
        :param task: The name of current task.
        :param logger: The logger for the response and error.
        :param request_logger: The logger for the request string.
        :param photographer: The photographer facade to process the screenshots.
        :param HostAgent: The host agent.
        :param request: The user request at the current round.
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

        self.round_num = None
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
        Set the round index of the session.
        """
        self.round_num = index


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



class BaseSession(ABC):
    """
    A basic session in UFO. A session consists of multiple rounds of interactions.
    The handle function is the core function to handle the session. UFO runs with the state transition and handles the different states, using the state pattern.
    A session follows the following steps: 
    1. Begins with the ''APP_SELECTION'' state for the HostAgent to select an application.
    2. After the application is selected, the session moves to the ''CONTINUE'' state for the AppAgent to select an action. This process continues until all the actions are completed.
    3. When all the actions are completed for the current user request at a round, the session moves to the ''FINISH'' state.
    4. The session will ask the user if they want to continue with another request. If the user wants to continue, the session will start a new round and move to the ''APP_SELECTION'' state.
    5. If the user does not want to continue, the session will transition to the ''COMPLETE'' state. 
    6. At this point, the session will ask the user if they want to save the experience. If the user wants to save the experience, the session will save the experience and terminate.
    """
    
    def __init__(self, task):
        """
        Initialize a session.
        :param task: The name of current task.
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


    @abstractmethod
    def start_new_round(self) -> None:
        """
        Start a new round.
        """

        pass
        
        
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

    @property
    def session_type(self) -> str:
        """
        Get the class name of the session.
        return: The class name of the session.
        """
        return self.__class__.__name__



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
