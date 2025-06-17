# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Actions module - provides backward compatibility by importing from the split modules.

This module re-exports all classes and functionality from the separated contract and execution modules
to maintain backward compatibility with existing code that imports from this file.
"""

import sys
sys.path.append("./")

# Import contracts (data structures and interfaces)
from .action_contracts import (
    BaseControlLog,
    ActionExecutionLog,
    OneStepAction,
    ActionSequence,
)

# Import execution logic 
from ...automator.action_execution import (
    OneStepActionExecutor,
    ActionSequenceExecutor,
)

# Patch execution methods onto the contract classes for backward compatibility
def _patch_methods():
    """Patch execution methods onto contract classes for backward compatibility."""
    
    # Patch OneStepAction with execution methods
    OneStepAction._control_validation = OneStepActionExecutor._control_validation
    OneStepAction.execute = lambda self, puppeteer: OneStepActionExecutor.execute(self, puppeteer)
    OneStepAction.action_flow = lambda self, puppeteer, control_dict, application_window: OneStepActionExecutor.action_flow(self, puppeteer, control_dict, application_window)
    OneStepAction._get_control_log = lambda self, control_selected, application_window: OneStepActionExecutor._get_control_log(self, control_selected, application_window)
    OneStepAction.print_result = lambda self: OneStepActionExecutor.print_result(self)
    
    # Patch ActionSequence with execution methods
    ActionSequence.execute_all = lambda self, puppeteer, control_dict, application_window: ActionSequenceExecutor.execute_all(self, puppeteer, control_dict, application_window)
    ActionSequence.print_all_results = lambda self, success_only=False: ActionSequenceExecutor.print_all_results(self, success_only)

# Apply patches
_patch_methods()

# Re-export all classes for backward compatibility
__all__ = [
    "BaseControlLog",
    "ActionExecutionLog", 
    "OneStepAction",
    "ActionSequence",
    "OneStepActionExecutor",
    "ActionSequenceExecutor",
]


# Test code for backward compatibility
if __name__ == "__main__":

    action1 = OneStepAction(
        function="click",
        args={"button": "left"},
        control_label="1",
        control_text="OK",
        after_status="success",
        results=ActionExecutionLog(status="success"),
    )

    action2 = OneStepAction(
        function="click",
        args={"button": "right"},
        control_label="2",
        control_text="NotOK",
        after_status="success",
        results=ActionExecutionLog(status="success"),
    )

    action_sequence = ActionSequence([action1, action2])

    previous_actions = [
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "right"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
        {"Function": "click", "Args": {"button": "left"}, "ControlText": "OK"},
    ]

    print(action_sequence.to_list_of_dicts(previous_actions=previous_actions))
