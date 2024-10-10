r"""Provide metadata processing utilities."""

__all__ = [
    "parse_metadata",
]

from pathlib import Path

import pandas as pd


def parse_metadata(  # noqa: PLR0912
    file_name: str,
    instrument: str,
) -> dict[str, str]:
    r"""Parse metadata from file name.

    Parameters
    ----------
    file_name : str
        CDF file name.
    instrument : str
        Expected instrument in ``file_name``.

    Returns
    -------
    metadata : dict[str, str]
        Dictionary containing metadata of ``file_name``.

    """
    data_type: str | None

    # Initial parsing
    name = Path(file_name).stem
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
            raise ValueError(msg)

    # Check file mismatch
    msg = f"File mismatch ({instrument!r} != {_instrument!r})!"
    assert instrument == _instrument, msg

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
            raise ValueError(msg)

    new_fmt = "%Y-%m-%d-%H-%M-%S-%f"
    time_string = pd.to_datetime(time_string, format=old_fmt).strftime(new_fmt)

    # Transform data type
    match instrument:
        case "fpi":
            data_type = (
                str(data_type)
                .replace("dis-", "ion-")
                .replace("des-", "elc-")
                .replace("-dist", "_distribution")
                .replace("-moms", "_moments")
                .replace("-partmoms", "_partial_moments")
            )
        case "feeps":
            data_type = str(data_type).replace("electron", "elc")
            data_type = f"{data_type}_distribution"

    # Define extra
    end = f"{data_rate}/{data_level}/{time_string}"
    match instrument:
        case "mec":
            extra = {
                "group": f"/{probe}/{instrument}_{data_type}/{end}",
            }
        case "fgm":
            extra = {
                "group": f"/{probe}/{instrument}_bfield/{end}",
                "eph_group": f"/{probe}/{instrument}_ephemeris/{end}",
            }
        case "edp":
            match data_type:
                case "dce":
                    sfx = "efield"
                case "scpot":
                    sfx = "potential"
                case _:
                    msg = (
                        f"Data type {data_type!r} currently not supported "
                        f"for {instrument!r} instrument."
                    )
                    raise ValueError(msg)

            extra = {
                "group": f"/{probe}/{instrument}_{sfx}/{end}",
            }
        case "fpi" | "feeps":
            extra = {
                "species": str(data_type)[:3],
                "group": f"/{probe}/{instrument}_{data_type}/{end}",
            }

    return {
        "file_name": file_name,
        "probe": probe,
        "instrument": instrument,
        "data_rate": data_rate,
        "data_level": data_level,
        "version": version.replace("v", ""),
        **extra,
    }
