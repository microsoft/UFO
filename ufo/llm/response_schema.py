from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


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

    Status: str = Field(
        description="Status of the HostAgent: 'FINISH' (user request completed), 'CONTINUE' (further actions needed), 'PENDING' (questions for user clarification), or 'ASSIGN' (sub-tasks need to be assigned to AppAgent).",
        enum=["FINISH", "CONTINUE", "PENDING", "ASSIGN"],
    )

    Plan: List[str] = Field(
        description="List of future sub-tasks to be completed by the AppAgent after the current sub-task is finished. Empty list if task is finished and no further actions required."
    )

    Questions: List[str] = Field(
        description="List of questions that need to be answered by the user to get information missing but necessary to complete the task. Empty list if no questions needed."
    )

    Comment: str = Field(
        description="Additional comments or information. If task is finished, provides a brief summary of the task or action flow. If task is not finished, provides a brief summary of screenshots, current progress, or future actions requiring attention."
    )


class SaveScreenshotConfig(BaseModel):
    save: bool = Field(
        description="Whether to save the screenshot of the current application window"
    )
    reason: str = Field(description="The reason for saving the screenshot")


class AppAgentResponse(BaseModel):
    Observation: str = Field(
        description="Detailed description of the screenshot of the current application window, including observations of the application and its current status related to the user request. Can also compare with previous screenshots."
    )

    Thought: str = Field(
        description="Thinking and logic for the current one-step action required to fulfill the given sub-task. Restricted to providing thought for only one step action."
    )

    Function: str = Field(
        description="Precise API function name without arguments to be called on the control item (e.g., click_input). Empty string if no suitable API function or if task is complete."
    )

    Args: str = Field(
        description="Precise arguments in a dictionary in string format. Empty dict if API doesn't require arguments or if no function is needed. Must be a valid JSON string."
    )

    Status: str = Field(description="Status of the task given the action.")

    Plan: List[str] = Field(
        description="List of future actions to complete the subtask after taking the current action. Must provide detailed steps. May reference previous plan and revise if necessary. '<FINISH>' if task will be complete after current action."
    )

    Comment: str = Field(
        description="Additional comments or information. If task is finished, provides a brief summary of the action flow. If not finished, summarizes current progress, describes what is observed, and explains any plan changes."
    )

    SaveScreenshot: SaveScreenshotConfig = Field(
        description="Configuration for saving the screenshot of the current application window and its reason."
    )


class EvaluationSubsore(BaseModel):
    name: str = Field(description="The sub-score name")

    evaluation: Literal["yes", "no", "unsure"] = Field(
        description="The sub-score result for the evaluation, which can be 'yes', 'no', or 'unsure'."
    )


class EvaluationResponse(BaseModel):
    reason: str = Field(
        description="The detailed reason for your judgment, by observing the screenshot differences and the Execution Trajectory"
    )

    sub_scores: List[EvaluationSubsore] = Field(
        description="Dictionary of sub-scores with yes/no/unsure values",
    )

    complete: Literal["yes", "no", "unsure"] = Field(
        description="Overall completion status of the evaluation"
    )
