
| Usage                                                                                                                                        | Release                                                                                                                                   | Development                                                                                                                                                               |
|----------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)                                                                 | [![PyPI version](https://img.shields.io/pypi/v/aiosubprocess.svg)](https://pypi.org/project/aiosubprocess/)                               | [![Build status](https://github.com/Mulugruntz/aiosubprocess/workflows/Python%20application/badge.svg)](https://github.com/Mulugruntz/aiosubprocess/actions)              |
| [![Python versions](https://img.shields.io/pypi/pyversions/aiosubprocess.svg)](https://pypi.org/project/aiosubprocess/)                      | [![Tag](https://img.shields.io/github/v/tag/Mulugruntz/aiosubprocess.svg)](https://github.com/Mulugruntz/aiosubprocess/tags)              | [![Maintainability](https://api.codeclimate.com/v1/badges/7fbd03d62e85fc10c3d6/maintainability)](https://codeclimate.com/github/Mulugruntz/aiosubprocess/maintainability) |
| [![pip install aiosubprocess](https://img.shields.io/badge/pip%20install-aiosubprocess-ff69b4.svg)](https://pypi.org/project/aiosubprocess/) | [![This project uses calendar-based versioning scheme](https://img.shields.io/badge/calver-YYYY.MM.MINOR-22bfda.svg)](http://calver.org/) | [![Test Coverage](https://api.codeclimate.com/v1/badges/7fbd03d62e85fc10c3d6/test_coverage)](https://codeclimate.com/github/Mulugruntz/aiosubprocess/test_coverage)       |
| [ ![Downloads](https://pepy.tech/badge/aiosubprocess)](https://pepy.tech/project/aiosubprocess)                                              |                                                                                                                                           | [![This project uses the "black" style formatter for Python code](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)           |

# aiosubprocess

A **zero-dependency** async subprocess that keeps on getting stdout and stderr.

## How to use

#### Example 1: Hello World
A classic Hello World. It prints `Hello World!` in the shell and
redirects the stdout to `print()`.
```python
import asyncio
from aiosubprocess import Process

asyncio.get_event_loop().run_until_complete(
    Process("echo Hello World!", stdout=print).shell()
)
```
```shell
$> python ex1_minimal.py
[AIO Subprocess-0] Hello World!

Process finished with exit code 0
```

#### Example 2: Two Processes
One process writes to a file, and a second process logs the content of the file
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

![Example animation](https://github.com/Mulugruntz/aiosubprocess/blob/master/docs/example2.gif?raw=true)

## Why?

There are many scenario where we need to keep an eye on
a subprocess output. If we want to do so in realtime 
(and redirect it to logs or a GUI), the boilerplate is
tedious.

The other solution is to wait for the subprocess to
exit and read the stdout/stderr afterwards.

This library implements this boilerplate, so you don't have to.