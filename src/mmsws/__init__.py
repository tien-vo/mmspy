r"""MMS Web Services API.

MmsWs is an open source Python package for scientific research with
data from NASA Magnetospheric Multiscale (MMS) mission.
"""

import logging.config

from mmsws.utils.logging import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
