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
from pint_xarray import unit_registry as u
from xarray.core.types import T_Xarray


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
    data: T_Xarray,
    target: T_Xarray | u.Quantity,
    average: bool = True,
    kwargs: dict[str, Any] = {"fill_value": np.nan, "bounds_error": False},
) -> T_Xarray:
    r"""Match time resolution onto a target time resolution.

    Parameters
    ----------
    data : DataArray or Dataset
        Data to interpolate
    target : DataArray or Quantity
        Target resolution in astropy Quantity or xarray with time coordinates
    average : bool
        Whether to perform a rolling average before interpolation
    kwargs : dict
        Extra keywords for the interpolation routine

    Returns
    -------
    interpolated_data : DataArray or Dataset
        Interpolated data that match the time resolution of `data_reference`

    """
    data = data.copy()

    if not isinstance(target, (xr.DataArray, u.Quantity)):
        msg = "'target' must be an xarray or pint quantity."
        raise ValueError(msg)

    if isinstance(target, xr.DataArray):
        if "time" not in target.dims or target.sizes["time"] <= 1:
            return data
        target_resolution = pd.Timedelta(target.time.diff("time").min().values)
        time = target.time.reset_coords(drop=True)

    if isinstance(target, u.Quantity):
        target_resolution = pd.Timedelta(int(target.to("ns").magnitude), "ns")
        time = np.arange(
            data.time[0].values,
            data.time[-1].values + target_resolution,
            target_resolution,
        ).astype("datetime64[ns]")

    if not average:
        return data.interp(time=time, kwargs=kwargs)

    data_resolution = pd.Timedelta(data.time.diff("time").min().values)
    window_length = force_odd(max(1, int(data_resolution / target_resolution)))

    return (
        data.rolling(time=window_length, center=True)
        .mean()
        .interp(time=time, kwargs=kwargs)
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
    window = u.Quantity(time[-1] - time[0], unit).to("s")
    period = u.Quantity(np.diff(time).min(), unit).to("s")
    frequency = (1 / period).to("Hz")
    return {
        "number_of_samples": time.size,
        "window": window,
        "period": period,
        "frequency": frequency,
    }
