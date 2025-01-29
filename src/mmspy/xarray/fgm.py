r"""Provide xarray accessor for FGM datasets."""

__all__ = [
    "FgmAccessor",
]

import numpy as np
import xarray as xr

from mmspy.xarray._utils import validate_dataset


@xr.register_dataset_accessor("fgm")
class FgmAccessor:
    r"""Xarray accessor for FGM datasets."""

    def __init__(self, ds: xr.Dataset) -> None:
        r"""Validate and initialize accessor for a dataset.

        Parameters
        ----------
        ds : Dataset
            Xarray dataset

        """
        validate_dataset(ds, "FGM", ["FGM", "Flux Gate Magnetometer"])
        self._ds = ds.pint.quantify()

    def mask_data(self) -> xr.Dataset:
        r"""Mask flag > 0."""
        ds = self._ds.copy()
        flag = ds.flag.pint.dequantify()
        for variable in ds.data_vars:
            if variable == "flag":
                continue
            ds[variable] = xr.where(flag == 0, ds[variable], np.nan)

        return ds
