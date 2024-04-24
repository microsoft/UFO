# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from .. import utils
from ..agent.agent import AgentFactory
from ..automator.ui_control.screenshot import PhotographerFacade
from ..config.config import Config

from . import interactor, round
from .state import StatusToStateMapper
from .basic import BaseSession

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]



class Session(BaseSession):
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


    def create_round(self) -> round.Round:
        """
        Create a new round.
        """

        new_round = round.Round(task=self.task, logger=self.logger, request_logger=self.request_logger, photographer=PhotographerFacade(), HostAgent=self.HostAgent, request=self.request)
        new_round.set_index(self.get_round_num())
        new_round.set_global_step(self.get_step())

        self.round_list.append(new_round)
        
        return new_round
        

    def round_hostagent_execution(self) -> None:
        """
        Execute the host agent in the current round.
        """

        current_round = self.get_current_round()
        current_round.set_global_step(self.get_step())

        current_round.process_application_selection()

        self._status = current_round.get_status()
        self._step += 1

        self.app_window = current_round.get_application_window()


    def round_appagent_execution(self) -> None:
        """
        Execute the app agent in the current round.
        """
        
        current_round = self.get_current_round()
        current_round.set_global_step(self.get_step())

        current_round.process_action_selection()

        self._status = current_round.get_status()
        self._step += 1
    
