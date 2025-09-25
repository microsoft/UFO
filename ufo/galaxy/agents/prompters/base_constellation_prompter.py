# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Constellation Agent Prompter.

This module provides the base prompter class for Constellation Agents with
shared functionality between different weaving modes.
"""

from abc import ABC
from typing import Dict, List, Type
from ufo.contracts.contracts import MCPToolInfo
from ufo.galaxy.agents.schema import WeavingMode
from ufo.galaxy.constellation.task_constellation import TaskConstellation
from ufo.prompter.basic import BasicPrompter


class BaseConstellationPrompter(BasicPrompter, ABC):
    """
    Base prompter for Constellation Agent with shared functionality.

    This class provides common prompt construction logic that is shared
    between different weaving modes (CREATION and EDITING).
    """

    def __init__(self, prompt_template: str, example_prompt_template: str):
        """
        Initialize base constellation prompter.

        :param prompt_template: Main prompt template or template string
        :param example_prompt_template: Example prompt template or template string
        """
        # Initialize with empty templates to avoid file loading
        super().__init__(None, prompt_template, example_prompt_template)

    def _format_device_info(self, device_info: List[str]) -> str:
        """
        Format device information for prompt inclusion.

        :param device_info: List of device information
        :return: Formatted device information string
        """
        if not device_info:
            return "No device information available."

        return "\n".join([f"- {info}" for info in device_info])

    def _format_constellation(self, constellation) -> str:
        """
        Format constellation information for prompt inclusion.

        :param constellation: Task constellation object
        :return: Formatted constellation string
        """
        if constellation is None:
            return "No constellation information available."

        try:
            return (
                constellation.to_json()
                if hasattr(constellation, "to_json")
                else str(constellation)
            )
        except Exception:
            return "Constellation information unavailable due to formatting error."

    def user_content_construction(
        self,
        request: str,
        device_info: List[str],
        constellation: TaskConstellation,
    ) -> List[Dict[str, str]]:
        """
        Construct the prompt for LLMs.
        :param request: The user request.
        :param device_info: The device information.
        :param constellation: The task constellation.
        return: The prompt for LLMs.
        """

        prompt_text = self.user_prompt_construction(request, device_info, constellation)

        return [{"type": "text", "text": prompt_text}]

    def system_prompt_construction(self) -> str:
        """
        Construct the prompt for app selection.
        return: The prompt for app selection.
        """
        examples = self.examples_prompt_helper()

        return self.prompt_template["system"].format(
            examples=examples,
        )

    def user_prompt_construction(
        self,
        request: str,
        device_info: List[str],
        constellation: TaskConstellation,
    ) -> str:
        """
        Construct the prompt for LLMs.
        :param request: The user request.
        :param device_info: The device information.
        :param constellation: The task constellation.
        return: The prompt for LLMs.
        """

        prompt = self.prompt_template["user"].format(
            request=request,
            device_info=self._format_device_info(device_info),
            constellation=self._format_constellation(constellation),
        )

        return prompt

    def create_api_prompt_template(self, tools: List[MCPToolInfo]):
        """
        Create the API prompt template.
        :param tools: The list of tools.
        """
        self.api_prompt_template = BasicPrompter.tools_to_llm_prompt(tools)


class ConstellationPrompterFactory:
    """
    Factory class for creating Constellation prompters based on weaving mode.

    This factory ensures that the correct prompter implementation is used
    based on the current weaving mode (CREATION or EDITING).

    Benefits:
    - Centralized prompter creation logic
    - Type-safe prompter selection
    - Easy extensibility for new modes
    - Consistent parameter handling
    """

    # Prompter mappings for each weaving mode - using lazy imports to avoid circular dependencies
    _prompter_classes: Dict[WeavingMode, Type[BasicPrompter]] = {}

    @classmethod
    def create_prompter(
        cls,
        weaving_mode: WeavingMode,
        creation_prompt_template: str,
        editing_prompt_template: str,
        creation_example_prompt_template: str,
        editing_example_prompt_template: str,
    ) -> BasicPrompter:
        """
        Create prompter based on weaving mode.

        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param creation_prompt_template: Template for creation prompts
        :param editing_prompt_template: Template for editing prompts
        :param creation_example_prompt_template: Template for creation examples
        :param editing_example_prompt_template: Template for editing examples
        :return: Appropriate prompter instance
        :raises ValueError: If weaving mode is not supported
        """
        # Lazy loading to avoid circular imports
        if not cls._prompter_classes:
            from ufo.galaxy.agents.prompters.constellation_creation_prompter import (
                ConstellationCreationPrompter,
            )
            from ufo.galaxy.agents.prompters.constellation_editing_prompter import (
                ConstellationEditingPrompter,
            )

            cls._prompter_classes = {
                WeavingMode.CREATION: ConstellationCreationPrompter,
                WeavingMode.EDITING: ConstellationEditingPrompter,
            }

        if weaving_mode not in cls._prompter_classes:
            raise ValueError(f"Unsupported weaving mode for prompter: {weaving_mode}")

        prompter_class = cls._prompter_classes[weaving_mode]

        if weaving_mode == WeavingMode.CREATION:
            return prompter_class(
                creation_prompt_template, creation_example_prompt_template
            )
        elif weaving_mode == WeavingMode.EDITING:
            return prompter_class(
                editing_prompt_template, editing_example_prompt_template
            )
        else:
            # Should not reach here due to earlier check
            raise ValueError(f"Unsupported weaving mode: {weaving_mode}")

    @classmethod
    def get_supported_weaving_modes(cls) -> list[WeavingMode]:
        """
        Get list of supported weaving modes.

        :return: List of supported WeavingMode values
        """
        return list(cls._prompter_classes.keys())
