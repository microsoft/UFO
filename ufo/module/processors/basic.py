# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json

from abc import ABC, abstractmethod
from logging import Logger
from typing import Type

from ...automator.ui_control.screenshot import PhotographerFacade
from ...config.config import Config


configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class BaseProcessor(ABC):
    """
    The base processor for the session. A session consists of multiple rounds of conversation with the user, completing a task. 
    At each round, the HostAgent and AppAgent interact with the user and the application with the processor. 
    Each processor is responsible for processing the user request and updating the HostAgent and AppAgent at a single step in a round.
    """

    def __init__(self, round_num: int, log_path: str, photographer: PhotographerFacade, request: str, request_logger: Logger, logger: Logger, 
                 round_step: int, global_step: int, prev_status: str, app_window:Type) -> None:
        """
        Initialize the processor.
        :param round_num: The index of the processor. The round_num is the total number of rounds in the session.
        :param log_path: The log path.
        :param photographer: The photographer facade to process the screenshots.
        :param request: The user request.
        :param request_logger: The logger for the request string.
        :param logger: The logger for the response and error.
        :param round_step: The step of the round.
        :param global_step: The global step of the session.
        :param prev_status: The previous status of the session.
        :param app_window: The application window.
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
        self.round_num = round_num
        
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

        
    def process(self) -> None:
        """
        Process a single step in a round.
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

        # Step 1: Print the step information.
        self.print_step_info()

        # Step 2: Capture the screenshot.
        self.capture_screenshot()

        # Step 3: Get the control information.
        self.get_control_info()

        # Step 4: Get the prompt message.
        self.get_prompt_message()

        # Step 5: Get the response.
        self.get_response()

        if self.is_error():
            return
        
        # Step 6: Parse the response, if there is no error.
        self.parse_response()

        if self.is_error():
            return
        
        # Step 7: Execute the action.
        self.execute_action()

        # Step 8: Update the memory.
        self.update_memory()

        # Step 9: Create the app agent if necessary.
        if self.should_create_subagent():
            self.create_sub_agent()

        # Step 10: Update the step and status.
        self.update_step_and_status()
        
    
    @abstractmethod
    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        pass
    
    @abstractmethod 
    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """
        pass
    
    @abstractmethod 
    def get_control_info(self) -> None:
        """
        Get the control information.
        """
        pass
  

    @abstractmethod  
    def get_prompt_message(self) -> None:
        """
        Get the prompt message.
        """
        pass  
  
    @abstractmethod  
    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """
        pass  
  
    @abstractmethod  
    def parse_response(self) -> None:
        """
        Parse the response.
        """
        pass  

    @abstractmethod  
    def execute_action(self) -> None:
        """
        Execute the action.
        """
        pass  

    @abstractmethod
    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """
        pass


    @abstractmethod  
    def update_status(self) -> None:
        """
        Update the status of the session.
        """
        pass

    
    def create_sub_agent(self) -> None:
        """
        Create the app agent.
        """
        pass


    def update_step_and_status(self) -> None:
        """
        Update the step and status of the process.
        """
        self._step += 1  
        self.update_status()


    def get_active_window(self) -> Type:
        """
        Get the active window.
        :return: The active window.
        """
        return self._app_window
    
    
    def get_active_control_text(self) -> str:
        """
        Get the active application.
        :return: The active application.
        """
        return self._control_text
    

    def get_process_status(self) -> str:
        """
        Get the process status.
        :return: The process status.
        """
        return self._status
    
    
    def get_process_step(self) -> int:
        """
        Get the process step.
        :return: The process step.
        """
        return self._step
    
    
    def get_process_cost(self) -> float:
        """
        Get the process cost.
        :return: The process cost.
        """
        return self._cost
    

    def is_error(self) -> bool:
        """
        Check if the process is in error.
        :return: The boolean value indicating if the process is in error.
        """

        return self._status == "ERROR"
    

    def should_create_subagent(self) -> bool:
        """
        Check if the app agent should be created.
        :return: The boolean value indicating if the app agent should be created.
        """

        return False


    def log(self, response_json: dict) -> None:
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