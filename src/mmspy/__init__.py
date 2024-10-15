"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version

__all__ = [
    "api",
    "computation",
    "utils",
    "xarray",
]
__version__ = version("mmspy")

import logging.config
from os import environ

from mmspy import api, computation, utils, xarray

logging.captureWarnings(True)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%y-%b-%d %H:%M:%S",
    level="INFO" if not bool(environ.get("DEBUG")) else "DEBUG",
)
