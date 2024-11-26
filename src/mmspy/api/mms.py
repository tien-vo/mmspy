r""".. todo:: Write docstring."""

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

    def load(
        self,
        parallel: int = 1,
        dry_run: bool = False,
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
        quantify : bool
            Whether to quantify the returned dataset.
        kwargs : dict
            Keyword arguments for `mmspy.api.query.Query`.

        Returns
        -------
        ds : Dataset
            Dataset from an MMS instrument.

        """
        for parameter, value in kwargs.items():
            if value is None:
                continue
            setattr(self.query, parameter, value)

        datasets = self.sync.sync(parallel=parallel, dry_run=dry_run)
        if not bool(datasets):
            return xr.Dataset()

        ds = xr.open_mfdataset(datasets, engine="zarr")
        if quantify:
            return ds.pint.quantify()

        return ds
