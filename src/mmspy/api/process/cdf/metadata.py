r"""Process metadata from raw CDF files."""

__all__ = [
    "process_cdf_metadata",
]

import numpy as np
from xarray.core.types import T_Dataset

_keys_to_remove = [
    "UNITS",
    "DEPEND_0",
    "DISPLAY_TYPE",
    "FIELDNAM",
    "FORMAT",
    "LABL_PTR_1",
    "REPRESENTATION_1",
    "SI_CONVERSION",
    "LABLAXIS",
    "VAR_TYPE",
    "standard_name",
    "long_name",
]


def process_cdf_metadata(ds: T_Dataset) -> T_Dataset:
    r"""Process CDF metadata.

    Remove some unnecessary metadata and clean up one-element attribute
    entries

    Parameters
    ----------
    ds : Dataset
        xarray object

    Returns
    -------
    ds : Dataset
        Processed dataset

    """
    ds = ds.copy()

    for var in ds:
        for key in _keys_to_remove:
            if key in ds[var].attrs:
                del ds[var].attrs[key]

    for attrs in [ds.attrs] + [ds[var].attrs for var in ds]:
        for key, value in attrs.items():
            if isinstance(value, (list, np.ndarray)) and len(value) == 1:
                attrs[key] = value[0]

    return ds
