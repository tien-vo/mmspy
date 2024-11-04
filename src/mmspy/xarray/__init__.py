r"""Provide `xarray` accessors to datasets."""

__all__ = [
    "FeepsAccessor",
    "FpiAccessor",
    "SpeciesAccessor",
    "RankOneAccessor",
    "RankTwoAccessor",
]

import xarray as xr

xr.set_options(keep_attrs=True)

from .feeps.accessor import FeepsAccessor  # noqa: E402
from .fpi import FpiAccessor  # noqa: E402
from .species import SpeciesAccessor  # noqa: E402
from .tensors import RankOneAccessor, RankTwoAccessor  # noqa: E402
