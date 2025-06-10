"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version as _version

__all__ = [
    "api",
    "config",
    "CACHE_DIR",
    "DATA_DIR",
    "STATE_DIR",
]
__version__ = _version("mmspy")

from mmspy.utils.config import config
from mmspy.utils.directories import CACHE_DIR, DATA_DIR, STATE_DIR
from mmspy.utils.logging import configure_logger
from mmspy.utils.pint import configure_units

configure_logger(CACHE_DIR)
units = configure_units()

from mmspy import api

#  import mmspy.xarray
#  from mmspy import api, computation, utils
