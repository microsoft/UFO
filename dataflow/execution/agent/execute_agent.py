# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from ufo.agents.agent.app_agent import AppAgent


class ExecuteAgent(AppAgent):
    """
    The Agent for task execution.
    """

    def __init__(
        self,
        name: str,
        process_name: str,
        app_root_name: str,
    ):
        """
        Initialize the ExecuteAgent.
        :param name: The name of the agent.
        :param process_name: The name of the process.
        :param app_root_name: The name of the app root.
        """

        self._step = 0
        self._complete = False
        self._name = name
        self._status = None
        self._process_name = process_name
        self._app_root_name = app_root_name
        self.Puppeteer = self.create_puppeteer_interface()