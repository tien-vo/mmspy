"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version as _version

__all__ = [
    "api",
    "computation",
    "CACHE_DIR",
    "DATA_DIR",
    "STATE_DIR",
]
__version__ = _version("mmspy")

from mmspy.config.directories import CACHE_DIR, DATA_DIR, STATE_DIR
from mmspy.config.logging import configure_logger
from mmspy.config.units import configure_units

configure_logger(CACHE_DIR)
units = configure_units()

#  import mmspy.xarray
#  from mmspy import api, computation, utils
