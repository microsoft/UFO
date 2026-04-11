#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import sys
import types

import pytest

# Add the project root to the Python path (matches existing unit tests style).
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, project_root)

# ufo.utils conditionally imports pywinauto on Windows. This unit test doesn't
# need the real dependency, so we stub the minimal symbol to keep the test
# environment lightweight.
if "pywinauto" not in sys.modules:
    pywinauto_mod = types.ModuleType("pywinauto")
    win32structures_mod = types.ModuleType("pywinauto.win32structures")

    class RECT:  # pragma: no cover
        pass

    win32structures_mod.RECT = RECT
    sys.modules["pywinauto"] = pywinauto_mod
    sys.modules["pywinauto.win32structures"] = win32structures_mod

if "fastmcp" not in sys.modules:
    fastmcp_mod = types.ModuleType("fastmcp")
    fastmcp_client_mod = types.ModuleType("fastmcp.client")
    fastmcp_client_transports_mod = types.ModuleType("fastmcp.client.transports")

    class FastMCP:  # pragma: no cover
        pass

    class StdioTransport:  # pragma: no cover
        pass

    fastmcp_mod.FastMCP = FastMCP
    fastmcp_client_transports_mod.StdioTransport = StdioTransport

    sys.modules["fastmcp"] = fastmcp_mod
    sys.modules["fastmcp.client"] = fastmcp_client_mod
    sys.modules["fastmcp.client.transports"] = fastmcp_client_transports_mod

import ufo.utils
from ufo.prompter.eva_prompter import EvaluationAgentPrompter


class _FakeTrajectory:
    def __init__(self, app_agent_log, final_screenshot_image):
        self.app_agent_log = app_agent_log
        self.final_screenshot_image = final_screenshot_image


def _mk_prompter(monkeypatch, trajectory: _FakeTrajectory):
    p = EvaluationAgentPrompter(is_visual=False, prompt_template="", example_prompt_template="")

    # Avoid needing prompt templates; we only care about screenshot handling.
    monkeypatch.setattr(p, "user_prompt_construction", lambda request, log_eva: "ok", raising=True)
    monkeypatch.setattr(p, "load_logs", lambda log_path: trajectory, raising=True)

    calls = []

    def _encode_image(path):
        calls.append(path)
        return f"encoded:{path}"

    monkeypatch.setattr(ufo.utils, "encode_image", _encode_image, raising=True)
    return p, calls


def test_head_tail_does_not_crash_when_app_agent_log_empty(monkeypatch):
    traj = _FakeTrajectory(app_agent_log=[], final_screenshot_image="final.png")
    p, calls = _mk_prompter(monkeypatch, traj)

    content = p.user_content_construction_head_tail(log_path="unused", request="req")

    assert calls == ["final.png"]
    assert any(item.get("type") == "text" and item.get("text") == "ok" for item in content)


def test_head_tail_encodes_initial_when_app_agent_log_present(monkeypatch):
    traj = _FakeTrajectory(
        app_agent_log=[{"ScreenshotImages": {"clean_screenshot_path": "init.png"}}],
        final_screenshot_image="final.png",
    )
    p, calls = _mk_prompter(monkeypatch, traj)

    content = p.user_content_construction_head_tail(log_path="unused", request="req")

    assert calls == ["init.png", "final.png"]
    assert any(item.get("type") == "text" and item.get("text") == "ok" for item in content)
