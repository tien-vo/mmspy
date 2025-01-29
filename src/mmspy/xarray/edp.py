r"""Provide xarray accessor for EDP datasets."""

__all__ = [
    "EdpAccessor",
]

import numpy as np
import xarray as xr

from mmspy.xarray._utils import validate_dataset


@xr.register_dataset_accessor("edp")
class EdpAccessor:
    r"""Xarray accessor for EDP datasets."""

    def __init__(self, ds: xr.Dataset) -> None:
        r"""Validate and initialize accessor for a dataset.

        Parameters
        ----------
        ds : Dataset
            Xarray dataset

        """
        validate_dataset(ds, "EDP", ["EDP", "Electric Double Probe"])
        self._ds = ds.pint.quantify()

    def mask_data(self, min_bit: int = 6, max_bit: int = 8) -> xr.Dataset:
        r"""Allow bitmask = 0 or between a range of bits."""
        ds = self._ds.copy()
        bitmask = ds.bitmask.pint.dequantify()
        for variable in ds.data_vars:
            if variable == "bitmask":
                continue
            ds[variable] = xr.where(
                (bitmask == 0)
                | ((bitmask >= 2**min_bit) | (bitmask <= 2**max_bit)),
                ds[variable],
                np.nan,
            )

        return ds
