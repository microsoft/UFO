# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from logging import Logger

from ..agent.agent import HostAgent
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config
from .processors import processor, follower_processor   

from .basic import BaseRound

configs = Config.get_instance().config_data



class Round(BaseRound):
    """
    A round of a session in UFO.
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

        # Step-related properties  
        self._step = 0  
  
        # Logging-related properties  
        self.log_path = f"logs/{task}/"  
        self.logger = logger  
        self.request_logger = request_logger  
  
        # Agent-related properties  
        self.HostAgent = HostAgent  
        self.AppAgent = None  
  
        # Photographer-related properties  
        self.photographer = photographer  
  
        # Status-related properties  
        self._status = "APP_SELECTION"  
  
        # Application-related properties  
        self.application = ""  
        self.app_root = ""  
        self.app_window = None  
  
        # Cost and reannotate-related properties  
        self._cost = 0.0  
        self.control_reannotate = []  
  
        # Request-related properties  
        self.request = request  
  
        # round_num and global step-related properties  
        self.round_num = None  
        self.global_step = None


    def process_application_selection(self) -> None:

        """
        Select an application to interact with.
        """

        host_agent_processor = processor.HostAgentProcessor(round_num=self.round_num, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step,
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

        app_agent_processor = processor.AppAgentProcessor(round_num=self.round_num, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step, 
                                                          process_name=self.application, request_logger=self.request_logger, logger=self.logger, app_agent=self.AppAgent, app_window=self.app_window, 
                                                            control_reannotate=self.control_reannotate, prev_status=self.get_status())

        app_agent_processor.process()

        self._status = app_agent_processor.get_process_status()
        self._step += app_agent_processor.get_process_step()
        self.update_cost(app_agent_processor.get_process_cost())

        self.control_reannotate = app_agent_processor.get_control_reannotate()




class FollowerRound(Round):

    def __init__(self, task: str, logger: Logger, request_logger: Logger, photographer: PhotographerFacade, HostAgent: HostAgent, request: str) -> None:
        """
        Initialize a follower round.
        :param task: The name of current task.
        :param logger: The logger for the response and error.
        :param request_logger: The logger for the request string.
        :param photographer: The photographer facade to process the screenshots.
        :param HostAgent: The host agent.
        :param request: The user request at the current round.
        """

        super().__init__(task, logger, request_logger, photographer, HostAgent, request)


    def process_application_selection(self) -> None:

        """
        Select an application to interact with.
        """

        host_agent_processor = follower_processor.FollowerHostAgentProcessor(round_num=self.round_num, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step,
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

        app_agent_processor = follower_processor.FollowerAppAgentProcessor(round_num=self.round_num, log_path=self.log_path, photographer=self.photographer, request=self.request, round_step=self.get_step(), global_step=self.global_step, 
                                                          process_name=self.application, request_logger=self.request_logger, logger=self.logger, app_agent=self.AppAgent, app_window=self.app_window, 
                                                            control_reannotate=self.control_reannotate, prev_status=self.get_status())

        app_agent_processor.process()

        self._status = app_agent_processor.get_process_status()
        self._step += app_agent_processor.get_process_step()
        self.update_cost(app_agent_processor.get_process_cost())

        self.control_reannotate = app_agent_processor.get_control_reannotate()
