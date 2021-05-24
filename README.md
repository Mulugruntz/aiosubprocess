# aiosubprocess

An async subprocess that keeps on getting stdout and stderr.

## How to use

An example where one process writes to a file 
and a second process logs the content of the file
in real time.

```python
import asyncio
from aiosubprocess import Process

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
```

Which does exactly this:

![Example animation](docs/example1.gif)

## Why?

There are many scenario where we need to keep an eye on
a subprocess output. If we want to do so in realtime 
(and redirect it to logs or a GUI), the boilerplate is
tedious.

The other solution is to wait for the subprocess to
exit and read the stdout/stderr afterwards.

This library implements this boilerplate, so you don't have to.