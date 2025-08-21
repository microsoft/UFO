# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from ufo.agents.processors.action_contracts import ActionSequence, OneStepAction
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.processors.basic import BaseProcessor
from ufo.config import Config
from ufo.contracts.contracts import Command

configs = Config.get_instance().config_data


class AppAgentActionSequenceProcessor(AppAgentProcessor):
    """
    The processor for the app agent at a single step.
    """

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    def parse_response(self) -> None:
        """
        Parse the response.
        """

        self._response_json = self.app_agent.response_to_dict(self._response)

        self.question_list = self._response_json.get("Questions", [])

        # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        self.app_agent.print_response(self._response_json, print_action=False)

    @BaseProcessor.exception_capture
    @BaseProcessor.method_timer
    async def execute_action(self) -> None:
        """
        Execute the action sequence.
        """

        action_sequence_dicts = self._response_json.get("ActionList", [])
        action_list = [
            OneStepAction(
                function=action_dict.get("Function", ""),
                args=action_dict.get("Args", {}),
                control_label=action_dict.get("ControlLabel", ""),
                control_text=action_dict.get("ControlText", ""),
                after_status=action_dict.get("Status", "CONTINUE"),
            )
            for action_dict in action_sequence_dicts
        ]
        self.actions = ActionSequence(action_list)
        self.function_calls = self.actions.get_function_calls()

        commands = [
            Command(
                tool_name=action.function,
                parameters=action.args,
                tool_type="action",
            )
            for action in self.function_calls
        ]

        results = await self.context.message_bus.publish_commands(commands)

        for i, action in enumerate(self.function_calls):
            self.logger.info(f"Result for execution {action}: {results[i].result}")
