r"""Provide computational utilities."""

__all__ = [
    "curlometer",
    "integrate_distribution",
    "interpolate_distribution",
    #  "smooth_distribution",
    "cwt",
    "cross",
    "fft",
    "icwt",
    "stft",
    "xr_fft",
    "xr_icwt",
    "xr_stft",
    "cartesian_to_fac",
    "fac_to_cartesian",
    "quaternion_rotate",
    "rotation_matrix",
    "matrix_multiply",
    "quaternion_conjugate",
    "quaternion_dot",
    "vector_norm",
]

import mmspy.computation.particle
import mmspy.computation.time_frequency
from mmspy.computation.curlometer import curlometer
from mmspy.computation.particle import (
    ParticleGrid,
    integrate_distribution,
    interpolate_distribution,
)
from mmspy.computation.time_frequency import (
    cwt,
    fft,
    icwt,
    stft,
    xr_fft,
    xr_icwt,
    xr_stft,
)
from mmspy.computation.transform import (
    cartesian_to_fac,
    fac_to_cartesian,
    quaternion_rotate,
    rotation_matrix,
)
from mmspy.computation.vector import (
    cross,
    matrix_multiply,
    quaternion_conjugate,
    quaternion_dot,
    vector_norm,
)
