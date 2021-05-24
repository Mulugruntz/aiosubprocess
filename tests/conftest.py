import asyncio
import os
from pathlib import Path
import sys
import logging

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsProactorEventLoopPolicy()
    )

# it makes it easier if all tests are forced to
# have the package root as the CWD.
os.chdir(str(Path(__file__).parent.parent))
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-15s %(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout,
)
