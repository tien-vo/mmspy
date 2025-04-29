r"""Provides functionality for time-frequency analysis."""

__all__ = [
    "fft",
    "stft",
    "xr_fft",
    "xr_stft",
]

from ._fft import fft, xr_fft
from ._stft import stft, xr_stft
