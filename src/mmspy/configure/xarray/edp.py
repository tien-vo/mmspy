"""Provide xarray accessor for EDP datasets."""

__all__ = ["EdpAccessor"]

import logging

import numpy as np
import xarray as xr

from mmspy.configure.xarray.utils import validate_dataset

log = logging.getLogger(__name__)


@xr.register_dataset_accessor("edp")
class EdpAccessor:
    """Xarray accessor for EDP datasets."""

    def __init__(self, dataset: xr.Dataset) -> None:
        """Validate and initialize accessor for a dataset.

        Parameters
        ----------
        dataset : Dataset
            Xarray dataset

        """
        validate_dataset(dataset, "EDP", ["EDP", "Electric Double Probe"])
        self._dataset = dataset.pint.quantify()

    def mask_data(self, min_bit: int = 6, max_bit: int = 8) -> xr.Dataset:
        """Allow bitmask = 0 or between a range of bits."""
        dataset = self._dataset.copy()
        if not hasattr(dataset, "flag"):
            msg = "'flag' variable not found in dataset."
            log.warning(msg)
            return dataset

        if not hasattr(dataset, "bitmask"):
            msg = "'bitmask' variable not found in dataset."
            log.warning(msg)
            return dataset

        bitmask = dataset.bitmask.pint.dequantify()
        for variable in dataset.data_vars:
            if variable == "bitmask":
                continue
            dataset[variable] = xr.where(
                (bitmask == 0)
                | ((bitmask >= 2**min_bit) | (bitmask <= 2**max_bit)),
                dataset[variable],
                np.nan,
            )

        return dataset
