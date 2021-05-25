"""A zero-dependence async subprocess that keeps on getting stdout and stderr."""

from .aiosubprocess import Process

__version__ = "2021.5.2"
__all__ = ["Process"]
