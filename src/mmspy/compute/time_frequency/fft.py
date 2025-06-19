"""FFT a signal defined on datetime array and xarray wrappers."""

__all__ = ["fft", "xr_fft"]

import numpy as np
import xarray as xr
from scipy.fft import fft as _fft
from scipy.fft import fftfreq, next_fast_len
from scipy.signal import get_window

from mmspy.compute.time_frequency.utils import pad
from mmspy.compute.utils import sampling_information
from mmspy.types import NDArray, Quantity, Hashable


def fft(  # noqa: PLR0913
    time: NDArray[np.datetime64],
    signal: Quantity,
    axis: int = -1,
    window_type: str | float | tuple = "hann",
    normalization: str = "spectrum",
    pad_fraction: float = 1.0,
) -> tuple:
    """Fourier transform with `scipy.fft`.

    Parameters
    ----------
    time : array_like
        `numpy.datetime64` array
    signal : QuantityLike
        Signal data
    axis : int, optional
        Axis over which to transform. If not given, the last axis is used.
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    normalization : {'spectrum', 'density'}
        The default 'spectrum' returns a transformed spectrum with the
        same unit as that of the signal. The 'density' option returns a
        spectrum with units of [signal / sqrt(fs)]
    pad_fraction : float
        A non-negative scalar determining the length of the padded
        portion of the output. The default is 1.0, resulting in an
        output with twice the length.

    Returns
    -------
    spectrum : Quantity
        Fourier spectrum of the input signal
    frequency : Quantity["Hz"]
        Fourier frequency

    """
    time = time.astype("datetime64[ns]")
    signal = Quantity(signal)
    axis = axis % signal.ndim
    signal_unit = signal.units
    signal_data = np.asarray(signal.magnitude)

    # Unpack sampling information
    sampling = sampling_information(time)
    fs = sampling["frequency"].to("Hz")
    Ns = sampling["number_of_samples"]

    # Window signal
    window = np.expand_dims(
        get_window(window_type, Ns),
        [i for i in range(signal.ndim) if i != axis],
    )
    signal_data *= window

    # Zero-pad signal
    Np = next_fast_len(int((1 + pad_fraction) * Ns))
    _, signal_data = pad(signal_data, Np, axis=axis, padtype="both")

    # Calculate frequency slice
    if Np % 2 == 0:
        positive_indices = slice(1, Np // 2)
        negative_indices = slice(Np // 2 + 1, Np)
    else:
        positive_indices = slice(1, (Np + 1) // 2)
        negative_indices = slice((Np + 1) // 2, Np)

    # Calculate spectrum and frequency
    f_twosided = fftfreq(Np, sampling["period"])
    F_twosided = _fft(signal_data, axis=axis) * signal_unit

    # Fold over the two-sided results
    frequency = f_twosided[positive_indices]
    spectrum_positive = F_twosided[positive_indices]
    spectrum_negative = F_twosided[negative_indices][::-1]
    if normalization == "density":
        spectrum_positive *= 1 / np.sqrt(Np * fs)
        spectrum_negative *= 1 / np.sqrt(Np * fs)

    return (spectrum_positive, spectrum_negative, frequency)


def xr_fft(
    signal: xr.DataArray,
    axis: int | Hashable = "time",
    window_type: str | float | tuple = "hann",
    normalization: str = "spectrum",
    pad_fraction: float = 1.0,
) -> xr.DataArray:
    """Xarray wrapper for `mmspy.compute.time_frequency.fft.fft` routine.

    Parameters
    ----------
    signal : DataArray
        Signal data
    axis : int, optional
        Axis over which to transform. If not given, the time axis is used.
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    normalization : {"spectrum", "density"}
        The default "spectrum" returns a transformed spectrum with the
        same unit as that of the signal. The "density" option returns a
        spectrum with units of [signal / sqrt(fs)]
    pad_fraction : float
        A non-negative scalar determining the length of the padded
        portion of the output. The default is 1.0, resulting in an
        output with twice the length.

    Returns
    -------
    spectrum : DataArray
        Fourier spectrum of the input signal

    """
    if not isinstance(axis, int):
        axis = signal.get_axis_num(axis)

    spectrum_positive, spectrum_negative, frequency = fft(
        signal.time.values,
        signal.pint.quantify().data,
        axis=axis,
        window_type=window_type,
        normalization=normalization,
        pad_fraction=pad_fraction,
    )
    dims = list(signal.dims)
    dims[axis] = "frequency"
    return xr.DataArray(
        data=np.stack([spectrum_positive, spectrum_negative]),
        dims=("sign", *dims),
        coords={
            "sign": ("sign", ["positive", "negative"]),
            "frequency": ("frequency", frequency.magnitude),
        }
        | {
            coord: signal.coords[coord]
            for coord in signal.coords
            if coord != "time"
        },
        attrs={"normalization": normalization},
    ).pint.quantify(frequency=frequency.units)
