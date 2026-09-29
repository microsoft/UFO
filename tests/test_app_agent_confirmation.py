# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Regression tests for consent before AppAgent action dispatch."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from aip.messages import Result, ResultStatus
from config.config_loader import get_ufo_config
from ufo.agents.agent.app_agent import AppAgent
from ufo.agents.memory.blackboard import Blackboard
from ufo.agents.processors.context.processing_context import ProcessingResult
from ufo.agents.processors.schemas.response_schema import AppAgentResponse
from ufo.agents.processors.schemas.target import TargetInfo, TargetKind
from ufo.agents.processors.strategies.app_agent_processing_strategy import (
    AppActionExecutionStrategy,
    AppControlInfoStrategy,
    AppLLMInteractionStrategy,
    AppScreenshotCaptureStrategy,
)
from ufo.agents.states.app_agent_state import ConfirmAppAgentState
from ufo.agents.states.operator_state import ConfirmOpenAIOperatorState
from ufo.module import interactor
from ufo.module.context import Context, ContextNames


class RecordingDispatcher:
    def __init__(self):
        self.calls = []
        self.error = None

    async def execute_commands(self, commands):
        self.calls.append(commands)
        if self.error:
            raise self.error
        return [
            Result(status=ResultStatus.SUCCESS, result="executed", namespace="test")
            for _ in commands
        ]


class RecordingLog:
    def __init__(self):
        self.entries = []

    def write(self, text):
        self.entries.append(json.loads(text))


@pytest.fixture
def harness(monkeypatch):
    dispatcher = RecordingDispatcher()
    log = RecordingLog()
    context = Context(command_dispatcher=dispatcher)
    context.set(ContextNames.LOGGER, log)
    context.set(ContextNames.APPLICATION_PROCESS_NAME, "Test editor")
    agent = AppAgent("test", "editor", "editor", False, "", "", skip_prompter=True)
    agent.host = SimpleNamespace(blackboard=Blackboard())
    agent._context_provision_executed = True
    target = TargetInfo(kind=TargetKind.CONTROL, id="1", name="Document")
    data = SimpleNamespace(
        agent=agent,
        context=context,
        dispatcher=dispatcher,
        log=log,
        prompts=[],
        decision=True,
        prompt_error=None,
        llm_calls=0,
        response=None,
    )

    async def collect_screenshot(self, agent, context):
        return ProcessingResult(
            success=True,
            data={"clean_screenshot_path": "", "application_window_info": target},
        )

    async def collect_controls(self, agent, context):
        return ProcessingResult(success=True, data={"annotation_dict": {"1": target}})

    async def model_response(self, agent, context):
        data.llm_calls += 1
        return ProcessingResult(
            success=True,
            data={
                "parsed_response": data.response,
                "llm_cost": 0.25,
                "response_text": data.response.model_dump_json(),
                "prompt_message": [],
                "last_control_screenshot_path": "",
                "concat_screenshot_path": "",
                **data.response.model_dump(),
            },
        )

    def ask(action, target):
        # The real gate must run before any command reaches the dispatcher.
        assert dispatcher.calls == []
        data.prompts.append((action, target))
        if data.prompt_error:
            raise data.prompt_error
        return data.decision

    monkeypatch.setattr(get_ufo_config().system, "safe_guard", True)
    monkeypatch.setattr(AppScreenshotCaptureStrategy, "execute", collect_screenshot)
    monkeypatch.setattr(AppControlInfoStrategy, "execute", collect_controls)
    monkeypatch.setattr(AppLLMInteractionStrategy, "execute", model_response)
    monkeypatch.setattr(
        AppActionExecutionStrategy, "_save_annotated_screenshot", lambda *a, **kw: None
    )
    monkeypatch.setattr(interactor, "sensitive_step_asker", ask)
    return data


def response(*statuses):
    actions = [
        {
            "function": "set_edit_text",
            "arguments": {"id": "1", "text": f"marker-{index}"},
            "status": status,
        }
        for index, status in enumerate(statuses)
    ]
    return AppAgentResponse(
        observation="Test document",
        thought="Perform the requested edit",
        action=actions[0] if len(actions) == 1 else actions,
    )


@pytest.mark.parametrize(
    "statuses", [("CONFIRM",), ("CONTINUE", "CONFIRM"), ("CONFIRM", "FINISH")]
)
def test_confirm_suspends_entire_batch_before_dispatch(harness, statuses):
    harness.response = response(*statuses)
    asyncio.run(harness.agent.process(harness.context))

    assert harness.agent.status == "CONFIRM"
    assert harness.dispatcher.calls == []
    assert harness.prompts == []
    assert harness.agent.memory.length == 0
    assert harness.log.entries[-1]["status"] == "CONFIRM"
    assert all(
        action["result"]["status"] == "none"
        for action in harness.log.entries[-1]["action"]
    )


@pytest.mark.parametrize("state_class", [ConfirmAppAgentState, ConfirmOpenAIOperatorState])
def test_approval_executes_saved_action_once_without_new_model_call(harness, state_class):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    state = state_class()
    asyncio.run(state.handle(harness.agent, harness.context))

    assert len(harness.prompts) == 1
    assert "set_edit_text" in str(harness.prompts[0][0])
    assert "marker-0" in str(harness.prompts[0][0])
    assert "Document" in str(harness.prompts[0][1])
    assert len(harness.dispatcher.calls) == 1
    command = harness.dispatcher.calls[0][0]
    assert command.tool_name == "set_edit_text"
    assert command.parameters == {"id": "1", "text": "marker-0"}
    assert harness.llm_calls == 1
    assert harness.context.get(ContextNames.SESSION_COST) == 0.25
    assert harness.agent.memory.length == 1
    assert harness.log.entries[-1]["action"][0]["result"]["status"] == "success"
    assert state.next_state(harness.agent).name() == "CONTINUE"

    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())
    assert len(harness.dispatcher.calls) == 1


@pytest.mark.parametrize("state_class", [ConfirmAppAgentState, ConfirmOpenAIOperatorState])
def test_denial_discards_action_and_records_skipped_result(harness, state_class):
    harness.response = response("CONFIRM")
    harness.decision = False
    asyncio.run(harness.agent.process(harness.context))
    state = state_class()
    asyncio.run(state.handle(harness.agent, harness.context))

    assert harness.dispatcher.calls == []
    assert state.next_state(harness.agent).name() == "FINISH"
    assert harness.agent.memory.length == 1
    entry = harness.log.entries[-1]
    assert entry["status"] == "FINISH"
    assert entry["action"][0]["result"]["status"] == "skipped"
    assert entry["action_success"] == []
    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())
    assert harness.dispatcher.calls == []


@pytest.mark.parametrize("safe_guard,status", [(True, "CONTINUE"), (False, "CONFIRM")])
def test_unblocked_action_executes_without_confirmation(
    harness, monkeypatch, safe_guard, status
):
    monkeypatch.setattr(get_ufo_config().system, "safe_guard", safe_guard)
    harness.response = response(status)
    asyncio.run(harness.agent.process(harness.context))

    assert len(harness.dispatcher.calls) == 1
    assert harness.prompts == []
    assert harness.agent.status == "CONTINUE"


def test_resume_without_decision_cannot_execute(harness):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))

    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())
    assert harness.dispatcher.calls == []


def test_prompt_failure_keeps_action_unexecuted(harness):
    harness.response = response("CONFIRM")
    harness.prompt_error = EOFError("No interactive input")
    asyncio.run(harness.agent.process(harness.context))

    with pytest.raises(EOFError):
        asyncio.run(ConfirmAppAgentState().handle(harness.agent, harness.context))
    assert harness.dispatcher.calls == []
    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())


def test_approved_batch_preserves_finish_status(harness):
    harness.response = response("CONFIRM", "FINISH")
    asyncio.run(harness.agent.process(harness.context))
    state = ConfirmAppAgentState()
    asyncio.run(state.handle(harness.agent, harness.context))

    assert len(harness.dispatcher.calls) == 1
    assert len(harness.dispatcher.calls[0]) == 2
    assert state.next_state(harness.agent).name() == "FINISH"


def test_dispatch_failure_is_not_replayed_or_changed_to_continue(harness):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    harness.dispatcher.error = RuntimeError("Dispatch failed")
    state = ConfirmAppAgentState()
    asyncio.run(state.handle(harness.agent, harness.context))

    assert len(harness.dispatcher.calls) == 1
    assert harness.agent.status == "ERROR"
    assert state.next_state(harness.agent).name() == "ERROR"
    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())
    assert len(harness.dispatcher.calls) == 1


def test_confirmation_uses_snapshot_not_a_later_model_response(harness):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    harness.response.action.arguments["text"] = "unapproved replacement"
    asyncio.run(ConfirmAppAgentState().handle(harness.agent, harness.context))

    assert harness.dispatcher.calls[0][0].parameters["text"] == "marker-0"
    assert "unapproved replacement" not in str(harness.prompts)


def test_operator_preserves_finish_plan_without_obsolete_processor_attribute(harness):
    harness.response = response("CONFIRM")
    harness.response.plan = ["FINISH"]
    asyncio.run(harness.agent.process(harness.context))
    state = ConfirmOpenAIOperatorState()
    asyncio.run(state.handle(harness.agent, harness.context))

    assert state.next_state(harness.agent).name() == "FINISH"
    assert harness.agent.status == "FINISH"


def test_cancelled_dispatch_is_not_replayed(harness):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    harness.dispatcher.error = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(ConfirmAppAgentState().handle(harness.agent, harness.context))
    assert harness.agent.status == "ERROR"
    with pytest.raises(RuntimeError):
        asyncio.run(harness.agent.process_resume())
    assert len(harness.dispatcher.calls) == 1


def test_multiple_confirm_actions_require_one_decision_for_whole_batch(harness):
    harness.response = response("CONFIRM", "CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    asyncio.run(ConfirmAppAgentState().handle(harness.agent, harness.context))

    assert len(harness.prompts) == 1
    assert "marker-0" in harness.prompts[0][0]
    assert "marker-1" in harness.prompts[0][0]
    assert len(harness.dispatcher.calls) == 1
    assert len(harness.dispatcher.calls[0]) == 2
    assert harness.agent.status == "CONTINUE"


def test_disabling_guard_while_paused_resumes_without_prompt(harness, monkeypatch):
    harness.response = response("CONFIRM")
    asyncio.run(harness.agent.process(harness.context))
    monkeypatch.setattr(get_ufo_config().system, "safe_guard", False)
    asyncio.run(ConfirmAppAgentState().handle(harness.agent, harness.context))

    assert harness.prompts == []
    assert len(harness.dispatcher.calls) == 1
    assert harness.agent.status == "CONTINUE"


@pytest.mark.parametrize("statuses", [(), ("FINISH",), ("CONTINUE", "FINISH")])
def test_unflagged_batches_preserve_finish_behavior(harness, statuses):
    harness.response = response(*statuses)
    asyncio.run(harness.agent.process(harness.context))

    assert harness.agent.status == "FINISH"
    assert harness.prompts == []
    assert len(harness.dispatcher.calls) == (1 if statuses else 0)
