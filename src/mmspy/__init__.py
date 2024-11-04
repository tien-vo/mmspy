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
    "unit_registry",
]
__version__ = version("mmspy")

import mmspy.logging
import mmspy.xarray
from mmspy.pint import unit_registry
from mmspy import api, computation, models, utils
