r"""Process epoch information from raw CDF files."""

__all__ = [
    "process_cdf_epoch",
]

from collections.abc import Sequence

import pandas.api.types as pd
from xarray.core.types import T_Dataset

_keys_to_remove = [
    "units",
    "UNITS",
    "FIELDNAM",
    "LABLAXIS",
    "TIME_BASE",
    "TIME_SCALE",
    "long_name",
]


def process_cdf_epoch(
    ds: T_Dataset,
    epoch_variables: Sequence[str],
) -> T_Dataset:
    r"""Process CDF epoch.

    Assuming CDF time conversion is handled correctly by `cdflib`, some
    unnecessary metadata are removed with this function.

    Parameters
    ----------
    ds : Dataset
        Xarray dataset
    epoch_variables : list of str
        Epoch variables from the raw CDF file to process

    Returns
    -------
    ds : Dataset
        Dataset with epoch variables processed

    """
    ds = ds.copy()

    for var in epoch_variables:
        for key in _keys_to_remove:
            if key in ds[var].attrs:
                del ds[var].attrs[key]

        for key, value in ds[var].attrs.items():
            if pd.is_datetime64_dtype(value):
                ds[var].attrs[key] = value.astype(str)

        ds[var].attrs["standard_name"] = "Time"

    return ds
