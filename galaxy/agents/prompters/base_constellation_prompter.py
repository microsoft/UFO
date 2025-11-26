# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Base Constellation Agent Prompter.

This module provides the base prompter class for Constellation Agents with
shared functionality between different weaving modes.
"""

from abc import ABC
import json
from typing import Dict, List, Type
from config.config_loader import get_galaxy_config
from aip.messages import MCPToolInfo
from galaxy.agents.schema import WeavingMode
from galaxy.client.components.types import AgentProfile, DeviceStatus
from galaxy.constellation.task_constellation import TaskConstellation
from ufo.prompter.basic import BasicPrompter


# Load Galaxy configuration
galaxy_config = get_galaxy_config()


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

    def _format_agent_profile(self, device_info: Dict[str, AgentProfile]) -> str:
        """
        Format device information for prompt inclusion.

        :param device_info: Dictionary of device information
        :return: Formatted device information string
        """
        if not device_info:
            return "No devices available."

        formatted_agent_profiles = []

        for _, info in device_info.items():
            # Format capabilities as a comma-separated list

            # Skip disconnected devices, as they cannot be used
            if info.status == DeviceStatus.DISCONNECTED:
                continue

            capabilities = ", ".join(info.capabilities) if info.capabilities else "None"
            os = info.os if info.os else "Unknown"

            # Format metadata as key-value pairs
            metadata_str = ""
            if info.metadata:
                metadata_items = [f"{k}: {v}" for k, v in info.metadata.items()]
                metadata_str = f" | Metadata: {', '.join(metadata_items)}"

            # Create device summary
            device_summary = (
                f"Device ID: {info.device_id}\n"
                f"OS: {os}\n"
                f"  - Capabilities: {capabilities}\n"
                f"{metadata_str}"
            )

            formatted_agent_profiles.append(device_summary)

        return "Available Device Agent Profiles:\n\n" + "\n\n".join(
            formatted_agent_profiles
        )

    def _format_constellation(self, constellation: TaskConstellation) -> str:
        """
        Format constellation information for prompt inclusion with modification hints.

        :param constellation: Task constellation object
        :return: Formatted constellation string with modification indicators
        """
        if constellation is None:
            return "No constellation information available."

        try:
            constellation_dict = constellation.to_dict()
        except Exception:
            return "Constellation information unavailable due to formatting error."

        lines = []

        # Header information
        lines.append(f"Task Constellation: {constellation_dict.get('name', 'Unnamed')}")
        lines.append(f"Status: {constellation_dict.get('state', 'unknown')}")
        lines.append(f"Total Tasks: {len(constellation_dict.get('tasks', {}))}")
        lines.append("")

        # Get modifiable items for reference
        try:
            modifiable_task_ids = {
                task.task_id for task in constellation.get_modifiable_tasks()
            }
            modifiable_dep_ids = {
                dep.line_id for dep in constellation.get_modifiable_dependencies()
            }
        except Exception:
            # Fallback if methods are not available
            modifiable_task_ids = set()
            modifiable_dep_ids = set()

        # Tasks section - focus on LLM-relevant information
        tasks = constellation_dict.get("tasks", {})
        if tasks:
            lines.append("Tasks:")
            for task_id, task_data in tasks.items():
                # Task header with modification indicator
                task_name = task_data.get("name", task_id)
                task_status = task_data.get("status", "unknown")
                target_device = task_data.get("target_device_id", "unassigned")

                # Modifiable indicator
                modifiable_indicator = (
                    "✏️ [MODIFIABLE]"
                    if task_id in modifiable_task_ids
                    else "🔒 [READ-ONLY]"
                )

                lines.append(f"  [{task_id}] {task_name} {modifiable_indicator}")
                lines.append(f"    Status: {task_status}")
                lines.append(f"    Device: {target_device}")

                # Task description
                description = task_data.get("description", "")
                if description:
                    lines.append(f"    Description: {description}")

                # Tips for task completion
                tips = task_data.get("tips", [])
                if tips:
                    lines.append("    Tips:")
                    for tip in tips:
                        lines.append(f"      - {tip}")

                # Result (if completed)
                result = task_data.get("result")
                if result is not None:
                    result_str = str(result)
                    lines.append(f"    Result: {result_str}")

                # Error (if failed)
                error = task_data.get("error")
                if error:
                    lines.append(f"    Error: {error}")

                # Add modification hint
                if task_id in modifiable_task_ids:
                    lines.append(
                        f"    💡 Hint: This task can be modified (description, tips, device assignment, etc.)"
                    )

                lines.append("")  # Empty line between tasks

        # Dependencies section - show task relationships
        dependencies = constellation_dict.get("dependencies", {})
        if dependencies:
            lines.append("Task Dependencies:")
            for dep_id, dep_data in dependencies.items():
                from_task = dep_data.get("from_task_id", "unknown")
                to_task = dep_data.get("to_task_id", "unknown")
                # dep_type = dep_data.get("dependency_type", "unknown")
                condition_desc = dep_data.get("condition_description", "")
                # is_satisfied = dep_data.get("is_satisfied", False)

                # Modifiable indicator
                modifiable_indicator = (
                    "✏️ [MODIFIABLE]"
                    if dep_id in modifiable_dep_ids
                    else "🔒 [READ-ONLY]"
                )

                dependency_line = (
                    f"  [{dep_id}] {from_task} → {to_task} {modifiable_indicator}"
                )
                if condition_desc:
                    dependency_line += f" - {condition_desc}"
                # dependency_line += (
                #     f" [{'✓ Satisfied' if is_satisfied else '✗ Not Satisfied'}]"
                # )

                lines.append(dependency_line)

                # Add modification hint
                if dep_id in modifiable_dep_ids:
                    lines.append(
                        f"    💡 Hint: This dependency can be modified (condition, type, etc.)"
                    )

            lines.append("")

        # Add summary section
        total_tasks = len(tasks)
        total_deps = len(dependencies)
        modifiable_tasks_count = len(modifiable_task_ids)
        modifiable_deps_count = len(modifiable_dep_ids)

        lines.append("📊 Modification Summary:")
        lines.append(
            f"   Tasks: {total_tasks} total, {modifiable_tasks_count} modifiable"
        )
        lines.append(
            f"   Dependencies: {total_deps} total, {modifiable_deps_count} modifiable"
        )
        lines.append("")
        lines.append(
            "💡 Note: Only PENDING or WAITING_DEPENDENCY items can be modified."
        )
        lines.append("   RUNNING, COMPLETED, or FAILED items are read-only.")

        result = "\n".join(lines)

        # print(result)

        return result

    def user_content_construction(
        self,
        request: str,
        device_info: Dict[str, AgentProfile],
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
        apis = self.api_prompt_template

        return self.prompt_template["system"].format(
            examples=examples,
            apis=apis,
        )

    def user_prompt_construction(
        self,
        request: str,
        device_info: Dict[str, AgentProfile],
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
            device_info=self._format_agent_profile(device_info),
            constellation=self._format_constellation(constellation),
        )

        return prompt

    def examples_prompt_helper(
        self,
        header: str = "## Response Examples",
        separator: str = "Example",
    ) -> str:
        """
        Construct the prompt for examples.
        :param examples: The examples.
        :param header: The header of the prompt.
        :param separator: The separator of the prompt.
        :param additional_examples: The additional examples added to the prompt.
        return: The prompt for examples.
        """

        template = """
        [User Request]:
            {request}
        [Device Info]:
            {device_info}
        [Response]:
            {response}"""

        example_dict = [
            self.example_prompt_template[key]
            for key in self.example_prompt_template.keys()
            if key.startswith("example")
        ]

        example_list = []

        for example in example_dict:
            example_str = template.format(
                request=example.get("Request"),
                device_info=json.dumps(example.get("Device-Info")),
                response=json.dumps(example.get("Response")),
            )
            example_list.append(example_str)

        return self.retrieved_documents_prompt_helper(header, separator, example_list)

    def create_api_prompt_template(self, tools: List[MCPToolInfo]):
        """
        Create the API prompt template.
        :param tools: The list of tools.
        """
        tool_prompt = BasicPrompter.tools_to_llm_prompt(tools, generate_example=False)
        self.api_prompt_template = tool_prompt
        return tool_prompt


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
    ) -> BasicPrompter:
        """
        Create prompter based on weaving mode.

        :param weaving_mode: The weaving mode (CREATION or EDITING)
        :param prompt_template: The prompt template for the prompter
        :param example_prompt_template: The example prompt template for the prompter
        :raises ValueError: If weaving mode is not supported
        """
        # Lazy loading to avoid circular imports
        if not cls._prompter_classes:
            from galaxy.agents.prompters.constellation_creation_prompter import (
                ConstellationCreationPrompter,
            )
            from galaxy.agents.prompters.constellation_editing_prompter import (
                ConstellationEditingPrompter,
            )

            cls._prompter_classes = {
                WeavingMode.CREATION: ConstellationCreationPrompter,
                WeavingMode.EDITING: ConstellationEditingPrompter,
            }

        if weaving_mode not in cls._prompter_classes:
            raise ValueError(f"Unsupported weaving mode for prompter: {weaving_mode}")

        # Load prompt templates from new config system
        agent_config = galaxy_config.agent.CONSTELLATION_AGENT
        if weaving_mode == WeavingMode.CREATION:
            prompt_template = agent_config.CONSTELLATION_CREATION_PROMPT
            example_prompt_template = agent_config.CONSTELLATION_CREATION_EXAMPLE_PROMPT
        elif weaving_mode == WeavingMode.EDITING:
            prompt_template = agent_config.CONSTELLATION_EDITING_PROMPT
            example_prompt_template = agent_config.CONSTELLATION_EDITING_EXAMPLE_PROMPT

        prompter_class = cls._prompter_classes[weaving_mode]

        return prompter_class(prompt_template, example_prompt_template)

    @classmethod
    def get_supported_weaving_modes(cls) -> list[WeavingMode]:
        """
        Get list of supported weaving modes.

        :return: List of supported WeavingMode values
        """
        return list(cls._prompter_classes.keys())
