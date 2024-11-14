r"""Path-related utilities."""

__all__ = [
    "CACHE_DIR",
    "PARTICLE_UNITS",
    "is_quantified",
]

from importlib.resources import files
from pathlib import Path

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


CACHE_DIR = Path("~").expanduser() / ".cache" / "mmspy" / "units"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PARTICLE_UNITS = files("mmspy.units") / "data" / "particle.txt"
