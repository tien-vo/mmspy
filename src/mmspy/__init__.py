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
]
__version__ = version("mmspy")

import mmspy.logging
import mmspy.xarray
import mmspy.units
from mmspy import api, computation, models, utils
