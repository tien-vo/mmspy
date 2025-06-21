"""Provide necessary configurations."""

__all__ = [
    "Config",
    "config",
    "enable_log",
    "units",
    "enable_diagnostics",
    "configure_matplotlib",
]


import mmspy.configure.numba
import mmspy.configure.paths
import mmspy.configure.xarray
from mmspy.configure.logging import enable_log
from mmspy.configure.config import Config, config
from mmspy.configure.dask import enable_diagnostics
from mmspy.configure.matplotlib import configure_matplotlib
from mmspy.configure.units import units
