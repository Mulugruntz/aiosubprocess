import asyncio
from aiosubprocess import Process

asyncio.get_event_loop().run_until_complete(
    Process("echo Hello World!", stdout=print).shell()
)
