# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from logging import Logger

from .. import utils
from ..agent.agent import HostAgent
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from . import processor

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]



class Round(object):
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

        host_agent_processor = processor.HostAgentProcessor(index=self.index, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step,
                                                            request_logger=self.request_logger, logger=self.logger, host_agent=self.HostAgent, prev_status=self.get_status(), app_window=self.app_window)

        host_agent_processor.process()

        self._status = host_agent_processor.get_process_status()
        self._step += host_agent_processor.get_process_step()
        self.update_cost(host_agent_processor.get_process_cost())

        self.AppAgent = self.HostAgent.get_active_appagent()
        self.app_window = host_agent_processor.get_active_window()
        self.application = host_agent_processor.get_active_control_text()


    def process_action_selection(self) -> None:
        """
        Select an action with the application.
        """

        app_agent_processor = processor.AppAgentProcessor(index=self.index, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step, 
                                                          process_name=self.application, request_logger=self.request_logger, logger=self.logger, app_agent=self.AppAgent, app_window=self.app_window, 
                                                            control_reannotate=self.control_reannotate, prev_status=self.get_status(), host_agent=self.HostAgent)

        app_agent_processor.process()

        self._status = app_agent_processor.get_process_status()
        self._step += app_agent_processor.get_process_step()
        self.update_cost(app_agent_processor.get_process_cost())

        self.control_reannotate = app_agent_processor.get_control_reannotate()


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