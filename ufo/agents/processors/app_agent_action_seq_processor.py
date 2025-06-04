# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Any, Dict, List

from ufo import utils
from ufo.agents.processors.actions import ActionSequence, OneStepAction
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.processors.basic import BaseProcessor
from ufo.config.config import Config
from ufo.cs.contracts import OperationCommand, OperationSequenceAction

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
    def execute_action(self) -> None:
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

        # Check if we should use MCP for any operations in the sequence
        if self.mcp_enabled and self._should_use_mcp_for_sequence(action_list):
            self._execute_mcp_action_sequence(action_list)
        else:
            self._execute_ui_action_sequence(action_list)

    def _should_use_mcp_for_sequence(self, action_list: List[OneStepAction]) -> bool:
        """
        Determine if the action sequence should use MCP.
        :param action_list: List of actions in the sequence
        :return: True if MCP should be used
        """
        # Use MCP if any action in the sequence prefers MCP
        return any(self.app_agent.should_use_mcp(action.function) for action in action_list)

    def _execute_mcp_action_sequence(self, action_list: List[OneStepAction]) -> None:
        """
        Execute an action sequence using MCP.
        :param action_list: List of actions to execute
        """
        from ufo.cs.contracts import MCPToolExecutionAction, MCPToolExecutionParams
        
        utils.print_with_color("Executing action sequence via MCP", "green")
        
        # For action sequences, we need to execute actions sequentially
        # and handle MCP/UI automation mixing
        for i, action in enumerate(action_list):
            if self.app_agent.should_use_mcp(action.function):
                # Execute this action via MCP
                app_namespace = self.app_agent._get_app_namespace()
                
                mcp_action = MCPToolExecutionAction(
                    params=MCPToolExecutionParams(
                        tool_name=action.function,
                        tool_args={**action.args, 
                                 "control_label": action.control_label,
                                 "control_text": action.control_text},
                        app_namespace=app_namespace
                    )
                )
                
                # Add action with callback to handle result
                self.session_data_manager.add_action(
                    mcp_action,
                    setter=lambda result, idx=i: self._handle_mcp_sequence_action_callback(result, idx)
                )
                
                utils.print_with_color(
                    f"Action {i+1}/{len(action_list)}: {action.function} sent to MCP server", 
                    "cyan"
                )
            else:
                # Execute this action via UI automation
                command = OperationCommand(
                    command_id=action.function,
                    **{
                        action.function: {
                        **action.args,
                        "control_label": action.control_label,
                        "control_text": action.control_text,
                        "after_status": action.after_status,
                        }
                    }
                )
                
                # For UI actions in sequence, we still use the session manager
                self.session_data_manager.add_action(OperationSequenceAction(
                    params=[command],
                ))
                
                utils.print_with_color(
                    f"Action {i+1}/{len(action_list)}: {action.function} sent to UI automation", 
                    "cyan"
                )

    def _execute_ui_action_sequence(self, action_list: List[OneStepAction]) -> None:
        """
        Execute an action sequence using UI automation.
        :param action_list: List of actions to execute
        """
        utils.print_with_color("Executing action sequence via UI automation", "blue")
        
        commands = [
            OperationCommand(
                command_id=action.function,
                **{
                    action.function: {
                    **action.args,
                    "control_label": action.control_label,
                    "control_text": action.control_text,
                    "after_status": action.after_status,
                    }
                }
            )
            for action in action_list
        ]

        self.session_data_manager.add_action(OperationSequenceAction(
            params=commands,
        ))

    def _handle_mcp_sequence_action_callback(self, result: Any, action_index: int) -> None:
        """
        Callback to handle MCP tool execution result for sequence actions.
        :param result: The result from the MCP tool execution
        :param action_index: Index of the action in the sequence
        """
        try:
            if result and isinstance(result, dict):
                success = result.get("success", False)
                if success:
                    utils.print_with_color(
                        f"MCP sequence action {action_index+1} completed successfully: {result.get('tool_name', 'unknown')}", 
                        "green"
                    )
                else:
                    error_msg = result.get("error", "Unknown error")
                    utils.print_with_color(
                        f"MCP sequence action {action_index+1} failed: {error_msg}", 
                        "red"
                    )
                    # Could implement fallback to UI automation here if needed
            else:
                utils.print_with_color(
                    f"Received unexpected MCP sequence action {action_index+1} result type: {type(result)}", 
                    "yellow"
                )
        except Exception as e:
            utils.print_with_color(
                f"Error handling MCP sequence action {action_index+1} callback: {str(e)}", 
                "red"
            )

        # self.actions.execute_all(
        #     puppeteer=self.app_agent.Puppeteer,
        #     control_dict=self._annotation_dict,
        #     application_window=self.application_window,
        # )

        # self.status = self.actions.status

        # success_control_adjusted_coords = self.actions.get_success_control_coords()
        # self.capture_control_screenshot_from_adjusted_coords(
        #     control_adjusted_coords=success_control_adjusted_coords
        # )

        # self.actions.print_all_results()

        # if self.is_application_closed():
        #     utils.print_with_color("Warning: The application is closed.", "yellow")
        #     self.status = "FINISH"

    # def capture_control_screenshot_from_adjusted_coords(
    #     self, control_adjusted_coords: List[Dict[str, Any]]
    # ) -> None:
    #     """
    #     Capture the screenshot of the selected control.
    #     :param control_selected: The selected control item or a list of selected control items.
    #     """
    #     control_screenshot_save_path = (
    #         self.log_path + f"action_step{self.session_step}_selected_controls.png"
    #     )

    #     self._memory_data.add_values_from_dict(
    #         {"SelectedControlScreenshot": control_screenshot_save_path}
    #     )
    #     self.photographer.capture_app_window_screenshot_with_rectangle_from_adjusted_coords(
    #         self.application_window,
    #         control_adjusted_coords=control_adjusted_coords,
    #         save_path=control_screenshot_save_path,
    #         background_screenshot_path=self.screenshot_save_path,
    #     )
