"""MMS in Python.

MmsPy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version as _version

__version__ = _version("mmspy")

__all__ = [
    "MMS",
    "Query",
    "Request",
]

import logging.config

from mmspy.api import MMS, Query, Request
from mmspy.utils.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
