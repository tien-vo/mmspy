"""Process metadata from raw CDF files."""

__all__ = ["process_cdf_metadata", "process_cdf_time"]

from collections.abc import Sequence

import numpy as np
import pandas.api.types as pd
import xarray as xr

variable_keys_to_remove = [
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
]
time_keys_to_remove = [
    "units",
    "UNITS",
    "FIELDNAM",
    "LABLAXIS",
    "TIME_BASE",
    "TIME_SCALE",
    "long_name",
]


def process_cdf_metadata(dataset: xr.Dataset) -> xr.Dataset:
    """Process CDF metadata.

    Remove some unnecessary metadata and clean up one-element attribute
    entries

    Parameters
    ----------
    dataset : Dataset
        xarray object

    Returns
    -------
    dataset : Dataset
        Processed dataset

    """
    dataset = dataset.copy()

    for variable in list(dataset.data_vars) + list(dataset.coords):
        for key in variable_keys_to_remove:
            if key in dataset[variable].attrs:
                del dataset[variable].attrs[key]

    attrs_list = [dataset.attrs] + [
        dataset[variable].attrs for variable in dataset
    ]
    for attrs in attrs_list:
        for key, value in attrs.items():
            if isinstance(value, (list, np.ndarray)) and len(value) == 1:
                attrs[key] = value[0]

    version = dataset.attrs.get("Data_version")
    if version is not None:
        dataset.attrs["version"] = version.replace("v", "")
        del dataset.attrs["Data_version"]

    return dataset


def process_cdf_time(
    dataset: xr.Dataset,
    time_variables: Sequence[str],
) -> xr.Dataset:
    """Process CDF epoch.

    Assuming CDF time conversion is handled correctly by `cdflib`, some
    unnecessary metadata are removed with this function.

    Parameters
    ----------
    dataset : Dataset
        Xarray dataset
    time_variables : list of str
        Time (epoch) variables from the raw CDF file to process

    Returns
    -------
    dataset : Dataset
        Dataset with time variables processed

    """
    dataset = dataset.copy()

    for variable in time_variables:
        for key in time_keys_to_remove:
            if key in dataset[variable].attrs:
                del dataset[variable].attrs[key]

        for key, value in dataset[variable].attrs.items():
            if pd.is_datetime64_dtype(value):
                dataset[variable].attrs[key] = value.astype(str)

        dataset[variable].attrs["standard_name"] = "Time"

    return dataset
