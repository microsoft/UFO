# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import openai

from ufo import utils
from ufo.agents.agent.basic import AgentRegistry, BasicAgent
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.app_agent_action_seq_processor import (
    AppAgentActionSequenceProcessor,
)
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.processors.operator_processor import OpenAIOperatorProcessor
from ufo.agents.states.app_agent_state import AppAgentStatus, ContinueAppAgentState
from ufo.agents.states.operator_state import ContinueOpenAIOperatorState
from ufo.config import Config
from ufo.contracts.contracts import Command, MCPToolInfo
from ufo.llm import AgentType
from ufo.module import interactor
from ufo.module.context import Context
from ufo.prompter.agent_prompter import AppAgentPrompter

configs = Config.get_instance().config_data


@AgentRegistry.register(agent_name="appagent")
class AppAgent(BasicAgent):
    """
    The AppAgent class that manages the interaction with the application.
    """

    def __init__(
        self,
        name: str,
        process_name: str,
        app_root_name: str,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        skip_prompter: bool = False,
        mode: str = "normal",
    ) -> None:
        """
        Initialize the AppAgent.
        :name: The name of the agent.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param skip_prompter: The flag indicating whether to skip the prompter initialization.
        :param mode: The mode of the agent.
        """
        super().__init__(name=name)
        if not skip_prompter:
            self.prompter = self.get_prompter(
                is_visual, main_prompt, example_prompt, api_prompt, app_root_name
            )
        self._process_name = process_name
        self._app_root_name = app_root_name
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None

        self._mode = mode

        self.set_state(self.default_state)

        self._context_provision_executed = False
        self.logger = logging.getLogger(__name__)

    def get_prompter(
        self,
        is_visual: bool,
        main_prompt: str,
        example_prompt: str,
        api_prompt: str,
        app_root_name: str,
    ) -> AppAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param app_root_name: The root name of the app.
        :return: The prompter instance.
        """
        return AppAgentPrompter(is_visual, main_prompt, example_prompt)

    def message_constructor(
        self,
        dynamic_examples: str,
        dynamic_knowledge: str,
        image_list: List,
        control_info: str,
        prev_subtask: List[Dict[str, str]],
        plan: List[str],
        request: str,
        subtask: str,
        current_application: str,
        host_message: List[str],
        blackboard_prompt: List[Dict[str, str]],
        last_success_actions: List[Dict[str, Any]],
        include_last_screenshot: bool,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_knowledge: The dynamic knowledge retrieved from the external knowledge base.
        :param image_list: The list of screenshot images.
        :param control_info: The control information.
        :param plan: The plan list.
        :param request: The overall user request.
        :param subtask: The subtask for the current AppAgent to process.
        :param current_application: The current application name.
        :param host_message: The message from the HostAgent.
        :param blackboard_prompt: The prompt message from the blackboard.
        :param last_success_actions: The list of successful actions in the last step.
        :param include_last_screenshot: The flag indicating whether to include the last screenshot.
        :return: The prompt message.
        """
        appagent_prompt_system_message = self.prompter.system_prompt_construction(
            dynamic_examples
        )

        appagent_prompt_user_message = self.prompter.user_content_construction(
            image_list=image_list,
            control_item=control_info,
            prev_subtask=prev_subtask,
            prev_plan=plan,
            user_request=request,
            subtask=subtask,
            current_application=current_application,
            host_message=host_message,
            retrieved_docs=dynamic_knowledge,
            last_success_actions=last_success_actions,
            include_last_screenshot=include_last_screenshot,
        )

        if blackboard_prompt:
            appagent_prompt_user_message = (
                blackboard_prompt + appagent_prompt_user_message
            )

        appagent_prompt_message = self.prompter.prompt_construction(
            appagent_prompt_system_message, appagent_prompt_user_message
        )

        return appagent_prompt_message

    def print_response(
        self, response_dict: Dict[str, Any], print_action: bool = True
    ) -> None:
        """
        Print the response.
        :param response_dict: The response dictionary to print.
        :param print_action: The flag indicating whether to print the action.
        """

        control_text = response_dict.get("ControlText")
        control_label = response_dict.get("ControlLabel")
        if not control_text and not control_label:
            control_text = "[No control selected.]"
            control_label = "[No control label selected.]"
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        plan = response_dict.get("Plan")
        status = response_dict.get("Status")
        comment = response_dict.get("Comment")
        function_call = response_dict.get("Function")
        if configs.get(AgentType.APP).get("JSON_SCHEMA", False):
            args = utils.revise_line_breaks(json.loads(response_dict.get("Args")))
        else:
            args = utils.revise_line_breaks(response_dict.get("Args"))

        # Generate the function call string
        action = AppAgent.get_command_string(function_call, args)

        utils.print_with_color(
            "Observations👀: {observation}".format(observation=observation), "cyan"
        )
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        if print_action:
            utils.print_with_color(
                "Selected item🕹️: {control_text}, Label: {label}".format(
                    control_text=control_text, label=control_label
                ),
                "yellow",
            )
            utils.print_with_color(
                "Action applied⚒️: {action}".format(action=action), "blue"
            )
            utils.print_with_color("Status📊: {status}".format(status=status), "blue")
        utils.print_with_color(
            "Next Plan📚: {plan}".format(plan="\n".join(plan)), "cyan"
        )
        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")

        screenshot_saving = response_dict.get("SaveScreenshot", {})

        if screenshot_saving.get("save", False):
            utils.print_with_color(
                "Notice: The current screenshot📸 is saved to the blackboard.",
                "yellow",
            )
            utils.print_with_color(
                "Saving reason: {reason}".format(
                    reason=screenshot_saving.get("reason")
                ),
                "yellow",
            )

    def demonstration_prompt_helper(self, request) -> Tuple[List[Dict[str, Any]]]:
        """
        Get the examples and tips for the AppAgent using the demonstration retriever.
        :param request: The request for the AppAgent.
        :return: The examples and tips for the AppAgent.
        """

        # Get the examples and tips for the AppAgent using the experience and demonstration retrievers.
        if configs["RAG_EXPERIENCE"]:
            experience_results = self.rag_experience_retrieve(
                request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
            )
        else:
            experience_results = []

        if configs["RAG_DEMONSTRATION"]:
            demonstration_results = self.rag_demonstration_retrieve(
                request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
            )
        else:
            demonstration_results = []

        return experience_results, demonstration_results

    def external_knowledge_prompt_helper(
        self, request: str, offline_top_k: int, online_top_k: int
    ) -> Tuple[str, str]:
        """
        Retrieve the external knowledge and construct the prompt.
        :param request: The request.
        :param offline_top_k: The number of offline documents to retrieve.
        :param online_top_k: The number of online documents to retrieve.
        :return: The prompt message for the external_knowledge.
        """

        # Retrieve offline documents and construct the prompt
        if self.offline_doc_retriever:

            offline_docs = self.offline_doc_retriever.retrieve(
                request,
                offline_top_k,
                filter=None,
            )

            format_string = "[Similar Requests]: {question}\nStep: {answer}\n"

            offline_docs_prompt = self.prompter.retrieved_documents_prompt_helper(
                "[Help Documents]",
                "",
                [
                    format_string.format(
                        question=doc.metadata.get("title", ""),
                        answer=doc.metadata.get("text", ""),
                    )
                    for doc in offline_docs
                ],
            )
        else:
            offline_docs_prompt = ""

        # Retrieve online documents and construct the prompt
        if self.online_doc_retriever:
            online_search_docs = self.online_doc_retriever.retrieve(
                request, online_top_k, filter=None
            )
            online_docs_prompt = self.prompter.retrieved_documents_prompt_helper(
                "Online Search Results",
                "Search Result",
                [doc.page_content for doc in online_search_docs],
            )
        else:
            online_docs_prompt = ""

        return offline_docs_prompt, online_docs_prompt

    def rag_experience_retrieve(
        self, request: str, experience_top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieving experience examples for the user request.
        :param request: The user request.
        :param experience_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips dictionary.
        """

        retrieved_docs = []

        # Retrieve experience examples. Only retrieve the examples that are related to the current application.
        experience_docs = self.experience_retriever.retrieve(
            request,
            experience_top_k,
            filter=lambda x: self._app_root_name.lower()
            in [app.lower() for app in x["app_list"]],
        )

        if experience_docs:
            for doc in experience_docs:
                example_request = doc.metadata.get("request", "")
                response = doc.metadata.get("example", {})
                tips = doc.metadata.get("Tips", "")
                subtask = doc.metadata.get("Sub-task", "")
                retrieved_docs.append(
                    {
                        "Request": example_request,
                        "Response": response,
                        "Sub-task": subtask,
                        "Tips": tips,
                    }
                )

        return retrieved_docs

    def rag_demonstration_retrieve(self, request: str, demonstration_top_k: int) -> str:
        """
        Retrieving demonstration examples for the user request.
        :param request: The user request.
        :param demonstration_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips string.
        """

        retrieved_docs = []

        # Retrieve demonstration examples.
        demonstration_docs = self.human_demonstration_retriever.retrieve(
            request, demonstration_top_k
        )

        if demonstration_docs:
            for doc in demonstration_docs:
                example_request = doc.metadata.get("request", "")
                response = doc.metadata.get("example", {})
                subtask = doc.metadata.get("Sub-task", "")
                tips = doc.metadata.get("Tips", "")
                retrieved_docs.append(
                    {
                        "Request": example_request,
                        "Response": response,
                        "Sub-task": subtask,
                        "Tips": tips,
                    }
                )

            return retrieved_docs
        else:
            return []

    async def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        if not self._context_provision_executed:
            await self.context_provision(context=context)
            self._context_provision_executed = True

        if configs.get("ACTION_SEQUENCE", False):
            self.processor = AppAgentActionSequenceProcessor(
                agent=self, context=context
            )
        else:
            self.processor = AppAgentProcessor(agent=self, context=context)
        await self.processor.process()

        self.status = self.processor.status

    def process_comfirmation(self) -> bool:
        """
        Process the user confirmation.
        :return: The decision.
        """
        action = self.processor.actions
        control_text = self.processor.control_text

        decision = interactor.sensitive_step_asker(action, control_text)

        if not decision:
            utils.print_with_color("The user has canceled the action.", "red")

        return decision

    @property
    def status_manager(self) -> AppAgentStatus:
        """
        Get the status manager.
        """
        return AppAgentStatus

    @property
    def mode(self) -> str:
        """
        Get the mode of the session.
        """
        return self._mode

    def build_offline_docs_retriever(self) -> None:
        """
        Build the offline docs retriever.
        """
        self.offline_doc_retriever = self.retriever_factory.create_retriever(
            "offline", self._app_root_name
        )

    def build_online_search_retriever(self, request: str, top_k: int) -> None:
        """
        Build the online search retriever.
        :param request: The request for online Bing search.
        :param top_k: The number of documents to retrieve.
        """
        self.online_doc_retriever = self.retriever_factory.create_retriever(
            "online", request, top_k
        )

    def build_experience_retriever(self, db_path: str) -> None:
        """
        Build the experience retriever.
        :param db_path: The path to the experience database.
        :return: The experience retriever.
        """
        self.experience_retriever = self.retriever_factory.create_retriever(
            "experience", db_path
        )

    def build_human_demonstration_retriever(self, db_path: str) -> None:
        """
        Build the human demonstration retriever.
        :param db_path: The path to the human demonstration database.
        :return: The human demonstration retriever.
        """
        self.human_demonstration_retriever = self.retriever_factory.create_retriever(
            "demonstration", db_path
        )

    async def context_provision(
        self, request: str = "", context: Context = None
    ) -> None:
        """
        Provision the context for the app agent.
        :param request: The request sent to the Bing search retriever.
        """

        # Load the offline document indexer for the app agent if available.
        if configs["RAG_OFFLINE_DOCS"]:
            utils.print_with_color(
                "Loading offline help document indexer for {app}...".format(
                    app=self._process_name
                ),
                "magenta",
            )
            self.build_offline_docs_retriever()

        # Load the online search indexer for the app agent if available.

        if configs["RAG_ONLINE_SEARCH"] and request:
            utils.print_with_color("Creating a Bing search indexer...", "magenta")
            self.build_online_search_retriever(
                request, configs["RAG_ONLINE_SEARCH_TOPK"]
            )

        # Load the experience indexer for the app agent if available.
        if configs["RAG_EXPERIENCE"]:
            utils.print_with_color("Creating an experience indexer...", "magenta")
            experience_path = configs["EXPERIENCE_SAVED_PATH"]
            db_path = os.path.join(experience_path, "experience_db")
            self.build_experience_retriever(db_path)

        # Load the demonstration indexer for the app agent if available.
        if configs["RAG_DEMONSTRATION"]:
            utils.print_with_color("Creating an demonstration indexer...", "magenta")
            demonstration_path = configs["DEMONSTRATION_SAVED_PATH"]
            db_path = os.path.join(demonstration_path, "demonstration_db")
            self.build_human_demonstration_retriever(db_path)

        await self._load_mcp_context(context)

    async def _load_mcp_context(self, context: Context) -> None:
        """
        Load MCP context information for the current application.
        """

        self.logger.info("Loading MCP tool information...")
        result = await context.command_dispatcher.execute_commands(
            [
                Command(
                    tool_name="list_tools",
                    parameters={
                        "tool_type": "action",
                    },
                    tool_type="action",
                )
            ]
        )

        tool_list = result[0].result if result else None

        tool_name_list = (
            [tool.get("tool_name") for tool in tool_list] if tool_list else []
        )

        self.logger.info(
            f"Loaded tool list: {tool_name_list} for the application {self._process_name}."
        )

        tools_info = [MCPToolInfo(**tool) for tool in tool_list]

        self.prompter.create_api_prompt_template(tools=tools_info)

    @property
    def default_state(self) -> ContinueAppAgentState:
        """
        Get the default state.
        """
        return ContinueAppAgentState()

    @property
    def tools_info(self) -> List[MCPToolInfo]:
        """
        Get the tools information.
        :return: The list of MCPToolInfo objects.
        """
        if not hasattr(self, "_tools_info"):
            self._tools_info = []
        return self._tools_info

    @tools_info.setter
    def tools_info(self, tools: List[MCPToolInfo]) -> None:
        """
        Set the tools information.
        :param tools: The list of MCPToolInfo objects.
        """
        self._tools_info = tools

    @staticmethod
    def get_command_string(command_name: str, params: Dict[str, str]) -> str:
        """
        Generate a function call string.
        :param command_name: The function name.
        :param params: The arguments as a dictionary.
        :return: The function call string.
        """
        # Format the arguments
        args_str = ", ".join(f"{k}={v!r}" for k, v in params.items())

        # Return the function call string
        return f"{command_name}({args_str})"


@AgentRegistry.register(agent_name="operator")
class OpenAIOperatorAgent(AppAgent):
    """
    The OpenAIOperatorAgent class that manages the interaction with the OpenAI Operator.
    """

    _continue_type = "computer_call"
    _message_type = "message"

    def __init__(
        self,
        name: str,
        process_name: str,
        app_root_name: str,
    ) -> None:
        """
        Initialize the OpenAIOperatorAgent.
        :name: The name of the agent.
        :param main_prompt: The main prompt file path.
        :param process_name: The process name of the app.
        :param app_root_name: The root name of the app.
        """
        BasicAgent.__init__(self, name=name)

        self._process_name = process_name
        self._app_root_name = app_root_name
        self._blackboard = Blackboard()
        self._response_id = None
        self._previous_computer_id = None

        self._message = ""
        self._pending_safety_checks = []

        self.set_state(self.default_state)

    def process(self, context: Context) -> None:
        """
        Process the agent workflow in each step.
        :param context: The context.
        """

        scaler = configs.get("OPERATOR", {}).get("SCALER", None)
        self.processor = OpenAIOperatorProcessor(
            agent=self, context=context, scaler=scaler
        )
        self.processor.process()
        self.status = self.processor.status

    def get_prompter(self, main_prompt: str, app_root_name: str) -> AppAgentPrompter:
        """
        Get the prompt for the agent.
        :param main_prompt: The main prompt file path.
        :param app_root_name: The root name of the app.
        :return: The prompter instance.
        """
        pass

    def message_constructor(
        self,
        subtask: str,
        image: str,
        tools: List[Dict[str, str]],
        response_id: str,
        previous_computer_id: str,
        host_message: List[str],
        acknowledged_safety_checks: List[str],
        is_first_step: bool,
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """
        Construct the prompt message for the AppAgent.
        :param subtask: The subtask for the current OpenAIOperatorAgent to process.
        :param image: The screenshot images.
        :param tools: The list of tools.
        :param subtask: The subtask for the current OpenAIOperatorAgent to process.
        :param response_id: The response id of the last step.
        :param host_message: The message from the HostAgent.
        :param is_first_step: The flag indicating whether to include the last screenshot.
        :param acknowledged_safety_checks: The list of acknowledged safety checks.
        :return: The prompt message.
        """

        subtask_request = f"Please complete the following subtask: {subtask}"

        if host_message:
            host_message += [
                "Please do not ask for consent to perform the task, just execute the action."
            ]
            tips_template = (
                "Here are some tips for you to complete the task:\n - {tips}"
            )
            tips = tips_template.format(tips="\n- ".join(host_message))
            subtask_request += "\n" + tips

        if is_first_step:
            return {"inputs": subtask_request, "tools": tools}

        else:
            output_message = (
                openai.types.responses.response_input_param.ComputerCallOutput(
                    type="computer_screenshot",  # TODO
                    image_url=image,
                )
            )

            messages = openai.types.responses.response_input_param.ComputerCallOutput(
                type="computer_call_output",
                call_id=previous_computer_id,
                output=output_message,
                acknowledged_safety_checks=acknowledged_safety_checks,
            )

            return {
                "inputs": [messages],
                "tools": tools,
                "previous_response_id": response_id,
            }

    def print_response(self, response_dict: Dict[str, Any]) -> None:
        """
        Print the response.
        :param response_dict: The response dictionary to print.
        :param print_action: The flag indicating whether to print the action.
        """

        message = response_dict.get("message", "")
        thought = response_dict.get("thought", "")

        if message:
            utils.print_with_color(
                "Agent message📝: {message}".format(message=message), "yellow"
            )

        if thought:
            utils.print_with_color(
                "Thoughts💡: {thought}".format(thought=thought), "green"
            )

        function_call = response_dict.get("operation", "")
        args = response_dict.get("args", {})

        # Generate the function call string
        action = AppAgent.get_command_string(function_call, args)
        utils.print_with_color(
            "Action applied⚒️: {action}".format(action=action), "blue"
        )

    @property
    def default_state(self) -> ContinueOpenAIOperatorState:
        """
        Get the default state.
        """
        return ContinueOpenAIOperatorState()

    @property
    def blackboard(self) -> Blackboard:
        """
        Get the blackboard.
        """

        if self.host is not None:
            return self.host.blackboard
        else:
            return self._blackboard

    @property
    def response_id(self) -> Optional[str]:
        """
        Get the response id.
        """
        return self._response_id

    @response_id.setter
    def response_id(self, response_id: str) -> None:
        """
        Set the response id.
        :param response_id: The response id.
        """
        self._response_id = response_id

    @property
    def previous_computer_id(self) -> Optional[str]:
        """
        Get the previous computer id.
        """
        return self._previous_computer_id

    @previous_computer_id.setter
    def previous_computer_id(self, computer_id: str) -> None:
        """
        Set the previous computer id.
        :param computer_id: The computer id.
        """
        self._previous_computer_id = computer_id

    @property
    def message(self) -> str:
        """
        Get the message.
        """
        return self._message

    @message.setter
    def message(self, message: str) -> None:
        """
        Set the message.
        :param message: The message.
        """
        self._message = message

    @property
    def pending_safety_checks(self) -> List[str]:
        """
        Get the pending safety checks.
        """
        return self._pending_safety_checks

    @pending_safety_checks.setter
    def pending_safety_checks(self, safety_checks: List[str]) -> None:
        """
        Set the pending safety checks.
        :param safety_checks: The safety checks.
        """
        self._pending_safety_checks = safety_checks
