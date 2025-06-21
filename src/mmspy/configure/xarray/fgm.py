"""Provide xarray accessor for FGM datasets."""

__all__ = ["FgmAccessor"]

import logging

import numpy as np
import xarray as xr

from mmspy.configure.xarray.utils import validate_dataset

log = logging.getLogger(__name__)


@xr.register_dataset_accessor("fgm")
class FgmAccessor:
    """Xarray accessor for FGM datasets."""

    def __init__(self, dataset: xr.Dataset) -> None:
        """Validate and initialize accessor for a dataset.

        Parameters
        ----------
        dataset : Dataset
            Xarray dataset

        """
        validate_dataset(dataset, "FGM", ["FGM", "Flux Gate Magnetometer"])
        self._dataset = dataset.pint.quantify()

    def mask_data(self) -> xr.Dataset:
        """Mask flag > 0."""
        dataset = self._dataset.copy()
        if not hasattr(dataset, "flag"):
            msg = "'flag' variable not found in dataset."
            log.warning(msg)
            return dataset

        flag = dataset.flag.pint.dequantify()
        for variable in dataset.data_vars:
            if variable == "flag":
                continue
            dataset[variable] = xr.where(flag == 0, dataset[variable], np.nan)

        return dataset
