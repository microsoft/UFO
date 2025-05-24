from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Union, Dict, Any, Callable
from openai import pydantic_function_tool


class HostAgentResponse(BaseModel):
    Observation: str = Field(
        description="Detailed description of the screenshot of the current window, including observations of applications and their current status related to the user request."
    )
    
    Thought: str = Field(
        description="Logical thinking process that decomposes the user request into a list of sub-tasks, each of which can be completed by an AppAgent."
    )
    
    CurrentSubtask: str = Field(
        description="Description of current sub-task to be completed by an AppAgent to fulfill the user request. Empty string if the task is finished."
    )
    
    Message: List[str] = Field(
        description="List of messages and information for the AppAgent to better understand the user request and complete the current sub-task. Can include tips, instructions, necessary information, or content summarized from history of actions, thoughts, and previous results. Empty list if no message is needed."
    )
    
    ControlLabel: str = Field(
        description="Precise label of the application to be selected for the current sub-task, strictly adhering to the provided options in the 'label' field of the application information. Empty string if no suitable application or if task is complete."
    )
    
    ControlText: str = Field(
        description="Precise title of the application or control to be selected for the current sub-task, strictly adhering to the provided options. Empty string if no suitable application."
    )
    
    Status: str = Field(
        description="Status of the HostAgent: 'FINISH' (user request completed), 'CONTINUE' (further actions needed), 'PENDING' (questions for user clarification), or 'ASSIGN' (sub-tasks need to be assigned to AppAgent).",
        enum=["FINISH", "CONTINUE", "PENDING", "ASSIGN"]
    )
    
    Plan: List[str] = Field(
        description="List of future sub-tasks to be completed by the AppAgent after the current sub-task is finished. Empty list if task is finished and no further actions required."
    )
    
    Bash: str = Field(
        description="Bash command to be executed by the HostAgent before assigning sub-tasks to the AppAgent. For example, to open an application. Empty string if no bash command needed. If this is specified, 'Status' must be set to 'CONTINUE'."
    )
    
    Questions: List[str] = Field(
        description="List of questions that need to be answered by the user to get information missing but necessary to complete the task. Empty list if no questions needed."
    )
    
    Comment: str = Field(
        description="Additional comments or information. If task is finished, provides a brief summary of the task or action flow. If task is not finished, provides a brief summary of screenshots, current progress, or future actions requiring attention."
    )

    class Config:
        extra = "forbid"

class SaveScreenshotConfig(BaseModel):
    save: bool = Field(
        description="Whether to save the screenshot of the current application window"
    )
    reason: str = Field(
        description="The reason for saving the screenshot"
    )
    
    class Config:
        extra = "forbid"


class FunctionArg(BaseModel):
    name: bool = Field(
        description="The name of the argument"
    )

    value: str = Field(
        description="The argument value"
    )
    
    class Config:
        extra = "forbid"

class AppAgentResponse(BaseModel):
    Observation: str = Field(
        description="Detailed description of the screenshot of the current application window, including observations of the application and its current status related to the user request. Can also compare with previous screenshots."
    )
    
    Thought: str = Field(
        description="Thinking and logic for the current one-step action required to fulfill the given sub-task. Restricted to providing thought for only one step action."
    )
    
    ControlLabel: str = Field(
        description="Precise annotated label of the control item to be selected, adhering strictly to the provided options in the 'label' field. Empty string if no suitable control item or if task is complete."
    )
    
    ControlText: str = Field(
        description="Precise control_text of the control item to be selected, strictly matching the provided options in the 'control_text' field. Empty string if no suitable control item or if task is complete. Must match exactly with the selected control label."
    )
    
    Function: str = Field(
        description="Precise API function name without arguments to be called on the control item (e.g., click_input). Empty string if no suitable API function or if task is complete."
    )
    
    Args: List[FunctionArg] = Field(
        description="Precise arguments in a list of key-value pairs"
    )
    
    Status: str = Field(
        description="Status of the task given the action."
    )
    
    Plan: str = Field(
        description="List of future actions to complete the subtask after taking the current action. Must provide detailed steps. May reference previous plan and revise if necessary. '<FINISH>' if task will be complete after current action."
    )
    
    Comment: str = Field(
        description="Additional comments or information. If task is finished, provides a brief summary of the action flow. If not finished, summarizes current progress, describes what is observed, and explains any plan changes."
    )
    
    SaveScreenshot: SaveScreenshotConfig = Field(
        description="Configuration for saving the screenshot of the current application window and its reason."
    )

    class Config:
        extra = "forbid"

# To get the JSON schema from the model
schema = HostAgentResponse.model_json_schema()
# print(schema)

# To get JSON Schema as a formatted string
import json
print(json.dumps(schema, indent=2))