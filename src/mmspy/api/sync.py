r"""Provide interface for data synchronization."""

import logging
from collections.abc import Callable
from pathlib import Path

import zarr
from attr import define, field
from attr.converters import pipe
from pathos.threading import ThreadPool
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm
from zarr._storage.store import Store

from .process._edp import process_dce, process_scpot
from .process._fgm import process_fgm
from .process.parse_metadata import parse_metadata
from .query import Query
from .request import Request

log = logging.getLogger(__name__)


@define
class Synchronizer:
    r"""Interface for synchronizing data.

    .. todo:: Write docstring
    """

    query: Query

    request: Request

    store: Store = field(
        default="./data.zarr",
        converter=pipe(Path, zarr.DirectoryStore),  # type: ignore[misc]
    )

    update: bool = False

    def dataset_is_updated(self, metadata: dict) -> bool:
        r"""Determine if local dataset is updated with remote."""
        try:
            ds = zarr.open(self.store)
            group = metadata["group"]
            local_version = ds[group].attrs["Data_version"].replace("v", "")
            remote_version = metadata["version"].replace("v", "")
            return local_version == remote_version
        except KeyError:
            return False

    def parse_metadata(self, file_name: str) -> dict[str, str]:
        r"""Parse metadata from file name.

        Parameters
        ----------
        file_name : str
            CDF file name.

        Returns
        -------
        metadata : dict[str, str]
            Dictionary containing metadata of ``file_name``.

        """
        return parse_metadata(file_name, self.query.instrument)

    @property
    def process_file(self) -> Callable:
        r"""Call process functions based on query instrument."""
        match self.query.instrument:
            case "fgm":
                return process_fgm
            case "edp":
                match self.query.data_type:
                    case "dce":
                        return process_dce
                    case "scpot":
                        return process_scpot

        raise NotImplementedError

    def sync(self, parallel: int = 1, dry_run: bool = True) -> None:
        r"""Sync data store."""
        q = self.query

        def _helper(cdf_file_name: str) -> None:
            metadata = self.parse_metadata(cdf_file_name)
            if not self.update and self.dataset_is_updated(metadata):
                msg = f"Data from {cdf_file_name} is up-to-date"
                log.info(msg)
                return

            store_path = Path(self.store.path)
            temporary_file = self.request.download_file(cdf_file_name)
            if temporary_file is not None:
                self.process_file(store_path, temporary_file, metadata)
                Path(temporary_file).unlink(missing_ok=True)

                msg = f"Processed {cdf_file_name}"
                log.info(msg)

        for parameter in ["start_date", "end_date"]:
            if getattr(q, parameter) is None:
                msg = f"{parameter!r} is None. This may query a lot of files."
                log.warning(msg)

        cdf_file_list = self.request.cdf_file_list
        if dry_run:
            return

        # Create directory before anything to avoid multi-threading issue
        zarr.open(self.store)
        kw = {
            "desc": (
                f"Synchronizing {q.instrument!r} "
                f"from {q.start_date} to {q.end_date}."
            ),
            "total": len(cdf_file_list),
            "bar_format": self.request.bar_format,
            "dynamic_ncols": True,
            "ascii": "-#",
            "position": 1,
        }
        with ThreadPool(nodes=parallel) as pool, tqdm(**kw) as bar:
            for _ in pool.uimap(_helper, cdf_file_list):
                bar.update()
