"""Provided unit-related utilities."""

__all__ = ["is_quantified", "ensure_quantifiable"]

import xarray as xr

from mmspy.types import Quantity, T_Xarray


def is_quantified(array: xr.DataArray) -> bool:
    """Check if a data array is quantified with ``pint``.

    Parameters
    ----------
    array : DataArray
        Data array to check.

    Returns
    -------
    is_quantified : bool
        Condition

    """
    array = getattr(array, "data", None)
    if array is None:
        return False

    return isinstance(array, Quantity)


def ensure_quantifiable(xarray: T_Xarray) -> T_Xarray:
    """Quantify and dequantify an xarray to make sure it is quantifiable.

    Parameters
    ----------
    xarray : Dataset or DataArray
        Dataset or data array to check.

    Returns
    -------
    xarray : Dataset or DataArray
        The same dataset/array.

    """
    return xarray.pint.quantify().pint.dequantify()
