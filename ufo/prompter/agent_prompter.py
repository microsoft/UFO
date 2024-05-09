# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import json
from typing import Dict, List, Optional

from ufo.config.config import Config
from ufo.prompter.basic import BasicPrompter

configs = Config.get_instance().config_data


class HostAgentPrompter(BasicPrompter):
    """
    The HostAgentPrompter class is the prompter for the host agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        allow_openapp=False,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.api_prompt_template = self.load_prompt_template(api_prompt_template)
        self.allow_openapp = allow_openapp

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """
        if self.allow_openapp:
            open_app_guideline = self.prompt_template["open_app_guideline"]
            open_app_comment = self.prompt_template["open_app_comment"]
        else:
            open_app_guideline = ""
            open_app_comment = ""
        apis = self.api_prompt_helper(verbose=0)
        examples = self.examples_prompt_helper()

        system_key = "system" if self.is_visual else "system_nonvisual"

        return self.prompt_template[system_key].format(
            apis=apis,
            examples=examples,
            open_app_guideline=open_app_guideline,
            open_app_comment=open_app_comment,
        )

    def user_prompt_construction(
        self,
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
    ) -> str:
        """
        Construct the prompt for action selection.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            action_history=json.dumps(action_history),
            request_history=json.dumps(request_history),
            control_item=json.dumps(control_item),
            prev_plan=json.dumps(prev_plan),
            user_request=user_request,
            retrieved_docs=retrieved_docs,
        )

        return prompt

    def user_content_construction(
        self,
        image_list: List[str],
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: str,
        user_request: str,
        retrieved_docs: str = "",
    ) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param image_list: The list of images.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for LLMs.
        """

        user_content = []

        if self.is_visual:
            screenshot_text = ["Current Screenshots:"]

            for i, image in enumerate(image_list):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    request_history,
                    action_history,
                    control_item,
                    prev_plan,
                    user_request,
                    retrieved_docs,
                ),
            }
        )

        return user_content

    def examples_prompt_helper(
        self, header: str = "## Response Examples", separator: str = "Example"
    ) -> str:
        """
        Construct the prompt for examples.
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        return: The prompt for examples.
        """
        template = """
        [User Request]:
            {request}
        [Response]:
            {response}"""
        example_list = []

        for key, values in self.example_prompt_template.items():

            if key.startswith("example"):
                if key.startswith("example_openapp") and not self.allow_openapp:
                    continue
                if not self.allow_openapp:
                    del values["Response"]["AppsToOpen"]
                example = template.format(
                    request=values.get("Request"),
                    response=json.dumps(values.get("Response")),
                )
                example_list.append(example)

        return self.retrived_documents_prompt_helper(header, separator, example_list)

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """

        # Construct the prompt for APIs
        api_list = [
            "- The action type are limited to {actions}.".format(
                actions=list(self.api_prompt_template.keys())
            )
        ]

        # Construct the prompt for each API
        for key in self.api_prompt_template.keys():
            api = self.api_prompt_template[key]
            if verbose > 0:
                api_text = "{summary}\n{usage}".format(
                    summary=api["summary"], usage=api["usage"]
                )
            else:
                api_text = api["summary"]

            api_list.append(api_text)

        api_prompt = self.retrived_documents_prompt_helper("", "", api_list)

        return api_prompt


class AppAgentPrompter(BasicPrompter):
    """
    The AppAgentPrompter class is the prompter for the application agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        root_name: Optional[str] = None,
    ):
        """
        Initialize the ApplicationAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        """
        super().__init__(is_visual, prompt_template, example_prompt_template)
        self.root_name = root_name
        self.app_prompter = APIPromptLoader(self.root_name)
        self.api_prompt_template = self.load_prompt_template(api_prompt_template)

        self.app_api_prompt_template = None

        if configs.get("USE_APIS", False):
            self.app_api_prompt_template = self.app_prompter.load_com_api_prompt()

    def system_prompt_construction(
        self, additional_examples: List[str] = [], tips: List[str] = []
    ) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """

        apis = self.api_prompt_helper(verbose=1)
        examples = self.examples_prompt_helper(additional_examples=additional_examples)
        tips_prompt = "\n".join(tips)

        # Remove empty lines
        tips_prompt = "\n".join(filter(None, tips_prompt.split("\n")))

        system_key = "system" if self.is_visual else "system_nonvisual"

        return self.prompt_template[system_key].format(
            apis=apis, examples=examples, tips=tips_prompt
        )

    def user_prompt_construction(
        self,
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
    ) -> str:
        """
        Construct the prompt for action selection.
        :param prompt_template: The template of the prompt.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            action_history=json.dumps(action_history),
            request_history=json.dumps(request_history),
            control_item=json.dumps(control_item),
            prev_plan=json.dumps(prev_plan),
            user_request=user_request,
            retrieved_docs=retrieved_docs,
        )

        return prompt

    def user_content_construction(
        self,
        image_list: List[str],
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
        include_last_screenshot: bool = True,
    ) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param image_list: The list of images.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        return: The prompt for LLMs.
        """

        user_content = []

        if self.is_visual:

            screenshot_text = []
            if include_last_screenshot:
                screenshot_text += ["Screenshot for the last step:"]

                screenshot_text += ["Current Screenshots:", "Annotated Screenshot:"]

            for i, image in enumerate(image_list):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    request_history,
                    action_history,
                    control_item,
                    prev_plan,
                    user_request,
                    retrieved_docs,
                ),
            }
        )

        return user_content

    def examples_prompt_helper(
        self,
        header: str = "## Response Examples",
        separator: str = "Example",
        additional_examples: List[str] = [],
    ) -> str:
        """
        Construct the prompt for examples.
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Response]:
            {response}"""

        example_list = []

        for key in self.example_prompt_template.keys():
            if key.startswith("example"):
                example = template.format(
                    request=self.example_prompt_template[key].get("Request"),
                    response=json.dumps(
                        self.example_prompt_template[key].get("Response")
                    ),
                )
                example_list.append(example)

        example_list += [json.dumps(example) for example in additional_examples]

        return self.retrived_documents_prompt_helper(header, separator, example_list)

    def api_prompt_helper(self, verbose: int = 1) -> str:
        """
        Construct the prompt for APIs.
        :param apis: The APIs.
        :param verbose: The verbosity level.
        return: The prompt for APIs.
        """

        # Construct the prompt for each UI control action.
        api_list = [
            "- The action types for UI elements are: {actions}.".format(
                actions=list(self.api_prompt_template.keys())
            )
        ]

        for key in self.api_prompt_template.keys():
            api = self.api_prompt_template[key]
            if verbose > 0:
                api_text = "{summary}\n{usage}".format(
                    summary=api["summary"], usage=api["usage"]
                )
            else:
                api_text = api["summary"]

            api_list.append(api_text)

        # Construct the prompt for COM APIs
        if self.app_api_prompt_template:

            api_list += [
                "- There are additional shortcut APIs for your operations. You should **prioritize** using these APIs if they are available since they are more reliable and efficient. The avaliable APIs are: {apis}".format(
                    apis=list(self.app_api_prompt_template.keys())
                )
            ]
            for key in self.app_api_prompt_template.keys():
                api = self.app_api_prompt_template[key]
                if verbose > 0:
                    api_text = "{summary}\n{usage}".format(
                        summary=api["summary"], usage=api["usage"]
                    )
                else:
                    api_text = api["summary"]

                api_list.append(api_text)

        api_prompt = self.retrived_documents_prompt_helper("", "", api_list)

        return api_prompt


class FollowerAgentPrompter(AppAgentPrompter):
    """
    The FollowerAgentPrompter class is the prompter for the follower agent.
    """

    def __init__(
        self,
        is_visual: bool,
        prompt_template: str,
        example_prompt_template: str,
        api_prompt_template: str,
        app_info_prompt_template: Optional[str] = None,
        root_name: Optional[str] = None,
    ) -> None:
        """
        Initialize the FollowerAgentPrompter.
        :param is_visual: Whether the request is for visual model.
        :param prompt_template: The path of the prompt template.
        :param example_prompt_template: The path of the example prompt template.
        :param api_prompt_template: The path of the api prompt template.
        :param app_info_prompt_template: The path of the app info prompt template.
        :param root_name: The root name of the app.
        """
        super().__init__(
            is_visual,
            prompt_template,
            example_prompt_template,
            api_prompt_template,
            root_name,
        )

        if app_info_prompt_template is not None:
            self.app_info_prompt_template = self.load_prompt_template(
                app_info_prompt_template
            )
        else:
            self.app_info_prompt_template = None

    def system_prompt_construction(
        self, additional_examples: List[str] = [], tips: List[str] = []
    ) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """

        apis = self.api_prompt_helper(verbose=1)
        examples = self.examples_prompt_helper(additional_examples=additional_examples)
        tips_prompt = "\n".join(tips)

        # Remove empty lines
        tips_prompt = "\n".join(filter(None, tips_prompt.split("\n")))

        if self.app_info_prompt_template is None:
            app_name = self.root_name
            app_info = "The state of the application is not available."
        else:
            app_name = self.app_info_prompt_template["application_name"]
            app_info = self.app_info_prompt_template["state_description"]

        return self.prompt_template["system"].format(
            apis=apis,
            examples=examples,
            tips=tips_prompt,
            app_name=app_name,
            app_info=app_info,
        )

    def user_prompt_construction(
        self,
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
        current_state: dict = {},
        state_diff: dict = {},
    ) -> str:
        """
        Construct the prompt for action selection.
        :param prompt_template: The template of the prompt.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        :param current_state: The current state of the application.
        :param state_diff: The state difference of the application before and after the action.
        return: The prompt for action selection.
        """
        prompt = self.prompt_template["user"].format(
            action_history=json.dumps(action_history),
            request_history=json.dumps(request_history),
            control_item=json.dumps(control_item),
            prev_plan=json.dumps(prev_plan),
            user_request=user_request,
            retrieved_docs=retrieved_docs,
            current_state=json.dumps(current_state),
            state_diff=json.dumps(state_diff),
        )

        return prompt

    def user_content_construction(
        self,
        image_list: List[str],
        request_history: List[str],
        action_history: List[str],
        control_item: List[str],
        prev_plan: List[str],
        user_request: str,
        retrieved_docs: str = "",
        current_state: dict = {},
        state_diff: dict = {},
        include_last_screenshot: bool = True,
    ) -> List[Dict]:
        """
        Construct the prompt for LLMs.
        :param image_list: The list of images.
        :param action_history: The action history.
        :param control_item: The control item.
        :param user_request: The user request.
        :param retrieved_docs: The retrieved documents.
        :param current_state: The current state of the application (Optional).
        :param state_diff: The state difference of the application before and after the action (Optional).
        :param include_last_screenshot: Whether to include the last screenshot as input.
        return: The prompt for LLMs.
        """

        user_content = []

        if self.is_visual:

            screenshot_text = []
            if include_last_screenshot:
                screenshot_text += ["Screenshot for the last step:"]

                screenshot_text += ["Current Screenshots:", "Annotated Screenshot:"]

            for i, image in enumerate(image_list):
                user_content.append({"type": "text", "text": screenshot_text[i]})
                user_content.append({"type": "image_url", "image_url": {"url": image}})

        user_content.append(
            {
                "type": "text",
                "text": self.user_prompt_construction(
                    request_history,
                    action_history,
                    control_item,
                    prev_plan,
                    user_request,
                    retrieved_docs,
                    current_state,
                    state_diff,
                ),
            }
        )

        return user_content


class APIPromptLoader:
    """
    Load the prompt template for APIs.
    """

    def __init__(self, root_name: str) -> None:
        """
        Initialize the APIPromptLoader.
        :param root_name: The root name of the app.
        """
        self.root_name = root_name
        self.api_prompt_key = "class_name"

    def load_com_api_prompt(self) -> Dict[str, str]:
        """
        Load the prompt template for COM APIs.
        :return: The prompt template for COM APIs.
        """
        app2configkey_mapper = {
            "WINWORD.EXE": "WORD_API_PROMPT",
            "EXCEL.EXE": "EXCEL_API_PROMPT",
            "POWERPNT.EXE": "POWERPOINT_API_PROMPT",
            "olk.exe": "OUTLOOK_API_PROMPT",
        }

        # Get the config key of app
        config_key = app2configkey_mapper.get(self.root_name, None)
        # Get the prompt address from config
        prompt_address = configs.get(config_key, None)

        if prompt_address:
            return AppAgentPrompter.load_prompt_template(prompt_address, None)
        else:
            return {}

    @staticmethod
    def load_ui_api_prompt() -> Dict[str, str]:
        """
        Load the prompt template for UI APIs.
        :return: The prompt template for UI APIs.
        """

        config_key = "API_PROMPT"

        prompt_address = configs.get(config_key, None)

        if prompt_address:
            return AppAgentPrompter.load_prompt_template(
                prompt_address, is_visual=configs["APP_AGENT"]["VISUAL_MODE"]
            )
        else:
            return {}

    def filter_api_dict(self, api_prompt_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Filter the API prompt dictionary.
        :param api_prompt: The API prompt dictionary.
        :return: The filtered API prompt dictionary.
        """
        return {k: v.get(self.api_prompt_key, None) for k, v in api_prompt_dict.items()}
