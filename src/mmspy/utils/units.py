r"""Provides utilities for units."""

__all__ = ["is_quantified"]

import pint
import xarray as xr


def is_quantified(data: xr.DataArray) -> bool:
    r"""Check if a data array is quantified with ``pint``.

    Parameters
    ----------
    data : DataArray
        Data array to check.

    Returns
    -------
    is_quantified : bool
        Condition

    """
    return isinstance(data.data, pint.Quantity)
