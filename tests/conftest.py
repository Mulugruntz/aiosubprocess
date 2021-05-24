import asyncio
from pathlib import Path
import sys
import logging

import pytest

if sys.platform.startswith("win"):  # pragma: no cover
    if sys.version_info < (3, 7):
        # Python 3.6 has no WindowsProactorEventLoopPolicy class
        from asyncio import events

        class WindowsProactorEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
            _loop_factory = asyncio.ProactorEventLoop

    else:
        WindowsProactorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy


@pytest.fixture
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    if sys.platform.startswith("win"):  # pragma: no cover
        asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# it makes it easier if all tests are forced to
# have the package root as the CWD.
SOURCE_DIR = Path(__file__).parent.parent / "aiosubprocess"
sys.path.insert(0, str(SOURCE_DIR))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-15s %(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout,
)
