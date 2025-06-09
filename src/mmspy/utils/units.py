r"""Utilities for `pint`."""

__all__ = ["is_quantified"]

import xarray as xr
from pint import Quantity


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
    return isinstance(data.data, Quantity)
