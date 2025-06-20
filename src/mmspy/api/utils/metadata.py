"""Provide metadata processing utilities."""

__all__ = [
    "parse_metadata_from_file_name",
    "consolidate_metadata",
]

from pathlib import Path

import zarr


def parse_timestamp(timestamp: str) -> tuple[str, ...]:
    """Parse the timestamp on cdf files.

    The timestamps are often of the format YYYYMMDD or YYYYMMDDhhmmss.
    This function extracts the year, month, day, and parse the timestamp
    into YYYY_MM_DD_hh_mm_ss format.
    """
    # Extract the year
    year = timestamp[:4]
    # Split the rest into a list of 2-character strings
    remainder = list(map("".join, zip(*[iter(timestamp[4:])] * 2)))
    # If the time is missing up to seconds, pad them with 00's
    remainder += ["00"] * max(0, 5 - len(remainder))
    # Extract the month and day
    month, day = remainder[:2]
    # Combine everything into a YYYY_MM_DD_hh_mm_ss format
    time = "_".join([year] + remainder)
    return year, month, day, time


def parse_metadata_from_file_name(cdf_file_name: str):
    strings = Path(cdf_file_name).stem.split("_")
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
        data_type = None
    year, month, day, timestamp = parse_timestamp(timestamp)
    return {
        "cdf_file_name": cdf_file_name,
        "zarr_file_name": f"file_{timestamp}",
        "probe": probe,
        "instrument": instrument,
        "data_rate": data_rate,
        "data_type": str(data_type),
        "data_level": data_level,
        "version": version.replace("v", ""),
        "timestamp": timestamp,
        "year": year,
        "month": month,
        "day": day,
    }


def consolidate_metadata(
    query_metadata: dict[str, str],
    file_metadata: dict[str, str],
) -> dict[str, str]:
    """Merge metadata from query and CDF file name.

    Parameters
    ----------
    query_metadata : dict[str, str]
        Metadata from query.
    file_metadata : dict[str, str]
        Metadata from CDF file name.

    Returns
    -------
    metadata : dict[str, str]
        Dictionary containing consolidated metadata.

    """
    compare_keys = [
        "probe",
        "instrument",
        "data_rate",
        "data_type",
        "data_level",
    ]
    for key in compare_keys:
        query_parameter = query_metadata[key]
        file_parameter = file_metadata[key]
        assert query_parameter == file_parameter, (
            f"Query parameter {query_parameter!r} is different from "
            f"file parameter {file_parameter!r}."
        )

    metadata = {**file_metadata, **query_metadata}
    return metadata
