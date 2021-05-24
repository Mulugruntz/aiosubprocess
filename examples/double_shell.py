import asyncio
import logging
import sys

from aiosubprocess import Process

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)-15s %(levelname)s:%(name)s:%(message)s",
    stream=sys.stdout,
)

loop = asyncio.get_event_loop()
reader = Process(
    """for i in {1..5}
    do
       echo "Hello $i World" > tempfile.log
       sleep 1
    done""",
    loop=loop,
    name="Writer",
)
writer = Process(
    "timeout --foreground 10s tail -f tempfile.log",
    loop=loop,
    name="Reader",
    expected_returncode=124,  # Because timeout is expected
)
awaitable_reader = reader.shell()
awaitable_writer = writer.shell()
gathered = asyncio.gather(awaitable_reader, awaitable_writer, loop=loop)
asyncio.get_event_loop().run_until_complete(gathered)
assert gathered.result() == [True, True]
