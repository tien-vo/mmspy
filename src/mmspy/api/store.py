"""Provide handler for both remote and local data stores."""

__all__ = ["Store", "store"]

import logging
from collections.abc import Iterable
from os import PathLike
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import xarray as xr
import zarr
from attrs import define, field
from pathos.threading import ThreadPool
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm
from zarr.hierarchy import Group

from mmspy.api.processors import get_processor
from mmspy.api.query import query
from mmspy.api.utils.file import (
    CdfFile,
    dataset_is_updated,
    truncate_file_list_using_metadata,
    truncate_file_list_using_name,
)
from mmspy.api.utils.progress_bar import bar_config
from mmspy.api.utils.remote import download_cdf_file, get_remote_files
from mmspy.api.utils.render_tree import render_tree
from mmspy.api.utils.request import setup_request_session
from mmspy.api.utils.store import convert_path, setup_zarr_store
from mmspy.compute.utils import ensure_quantifiable, force_monotonic
from mmspy.configure.config import config
from mmspy.configure.units import units as u

log = logging.getLogger(__name__)


@define
class Store:
    """Manager for all data storages based on `~mmspy.query` parameters.

    .. todo:: Add examples.

    Parameter
    ---------
    path : path-like, optional
        Path to local storage. Default to system data directory.

    """

    zarr: Group = field(init=False, repr=False)
    request: requests.Session = field(
        init=False,
        repr=False,
        default=setup_request_session(),
    )

    path: str | PathLike = field(
        default=None,
        converter=convert_path,
        validator=setup_zarr_store,
    )

    @property
    def name(self) -> str:
        """Name of local storage."""
        return Path(self.path).name

    def sync(self, **kwargs) -> list[Path]:
        """Sync data store.

        Other Parameters
        ----------------
        **kwargs : dict
            Query arguments.

        Returns
        -------
        paths : list of path
            Paths to single datasets.

        """
        query.save_state()
        query.update(**kwargs)

        def helper(file: CdfFile) -> Path | None:
            processor = get_processor(file.metadata)
            metadata = file.metadata
            metadata["full_path"] = str(
                Path(store.path) / sync_store / metadata["local_path"]
            )
            if update_local or not dataset_is_updated(
                metadata["full_path"],
                metadata["version"],
                u(metadata["size"]),
                metadata["modified_date"],
            ):
                temporary_file = download_cdf_file(
                    file.cdf_file_name,
                    store.request,
                    query,
                )
                if temporary_file is None:
                    return None

                datasets = processor(temporary_file, metadata)
                for is_main, local_path, dataset in datasets:
                    store.write_dataset(dataset, sync_store, local_path)
                    if is_main:
                        main_file = store.path / sync_store / local_path

                Path(temporary_file).unlink(missing_ok=True)
                msg = (
                    f"Synchronized remote file {file.cdf_file_name} to "
                    f"local file {file.zarr}."
                )
                log.info(msg)
            else:
                main_file = metadata["full_path"]
                msg = f"Local {file.zarr} is up-to-date."
                log.info(msg)

            return main_file

        parallel = config.get("store/parallel", default=1)
        update_local = config.get("store/update_local", default=False)
        sync_store = config.get("store/sync_store", default="raise")

        log.info(f"Query is set from {query.start_time} to {query.stop_time}.")

        cdf_files = get_remote_files(store.request, query)
        remote_path = query.remote_path
        local_path = query.local_path
        bar = bar_config(
            desc=(
                f"Synchronizing remote store {remote_path} to "
                f"local store {local_path}."
            ),
            total=len(cdf_files),
            position=0,
            leave=False,
        )

        local_files: list[Path] = []

        with ThreadPool(nodes=parallel) as pool, tqdm(**bar) as bar:
            for path in pool.uimap(helper, cdf_files):
                if path is not None:
                    local_files.append(path)

                bar.update()

        log.info(
            f"Synchronized remote store {remote_path} to "
            f"local store {'/'.join([sync_store, local_path])}."
        )

        query.restore_state()
        return local_files

    def write_dataset(
        self,
        dataset: xr.Dataset,
        store: str,
        local_path: str,
        time_dependent: bool = True,
        time_dimension: str = "time",
        mode: str = "w",
        nochunk: bool = False,
    ) -> None:
        """Write a dataset to a data store.

        Parameters
        ----------
        dataset : Dataset
            Dataset.
        local_path : str
            Path to the file in the local store.
        store : str
            Name of the store.
        time_dimension : str
            Name of time dimension.
        mode : {'w', 'w-', 'a'}
            Write mode.
        nochunk : bool
            Whether to automatically chunk data.

        """
        relative_path = Path(store) / local_path
        full_path = self.path / relative_path
        self.zarr.require_group(str(relative_path))

        # Time
        if time_dependent:
            dataset = force_monotonic(dataset)
            dataset.attrs.update(
                start_time=str(dataset.time[0].values),
                stop_time=str(dataset.time[-1].values),
            )

        # Units
        dataset = ensure_quantifiable(dataset)

        # Chunk
        if not nochunk:
            for variable, chunk in config.get("store/chunk").items():
                if variable in dataset:
                    dataset = dataset.chunk({variable: chunk})

        log.info(f"Writing dataset to {full_path}.")
        dataset.to_zarr(
            store=str(full_path),
            consolidated=True,
            mode=mode,
        )  # type: ignore[call-overload]

    def get_local_files(self, store: str, **kwargs) -> list[Path]:
        """Get files from a local store.

        Parameters
        ----------
        store : str
            Name of the store

        Other Parameters
        ----------------
        **kwargs : dict
            Query parameters.

        Returns
        -------
        paths : list of path
            Paths to single datasets.

        """
        query.save_state()
        query.update(**kwargs)
        relative_path = Path(self.path) / store / query.metadata["local_path"]
        files = list(relative_path.glob("zarr_*"))
        files = sorted(
            files,
            key=lambda file: pd.to_datetime(
                file.name[5:],
                format="%Y_%m_%d_%H_%M_%S",
            ),
        )
        files = truncate_file_list_using_name(files, query)
        files = truncate_file_list_using_metadata(files, query)
        log.debug(
            f"Found {len(files)} files at "
            f"{self.path}/{store}/{query.metadata['local_path']}."
        )
        query.restore_state()
        return files

    def files(self, store: str, **kwargs) -> Iterable[Path]:
        """Iterator for `Store.get_local_files()`.

        Parameters
        ----------
        store : str
            Name of the store

        Other Parameters
        ----------------
        **kwargs : dict
            Query parameters.

        Returns
        -------
        paths : list of path
            Paths to single datasets.

        """
        for file in self.get_local_files(store, **kwargs):
            yield file

    def get_time_slices(self, store: str, **kwargs) -> list[slice]:
        """Get time slices from each file in a data store.

        Parameters
        ----------
        store : str
            Name of the store

        Other Parameters
        ----------------
        **kwargs : dict
            Query parameters.

        Returns
        -------
        slices : list of slice
            Slice for each file.

        """
        files = self.get_local_files(store, **kwargs)

        time_slices: list[slice] = []
        for file in files:
            try:
                attrs = zarr.open(file, mode="r").attrs
                start_time = np.datetime64(attrs.get("start_time"))
                stop_time = np.datetime64(attrs.get("stop_time"))
                time_slices.append(slice(start_time, stop_time))
            except (FileNotFoundError, zarr.errors.PathNotFoundError):
                continue

        return time_slices

    def time_slices(self, store: str, **kwargs) -> Iterable[slice]:
        """Iterator for `Store.get_time_slices()`.

        Parameters
        ----------
        store : str
            Name of the store

        Other Parameters
        ----------------
        **kwargs : dict
            Query parameters.

        Returns
        -------
        slices : list of slice
            Slice for each file.

        """
        for time_slice in self.get_time_slices(store, **kwargs):
            yield time_slice

    def show(self, pattern: str = "") -> None:
        """Show the data store tree."""
        render_tree(self, pattern)

    def __del__(self) -> None:
        """Close request session."""
        self.request.close()


store = Store()
