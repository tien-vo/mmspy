"""STFT a signal defined on datetime array and xarray wrappers."""

__all__ = ["stft", "xr_stft"]


import numpy as np
import xarray as xr
from scipy.fft import next_fast_len
from scipy.signal import ShortTimeFFT, get_window

from mmspy.compute.utils import sampling_information
from mmspy.types import Hashable, NDArray, Quantity


def stft(  # noqa: PLR0913
    time: NDArray[np.datetime64],
    signal: Quantity,
    axis: int = -1,
    window_type: str | float | tuple = "hann",
    window_length: Quantity | None = None,
    normalization: str = "spectrum",
    pad_fraction: float = 1.0,
) -> tuple[Quantity, Quantity, Quantity]:
    """Short-time Fourier transform with `scipy.signal.ShortTimeFFT`.

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
    window_length : Quantity, optional
        Length of sliding FFT window, default to 10 times the sampling
        period
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
    spectrum : Quantity
        Sliding Fourier spectrum of the input signal
    window_time : np.ndarray[np.datetime64]
        Central time of each window
    window_frequency : Quantity["Hz"]
        Central frequency of each window

    """
    time = time.astype("datetime64[ns]")
    signal = Quantity(signal)
    signal = np.asarray(signal.magnitude) * signal.units

    # Unpack and do sanity check on sampling information
    sampling = sampling_information(time)
    if window_length is None:
        window_length = 10 * sampling["period"]
    elif not (2 * sampling["period"] <= window_length <= sampling["window"]):
        msg = (
            "Window length must be between the sampling period and "
            "the length of the signal!"
        )
        raise ValueError(msg)

    Nw = int(window_length / sampling["period"])
    Ns = sampling["number_of_samples"]
    fs = sampling["frequency"]
    Np = next_fast_len(int((1 + pad_fraction) * Ns))

    # Calculate FFT spectrum (throwing away zero frequency)
    STFT = ShortTimeFFT(
        win=get_window(window_type, Nw),
        hop=Nw // 2,
        fs=sampling["frequency"].magnitude,
        mfft=Np,
        scale_to="psd" if normalization == "density" else "magnitude",
        fft_mode="onesided",
    )
    window_time = time[0] + (1e9 * STFT.t(Ns)).astype("timedelta64[ns]")
    window_frequency = STFT.f[1:] * fs.units
    spectrum = (
        STFT.stft(signal.magnitude, axis=axis).take(
            indices=range(1, window_frequency.size + 1),
            axis=axis,
        )
        * signal.units
    )

    if normalization == "density":
        spectrum /= np.sqrt(1.0 * fs.units)

    return spectrum, window_time, window_frequency


def xr_stft(  # noqa: PLR0913
    signal: xr.DataArray,
    axis: int | Hashable = "time",
    window_type: str | float | tuple = "hann",
    window_length: Quantity | None = None,
    normalization: str = "spectrum",
    pad_fraction: float = 1.0,
) -> xr.DataArray:
    """Xarray wrapper for `mmsws.computation.time_frequency.stft` routine.

    Parameters
    ----------
    signal : DataArray
        Signal data
    axis : int, optional
        Axis over which to transform. If not given, the time axis is used.
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    window_length : Quantity, optional
        Length of sliding FFT window, default to 10 times the sampling
        period
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
        Sliding Fourier spectrum of the input signal

    """
    if not isinstance(axis, int):
        axis = signal.get_axis_num(axis)

    spectrum, window_time, window_frequency = stft(
        signal.time.values,
        signal.pint.quantify().data,
        axis=axis,
        window_type=window_type,
        window_length=window_length,
        normalization=normalization,
        pad_fraction=pad_fraction,
    )
    dims = list(signal.dims)
    dims[axis] = "frequency"
    return (
        xr.DataArray(
            data=spectrum,
            dims=(*dims, "time"),
            coords={
                "time": ("time", window_time),
                "frequency": ("frequency", window_frequency.magnitude),
            }
            | {
                coord: signal.coords[coord]
                for coord in signal.coords
                if coord != "time"
            },
            attrs={"normalization": normalization},
        )
        .pint.quantify(frequency=str(window_frequency.units))
        .transpose("time", "frequency", ...)
    )
