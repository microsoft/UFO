# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from logging import Logger
from typing import Optional, Type

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo.agent.agent import FollowerAgent, HostAgent
from ufo.config.config import Config
from ufo.module.basic import BaseRound
from ufo.module.processors import follower_processor, processor

configs = Config.get_instance().config_data


class Round(BaseRound):
    """
    A round of a session in UFO.
    """

    def __init__(
        self,
        task: str,
        logger: Logger,
        request_logger: Logger,
        host_agent: HostAgent,
        request: str,
    ) -> None:
        """
        Initialize a round.
        :param task: The name of current task.
        :param logger: The logger for the response and error.
        :param request_logger: The logger for the request string.
        :param host_agent: The host agent.
        :param request: The user request at the current round.
        """

        super().__init__(task, logger, request_logger, host_agent, request)

    def process_application_selection(self) -> None:
        """
        Select an application to interact with.
        """

        host_agent_processor = self._create_host_agent_processor(
            processor.HostAgentProcessor
        )

        self._run_step(host_agent_processor)

        self.app_agent = self.host_agent.get_active_appagent()
        self.app_window = host_agent_processor.get_active_window()
        self.application = host_agent_processor.get_active_control_text()

    def process_action_selection(self) -> None:
        """
        Select an action with the application.
        """

        app_agent_processor = self._create_app_agent_processor(
            processor.AppAgentProcessor
        )
        self._run_step(app_agent_processor)

        self.control_reannotate = app_agent_processor.get_control_reannotate()

    def _create_host_agent_processor(
        self, processor_class: Type["processor.BaseProcessor"]
    ) -> processor.HostAgentProcessor:

        return processor_class(
            round_num=self.round_num,
            log_path=self.log_path,
            request=self.request,
            round_step=self.get_step(),
            session_step=self.session_step,
            request_logger=self.request_logger,
            logger=self.logger,
            host_agent=self.host_agent,
            prev_status=self.get_status(),
            app_window=self.app_window,
        )

    def _create_app_agent_processor(
        self, processor_class: Type["processor.BaseProcessor"]
    ) -> processor.AppAgentProcessor:

        return processor_class(
            round_num=self.round_num,
            log_path=self.log_path,
            request=self.request,
            round_step=self.get_step(),
            session_step=self.session_step,
            process_name=self.application,
            request_logger=self.request_logger,
            logger=self.logger,
            app_agent=self.app_agent,
            app_window=self.app_window,
            control_reannotate=self.control_reannotate,
            prev_status=self.get_status(),
        )


class FollowerRound(Round):

    def __init__(
        self,
        task: str,
        logger: Logger,
        request_logger: Logger,
        host_agent: HostAgent,
        app_agent: Optional[FollowerAgent],
        app_window: Optional[UIAWrapper],
        application: Optional[str],
        request: str,
    ) -> None:
        """
        Initialize a follower round.
        :param task: The name of current task.
        :param logger: The logger for the response and error.
        :param request_logger: The logger for the request string.
        :param host_agent: The host agent.
        :param app_agent: The app agent.
        :param app_window: The window of the application.
        :param application: The name of the application.
        :param request: The user request at the current round.
        """

        super().__init__(task, logger, request_logger, host_agent, request)

        self.app_agent = app_agent
        self.app_window = app_window
        self.application = application

    def process_application_selection(self) -> None:
        """
        Select an application to interact with.
        """

        host_agent_processor = self._create_host_agent_processor(
            follower_processor.FollowerHostAgentProcessor
        )

        self._run_step(host_agent_processor)

        self.app_agent = self.host_agent.get_active_appagent()
        self.app_window = host_agent_processor.get_active_window()
        self.application = host_agent_processor.get_active_control_text()

    def process_action_selection(self) -> None:
        """
        Select an action with the application.
        """

        app_agent_processor = follower_processor.FollowerAppAgentProcessor(
            round_num=self.round_num,
            log_path=self.log_path,
            request=self.request,
            round_step=self.get_step(),
            session_step=self.session_step,
            process_name=self.application,
            request_logger=self.request_logger,
            logger=self.logger,
            app_agent=self.app_agent,
            app_window=self.app_window,
            control_reannotate=self.control_reannotate,
            prev_status=self.get_status(),
        )

        app_agent_processor = self._create_app_agent_processor(
            follower_processor.FollowerAppAgentProcessor
        )
        self._run_step(app_agent_processor)

        self.control_reannotate = app_agent_processor.get_control_reannotate()

    def _create_app_agent_processor(
        self, processor_class: Type["processor.BaseProcessor"]
    ) -> follower_processor.AppAgentProcessor:
        """
        Create an app agent processor for the follower round.
        :param processor_class: The class of the processor.
        :return: The app agent processor.
        """

        return processor_class(
            round_num=self.round_num,
            log_path=self.log_path,
            request=self.request,
            round_step=self.get_step(),
            session_step=self.session_step,
            process_name=self.application,
            request_logger=self.request_logger,
            logger=self.logger,
            app_agent=self.app_agent,
            app_window=self.app_window,
            control_reannotate=self.control_reannotate,
            prev_status=self.get_status(),
        )
