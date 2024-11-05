r"""Provides utilities for units."""

__all__ = ["is_quantified"]

import pint
import xarray as xr


def is_quantified(data: xr.DataArray) -> bool:
    return isinstance(data.data, pint.Quantity)
