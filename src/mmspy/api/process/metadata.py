r"""Provide metadata processing utilities."""

__all__ = [
    "consolidate_metadata",
    "dataset_is_updated",
    "parse_metadata_from_file_name",
]

from pathlib import Path

import pandas as pd
import xarray as xr


def consolidate_metadata(
    query_metadata: dict[str, str],
    file_metadata: dict[str, str],
    path: Path,
) -> dict[str, str]:
    r"""Merge metadata from query and CDF file name.

    Parameters
    ----------
    query_metadata : dict[str, str]
        Metadata from query.
    file_metadata : dict[str, str]
        Metadata from CDF file name.
    path : Path
        Path of the store to sync

    Returns
    -------
    metadata : dict[str, str]
        Dictionary containing consolidated metadata.

    """
    compare_keys = [
        ("probe", "probe"),
        ("instrument", "instrument"),
        ("_data_rate", "data_rate"),
        ("_data_type", "data_type"),
        ("data_level", "data_level"),
    ]
    for query_key, file_key in compare_keys:
        query_parameter = query_metadata[query_key]
        file_parameter = file_metadata[file_key]
        assert query_parameter == file_parameter, (
            f"Query parameter {query_parameter!r} is different from "
            f"file parameter {file_parameter!r}."
        )

    metadata = {**file_metadata, **query_metadata}

    # Extra metadata
    extras: dict = {
        "group": (
            path
            / metadata["probe"]
            / "{instrument}_{data_type}".format(**metadata)
            / metadata["data_rate"]
            / metadata["data_level"]
            / metadata["time_string"]
        ),
    }
    if metadata["instrument"] == "fpi":
        metadata["_data_type"] = metadata["_data_type"][:3]
    if metadata["instrument"] in ["fpi", "feeps"]:
        extras["species"] = metadata["data_type"][:3]

    return {**metadata, **extras}


def dataset_is_updated(metadata: dict[str, str]) -> bool:
    r"""Determine if local dataset is updated with remote.

    .. todo::

        Populate file size from downloader so that this method can
        compare file sizes, instead of just file versions.

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
        ds = xr.open_zarr(metadata["group"])
        local_version = ds.Data_version
        remote_version = metadata["version"]
        return local_version == remote_version
    except FileNotFoundError:
        return False


def parse_metadata_from_file_name(
    cdf_file_name: str,
    instrument: str,
) -> dict[str, str]:
    r"""Parse metadata from file name.

    .. todo::

        Refactor to reduce complexity.

    Parameters
    ----------
    cdf_file_name : str
        CDF file name.
    instrument : str
        Expected instrument in ``cdf_file_name``.

    Returns
    -------
    metadata : dict[str, str]
        Dictionary containing metadata of ``cdf_file_name``.

    """
    data_type: str | None

    # Initial parsing
    name = Path(cdf_file_name).stem
    match instrument:
        case "fgm":
            (
                probe,
                _instrument,
                data_rate,
                data_level,
                time_string,
                version,
            ) = name.split("_")
            data_type = None
        case "mec" | "edp" | "fpi" | "feeps":
            (
                probe,
                _instrument,
                data_rate,
                data_level,
                data_type,
                time_string,
                version,
            ) = name.split("_")
        case _:
            msg = f"Instrument {instrument!r} currently not supported."
            raise NotImplementedError(msg)

    # Set time string format
    match instrument:
        case "mec" | "fgm":
            old_fmt = "%Y%m%d%H%M%S" if data_rate == "brst" else "%Y%m%d"
        case "edp":
            old_fmt = (
                "%Y%m%d%H%M%S"
                if data_type == "scpot"
                or (data_rate == "brst" and data_type == "dce")
                else "%Y%m%d"
            )
        case "fpi" | "feeps":
            old_fmt = "%Y%m%d%H%M%S"
        case _:
            msg = f"Instrument {instrument!r} currently not supported."
            raise NotImplementedError(msg)

    new_fmt = "%Y-%m-%d-%H-%M-%S"
    time_string = pd.to_datetime(time_string, format=old_fmt).strftime(new_fmt)

    return {
        "cdf_file_name": cdf_file_name,
        "probe": probe,
        "instrument": instrument,
        "data_rate": data_rate,
        "data_type": str(data_type),
        "data_level": data_level,
        "version": version.replace("v", ""),
        "time_string": time_string,
    }
