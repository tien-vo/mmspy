"""Provide necessary configurations."""

__all__ = [
    "Config",
    "config",
    "enable_log",
    "units",
    "enable_diagnostics",
    "configure_matplotlib",
]


import mmspy.config.numba
import mmspy.config.paths
import mmspy.config.xarray
from mmspy.config.config import Config, config
from mmspy.config.dask import enable_diagnostics
from mmspy.config.logging import enable_log
from mmspy.config.matplotlib import configure_matplotlib
from mmspy.config.units import units
