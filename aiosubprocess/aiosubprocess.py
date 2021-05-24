"""Boilerplate for asyncio applications"""

import asyncio
import logging
from asyncio import AbstractEventLoop
from asyncio import create_subprocess_exec, create_subprocess_shell
from asyncio.subprocess import PIPE, Process as asyncioProcess
from functools import partial
from itertools import count
from typing import Callable, Tuple, Optional, Coroutine, Any

__all__ = ["Process"]
__version__ = "2021.05.1"
logger = logging.getLogger("aiosubprocess")

SLEEP_RESOLUTION = 0.1


class Process:
    name_count = count()

    def __init__(
        self,
        *command: str,
        loop: Optional[AbstractEventLoop] = None,
        name: Optional[str] = None,
        expected_returncode: int = 0,
        stdout: Callable[[str], None] = logger.info,
        stderr: Callable[[str], None] = logger.error,
        with_prefix: bool = True,
        sleep_resolution: float = SLEEP_RESOLUTION,
    ) -> None:
        """An async subprocess that keeps on getting stdout and stderr.

        :param command: The shell command.
        :param loop: An asyncio event loop.
        :param name: Optional name of the subprocess (useful when logging).
                    If not provided, will assign one automatically.
        :param expected_returncode: Which error code is considered a success?
        :param stdout: A callback called for every line of stdout.
                    Useful for printing and logging.
        :param stderr: A callback called for every line of stderr.
                    Useful for printing and logging.
        :param with_prefix: Should a prefix (based on `name`) be added before
                    each stdout/stderr?
        :param sleep_resolution: The minimum time resolution at which stdout/stderr
                    will be checked. This is not guaranteed, as there might be
                    long blocking operations somewhere else in the loop.
        """
        self._run_command: Tuple[str, ...] = command
        self.loop: AbstractEventLoop = loop or asyncio.get_event_loop()
        self.child: Optional[asyncioProcess] = None
        self.name = name or f"AIO Subprocess-{next(Process.name_count)}"
        self.expected_returncode = expected_returncode
        self.__prefix = f"[{self.name}] "
        self.__stdout = stdout
        self.__stderr = stderr
        self.with_prefix = with_prefix
        self.sleep_resolution = sleep_resolution

    async def exec(self) -> bool:
        return await self._run(partial(create_subprocess_exec, *self._run_command))

    async def shell(self) -> bool:
        return await self._run(
            partial(create_subprocess_shell, " ".join(self._run_command))
        )

    async def _run(
        self,
        create_subprocess_function: Callable[..., Coroutine[Any, Any, asyncioProcess]],
    ) -> bool:
        logger.info("%sAbout to start %s", self.__prefix, " ".join(self._run_command))
        self.child = await create_subprocess_function(stdout=PIPE, stderr=PIPE)
        while True:
            retcode = self.child.returncode
            if retcode is not None:  # Process finished
                await self._check_io()
                break
            else:
                await asyncio.sleep(self.sleep_resolution)
            await self._check_io()

        if retcode != self.expected_returncode:
            logger.error(
                "%sError! The subprocess terminated with a non-0 return code: %s",
                self.__prefix,
                retcode,
            )
            return False

        logger.info(
            "%sSuccess! The subprocess completed.",
            self.__prefix,
        )
        return True

    async def _check_io(self):
        out = asyncio.ensure_future(self._pipe_stdout(), loop=self.loop)
        err = asyncio.ensure_future(self._pipe_stderr(), loop=self.loop)
        await asyncio.gather(out, err, loop=self.loop)

    async def _pipe_stdout(self):
        while True:
            output = (
                (await self.child.stdout.readline())
                .decode(errors="backslashreplace")
                .rstrip()
            )
            if not output:
                break
            if self.with_prefix:
                self.__stdout(f"{self.__prefix}{output}")
            else:
                self.__stdout(output)

    async def _pipe_stderr(self):
        while True:
            error = (
                (await self.child.stderr.readline())
                .decode(errors="backslashreplace")
                .rstrip()
            )
            if not error:
                break
            if self.with_prefix:
                self.__stderr(f"{self.__prefix}{error}")
            else:
                self.__stderr(error)
