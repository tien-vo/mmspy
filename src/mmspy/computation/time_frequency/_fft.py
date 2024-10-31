__all__ = ["fft", "xr_fft"]

from typing import Union

import numpy as np
import xarray as xr
from numpy.typing import NDArray
from pint_xarray import unit_registry as u
from scipy.signal import get_window

from mmspy.utils.timing import sampling_information


def fft(
    time: NDArray[np.datetime64],
    signal: u.Quantity,
    window_type: Union[str, float, tuple] = "hann",
    normalization: str = "spectrum",
) -> tuple:
    r"""Fourier transform with `numpy.fft`.

    Parameters
    ----------
    time : array_like
        `numpy.datetime64` array
    signal : QuantityLike
        Signal data
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    normalization : {"spectrum", "density"}
        The default "spectrum" returns a transformed spectrum with the
        same unit as that of the signal. The "density" option returns a
        spectrum with units of [signal / sqrt(fs)]

    Returns
    -------
    spectrum : Quantity
        Fourier spectrum of the input signal
    frequency : Quantity["Hz"]
        Fourier frequency

    """
    time = time.astype("datetime64[ns]")
    signal = u.Quantity(signal)
    units = signal.units

    # Unpack sampling information
    sampling = sampling_information(time)
    Ns = sampling["number_of_samples"]
    if Ns % 2 == 0:
        positive_indices = slice(1, Ns // 2)
        negative_indices = slice(Ns // 2 + 1, Ns)
    else:
        positive_indices = slice(1, (Ns + 1) // 2)
        negative_indices = slice((Ns + 1) // 2, Ns)

    # Calculate spectrum and frequency
    window = get_window(window_type, Ns)
    f_twosided = np.fft.fftfreq(Ns, sampling["period"])
    F_twosided = np.fft.fft(signal.magnitude * window, norm="forward") * units

    # Fold over the two-sided results
    frequency = f_twosided[positive_indices]
    spectrum_positive = F_twosided[positive_indices]
    spectrum_negative = F_twosided[negative_indices][::-1]
    if normalization == "density":
        df = np.diff(frequency).mean().to("Hz")
        spectrum_positive *= np.sqrt(2 / df)
        spectrum_negative *= np.sqrt(2 / df)

    return (spectrum_positive, spectrum_negative, frequency)


def xr_fft(
    signal: xr.DataArray,
    window_type: Union[str, float, tuple] = "hann",
    normalization: str = "spectrum",
) -> xr.DataArray:
    r"""Xarray wrapper for `mmsws.computation.time_frequency.fft` routine.

    Parameters
    ----------
    signal : DataArray
        Signal data
    window_type : str, float, tuple
        Window that can be queried with `scipy.signal.get_window`
    normalization : {"spectrum", "density"}
        The default "spectrum" returns a transformed spectrum with the
        same unit as that of the signal. The "density" option returns a
        spectrum with units of [signal / sqrt(fs)]

    Returns
    -------
    spectrum : DataArray
        Fourier spectrum of the input signal

    """
    spectrum_positive, spectrum_negative, frequency = fft(
        signal.time.values,
        signal.pint.quantify().compute().data,
        window_type=window_type,
        normalization=normalization,
    )
    return xr.DataArray(
        data=np.vstack([spectrum_positive, spectrum_negative]),
        dims=("type", "frequency"),
        coords={
            "type": ("type", ["positive", "negative"]),
            "frequency": ("frequency", frequency.magnitude),
        },
        attrs={"normalization": normalization},
    ).pint.quantify(frequency=frequency.units)
