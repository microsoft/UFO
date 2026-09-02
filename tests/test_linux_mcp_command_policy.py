"""Security regression tests for the Linux MCP command allow-list."""

import os
from pathlib import Path

import pytest

from ufo.client.mcp.http_servers import linux_mcp_server


_is_command_allowed = linux_mcp_server._is_command_allowed


@pytest.mark.parametrize(
    "command",
    [
        "sort data.txt",
        "sort -S 1K --compress-program=make data.txt",
        "sort -S 1K --compress-program make data.txt",
        "sort --output=result.txt data.txt",
    ],
)
def test_sort_is_not_allowed(command: str) -> None:
    assert not _is_command_allowed(command)


def test_neighboring_read_only_command_remains_allowed() -> None:
    assert _is_command_allowed("uniq data.txt")


@pytest.mark.parametrize(
    "command",
    [
        "./uniq data.txt",
        "../project/test -e data.txt",
        "/tmp/attacker/uniq data.txt",
        "/usr/bin/uniq data.txt",
    ],
)
def test_path_qualified_executable_is_not_allowed(command: str) -> None:
    assert not _is_command_allowed(command)


def test_command_without_argument_policy_fails_closed(monkeypatch) -> None:
    monkeypatch.delitem(
        linux_mcp_server._ARGUMENT_POLICIES, "uniq", raising=False
    )

    assert not _is_command_allowed("uniq data.txt")


def test_every_allowed_command_has_an_argument_policy() -> None:
    assert set(linux_mcp_server._ARGUMENT_POLICIES) == set(
        linux_mcp_server.ALLOWED_SHELL_COMMANDS
    )


@pytest.mark.parametrize(
    "command",
    [
        "date -s 2030-01-01",
        "date --set=2030-01-01",
        "date --se=2030-01-01",
        "date 090212002026",
        "hostname attacker-host",
        "hostname -F attacker-hostname.txt",
        "file --compile -m attacker.magic",
        "file --comp -m attacker.magic",
        "file -C -m attacker.magic",
        "file -z archive.gz",
        "file --uncomp archive.gz",
        "file -S -z archive.gz",
        "diff --output=result.txt original.txt updated.txt",
        "diff --out=result.txt original.txt updated.txt",
        "diff -oresult.txt original.txt updated.txt",
        "uniq input.txt output.txt",
        "uniq -c input.txt output.txt",
        "uniq -- input.txt output.txt",
    ],
)
def test_mutating_command_arguments_are_not_allowed(command: str) -> None:
    assert not _is_command_allowed(command)


@pytest.mark.parametrize(
    "command",
    [
        "uniq data.txt",
        "uniq -c data.txt",
        "date",
        "date -u +%s",
        "hostname -f",
        "file data.txt",
        "diff original.txt updated.txt",
    ],
)
def test_read_only_command_arguments_remain_allowed(command: str) -> None:
    assert _is_command_allowed(command)


def test_resolve_allowed_executables_uses_only_trusted_directory(
    tmp_path: Path,
) -> None:
    trusted_dir = tmp_path / "trusted"
    trusted_dir.mkdir()
    trusted_executable = trusted_dir / "uniq"
    trusted_executable.write_text("executable", encoding="utf-8")
    trusted_executable.chmod(0o755)

    resolved = linux_mcp_server._resolve_allowed_executables(
        frozenset({"uniq"}), (trusted_dir,)
    )

    assert resolved == {"uniq": trusted_executable.resolve()}


def test_resolve_allowed_executables_rejects_symlink_outside_trusted_directory(
    tmp_path: Path,
) -> None:
    trusted_dir = tmp_path / "trusted"
    trusted_dir.mkdir()
    outside_executable = tmp_path / "attacker-controlled"
    outside_executable.write_text("executable", encoding="utf-8")
    outside_executable.chmod(0o755)
    try:
        (trusted_dir / "uniq").symlink_to(outside_executable)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    resolved = linux_mcp_server._resolve_allowed_executables(
        frozenset({"uniq"}), (trusted_dir,)
    )

    assert resolved == {}


@pytest.mark.asyncio
async def test_execution_uses_pinned_executable_with_attacker_controlled_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    attacker_executable = tmp_path / "uniq"
    attacker_executable.write_text("attacker-controlled", encoding="utf-8")
    attacker_executable.chmod(0o755)
    pinned_executable = Path("/usr/bin/uniq")
    executed_argv = []

    class CompletedProcess:
        returncode = 0

        def __init__(self):
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stdout.feed_data(b"trusted output")
            self.stdout.feed_eof()
            self.stderr = linux_mcp_server.asyncio.StreamReader()
            self.stderr.feed_eof()

        async def wait(self):
            return self.returncode

    async def capture_subprocess(*argv, **kwargs):
        executed_argv.append((argv, kwargs))
        return CompletedProcess()

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        capture_subprocess,
    )

    result = await linux_mcp_server._execute_allowed_command(
        "uniq data.txt",
        timeout=30,
        cwd=str(tmp_path),
        executable_paths={"uniq": pinned_executable},
    )

    assert result["success"] is True
    assert executed_argv == [
        (
            (str(pinned_executable), "data.txt"),
            {
                "stdout": linux_mcp_server.asyncio.subprocess.PIPE,
                "stderr": linux_mcp_server.asyncio.subprocess.PIPE,
                "cwd": str(tmp_path),
                "start_new_session": os.name == "posix",
            },
        )
    ]
    assert os.fspath(attacker_executable) not in executed_argv[0][0]


@pytest.mark.asyncio
async def test_execution_terminates_process_when_output_limit_is_exceeded(
    monkeypatch,
) -> None:
    class ExcessiveOutputProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stdout.feed_data(b"12345")
            self.stdout.feed_eof()
            self.stderr = linux_mcp_server.asyncio.StreamReader()
            self.stderr.feed_eof()

        def kill(self):
            self.killed = True
            self.returncode = -9

        async def wait(self):
            return self.returncode

    process = ExcessiveOutputProcess()

    async def create_subprocess(*argv, **kwargs):
        return process

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        create_subprocess,
    )

    result = await linux_mcp_server._execute_allowed_command(
        "uniq data.txt",
        timeout=30,
        cwd=None,
        executable_paths={"uniq": Path("/usr/bin/uniq")},
        output_limit=4,
    )

    assert result == {
        "success": False,
        "error": "Command output exceeded the 4-byte limit.",
    }
    assert process.killed is True


@pytest.mark.asyncio
async def test_output_limit_is_shared_by_stdout_and_stderr(monkeypatch) -> None:
    class CombinedOutputProcess:
        returncode = 0

        def __init__(self):
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stdout.feed_data(b"123")
            self.stdout.feed_eof()
            self.stderr = linux_mcp_server.asyncio.StreamReader()
            self.stderr.feed_data(b"45")
            self.stderr.feed_eof()

        async def wait(self):
            return self.returncode

    async def create_subprocess(*argv, **kwargs):
        return CombinedOutputProcess()

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        create_subprocess,
    )

    result = await linux_mcp_server._execute_allowed_command(
        "uniq data.txt",
        timeout=30,
        cwd=None,
        executable_paths={"uniq": Path("/usr/bin/uniq")},
        output_limit=4,
    )

    assert result == {
        "success": False,
        "error": "Command output exceeded the 4-byte limit.",
    }


@pytest.mark.asyncio
async def test_execution_terminates_process_when_request_is_cancelled(
    monkeypatch,
) -> None:
    started = linux_mcp_server.asyncio.Event()

    class RunningProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stderr = linux_mcp_server.asyncio.StreamReader()

        def kill(self):
            self.killed = True
            self.returncode = -9
            self.stdout.feed_eof()
            self.stderr.feed_eof()

        async def wait(self):
            return self.returncode

    process = RunningProcess()

    async def create_subprocess(*argv, **kwargs):
        started.set()
        return process

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        create_subprocess,
    )

    execution = linux_mcp_server.asyncio.create_task(
        linux_mcp_server._execute_allowed_command(
            "uniq data.txt",
            timeout=30,
            cwd=None,
            executable_paths={"uniq": Path("/usr/bin/uniq")},
        )
    )
    await started.wait()
    execution.cancel()

    with pytest.raises(linux_mcp_server.asyncio.CancelledError):
        await execution

    assert process.killed is True


@pytest.mark.asyncio
async def test_execution_timeout_includes_waiting_for_process_exit(
    monkeypatch,
) -> None:
    class SilentRunningProcess:
        returncode = None

        def __init__(self):
            self.killed = False
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stdout.feed_eof()
            self.stderr = linux_mcp_server.asyncio.StreamReader()
            self.stderr.feed_eof()
            self.finished = linux_mcp_server.asyncio.Event()

        def kill(self):
            self.killed = True
            self.returncode = -9
            self.finished.set()

        async def wait(self):
            await self.finished.wait()
            return self.returncode

    process = SilentRunningProcess()

    async def create_subprocess(*argv, **kwargs):
        return process

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        create_subprocess,
    )

    result = await linux_mcp_server.asyncio.wait_for(
        linux_mcp_server._execute_allowed_command(
            "uniq data.txt",
            timeout=0.01,
            cwd=None,
            executable_paths={"uniq": Path("/usr/bin/uniq")},
        ),
        timeout=1,
    )

    assert result == {"success": False, "error": "Timeout after 0.01s."}
    assert process.killed is True


@pytest.mark.asyncio
async def test_termination_kills_live_posix_process_group(
    monkeypatch,
) -> None:
    killed_groups = []

    class RunningProcess:
        pid = 1234
        returncode = None

        async def wait(self):
            self.returncode = -9
            return self.returncode

    monkeypatch.setattr(
        linux_mcp_server, "_USE_PROCESS_GROUPS", True, raising=False
    )
    monkeypatch.setattr(
        linux_mcp_server.signal, "SIGKILL", 9, raising=False
    )
    monkeypatch.setattr(
        linux_mcp_server.os,
        "killpg",
        lambda process_id, sig: killed_groups.append((process_id, sig)),
        raising=False,
    )

    await linux_mcp_server._terminate_process(RunningProcess())

    assert killed_groups == [(1234, linux_mcp_server.signal.SIGKILL)]


@pytest.mark.asyncio
async def test_termination_does_not_signal_group_after_leader_exits(
    monkeypatch,
) -> None:
    killed_groups = []

    class ExitedProcess:
        pid = 1234
        returncode = 0

    monkeypatch.setattr(
        linux_mcp_server, "_USE_PROCESS_GROUPS", True, raising=False
    )
    monkeypatch.setattr(
        linux_mcp_server.signal, "SIGKILL", 9, raising=False
    )
    monkeypatch.setattr(
        linux_mcp_server.os,
        "killpg",
        lambda process_id, sig: killed_groups.append((process_id, sig)),
        raising=False,
    )

    await linux_mcp_server._terminate_process(ExitedProcess())

    assert killed_groups == []


@pytest.mark.asyncio
async def test_system_info_collection_uses_pinned_executables(monkeypatch) -> None:
    executable_paths = {
        "uname": Path("/usr/bin/uname"),
        "uptime": Path("/usr/bin/uptime"),
        "free": Path("/usr/bin/free"),
        "df": Path("/usr/bin/df"),
    }
    executed_argv = []

    class CompletedProcess:
        returncode = 0

        def __init__(self):
            self.stdout = linux_mcp_server.asyncio.StreamReader()
            self.stdout.feed_data(b"system info\n")
            self.stdout.feed_eof()
            self.stderr = linux_mcp_server.asyncio.StreamReader()
            self.stderr.feed_eof()

        async def wait(self):
            return self.returncode

    async def capture_subprocess(*argv, **kwargs):
        executed_argv.append(argv)
        return CompletedProcess()

    monkeypatch.setattr(
        linux_mcp_server.asyncio,
        "create_subprocess_exec",
        capture_subprocess,
    )

    result = await linux_mcp_server._collect_system_info(
        executable_paths, timeout=10
    )

    assert result == {
        "uname": "system info",
        "uptime": "system info",
        "memory": "system info",
        "disk": "system info",
    }
    assert executed_argv == [
        (os.fspath(executable_paths["uname"]), "-a"),
        (os.fspath(executable_paths["uptime"]),),
        (os.fspath(executable_paths["free"]), "-h"),
        (os.fspath(executable_paths["df"]), "-h"),
    ]


@pytest.mark.asyncio
async def test_system_info_reports_unavailable_trusted_executables() -> None:
    result = await linux_mcp_server._collect_system_info({}, timeout=10)

    assert set(result) == {"uname", "uptime", "memory", "disk"}
    assert all(
        value
        == "Error: Command executable is unavailable in trusted directories."
        for value in result.values()
    )
