r"""Provides functionality for time-frequency analysis."""

__all__ = [
    "cwt",
    "fft",
    "icwt",
    "stft",
    "xr_cwt",
    "xr_fft",
    "xr_icwt",
    "xr_stft",
]

from ._fft import fft, xr_fft
from ._stft import stft, xr_stft
from ._cwt import cwt, icwt, xr_cwt, xr_icwt
