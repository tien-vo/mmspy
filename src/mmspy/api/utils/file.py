__all__ = [
    "dataset_is_updated",
    "truncate_file_list_using_metadata",
    "truncate_file_list_using_name",
    "CdfFile",
    "parse_file_name",
    "generate_file_name",
]

from bisect import bisect_left, bisect_right
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import xarray as xr
import zarr
from attrs import Attribute, asdict, define, field

from mmspy.configure.units import units as u
from mmspy.types import Date, Quantity, T_File

if TYPE_CHECKING:
    from mmspy.api.query import Query


def generate_file_name(time: Date) -> str:
    """Generate zarr filename from timestamp.

    Parameter
    ---------
    time : date-like
        Time stamp.

    Returns
    -------
    file_name : str
        Zarr file name for local storage.

    """
    if not isinstance(time, str):
        time = pd.Timestamp(time).strftime("%Y_%m_%d_%H_%M_%S")

    return f"zarr_{time}"


def parse_species(instrument: str, data_type: str) -> str:
    """Parse the species name for each instrument.

    Parameter
    ---------
    instrument : str
        Unaliased instrument name.
    data_type : str
        Unaliased data type.

    Returns
    -------
    species_name : str
        Name of species.

    """
    match instrument:
        case "feeps":
            return data_type
        case "fpi":
            if data_type.split("-")[0] == "dis":
                return "ion"
            if data_type.split("-")[0] == "des":
                return "electron"
        case "hpca":
            return "ion"

    msg = (
        f"Cannot parse species information from {instrument!r} "
        f"and {data_type!r}"
    )
    raise ValueError(msg)


def parse_timestamp(timestamp: str) -> str:
    """Parse the timestamp on cdf files.

    Parameter
    ---------
    timestamp : str
        Timestamp provided on CDF file names, often of format YYYYMMDD
        or YYYYMMDDhhmmss.

    Returns
    -------
    parsed_timestamp : str
        Timestamp in YYYY_MM_DD_hh_mm_ss format.

    """
    # Extract the year
    year = timestamp[:4]
    # Split the rest into a list of 2-character strings
    remainder = list(map("".join, zip(*[iter(timestamp[4:])] * 2)))
    # If the time is missing up to seconds, pad them with 00's
    remainder += ["00"] * max(0, 5 - len(remainder))
    return "_".join([year] + remainder)


def parse_file_name(file: "CdfFile", attribute: Attribute, name: str):
    """Parse the name of cdf files for metadata.

    This function is used for `CdfFile` initialization.

    .. todo:: Update docstring

    """
    strings = Path(name).stem.split("_")
    if len(strings) == 7:
        (
            probe,
            instrument,
            data_rate,
            data_level,
            data_type,
            timestamp,
            version,
        ) = strings
    else:
        (
            probe,
            instrument,
            data_rate,
            data_level,
            timestamp,
            version,
        ) = strings
        data_type = "None"
    timestamp = parse_timestamp(timestamp)
    setattr(file, "probe", probe)
    setattr(file, "instrument", instrument)
    setattr(file, "data_rate", data_rate)
    setattr(file, "data_type", data_type)
    setattr(file, "data_level", data_level)
    setattr(file, "timestamp", timestamp)
    setattr(file, "version", version.replace("v", ""))
    if instrument in ["feeps", "fpi", "hpca"]:
        species = parse_species(instrument, data_type)
        setattr(file, "species", species)


@define
class CdfFile:
    """CDF file.

    .. todo:: Update docstring

    """

    cdf_file_name: str = field(validator=parse_file_name)
    modified_date: str = ""
    size: str = ""
    probe: str = ""
    instrument: str = ""
    data_rate: str = ""
    data_type: str = ""
    data_level: str = ""
    timestamp: str = ""
    version: str = ""
    species: str = ""
    local_path: str = ""

    def validate(self, query: "Query"):
        """Validate the metadata from the file name with the query."""
        query_metadata = query.metadata
        compare_keys = [
            "probe",
            "instrument",
            "data_rate",
            "data_type",
            "data_level",
        ]
        for key in compare_keys:
            query_parameter = query_metadata[key]
            file_parameter = getattr(self, key)
            if query_parameter != file_parameter:
                msg = (
                    f"Query parameter {query_parameter!r} is different from "
                    f"file parameter {file_parameter!r}."
                )
                raise ValueError(msg)

    def consolidate(self, query: "Query"):
        """Validate the metadata and add the local path from the query."""
        self.validate(query)
        group_path = query.metadata["local_path"]
        self.local_path = str(Path(group_path) / self.zarr)

    @property
    def zarr(self) -> str:
        return f"zarr_{self.timestamp}"

    @property
    def metadata(self) -> dict[str, str]:
        return asdict(self)


def dataset_is_updated(
    local_file_path: str | Path,
    remote_version: str,
    remote_size: Quantity,
    remote_modified_date: str,
) -> bool:
    """Determine if local dataset is updated with remote.

    Compare the version, the file size, and the modified date.

    Parameters
    ----------
    metadata : dict[str, str]
        The dataset metadata.

    Returns
    -------
    is_updated : bool
        Whether the local store is updated with remote.

    """
    try:
        local_attrs = zarr.open(local_file_path, mode="r").attrs
        local_version = local_attrs.get("version", "")
        local_size = u(local_attrs.get("size", ""))
        local_modified_date = local_attrs.get("modified_date", "")
        same_version = local_version == remote_version
        same_size = np.isclose(local_size, remote_size)
        same_modified_date = local_modified_date == remote_modified_date
        return same_version and same_size and same_modified_date  # type: ignore[return-value]
    except (FileNotFoundError, zarr.errors.PathNotFoundError):
        return False


def time_in_range(time: Date, start_time: Date, stop_time: Date) -> bool:
    """Check if a given `time` is within range.

    Parameters
    ----------
    time : date-like
        Timestamp to check.
    start_time : date-like
        The start of the time range.
    stop_time : date-like
        The end of the time range.

    Returns
    -------
    in_range : bool
        Whether `time` is within range.

    """
    return (
        pd.Timestamp(start_time) < pd.Timestamp(time) < pd.Timestamp(stop_time)
    )


def truncate_file_list_using_metadata(
    files: list[Path],
    query: "Query",
) -> list[Path]:
    filtered_list: list[Path] = []
    local_start_time: str | None
    local_stop_time: str | None
    for file in files:
        try:
            local_attrs = zarr.open(file, mode="r").attrs
            local_start_time = local_attrs.get("start_time", None)
            local_stop_time = local_attrs.get("stop_time", None)
            if not (bool(local_start_time) and bool(local_stop_time)):
                dataset = xr.open_zarr(file)
                if "time" in dataset:
                    local_start_time = str(dataset.time[0].values)
                    local_stop_time = str(dataset.time[-1].values)
            if not (bool(local_start_time) and bool(local_stop_time)):
                filtered_list.append(file)
                continue
            if (
                time_in_range(
                    local_start_time,  # type: ignore[arg-type]
                    query.start_time,
                    query.stop_time,
                )
                or time_in_range(
                    local_stop_time,  # type: ignore[arg-type]
                    query.start_time,
                    query.stop_time,
                )
                or time_in_range(
                    query.start_time,
                    local_start_time,
                    local_stop_time,
                )
                or time_in_range(
                    query.stop_time,
                    local_start_time,
                    local_stop_time,
                )
            ):
                filtered_list.append(file)
        except (FileNotFoundError, zarr.errors.PathNotFoundError):
            continue

    return filtered_list


def truncate_file_list_using_name(
    files: list[T_File],
    query: "Query",
) -> list[T_File]:
    """Find truncated list based on `query` time range."""
    timestamps: list[pd.Timestamp] = []
    for file in files:
        time = (
            file.timestamp
            if isinstance(file, CdfFile)
            else file.name.replace("zarr_", "")
        )
        timestamps.append(pd.to_datetime(time, format="%Y_%m_%d_%H_%M_%S"))

    min_idx = max(
        0,
        bisect_left(timestamps, pd.Timestamp(query.start_time)) - 1,
    )
    max_idx = min(
        len(files) - 1,
        bisect_right(timestamps, pd.Timestamp(query.stop_time)) + 1,
    )
    return files[min_idx : max_idx + 1]
