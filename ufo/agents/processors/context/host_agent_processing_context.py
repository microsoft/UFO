from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ufo.agents.processors.context.processing_context import BasicProcessorContext
from ufo.agents.processors.schemas.actions import ActionCommandInfo
from ufo.agents.processors.schemas.target import TargetInfo


@dataclass
class HostAgentProcessorContext(BasicProcessorContext):
    """
    Host Agent specific processor context.

    This extends the basic context with Host Agent specific data including
    target management, application selection, and third-party agent coordination.
    """

    # Host Agent specific data
    agent_type: str = "HostAgent"

    # Plan and subtask management
    prev_plan: List[str] = field(default_factory=list)
    previous_subtasks: List[str] = field(default_factory=list)
    current_plan: List[str] = field(default_factory=list)

    # Target and application state
    target_info_list: List[Dict[str, TargetInfo]] = field(default_factory=list)
    selected_application_root: Optional[str] = None
    selected_target_id: Optional[str] = None
    assigned_third_party_agent: Optional[str] = None

    # Screenshot and visual data
    desktop_screenshot_url: Optional[str] = None
    screenshot_paths: Dict[str, str] = field(default_factory=dict)

    # Action and control information
    action_info: Optional[ActionCommandInfo] = None

    target: Optional[TargetInfo] = None

    agent_step: int = 0
    subtask_index: int = -1
    action: List[Dict[str, Any]] = field(default_factory=list)

    agent_name: str = ""
    application: str = ""

    control_log: Dict[str, Any] = field(default_factory=dict)

    # LLM and cost tracking
    llm_cost: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Logging and debugging
    log_path: str = ""

    @property
    def selected_keys(self) -> List[str]:
        """
        The list of selected keys for to dict.
        Returns fields corresponding to HostAgentAdditionalMemory.
        """
        return [
            "step",  # Step
            "observation",  # Observation
            "thought",  # Thought
            "status",  # Status
            "message",  # Message
            "questions",  # Questions
            "current_subtask",  # CurrentSubtask
            "plan",  # Plan
            "round_step",  # RoundStep
            "agent_step",  # AgentStep
            "round_num",  # RoundNum
            "subtask_index",  # SubtaskIndex
            "action",  # Action
            "function_call",  # FunctionCall
            "action_representation",
            "arguments",  # Arguments
            "action_type",  # ActionType
            "request",  # Request
            "agent_type",  # Agent
            "agent_name",  # AgentName
            "application",  # Application
            "cost",  # Cost
            "results",  # Results
            "result",
            "last_error",  # error (mapped to last_error)
            "execution_times",  # time_cost (mapped to execution_times)
            "total_time",
            "control_log",  # ControlLog
        ]
