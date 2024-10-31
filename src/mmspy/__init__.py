"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version

__all__ = [
    "api",
    "computation",
    "models",
    "utils",
    "xarray",
]
__version__ = version("mmspy")

import pint_xarray

from mmspy import api, computation, logging, models, utils, xarray
