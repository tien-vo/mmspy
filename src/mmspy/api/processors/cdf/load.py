__all__ = ["load_cdf"]

import xarray as xr
from cdflib.xarray import cdf_to_xarray

from mmspy.api.processors.cdf.metadata import process_cdf_time


def load_cdf(
    cdf_file_name: str,
    time_variables: list[str],
) -> xr.Dataset:
    """Load CDF file and apply common preprocessing steps."""
    ds = cdf_to_xarray(cdf_file_name, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_time(ds, time_variables=time_variables)
    return ds.reset_coords()
