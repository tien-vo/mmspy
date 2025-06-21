"""Generic load function for all MMS datasets."""

import logging
from functools import partial

import numpy as np
import xarray as xr

from mmspy.api.query import query
from mmspy.api.store import store as store_
from mmspy.api.utils.file import truncate_file_list_using_metadata
from mmspy.configure.config import config

log = logging.getLogger(__name__)
default_load_kwargs = {"combine": "nested", "parallel": True}


def preprocess(dataset: xr.Dataset, variables: list[str] | None) -> xr.Dataset:
    if variables is None:
        return dataset

    return dataset[[variable for variable in variables if variable in dataset]]


def load(
    store: str = "remote",
    variables: list[str] | None = None,
    quantify: bool = True,
    time_clip: bool = True,
    load_kwargs: dict = default_load_kwargs,
    **kwargs,
) -> xr.Dataset:
    """Load an MMS dataset with the data `~mmspy.store` manager.

    Parameters
    ----------
    store : str
        Data store to load from. Default to 'remote', which will sync
        with the SDC.
    variables : list of str
        Variables to load with dataset.
    quantify : bool
        Whether to quantify the returned dataset.
    time_clip : bool
        Whether to clip the time range to that in the query.
    load_kwargs : dict
        Additional keyword arguments for the `xr.open_mfdataset` call.
    kwargs : dict
        Additional keyword arguments for `Query` settings.

    Returns
    -------
    dataset : Dataset
        Merged dataset.

    """
    load_kwargs = {**default_load_kwargs, **load_kwargs}

    query.save_state()
    query.update(**kwargs)
    log.debug(f"Loading data with\n{query}")

    if store == "remote":
        paths = store_.sync()
        paths = truncate_file_list_using_metadata(paths, query)
    else:
        paths = store_.get_local_files(store)

    if not bool(paths):
        log.info("No file found. Please check your query parameters.")
        return xr.Dataset()

    dataset = xr.open_mfdataset(
        paths,
        preprocess=partial(preprocess, variables=variables),
        engine="zarr",
        **load_kwargs,
    )

    if time_clip:
        for coordinate in dataset.coords:
            if np.issubdtype(dataset[coordinate].dtype, np.datetime64):
                dataset = dataset.sel(
                    {coordinate: slice(query.start_time, query.stop_time)}
                ).transpose(coordinate, ...)

    if quantify:
        dataset = dataset.pint.quantify()

    query.restore_state()
    return dataset
