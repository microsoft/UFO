# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import logging
import os

from art import text2art
from ..automator.ui_control.screenshot import PhotographerFacade

from .. import utils
from ..agent.agent import AgentFactory
from ..config.config import Config
from ..experience.summarizer import ExperienceSummarizer
from . import interactor
from . import processor
from . import state




configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]



class Session(object):
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

        self.HostAgent = AgentFactory.create_agent("host", "HostAgent", configs["HOST_AGENT"]["VISUAL_MODE"], configs["HOSTAGENT_PROMPT"], configs["HOSTAGENT_EXAMPLE_PROMPT"], configs["API_PROMPT"])
    
        self.AppAgent = None

        self.photographer = PhotographerFacade()

        self._status = "APP_SELECTION"
        self._state = state.AppropriateState(self._status)(self)
        self.application = ""
        self.app_root = ""
        self.app_window = None
        

        self._cost = 0.0
        self.control_reannotate = None

        utils.print_with_color(interactor.WELCOME_TEXT, "cyan")
        
        self.request = interactor.first_request()


    def process_application_selection(self) -> None:

        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """

        host_agent_processor = processor.HostAgentProcessor(log_path=self.log_path, photographer=self.photographer, request=self.request, global_step=self._step,
                                                            request_logger=self.request_logger, logger=self.logger, host_agent=self.HostAgent, prev_status=self._status)
        
        host_agent_processor.process()

        self._status = host_agent_processor.get_process_status()
        self._step += host_agent_processor.get_process_step()
        self.update_cost(host_agent_processor.get_process_cost())

        self.AppAgent = self.HostAgent.get_active_appagent()
        self.app_window = host_agent_processor.get_active_window()
        self.application = host_agent_processor.get_active_control_text()


    def process_action_selection(self) -> None:
        """
        Select an action.
        header: The headers of the request.
        return: The outcome, the application window, and the action log.
        """


        control_reannotate = []

        while isinstance(control_reannotate, list):
            app_agent_processor = processor.AppAgentProcessor(log_path=self.log_path, photographer=self.photographer, request=self.request, global_step=self._step, process_name=self.application,
                                                                request_logger=self.request_logger, logger=self.logger, app_agent=self.AppAgent, app_window=self.app_window, 
                                                                control_reannotate=control_reannotate, prev_status=self._status)
            
            app_agent_processor.process()
        
            self._status = app_agent_processor.get_process_status()
            self._step += app_agent_processor.get_process_step()
            self.update_cost(app_agent_processor.get_process_cost())

            control_reannotate = app_agent_processor.get_control_reannotate()

        

    def experience_saver(self) -> None:
        """
        Save the current agent experience.
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


    def set_new_round(self) -> None:
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
            self._status = "APP_SELECTION"
            return
        

    def get_round(self) -> int:
        """
        Get the round of the session.
        return: The round of the session.
        """
        return self._round
    
    
    def set_round(self, new_round: int) -> None:
        """
        Set the round of the session.
        """
        self.round = new_round



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
    
    

    def update_cost(self, cost):
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
        self.state = state


    def handle(self) -> None:
        """
        Handle the session.
        """
        self.state.handle()



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