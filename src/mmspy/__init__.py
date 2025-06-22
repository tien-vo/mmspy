"""MMS in Python.

mmspy is an open source Python package for plasma research with data
from the NASA Magnetospheric Multiscale (MMS) mission.
"""

from importlib.metadata import version as _version
from typing import TYPE_CHECKING

from mmspy.configure import (
    config,
    configure_matplotlib,
    enable_diagnostics,
    enable_log,
    units,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from mmspy.api.query import Query
    from mmspy.api.store import Store

    query: Query
    """Package-level instance of `~mmspy.api.query.Query`."""

    store: Store
    """Package-level instance of `~mmspy.api.store.Store`."""

    load: Callable

import mmspy.plot
from mmspy.api import load, query, store
from mmspy.compute import (
    ParticleGrid,
    cartesian_to_fac,
    cross,
    curlometer,
    fac_to_cartesian,
    integrate_distribution,
    interpolate_distribution,
    lowpass_filter,
    matrix_multiply,
    quaternion_conjugate,
    quaternion_dot,
    quaternion_rotate,
    reduce_distribution,
    rotation_matrix,
    smooth_distribution,
    vector_norm,
)
from mmspy.compute.utils import (
    is_quantified,
    match_time_resolution,
    sampling_information,
    to_regular_time,
)

__all__ = [
    "Config",
    "config",
    "configure_matplotlib",
    "enable_diagnostics",
    "enable_log",
    "units",
    "load",
    "query",
    "store",
    "ParticleGrid",
    "cartesian_to_fac",
    "cross",
    "curlometer",
    "fac_to_cartesian",
    "integrate_distribution",
    "interpolate_distribution",
    "lowpass_filter",
    "matrix_multiply",
    "quaternion_conjugate",
    "quaternion_dot",
    "quaternion_rotate",
    "reduce_distribution",
    "rotation_matrix",
    "smooth_distribution",
    "vector_norm",
    "is_quantified",
    "match_time_resolution",
    "sampling_information",
    "to_regular_time",
]
__version__ = _version("mmspy")
