# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from dataclasses import asdict
from typing import TYPE_CHECKING

from ufo import utils
from ufo.agents.processors.actions import ActionCommandInfo
from ufo.agents.processors.app_agent_processor import (
    AppAgentProcessor,
    AppAgentRequestLog,
)
from ufo.agents.processors.basic import BaseProcessor
from ufo.config import Config
from ufo.contracts.contracts import Command
from ufo.module.context import Context

if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

configs = Config.get_instance().config_data

if configs is not None:
    CONTROL_BACKEND = configs.get("CONTROL_BACKEND", ["uia"])
    BACKEND = "win32" if "win32" in CONTROL_BACKEND else "uia"


class CustomizedAgentProcessor(AppAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "AppAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent = agent
        self.host_agent = agent.host

        self._image_url = []
        self.screenshot_save_path = None

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}, AppAgent: Completing the subtask [{subtask}] on application [{application}].".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                subtask=self.subtask,
                application=self.application_process_name,
            ),
            "magenta",
        )

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """

        # Define the paths for the screenshots saved.
        self.screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}.png"
        )

        self._memory_data.add_values_from_dict(
            {
                "CleanScreenshot": self.screenshot_save_path,
            }
        )

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="take_screenshot",
                    parameters={},
                    tool_type="data_collection",
                )
            ]
        )

        clean_screenshot_url = result[0].result
        utils.save_image_string(clean_screenshot_url, self.screenshot_save_path)
        self.logger.info(f"Clean screenshot saved to {self.screenshot_save_path}")

        self._image_url += [clean_screenshot_url]

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_control_info(self) -> None:
        """
        Get the control information.
        """
        pass

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """
        if not self.app_agent.blackboard.is_empty():
            blackboard_prompt = self.app_agent.blackboard.blackboard_to_prompt()
        else:
            blackboard_prompt = []

        # Construct the prompt message for the AppAgent.
        self._prompt_message = self.app_agent.message_constructor(
            dynamic_examples=[],
            dynamic_knowledge=[],
            image_list=self._image_url,
            control_info=[],
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=[],
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
        )

        # Log the prompt message. Only save them in debug mode.
        request_data = AppAgentRequestLog(
            step=self.session_step,
            experience_examples=[],
            demonstration_examples=[],
            dynamic_examples=[],
            offline_docs=[],
            online_docs=[],
            dynamic_knowledge=[],
            image_list=self._image_url,
            prev_subtask=self.previous_subtasks,
            plan=self.prev_plan,
            request=self.request,
            control_info=[],
            subtask=self.subtask,
            current_application=self.application_process_name,
            host_message=self.host_message,
            blackboard_prompt=blackboard_prompt,
            last_success_actions=[],
            include_last_screenshot=configs.get("INCLUDE_LAST_SCREENSHOT", True),
            prompt=self._prompt_message,
        )

        request_log_str = json.dumps(asdict(request_data), ensure_ascii=False)
        self.request_logger.write(request_log_str)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def execute_action(self) -> None:
        """
        Execute the action.
        """

        if not self.response.function:
            utils.print_with_color(
                "No action to execute. Skipping execution.", "yellow"
            )
            return

        result = await self.context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name=self.response.function,
                    parameters=self.response.arguments,
                    tool_type="action",
                )
            ]
        )

        self.logger.info(f"Result for execution of {self.response.function}: {result}")

        action = ActionCommandInfo(
            function=self.response.function,
            arguments=self.response.arguments,
            target=self.target_registry.get(self.control_label),
            status=self.response.status,
            result=result[0],
        )

        self.actions.add_action(action)


class HardwareAgentProcessor(CustomizedAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

    pass
