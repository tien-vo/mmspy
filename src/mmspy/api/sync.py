r"""Provide interface for data synchronization."""

__all__ = ["Synchronizer"]

import logging
from collections.abc import Callable
from pathlib import Path

import zarr
from attr import define, field
from attr.converters import pipe
from pathos.threading import ThreadPool
from tqdm.contrib.logging import tqdm_logging_redirect as tqdm
from zarr._storage.store import Store

from ._utils import bar_config
from .process._edp import process_efield, process_potential
from .process._feeps import process_feeps_distribution
from .process._fgm import process_fgm
from .process._fpi import (
    process_fpi_distribution,
    process_fpi_moments,
    process_fpi_partial_moments,
)
from .process._mec import process_mec
from .process.metadata import (
    consolidate_metadata,
    dataset_is_updated,
    parse_metadata_from_file_name,
)
from .query import Query
from .request import Request

LOG = logging.getLogger(__name__)


@define
class Synchronizer:
    r"""Interface for synchronizing data.

    .. todo:: Write docstring.
    .. todo:: Expose API to mirror file structure exactly.
    """

    query: Query = field(repr=False)

    request: Request = field(repr=False)

    store: Store = field(
        default="./data.zarr",
        converter=pipe(Path, zarr.DirectoryStore),  # type: ignore[misc]
    )

    update: bool = False

    @property
    def process_file(self) -> Callable:  # noqa: PLR0911
        r"""Call process functions based on query instrument.

        .. todo:: Refactor to reduce complexity.

        """
        query = self.query
        match query.instrument:
            case "mec":
                return process_mec
            case "fgm":
                return process_fgm
            case "edp":
                match query.data_type:
                    case "efield":
                        return process_efield
                    case "potential":
                        return process_potential
            case "fpi":
                match query.data_type[4:]:
                    case "distribution":
                        return process_fpi_distribution
                    case "moments":
                        return process_fpi_moments
                    case "partial_moments":
                        return process_fpi_partial_moments
            case "feeps":
                return process_feeps_distribution

        raise NotImplementedError

    def sync(self, parallel: int = 1, dry_run: bool = False) -> list[Path]:
        r"""Sync data store."""
        query = self.query
        store_path = Path(self.store.path)
        cdf_file_list = self.request.cdf_file_list
        groups: list[Path] = []

        if (number_of_files := len(cdf_file_list)) == 0:
            msg = "Query results in zero file."
            LOG.warning(msg)

        if dry_run:
            return groups

        def _helper(cdf_file_name: str) -> Path | None:
            metadata = consolidate_metadata(
                query.metadata,
                parse_metadata_from_file_name(cdf_file_name, query.instrument),
                store_path,
            )

            if self.update or not dataset_is_updated(metadata):
                temporary_file = self.request.download_file(cdf_file_name)
                if temporary_file is None:
                    return None

                self.process_file(temporary_file, metadata)
                Path(temporary_file).unlink(missing_ok=True)

                msg = f"Processed {cdf_file_name}"
                LOG.info(msg)
            else:
                msg = f"{cdf_file_name} is up-to-date."
                LOG.info(msg)

            return Path(metadata["group"])

        for parameter in ["start_date", "end_date"]:
            if getattr(query, parameter) is None:
                msg = f"{parameter!r} is None. This may query a lot of files!"
                LOG.warning(msg)

        # Create directory before anything to avoid multi-threading issue
        zarr.open(self.store)
        config = bar_config(
            desc=(
                f"Synchronizing {query.instrument} {query.data_type} "
                f"({query.start_date} - {query.end_date})."
            ),
            total=number_of_files,
            position=0,
        )
        with ThreadPool(nodes=parallel) as pool, tqdm(**config) as bar:
            for group in pool.uimap(_helper, cdf_file_list):
                if group is not None:
                    groups.append(group)

                bar.update()

        return groups
