# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from ufo import utils
from ufo.agents.agent.basic import BasicAgent
from ufo.agents.processors.app_agent_action_seq_processor import (
    AppAgentActionSequenceProcessor,
)
from ufo.agents.processors.app_agent_processor import AppAgentProcessor
from ufo.agents.states.app_agent_state import AppAgentStatus, ContinueAppAgentState
from ufo.automator import puppeteer
from ufo.automator.ui_control.grounding.basic import BasicGrounding
from ufo.automator.ui_control.grounding.omniparser import OmniparserGrounding
from ufo.config.config import Config
from ufo.llm.grounding_model.omniparser_service import OmniParser
from ufo.module import interactor
from ufo.module.context import Context
from ufo.prompter.agent_prompter import AppAgentPrompter

configs = Config.get_instance().config_data


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

        self.Puppeteer = self.create_puppeteer_interface()
        self._mode = mode

        control_detection_backend = configs.get("CONTROL_BACKEND", ["uia"])

        if "omniparser" in control_detection_backend:
            omniparser_endpoint = configs.get("OMNIPARSER", {}).get("ENDPOINT", "")
            omniparser_service = OmniParser(endpoint=omniparser_endpoint)
            self.grounding_service: Optional[BasicGrounding] = OmniparserGrounding(
                service=omniparser_service
            )
        else:
            self.grounding_service: Optional[BasicGrounding] = None

        self.set_state(ContinueAppAgentState())

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
        return AppAgentPrompter(
            is_visual, main_prompt, example_prompt, api_prompt, app_root_name
        )

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
        args = utils.revise_line_breaks(response_dict.get("Args"))

        # Generate the function call string
        action = self.Puppeteer.get_command_string(function_call, args)

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

            offline_docs_prompt = self.prompter.retrived_documents_prompt_helper(
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
            online_docs_prompt = self.prompter.retrived_documents_prompt_helper(
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
        else:
            examples = []
            tips = []

        return examples, tips

    def process(self, context: Context) -> None:
        """
        Process the agent.
        :param context: The context.
        """
        if configs.get("ACTION_SEQUENCE", False):
            self.processor = AppAgentActionSequenceProcessor(
                agent=self, context=context
            )
        else:
            self.processor = AppAgentProcessor(
                agent=self, context=context, ground_service=self.grounding_service
            )
        self.processor.process()
        self.status = self.processor.status

    def create_puppeteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the Puppeteer interface to automate the app.
        :return: The Puppeteer interface.
        """
        return puppeteer.AppPuppeteer(self._process_name, self._app_root_name)

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

    def context_provision(self, request: str = "") -> None:
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
