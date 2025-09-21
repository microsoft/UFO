# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
LLMParser - Parser for creating TaskConstellation from LLM output.

This module provides functionality to parse LLM-generated text into
structured TaskConstellation objects with tasks and dependencies.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from ...core.interfaces import IRequestProcessor
from ..enums import DependencyType, TaskPriority, DeviceType
from ..task_star import TaskStar
from ..task_star_line import TaskStarLine
from ..task_constellation import TaskConstellation


class LLMParser:
    """
    Parses LLM output to create TaskConstellation objects.

    Supports multiple input formats:
    - Natural language descriptions
    - Structured JSON
    - Mixed format with tasks and dependencies

    Implements ILLMParser interface for consistent parsing operations.
    """

    def __init__(self) -> None:
        """Initialize the LLM parser with keyword patterns and device mappings."""
        self._task_keywords: List[str] = [
            "task",
            "step",
            "action",
            "do",
            "execute",
            "run",
            "perform",
            "complete",
        ]
        self._dependency_keywords: List[str] = [
            "after",
            "before",
            "when",
            "if",
            "depends",
            "requires",
            "needs",
            "following",
        ]
        self._device_keywords: Dict[str, DeviceType] = {
            "windows": DeviceType.WINDOWS,
            "mac": DeviceType.MACOS,
            "macos": DeviceType.MACOS,
            "linux": DeviceType.LINUX,
            "android": DeviceType.ANDROID,
            "ios": DeviceType.IOS,
            "web": DeviceType.WEB,
            "api": DeviceType.API,
        }

    def parse_from_string(
        self, llm_output: str, constellation_name: Optional[str] = None
    ) -> TaskConstellation:
        """
        Parse LLM output string into a TaskConstellation.

        Args:
            llm_output: Raw LLM output string
            constellation_name: Optional name for the constellation

        Returns:
            TaskConstellation instance

        Raises:
            ValueError: If parsing fails
        """
        # Try to parse as JSON first
        try:
            return self._parse_json(llm_output, constellation_name)
        except (json.JSONDecodeError, KeyError):
            pass

        # Try structured text parsing
        try:
            return self._parse_structured_text(llm_output, constellation_name)
        except Exception:
            pass

        # Fall back to natural language parsing
        return self._parse_natural_language(llm_output, constellation_name)

    def parse_from_json(
        self, json_data: Dict[str, Any], constellation_name: Optional[str] = None
    ) -> TaskConstellation:
        """
        Parse JSON data into a TaskConstellation.

        Args:
            json_data: JSON data dictionary
            constellation_name: Optional name for the constellation

        Returns:
            TaskConstellation instance
        """
        constellation = TaskConstellation(name=constellation_name)
        constellation._llm_source = json.dumps(json_data)

        # Parse tasks
        tasks_data = json_data.get("tasks", [])
        if isinstance(tasks_data, dict):
            tasks_data = list(tasks_data.values())

        for task_data in tasks_data:
            task = self._create_task_from_data(task_data)
            constellation.add_task(task)

        # Parse dependencies
        dependencies_data = json_data.get("dependencies", [])
        for dep_data in dependencies_data:
            dependency = self._create_dependency_from_data(dep_data)
            try:
                constellation.add_dependency(dependency)
            except ValueError as e:
                # Skip invalid dependencies but log them
                print(f"Warning: Skipping invalid dependency: {e}")

        return constellation

    def _parse_json(
        self, json_str: str, constellation_name: Optional[str] = None
    ) -> TaskConstellation:
        """Parse JSON string format."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)

        data = json.loads(json_str)
        return self.parse_from_json(data, constellation_name)

    def _parse_structured_text(
        self, text: str, constellation_name: Optional[str] = None
    ) -> TaskConstellation:
        """Parse structured text format."""
        constellation = TaskConstellation(name=constellation_name)
        constellation._llm_source = text

        lines = text.strip().split("\n")
        current_section = None
        tasks = []
        dependencies = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Section headers
            if line.lower().startswith(("tasks:", "task list:", "steps:")):
                current_section = "tasks"
                continue
            elif line.lower().startswith(("dependencies:", "dependency:", "depends:")):
                current_section = "dependencies"
                continue

            # Parse based on current section
            if current_section == "tasks":
                task_data = self._parse_task_line(line)
                if task_data:
                    tasks.append(task_data)
            elif current_section == "dependencies":
                dep_data = self._parse_dependency_line(line)
                if dep_data:
                    dependencies.append(dep_data)

        # Create tasks
        for task_data in tasks:
            task = self._create_task_from_data(task_data)
            constellation.add_task(task)

        # Create dependencies
        for dep_data in dependencies:
            dependency = self._create_dependency_from_data(dep_data)
            try:
                constellation.add_dependency(dependency)
            except ValueError:
                # Skip invalid dependencies
                pass

        return constellation

    def _parse_natural_language(
        self, text: str, constellation_name: Optional[str] = None
    ) -> TaskConstellation:
        """Parse natural language description."""
        constellation = TaskConstellation(name=constellation_name)
        constellation._llm_source = text

        # Split into sentences and paragraphs
        sentences = re.split(r"[.!?]+", text)

        task_counter = 1
        tasks = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue

            # Look for task indicators
            if any(keyword in sentence.lower() for keyword in self._task_keywords):
                task_id = f"task_{task_counter}"
                device_type = self._detect_device_type(sentence)

                task_data = {
                    "task_id": task_id,
                    "description": sentence,
                    "device_type": device_type.value if device_type else None,
                    "priority": "medium",
                }

                tasks.append(task_data)
                task_counter += 1

        # Create tasks
        for task_data in tasks:
            task = self._create_task_from_data(task_data)
            constellation.add_task(task)

        # Try to infer dependencies from natural language
        task_list = list(constellation.tasks.values())
        for i in range(len(task_list) - 1):
            # Create sequential dependencies by default
            dependency = TaskStarLine.create_unconditional(
                from_task_id=task_list[i].task_id,
                to_task_id=task_list[i + 1].task_id,
                description=f"Sequential execution: {task_list[i].task_id} -> {task_list[i + 1].task_id}",
            )

            try:
                constellation.add_dependency(dependency)
            except ValueError:
                pass

        return constellation

    def _parse_task_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single task line."""
        # Remove list markers
        line = re.sub(r"^[-*+\d+\.)\s]+", "", line).strip()

        if not line:
            return None

        # Extract task ID if present
        task_id_match = re.search(r"\[([^\]]+)\]", line)
        task_id = task_id_match.group(1) if task_id_match else None

        # Remove task ID from description
        if task_id_match:
            line = line.replace(task_id_match.group(0), "").strip()

        # Detect device type
        device_type = self._detect_device_type(line)

        # Detect priority
        priority = self._detect_priority(line)

        return {
            "task_id": task_id,
            "description": line,
            "device_type": device_type.value if device_type else None,
            "priority": priority.value,
        }

    def _parse_dependency_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single dependency line."""
        # Remove list markers
        line = re.sub(r"^[-*+\d+\.)\s]+", "", line).strip()

        # Look for dependency patterns
        patterns = [
            r"(\w+)\s*->\s*(\w+)",  # task1 -> task2
            r"(\w+)\s+depends\s+on\s+(\w+)",  # task1 depends on task2
            r"(\w+)\s+after\s+(\w+)",  # task1 after task2
            r"(\w+)\s+requires\s+(\w+)",  # task1 requires task2
        ]

        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                from_task = (
                    match.group(2)
                    if "after" in pattern
                    or "depends" in pattern
                    or "requires" in pattern
                    else match.group(1)
                )
                to_task = (
                    match.group(1)
                    if "after" in pattern
                    or "depends" in pattern
                    or "requires" in pattern
                    else match.group(2)
                )

                # Detect dependency type
                dep_type = DependencyType.UNCONDITIONAL
                if "if" in line.lower() or "when" in line.lower():
                    dep_type = DependencyType.CONDITIONAL
                elif "success" in line.lower():
                    dep_type = DependencyType.SUCCESS_ONLY

                return {
                    "from_task_id": from_task,
                    "to_task_id": to_task,
                    "dependency_type": dep_type.value,
                    "condition_description": line,
                }

        return None

    def _detect_device_type(self, text: str) -> Optional[DeviceType]:
        """Detect device type from text."""
        text_lower = text.lower()
        for keyword, device_type in self._device_keywords.items():
            if keyword in text_lower:
                return device_type
        return None

    def _detect_priority(self, text: str) -> TaskPriority:
        """Detect priority from text."""
        text_lower = text.lower()
        if any(
            word in text_lower for word in ["urgent", "critical", "high", "important"]
        ):
            return TaskPriority.HIGH
        elif any(word in text_lower for word in ["low", "optional", "later"]):
            return TaskPriority.LOW
        else:
            return TaskPriority.MEDIUM

    def _create_task_from_data(self, task_data: Dict[str, Any]) -> TaskStar:
        """Create a TaskStar from parsed data."""
        device_type = None
        if task_data.get("device_type"):
            try:
                device_type = DeviceType(task_data["device_type"])
            except ValueError:
                pass

        priority = TaskPriority.MEDIUM
        if task_data.get("priority"):
            try:
                priority = TaskPriority(task_data["priority"])
            except ValueError:
                pass

        return TaskStar(
            task_id=task_data.get("task_id"),
            name=task_data.get("name", ""),
            description=task_data.get("description", ""),
            target_device_id=task_data.get("target_device_id"),
            device_type=device_type,
            priority=priority,
            timeout=task_data.get("timeout"),
            retry_count=task_data.get("retry_count", 0),
            task_data=task_data.get("task_data", {}),
            expected_output_type=task_data.get("expected_output_type"),
        )

    def _create_dependency_from_data(self, dep_data: Dict[str, Any]) -> TaskStarLine:
        """Create a TaskStarLine from parsed data."""
        dependency_type = DependencyType.UNCONDITIONAL
        if dep_data.get("dependency_type"):
            try:
                dependency_type = DependencyType(dep_data["dependency_type"])
            except ValueError:
                pass

        return TaskStarLine(
            from_task_id=dep_data["from_task_id"],
            to_task_id=dep_data["to_task_id"],
            dependency_type=dependency_type,
            condition_description=dep_data.get("condition_description", ""),
            metadata=dep_data.get("metadata", {}),
        )

    def generate_llm_prompt(self, constellation: TaskConstellation) -> str:
        """
        Generate a prompt string for LLM modification of the constellation.

        Args:
            constellation: TaskConstellation to generate prompt for

        Returns:
            Formatted prompt string
        """
        prompt = f"""
Current TaskConstellation: {constellation.name}

{constellation.to_llm_string()}

Please modify, add, or remove tasks and dependencies as needed.
Respond with a JSON structure containing:
{{
    "tasks": [
        {{
            "task_id": "unique_id",
            "description": "task description",
            "device_type": "windows|macos|linux|android|ios|web|api",
            "priority": "low|medium|high|critical",
            "target_device_id": "optional_device_id"
        }}
    ],
    "dependencies": [
        {{
            "from_task_id": "prerequisite_task_id",
            "to_task_id": "dependent_task_id",
            "dependency_type": "unconditional|conditional|success_only|completion_only",
            "condition_description": "description of the condition"
        }}
    ]
}}
"""
        return prompt.strip()

    def update_constellation_from_llm(
        self, constellation: TaskConstellation, llm_response: str
    ) -> TaskConstellation:
        """
        Update an existing constellation based on LLM response.

        Args:
            constellation: Existing TaskConstellation
            llm_response: LLM response with modifications

        Returns:
            Updated TaskConstellation
        """
        try:
            # Parse the LLM response
            new_constellation = self.parse_from_string(llm_response, constellation.name)

            # Merge the changes (simplified approach - replace entirely)
            # In a more sophisticated implementation, you could do incremental updates
            new_constellation._metadata.update(constellation.metadata)
            new_constellation._constellation_id = constellation.constellation_id

            return new_constellation

        except Exception as e:
            # If parsing fails, return original constellation
            print(f"Warning: Failed to parse LLM response: {e}")
            return constellation
