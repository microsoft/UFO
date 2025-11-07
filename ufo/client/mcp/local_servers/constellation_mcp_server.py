#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Constellation Editor MCP Server
Provides comprehensive MCP server for TaskConstellation operations:
- Task management (add, remove, update)
- Dependency management (add, remove, update)
- Bulk operations (build, clear constellation)
- File operations (load, save constellation)
"""

from pydantic import Field
from typing import Annotated, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from ufo.client.mcp.mcp_registry import MCPRegistry
from ufo.config import get_config
from galaxy.agents.schema import TaskConstellationSchema
from galaxy.constellation.editor.constellation_editor import ConstellationEditor

# Get config
configs = get_config()


@MCPRegistry.register_factory_decorator("ConstellationEditor")
def create_constellation_mcp_server(*args, **kwargs) -> FastMCP:
    """
    Create and return the Constellation Editor MCP server instance.
    :return: FastMCP instance for constellation operations.
    """

    constellation_mcp = FastMCP("UFO Constellation Editor MCP Server")

    editor = ConstellationEditor()

    # Task Management Tools

    @constellation_mcp.tool()
    def add_task(
        task_id: Annotated[
            str,
            Field(
                description="Unique identifier for the task within the constellation. This ID must be unique across the entire constellation and will be used to reference this task in dependencies. Examples: 'open_browser', 'login_system', 'process_data', 'send_email'. Use descriptive names that clearly indicate the task's purpose."
            ),
        ],
        name: Annotated[
            str,
            Field(
                description="Human-readable name for the task that briefly describes what the task does. This should be a concise, clear title that anyone can understand at a glance. Examples: 'Open Browser', 'Login to System', 'Process Data File', 'Send Notification Email'. Keep it short but descriptive."
            ),
        ],
        description: Annotated[
            str,
            Field(
                description="Detailed description of what this task should accomplish, including specific steps, expected outcomes, and any important details. This should provide enough information for someone to understand exactly what needs to be done and how to do it. Examples: 'Open Chrome browser and navigate to the specified URL, wait for the page to fully load, then take a screenshot and save it to the designated folder', 'Connect to the database using provided credentials, execute the data processing query, and export results to CSV format'."
            ),
        ],
        target_device_id: Annotated[
            str,
            Field(
                description="Identifier of the specific device where this task should be executed.  This is useful in multi-device environments where different tasks need to run on different machines, phones, or systems. Examples: 'DESKTOP-ABC123', 'iPhone-001', 'android_device_1', 'server_node_2'. It must be chosen from the provided Device Info List"
            ),
        ] = None,
        tips: Annotated[
            Optional[List[str]],
            Field(
                description="List of critical tips, hints, and key points for successfully completing this task. Include important considerations, potential pitfalls to avoid, troubleshooting advice, and best practices. This helps task executors perform the task more effectively and handle common issues. Examples: 'Wait for page to fully load before proceeding, close any popup dialogs that appear, ensure stable network connection throughout the process', 'Handle authentication timeouts gracefully, retry up to 3 times if connection fails, log all errors for debugging'."
            ),
        ] = None,
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object containing all tasks, dependencies, and metadata after adding the new task"
        ),
    ]:
        """
        Add a new task to the constellation. The task will be validated and automatically assigned timestamps and default values.
        Returns the complete constellation state after the operation.
        """
        try:
            task_data = {
                "task_id": task_id,
                "name": name,
                "description": description,
            }

            if target_device_id:
                task_data["target_device_id"] = target_device_id

            if tips:
                # Convert string tips to list format for TaskStar
                tips_list = [tips] if isinstance(tips, str) else tips
                task_data["tips"] = tips_list

            editor.add_task(task_data)
            # Return complete constellation instead of just the task
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to add task: {str(e)}")

    @constellation_mcp.tool()
    def remove_task(
        task_id: Annotated[
            str,
            Field(
                description="Unique identifier of the task to remove from the constellation. All dependencies involving this task will also be automatically removed to maintain constellation integrity."
            ),
        ],
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object after removing the task"
        ),
    ]:
        """
        Remove a task from the constellation. This operation will automatically remove all dependencies that reference this task (both incoming and outgoing) to maintain constellation integrity.
        Returns the complete constellation state after the operation.
        """
        try:
            editor.remove_task(task_id)
            # Return complete constellation instead of just the task ID
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to remove task: {str(e)}")

    @constellation_mcp.tool()
    def update_task(
        task_id: Annotated[
            str,
            Field(description="Unique identifier of the task to update"),
        ],
        name: Annotated[
            Optional[str],
            Field(
                description="New human-readable name for the task. This should be a concise, clear title that describes what the task does. Examples: 'Open Browser', 'Login to System', 'Process Data File'. Leave empty if you don't want to change the current name."
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Field(
                description="New detailed description of what this task should accomplish. Include specific steps, expected outcomes, and important details. This should provide enough information for task execution. Examples: 'Open Chrome browser, navigate to URL, wait for full page load, then take screenshot', 'Connect to database, execute query, export to CSV'. Leave empty if you don't want to change the current description."
            ),
        ] = None,
        target_device_id: Annotated[
            str,
            Field(
                description="New target device identifier where this task should execute. Use this to change which device will run the task. Examples: 'DESKTOP-ABC123', 'iPhone-001', 'android_device_1'. Leave empty string if you don't want to change the current target device. It must be chosen from the provided Device Info List"
            ),
        ] = None,
        tips: Annotated[
            Optional[List[str]],
            Field(
                description="List of New critical tips and key points for completing this task successfully. Include important considerations, potential pitfalls, troubleshooting advice, and best practices. Examples: 'Wait for page load, close popups, ensure stable network', 'Handle auth timeouts, retry 3 times, log errors'. Leave empty if you don't want to change the current tips."
            ),
        ] = None,
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object after updating the task"
        ),
    ]:
        """
        Update specific fields of an existing task in the constellation. Only the provided fields will be modified, other fields remain unchanged.
        Returns the complete constellation state after the operation.
        """
        try:
            # Build updates dictionary from provided parameters
            updates = {}
            if name is not None:
                updates["name"] = name
            if description is not None:
                updates["description"] = description
            if target_device_id is not None:
                updates["target_device_id"] = target_device_id
            if tips is not None:
                # Convert string tips to list format for TaskStar
                tips_list = [tips] if isinstance(tips, str) else tips
                updates["tips"] = tips_list

            if not updates:
                raise ToolError("At least one field must be provided for update")

            editor.update_task(task_id, **updates)
            # Return complete constellation instead of just the task
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to update task: {str(e)}")

    # Dependency Management Tools

    @constellation_mcp.tool()
    def add_dependency(
        dependency_id: Annotated[
            str,
            Field(
                description="Unique identifier of the dependency relationship to add. This is the line_id of the TaskStarLine object, typically in format 'from_task_id->to_task_id'. You MUST generate a unique dependency_id in the arguments, and do not omit it!"
            ),
        ],
        from_task_id: Annotated[
            str,
            Field(
                description="Unique identifier of the source/prerequisite task that must complete first before the target task can begin execution. This task acts as a dependency that the target task waits for. Examples: 'login_system', 'download_file', 'initialize_database'. The task with this ID must already exist in the constellation."
            ),
        ],
        to_task_id: Annotated[
            str,
            Field(
                description="Unique identifier of the target/dependent task that will wait for the source task to complete before it can start execution. This task depends on the completion of the source task. Examples: 'process_data', 'send_report', 'cleanup_files'. The task with this ID must already exist in the constellation."
            ),
        ],
        condition_description: Annotated[
            Optional[str],
            Field(
                description="Human-readable description explaining the specific conditions or requirements for this dependency relationship. Describe why the target task needs to wait for the source task and what conditions must be met. This helps with understanding the workflow logic and debugging. Examples: 'Wait for successful user authentication before accessing user data', 'Ensure file download completes successfully before processing the file', 'Database must be initialized and ready before running queries', 'Wait for data processing to finish before generating the final report'."
            ),
        ] = None,
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object after adding the dependency"
        ),
    ]:
        """
        Add a dependency relationship between two tasks in the constellation. This creates a directed edge from source to target task, establishing execution order constraints where the target task waits for the source task to complete.
        Returns the complete constellation state after the operation.
        """
        try:
            dependency_data = {
                "line_id": dependency_id,
                "from_task_id": from_task_id,
                "to_task_id": to_task_id,
                "dependency_type": "unconditional",  # Default to unconditional
            }

            if condition_description:
                dependency_data["condition_description"] = condition_description

            editor.add_dependency(dependency_data)
            # Return complete constellation instead of just the dependency
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to add dependency: {str(e)}")

    @constellation_mcp.tool()
    def remove_dependency(
        dependency_id: Annotated[
            str,
            Field(
                description="Unique identifier of the dependency relationship to remove. This is the line_id of the TaskStarLine object, typically in format 'from_task_id->to_task_id'."
            ),
        ],
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object after removing the dependency"
        ),
    ]:
        """
        Remove a specific dependency relationship from the constellation. This breaks the connection between two tasks without affecting the tasks themselves.
        Returns the complete constellation state after the operation.
        """
        try:
            editor.remove_dependency(dependency_id)
            # Return complete constellation instead of just the dependency ID
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to remove dependency: {str(e)}")

    @constellation_mcp.tool()
    def update_dependency(
        dependency_id: Annotated[
            str,
            Field(
                description="Unique identifier of the dependency to update (line_id of TaskStarLine)"
            ),
        ],
        condition_description: Annotated[
            str,
            Field(
                description="New human-readable description explaining the specific conditions or requirements for this dependency relationship. Describe why the target task needs to wait for the source task and what conditions must be met. This helps with understanding the workflow logic and debugging. Examples: 'Wait for successful user authentication before accessing user data', 'Ensure file download completes successfully before processing the file', 'Database must be initialized and ready before running queries', 'Wait for data processing to finish with valid output before generating the final report'."
            ),
        ],
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the complete updated TaskConstellation object after updating the dependency"
        ),
    ]:
        """
        Update the condition description of an existing dependency relationship. This allows you to modify the explanation of why and how tasks depend on each other.
        Returns the complete constellation state after the operation.
        """
        try:
            updates = {"condition_description": condition_description}
            editor.update_dependency(dependency_id, **updates)
            # Return complete constellation instead of just the dependency
            return editor.constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to update dependency: {str(e)}")

    # Bulk Operations Tools

    @constellation_mcp.tool()
    def build_constellation(
        config: Annotated[
            TaskConstellationSchema,
            Field(
                description="""Configuration dictionary for building constellation with the following structure:
            {
              "tasks": [
                {
                  "task_id": "string (required)",
                  "name": "string (optional)", 
                  "description": "string (required)",
                  "priority": int (1-4, optional),
                  "status": "string (optional)",
                  "task_data": dict (optional),
                  ... other task fields
                }
              ],
              "dependencies": [
                {
                  "from_task_id": "string (required)",
                  "to_task_id": "string (required)", 
                  "dependency_type": "string (optional)",
                  "condition_description": "string (optional)",
                  ... other dependency fields
                }
              ],
              "metadata": dict (optional) - constellation-level metadata
            }
            
            All tasks will be created first, then dependencies will be established. The constellation will be validated for DAG integrity."""
            ),
        ],
        clear_existing: Annotated[
            bool,
            Field(
                description="Whether to clear all existing tasks and dependencies before building the new constellation. If false, new tasks and dependencies will be added to existing ones."
            ),
        ] = True,
    ) -> Annotated[
        str,
        Field(
            description="JSON string representation of the built TaskConstellation object containing all created tasks, dependencies, and metadata"
        ),
    ]:
        """
        Build a complete constellation from configuration data. This allows batch creation of multiple tasks and dependencies in a single operation with automatic validation.
        """
        try:
            constellation = editor.build_constellation(config, clear_existing)
            return constellation.to_json()
        except Exception as e:
            raise ToolError(f"Failed to build constellation: {str(e)}")

    return constellation_mcp
