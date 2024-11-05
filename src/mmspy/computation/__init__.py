r"""Provide computational utilities."""

__all__ = [
    "curlometer",
    "integrate_3d_distribution",
    "interpolate_2d_distribution",
    "interpolate_3d_distribution",
    "smooth_distribution",
    "cwt",
    "cross",
    "fft",
    "icwt",
    "stft",
    "xr_cwt",
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

from .curlometer import curlometer
from .particles import (
    integrate_3d_distribution,
    interpolate_2d_distribution,
    interpolate_3d_distribution,
    smooth_distribution,
)
from .time_frequency import cwt, fft, icwt, stft, xr_cwt, xr_fft, xr_icwt, xr_stft
from .transform import (
    cartesian_to_fac,
    fac_to_cartesian,
    quaternion_rotate,
    rotation_matrix,
)
from .vector import (
    cross,
    matrix_multiply,
    quaternion_conjugate,
    quaternion_dot,
    vector_norm,
)
