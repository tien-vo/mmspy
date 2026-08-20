__all__ = ["load_cdf"]

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from importlib import import_module
from threading import RLock
from typing import Any

import numpy as np
import xarray as xr
from cdflib.epochs import CDFepoch
from cdflib.xarray import cdf_to_xarray

from mmspy.api.processors.cdf.metadata import process_cdf_time

_CDF_TIME_CONVERSION_LOCK = RLock()
_TT2000_SENTINELS = np.asarray(
    [
        CDFepoch.FILLED_TT2000_VALUE,
        CDFepoch.DEFAULT_TT2000_PADVALUE,
    ],
    dtype=np.int64,
)


def _convert_cdf_time_sentinels(
    values: Any,
    *,
    converter: Callable[[Any], Any],
) -> Any:
    """Convert CDF times while mapping reserved TT2000 values to ``NaT``.

    Parameters
    ----------
    values : Any
        Scalar or array-like CDF time values supplied by ``cdflib``.
    converter : callable
        Original CDF time converter. Values that are not TT2000 fill or pad
        sentinels are delegated to this callable unchanged.

    Returns
    -------
    Any
        The converter result. Reserved TT2000 fill and pad positions are
        represented as ``datetime64[ns]`` ``NaT`` values.
    """
    array = np.asarray(values)
    if not np.issubdtype(array.dtype, np.integer):
        return converter(values)

    sentinel_mask = np.isin(array, _TT2000_SENTINELS)
    if not np.any(sentinel_mask):
        return converter(values)

    safe_values = array.copy()
    safe_values[sentinel_mask] = np.int64(0)
    converted = np.asarray(converter(safe_values)).astype(
        "datetime64[ns]",
        copy=True,
    )
    converted.reshape(-1)[sentinel_mask.reshape(-1)] = np.datetime64(
        "NaT",
        "ns",
    )
    return converted


@contextmanager
def _sentinel_aware_cdf_time_conversion() -> Iterator[None]:
    """Temporarily make ``cdflib`` TT2000 sentinel conversion safe."""
    converter_module = import_module("cdflib.xarray.cdf_to_xarray")
    epoch_class = converter_module.cdfepoch
    with _CDF_TIME_CONVERSION_LOCK:
        original_descriptor = epoch_class.__dict__["to_datetime"]
        original_converter = epoch_class.to_datetime

        def sentinel_aware_converter(values: Any) -> Any:
            return _convert_cdf_time_sentinels(
                values,
                converter=original_converter,
            )

        epoch_class.to_datetime = sentinel_aware_converter
        try:
            yield
        finally:
            setattr(epoch_class, "to_datetime", original_descriptor)


def load_cdf(
    cdf_file_name: str,
    time_variables: list[str],
) -> xr.Dataset:
    """Load a CDF file and apply common preprocessing steps.

    Parameters
    ----------
    cdf_file_name : str
        Path to the CDF file.
    time_variables : list of str
        Names of CDF epoch variables to process as time coordinates.

    Returns
    -------
    xarray.Dataset
        Loaded dataset with CDF time metadata normalized. Reserved TT2000
        fill and pad attributes are excluded from the processed time
        variables.
    """
    with _sentinel_aware_cdf_time_conversion():
        ds = cdf_to_xarray(
            cdf_file_name,
            to_datetime=True,
            fillval_to_nan=True,
        )

    for variable in time_variables:
        ds[variable].attrs.pop("FILLVAL", None)

    ds = process_cdf_time(ds, time_variables=time_variables)
    return ds.reset_coords()
