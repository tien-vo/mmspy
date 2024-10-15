"""Provide utilities for indexing."""

__all__ = [
    "first_valid_index",
    "last_valid_index",
]
from typing import Hashable, TypeVar

import numpy as np
import xarray as xr
from numpy.typing import NDArray

array_or_xarray = TypeVar(
    "array_or_xarray",
    bound=NDArray | xr.Dataset | xr.DataArray,
)


def _validate_inputs(
    data: array_or_xarray,
    axis: int | Hashable,
) -> tuple[Hashable, int, int]:
    r"""Validate the inputs for `{first/last}_valid_index`.

    Since the input in `first_valid_index` and `last_valid_index` can
    either be a numpy array or an xarray, we must validate the `axis`
    parameter in the right context, i.e., `axis` must be
        - an integer when `data` is a numpy array
        - either an integer or string (specifying the dimension) when
            `data` is an xarray
    """
    axis_str: Hashable
    axis_num: int
    size: int
    if isinstance(data, np.ndarray):
        if not isinstance(axis, int):
            msg = "Axis must be an integer when `data` is a numpy array."
            raise ValueError(msg)
        axis_str = axis
        axis_num = axis

    if isinstance(data, xr.DataArray):
        if isinstance(axis, int):
            axis_num = axis
            axis_str = str(list(data.dims)[axis_num])
        else:
            axis_str = axis
            axis_num = data.get_axis_num(axis_str)

    size = data.shape[axis_num]
    return (axis_str, axis_num, size)


def last_valid_index(
    data: array_or_xarray,
    axis: int | Hashable = -1,
) -> array_or_xarray:
    r"""Find the first non-NaN indices along a given axis.

    Source: See this discussion (https://stackoverflow.com/a/49759690).

    Parameters
    ----------
    data : array-like, Dataset or DataArray
        Data
    axis : int or str
        Axis or name of dimension along which to search

    Returns
    -------
    index : array-like or DataArray
        The valid indices

    """
    axis_str, axis_num, size = _validate_inputs(data, axis)
    return (~np.isnan(data)).cumsum(axis_str).argmax(axis_str)


def first_valid_index(
    data: array_or_xarray,
    axis: int | Hashable = -1,
) -> array_or_xarray:
    r"""Find the last non-NaN indices along a given axis.

    Parameters
    ----------
    data : array-like, Dataset or DataArray
        Data
    axis : int or str
        Axis or name of dimension along which to search

    Returns
    -------
    index : array-like or DataArray
        The valid indices

    """
    axis_str, axis_num, size = _validate_inputs(data, axis)
    data = np.flip(data, axis_num)

    # Type hinting works in the following line; don't know why mypy is
    #   raising return-value error
    return np.mod(size - 1 - last_valid_index(data, axis_str), size - 1)  # type: ignore
