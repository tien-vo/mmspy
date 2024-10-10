"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

import logging.config
from importlib.metadata import version as _version

from mmspy.utils.logging import LOGGING_CONFIG

__version__ = _version("mmspy")

logging.config.dictConfig(LOGGING_CONFIG)
