r"""Provides functionality for timing utilities."""

__all__ = [
    "force_odd",
    "match_time_resolution",
    "sampling_information",
]

from typing import Any

import numpy as np
import pandas as pd
import xarray as xr
from numpy.typing import NDArray
from pint import Quantity

from mmspy.units import is_quantified


def force_odd(number: int) -> int:
    r"""Force an integer to an odd number.

    Parameters
    ----------
    number : int
        Integer

    Returns
    -------
    odd_number : int
        Odd number

    """
    return number + 1 if number % 2 == 0 else number


def match_time_resolution(
    data: xr.DataArray,
    target: xr.DataArray | Quantity,
    average: bool = False,
    kwargs: dict[str, Any] = {"fill_value": np.nan, "bounds_error": False},
) -> xr.DataArray:
    r"""Match time resolution onto a target time resolution.

    Parameters
    ----------
    data : DataArray or Dataset
        Data to interpolate.
    target : DataArray or Quantity
        Target resolution.
    average : bool
        Whether to perform a rolling average before interpolation.
    kwargs : dict
        Extra keywords for the interpolation routine.

    Returns
    -------
    interpolated_data : DataArray or Dataset
        Interpolated data that match the time resolution of `data_reference`

    """
    if not isinstance(target, (xr.DataArray, Quantity)):
        msg = "'target' must be an xarray or pint quantity."
        raise ValueError(msg)

    if isinstance(target, xr.DataArray):
        if "time" not in target.dims or target.sizes["time"] <= 1:
            return data
        target_resolution = pd.Timedelta(target.time.diff("time").min().values)
        time = target.time.reset_coords(drop=True)

    if isinstance(target, Quantity):
        target_resolution = pd.Timedelta(int(target.to("ns").magnitude), "ns")
        time = np.arange(
            data.time[0].values,
            data.time[-1].values + target_resolution,
            target_resolution,
        ).astype("datetime64[ns]")

    data = data.copy()
    if quantified := is_quantified(data):
        data = data.pint.dequantify()

    if average:
        data_resolution = pd.Timedelta(data.time.diff("time").min().values)
        window = force_odd(max(1, int(data_resolution / target_resolution)))
        interpolated_data = (
            data.rolling(time=window, center=True)
            .mean()
            .interp(time=time, kwargs=kwargs)
        )
    else:
        interpolated_data = data.interp(time=time, kwargs=kwargs)

    return (
        interpolated_data
        if not quantified
        else interpolated_data.pint.quantify()
    )


def sampling_information(time: NDArray[np.datetime64]) -> dict[str, Any]:
    r"""Extract sampling information from a time array.

    Parameters
    ----------
    time : array_like
        `numpy.datetime64` array

    Returns
    -------
    info : dict
        Dictionary of sampling information. The items are:
            - number_of_samples: Length of time array
            - window: Length of the time period
            - period: Sampling period
            - frequency: Sampling frequency

    """
    time = np.array(time)
    unit = np.datetime_data(time.dtype)[0]
    time = time.astype(float)
    window = Quantity(time[-1] - time[0], unit).to("s")
    period = Quantity(np.diff(time).min(), unit).to("s")
    frequency = (1 / period).to("Hz")
    return {
        "number_of_samples": time.size,
        "window": window,
        "period": period,
        "frequency": frequency,
    }
