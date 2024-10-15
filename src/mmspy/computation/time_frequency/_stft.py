__all__ = ["stft", "xr_stft"]

import astropy.units as u
import numpy as np
import xarray as xr
from astropy.units.typing import QuantityLike
from numpy.typing import NDArray
from scipy.signal import ShortTimeFFT, get_window

from mmspy.utils.timing import sampling_information


def stft(
    time: NDArray[np.datetime64],
    signal: QuantityLike,
    window_type: str | float | tuple = "hann",
    window_length: u.Quantity[u.s] | None = None,
    normalization: str = "spectrum",
) -> tuple:
    r"""Short-time Fourier transform with `scipy.signal.ShortTimeFFT`.

    Parameters
    ----------
    time : array_like
        `numpy.datetime64` array
    signal : QuantityLike
        Signal data
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    window_length : Quantity, optional
        Length of sliding FFT window, default to 10 times the sampling
        period
    normalization : {"spectrum", "density"}
        The default "spectrum" returns a transformed spectrum with the
        same unit as that of the signal. The "density" option returns a
        spectrum with units of [signal / sqrt(fs)]

    Returns
    -------
    spectrum : Quantity
        Sliding Fourier spectrum of the input signal
    window_time : np.ndarray[np.datetime64]
        Central time of each window
    window_frequency : Quantity["Hz"]
        Central frequency of each window

    """
    time = time.astype("datetime64[ns]")
    signal = u.Quantity(signal)

    # Unpack and do sanity check on sampling information
    sampling = sampling_information(time)
    if window_length is None:
        window_length = 10 * sampling["period"]
    elif not (
        (2 * sampling["period"] <= window_length)
        and (window_length <= sampling["window"])
    ):
        msg = (
            "Window length must be between the sampling period and "
            "the length of the signal!"
        )
        raise ValueError(msg)

    Nw = int((window_length // sampling["period"]).decompose())
    Ns = sampling["number_of_samples"]
    fs = sampling["frequency"]

    # Calculate FFT spectrum (throwing away zero frequency)
    STFT = ShortTimeFFT(
        win=get_window(window_type, Nw),
        hop=Nw // 2,
        fs=sampling["frequency"].value,
        scale_to="magnitude",
        fft_mode="onesided",
    )
    window_time = time[0] + (1e9 * STFT.t(Ns)).astype("timedelta64[ns]")
    window_frequency = STFT.f[1:] * fs.unit
    spectrum = STFT.stft(signal.value).T[:, 1:] * signal.unit
    if normalization == "density":
        df = np.diff(window_frequency).mean().to("Hz")
        spectrum *= np.sqrt(1 / df)

    return spectrum, window_time, window_frequency


def xr_stft(
    signal: xr.DataArray,
    window_type: str | float | tuple = "hann",
    window_length: u.Quantity[u.s] | None = None,
    normalization: str = "spectrum",
) -> xr.DataArray:
    r"""Xarray wrapper for `mmsws.computation.time_frequency.stft` routine.

    Parameters
    ----------
    signal : DataArray
        Signal data
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    window_length : Quantity, optional
        Length of sliding FFT window, default to 10 times the sampling
        period
    normalization : {"spectrum", "density"}
        The default "spectrum" returns a transformed spectrum with the
        same unit as that of the signal. The "density" option returns a
        spectrum with units of [signal / sqrt(fs)]

    Returns
    -------
    spectrum : DataArray
        Sliding Fourier spectrum of the input signal

    """
    spectrum, window_time, window_frequency = stft(
        signal.time.values,
        signal.values * signal.units.from_metadata,
        window_type=window_type,
        window_length=window_length,
        normalization=normalization,
    )
    return xr.DataArray(
        data=spectrum.value,
        dims=("time", "frequency"),
        coords={
            "time": ("time", window_time),
            "frequency": (
                "frequency",
                window_frequency.value,
                {"units": str(window_frequency.unit)},
            ),
        },
        attrs={"units": str(spectrum.unit), "normalization": normalization},
    )
