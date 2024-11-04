"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version

__all__ = [
    "api",
    "computation",
    "models",
    "units",
    "utils",
]
__version__ = version("mmspy")

import mmspy.xarray
from mmspy.pint import units
from mmspy import api, computation, logging, models, utils
