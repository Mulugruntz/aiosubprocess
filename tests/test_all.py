import asyncio
import sys
from datetime import timedelta, datetime
from itertools import zip_longest
from typing import Union

import pytest
from aiosubprocess import Process

# asyncio.Task.all_tasks is deprecated in favour of asyncio.all_tasks in Py3.7
try:
    from asyncio import all_tasks
except ImportError:  # pragma: no cover
    all_tasks = asyncio.Task.all_tasks


def get_command(cmd: Union[str, list]) -> Union[str, list]:  # pragma: no cover
    if not sys.platform.startswith("win"):
        return cmd
    if isinstance(cmd, str):
        return cmd.replace(";", "&")
    if isinstance(cmd, list):
        return list(map(lambda s: s.replace(";", "&"), cmd))
    return cmd


@pytest.mark.skipif(sys.platform.startswith("win"), reason="does not run on windows")
@pytest.mark.asyncio
async def test_double_shell(event_loop):
    reader = Process(
        """for i in {1..5}
        do
           echo "Hello $i World" > tempfile.log
           sleep 0.1
        done""",
        loop=event_loop,
        name="Writer",
    )
    writer = Process(
        "timeout --foreground 1s tail -f tempfile.log",
        loop=event_loop,
        name="Reader",
        expected_returncode=124,  # Because timeout is expected
        sleep_resolution=0.05,
    )
    awaitable_reader = reader.shell()
    awaitable_writer = writer.shell()
    gathered = asyncio.gather(awaitable_reader, awaitable_writer, loop=event_loop)
    await gathered
    assert gathered.result() == [True, True]
    deleter = Process(
        "unlink tempfile.log",
        loop=event_loop,
        name="Deleter",
    )
    result = await deleter.shell()
    assert result is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cmd,expected_returncode,expected_result",
    [
        pytest.param("exit 0", 0, True, id="retcode_ok_success"),
        pytest.param("exit 1", 0, False, id="retcode_nok_fail"),
        pytest.param("exit 0", 1, False, id="retcode_ok_fail"),
        pytest.param("exit 1", 1, True, id="retcode_nok_success"),
    ],
)
async def test_return_codes(event_loop, cmd, expected_returncode, expected_result):
    cmd = get_command(cmd)
    retcode_sub = Process(cmd, loop=event_loop, expected_returncode=expected_returncode)
    result = await retcode_sub.shell()
    assert result is expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cmd,expected_stdout,expected_stderr",
    [
        pytest.param("echo TEST", ["TEST"], [], id="one_stdout"),
        pytest.param("echo TEST >&2", [], ["TEST"], id="one_stderr"),
        pytest.param("echo TEST; echo TEST2", ["TEST", "TEST2"], [], id="two_stdout"),
        pytest.param(
            ["echo TEST;", "echo TEST2"], ["TEST", "TEST2"], [], id="two_stdout_list"
        ),
        pytest.param(
            "echo TEST; echo TEST2 >&2", ["TEST"], ["TEST2"], id="one_stdout_one_stderr"
        ),
    ],
)
async def test_shell(event_loop, cmd, expected_stdout, expected_stderr):
    cmd = get_command(cmd)
    output, errors = [], []
    aiosub = Process(
        *([cmd] if isinstance(cmd, str) else cmd),
        loop=event_loop,
        stdout=lambda s: output.append(s),
        stderr=lambda s: errors.append(s),
        with_prefix=False,
    )
    success = await aiosub.shell()
    assert success
    assert output == expected_stdout
    assert errors == expected_stderr


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cmd,expected_stdout,expected_stderr",
    [
        pytest.param("echo TEST", ["TEST"], [], id="one_stdout"),
        pytest.param("echo TEST >&2", [], ["TEST"], id="one_stderr"),
    ],
)
@pytest.mark.parametrize(
    "name",
    [
        pytest.param("Name 1", id="first"),
        pytest.param("Name 2", id="second"),
    ],
)
@pytest.mark.parametrize(
    "with_prefix",
    [
        pytest.param(True, id="with_prefix"),
        pytest.param(False, id="without_prefix"),
    ],
)
async def test_shell_prefix(
    event_loop, cmd, expected_stdout, expected_stderr, name, with_prefix
):
    cmd = get_command(cmd)
    output, errors = [], []
    aiosub = Process(
        *([cmd] if isinstance(cmd, str) else cmd),
        loop=event_loop,
        stdout=lambda s: output.append(s),
        stderr=lambda s: errors.append(s),
        name=name,
        with_prefix=with_prefix,
    )
    success = await aiosub.shell()
    assert success
    check_with_prefix(output, expected_stdout, with_prefix, name)
    check_with_prefix(errors, expected_stderr, with_prefix, name)


def check_with_prefix(received, expected, with_prefix, name):
    for recv, exp in zip_longest(received, expected):
        if with_prefix:
            assert recv == f"[{name}] {exp}"
        else:
            assert recv == exp


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cmd,expected_stdout,expected_stderr",
    [
        pytest.param(
            "echo TEST", ["TEST"], [], id="one_stdout_str", marks=[pytest.mark.xfail]
        ),
        pytest.param(["echo", "TEST"], ["TEST"], [], id="one_stdout"),
        pytest.param(
            ["echo", "TEST", ">&2"], ["TEST >&2"], [], id="one_stdout_no_pipe"
        ),
        pytest.param(
            ["echo", "TEST;", "echo", "TEST2"],
            ["TEST; echo TEST2"],
            [],
            id="two_stdout_no_injection",
        ),
    ],
)
async def test_exec(event_loop, cmd, expected_stdout, expected_stderr):
    cmd = get_command(cmd)
    expected_stdout = get_command(expected_stdout)
    expected_stderr = get_command(expected_stderr)
    output, errors = [], []
    aiosub = Process(
        *([cmd] if isinstance(cmd, str) else cmd),
        loop=event_loop,
        expected_returncode=0,  # Because timeout is expected
        stdout=lambda s: output.append(s),
        stderr=lambda s: errors.append(s),
        with_prefix=False,
    )
    success = await aiosub.exec()
    assert success
    assert output == expected_stdout
    assert errors == expected_stderr


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cmd,expected_stdout,expected_stderr",
    [
        pytest.param(
            "echo TEST; sleep 0.2; echo TEST2",
            [(0, "TEST"), (0.2, "TEST2")],
            [],
            id="two_stdout_str",
        ),
        pytest.param(
            "echo TEST; sleep 0.2; echo TEST2; sleep 0.3; echo TEST3",
            [(0, "TEST"), (0.2, "TEST2"), (0.5, "TEST3")],
            [],
            id="two_stdout_str",
        ),
    ],
)
async def test_realtime_shell(event_loop, cmd, expected_stdout, expected_stderr):
    cmd = get_command(cmd)
    output, errors = [], []
    s_res = 0.05
    aiosub = Process(
        cmd,
        loop=event_loop,
        stdout=lambda s: output.append((datetime.now(), s)),
        stderr=lambda s: errors.append((datetime.now(), s)),
        with_prefix=False,
        sleep_resolution=s_res,
    )
    success = await aiosub.shell()
    assert success
    check_with_timestamps(output, expected_stdout, s_res)
    check_with_timestamps(errors, expected_stderr, s_res)


def check_with_timestamps(received, expected, sleep_res):
    first_ts = None
    for (r_ts, result), (e_delta, expected) in zip_longest(received, expected):
        assert result == expected
        if first_ts is None:
            first_ts = r_ts
        assert r_ts - first_ts - timedelta(seconds=e_delta) < timedelta(
            seconds=sleep_res * 2
        )
