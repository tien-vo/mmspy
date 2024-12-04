r""".. todo:: Write docstring."""

from pathlib import Path

import xarray as xr
from attr import define

from mmspy.api.query import Query
from mmspy.api.request import Request
from mmspy.api.sync import Synchronizer


@define(repr=False)
class MMS:
    r"""Manager for MMS data.

    .. todo:: Write docstring

    """

    query: Query = Query(data="science", data_level="l2")
    request: Request = Request(query)
    sync: Synchronizer = Synchronizer(query, request)

    def load_dataset(
        self,
        parallel: int = 1,
        dry_run: bool = False,
        time_clip: bool = True,
        quantify: bool = True,
        **kwargs,
    ) -> xr.Dataset:
        r"""Load a dataset from an MMS instrument.

        Parameters
        ----------
        parallel : int
            Number of parallel threads to run the synchronizer.
        dry_run : bool
            Whether to stop after querying the file list.
        time_clip : bool
            Whether to clip the final dataset to queried time range.
        quantify : bool
            Whether to quantify the returned dataset.
        kwargs : dict
            Keyword arguments for `mmspy.api.query.Query`.

        Returns
        -------
        ds : Dataset
            Loaded dataset.

        """
        datasets = self.gather_path(
            parallel=parallel,
            dry_run=dry_run,
            **kwargs,
        )
        if not bool(datasets):
            return xr.Dataset()

        ds = xr.open_mfdataset(datasets, engine="zarr")

        if time_clip:
            ds = ds.sel(time=slice(self.query.start_date, self.query.end_date))

        if quantify:
            return ds.pint.quantify()

        return ds

    def gather_path(
        self,
        parallel: int = 1,
        dry_run: bool = False,
        **kwargs,
    ) -> list[Path]:
        r"""Gather a list of paths to datasets from an MMS instrument.

        Parameters
        ----------
        parallel : int
            Number of parallel threads to run the synchronizer.
        dry_run : bool
            Whether to stop after querying the file list.
        kwargs : dict
            Keyword arguments for `mmspy.api.query.Query`.

        Returns
        -------
        paths : list of Path
            Paths to datasets.

        """
        for parameter, value in kwargs.items():
            if value is None:
                continue
            setattr(self.query, parameter, value)

        return self.sync.sync(parallel=parallel, dry_run=dry_run)
