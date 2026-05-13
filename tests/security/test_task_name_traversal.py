"""
Regression tests for the ``task_name`` path-traversal hardening.

Covers:
- ``ufo.utils.sanitize_task_name`` / ``is_safe_task_name`` helpers
- ``BaseSession`` log-path confinement under ``logs/``
- HTTP ``/api/dispatch`` rejection of unsafe ``task_name`` values
"""

from __future__ import annotations

import os
import shutil
import sys
import types
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _ensure_repo_on_path() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    if "art" not in sys.modules:
        art_mod = types.ModuleType("art")
        art_mod.text2art = lambda *args, **kwargs: ""
        sys.modules["art"] = art_mod


_ensure_repo_on_path()


from ufo.utils import is_safe_task_name, sanitize_task_name  # noqa: E402


class SanitizeTaskNameTests(unittest.TestCase):
    def test_safe_name_passes_through(self):
        self.assertEqual(sanitize_task_name("alpha-1_v2.txt"), "alpha-1_v2.txt")

    def test_traversal_payload_is_neutralized(self):
        sanitized = sanitize_task_name("../escape")
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)
        self.assertNotIn("\\", sanitized)

    def test_double_dot_only_collapses_to_fallback(self):
        sanitized = sanitize_task_name("..", fallback="safe-fallback")
        self.assertEqual(sanitized, "safe-fallback")

    def test_separators_become_underscores(self):
        self.assertEqual(sanitize_task_name("a/b\\c"), "a_b_c")

    def test_windows_absolute_path_is_stripped(self):
        sanitized = sanitize_task_name(r"C:\escape")
        self.assertNotIn(":", sanitized)
        self.assertNotIn("\\", sanitized)

    def test_url_encoded_traversal_is_neutralized(self):
        sanitized = sanitize_task_name("..%2fescape")
        self.assertNotIn("/", sanitized)
        self.assertNotIn("\\", sanitized)
        self.assertFalse(sanitized.startswith("."))

    def test_empty_yields_fallback(self):
        self.assertEqual(sanitize_task_name("", fallback="fb"), "fb")

    def test_none_yields_uuid_when_no_fallback(self):
        result = sanitize_task_name(None)
        self.assertTrue(result)
        self.assertTrue(is_safe_task_name(result))

    def test_is_safe_task_name(self):
        self.assertTrue(is_safe_task_name("ok-name_1.2"))
        self.assertFalse(is_safe_task_name("../escape"))
        self.assertFalse(is_safe_task_name(".hidden"))
        self.assertFalse(is_safe_task_name(""))
        self.assertFalse(is_safe_task_name(None))
        self.assertFalse(is_safe_task_name("a/b"))
        self.assertFalse(is_safe_task_name("C:\\x"))


class BaseSessionLogPathConfinementTests(unittest.TestCase):
    """Defense-in-depth: BaseSession must keep log_path inside logs/."""

    @classmethod
    def setUpClass(cls):
        from ufo.module.basic import BaseSession

        class _DummySession(BaseSession):
            def _init_agents(self):
                return

            def create_new_round(self):
                return None

            def next_request(self) -> str:
                return ""

            def request_to_evaluate(self) -> str:
                return ""

            def reset(self) -> None:
                return

        cls.DummySession = _DummySession
        cls.logs_root = (REPO_ROOT / "logs").resolve()
        # Make sure the escape sentinel doesn't exist before the tests run.
        shutil.rmtree(REPO_ROOT / "ufo_taskname_escape_poc", ignore_errors=True)

    def setUp(self):
        # BaseSession resolves paths relative to CWD; pin CWD to repo root.
        self._prev_cwd = os.getcwd()
        os.chdir(REPO_ROOT)

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_traversal_task_name_is_confined(self):
        session = self.DummySession(
            task="../ufo_taskname_escape_poc",
            should_evaluate=False,
            id="sec-test",
        )
        resolved = Path(session.log_path).resolve()
        self.assertTrue(
            str(resolved).startswith(str(self.logs_root) + os.sep),
            f"log_path {resolved!r} escaped logs root {self.logs_root!r}",
        )
        # And the escape sentinel must NOT have been created.
        self.assertFalse(
            (REPO_ROOT / "ufo_taskname_escape_poc").exists(),
            "Traversal payload created a directory outside logs/",
        )

    def test_absolute_path_task_name_is_confined(self):
        if os.name == "nt":
            payload = r"C:\ufo_taskname_escape_poc_abs"
        else:
            payload = "/tmp/ufo_taskname_escape_poc_abs"
        session = self.DummySession(
            task=payload,
            should_evaluate=False,
            id="sec-test-abs",
        )
        resolved = Path(session.log_path).resolve()
        self.assertTrue(
            str(resolved).startswith(str(self.logs_root) + os.sep),
            f"log_path {resolved!r} escaped logs root {self.logs_root!r}",
        )


class HttpApiDispatchRejectionTests(unittest.TestCase):
    """The /api/dispatch endpoint must reject unsafe task_name values."""

    def _build_client(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from ufo.server.services.api import create_api_router

        class _StubSessionManager:
            def get_result_by_task(self, task_name):
                return None

        class _StubClientManager:
            def list_clients(self):
                return []

            def get_client(self, client_id):
                return None

        app = FastAPI()
        app.include_router(
            create_api_router(
                session_manager=_StubSessionManager(),
                client_manager=_StubClientManager(),
                api_key="test-key",
            )
        )
        return TestClient(app)

    def test_dispatch_rejects_traversal_task_name(self):
        try:
            client = self._build_client()
        except ModuleNotFoundError as exc:
            self.skipTest(f"fastapi/test client unavailable: {exc}")
            return

        resp = client.post(
            "/api/dispatch",
            headers={"X-API-Key": "test-key"},
            json={
                "client_id": "c1",
                "request": "do something",
                "task_name": "../escape",
            },
        )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertIn("task_name", resp.text)

    def test_dispatch_rejects_absolute_path_task_name(self):
        try:
            client = self._build_client()
        except ModuleNotFoundError as exc:
            self.skipTest(f"fastapi/test client unavailable: {exc}")
            return

        resp = client.post(
            "/api/dispatch",
            headers={"X-API-Key": "test-key"},
            json={
                "client_id": "c1",
                "request": "do something",
                "task_name": "/abs/escape",
            },
        )
        self.assertEqual(resp.status_code, 400, resp.text)


if __name__ == "__main__":
    unittest.main()
