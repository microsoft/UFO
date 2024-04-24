# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from logging import Logger

from .. import utils
from ..agent.agent import HostAgent
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from . import processor

from .basic import BaseRound

configs = Config.get_instance().config_data



class Round(BaseRound):
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
                                                            control_reannotate=self.control_reannotate, prev_status=self.get_status())

        app_agent_processor.process()

        self._status = app_agent_processor.get_process_status()
        self._step += app_agent_processor.get_process_step()
        self.update_cost(app_agent_processor.get_process_cost())

        self.control_reannotate = app_agent_processor.get_control_reannotate()