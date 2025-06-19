r"""Provide utilities for reading the FEEPS correction tables."""

__all__ = [
    "get_energy_table",
    "get_flat_field_table",
    "get_time_dependent_bad_eye_table",
    "get_time_independent_bad_eye_table",
    "get_sun_contamination_table",
]

import json
from pathlib import Path

import numpy as np
import xarray as xr

probes = ["mms1", "mms2", "mms3", "mms4"]
sensors = ["top", "bottom"]
eyes = np.arange(1, 13)
channels = np.arange(16)
sectors = np.arange(64)


def get_energy_table(keep_bad_eyes: bool = False) -> xr.DataArray:
    r"""Table for energy channel correction.

    Parameters
    ----------
    keep_bad_eyes : bool
        Toggle to keep the bad eyes.

    Returns
    -------
    table : DataArray
        Table containing the corrected energy channels

    """
    # Read json file
    path = Path(__file__).parent / "data" / "energy_table.json"
    data = json.load(path.open("r"))

    # Create table
    table = xr.DataArray(
        dims=("eye", "energy_channel"),
        coords={"eye": eyes, "energy_channel": channels},
    )
    table.loc[{"eye": data["ion_eyes"]}] = data["ion_energies"]
    table.loc[{"eye": data["elc_eyes"]}] = data["elc_energies"]

    # Create offsets
    offsets = xr.DataArray(
        dims=("probe", "sensor", "eye"),
        coords={"probe": probes, "sensor": sensors, "eye": eyes},
    )
    for probe in data["offsets"]:
        for sensor in data["offsets"][probe]:
            for eye, energy in enumerate(data["offsets"][probe][sensor]):
                offsets.loc[
                    {"probe": probe, "sensor": sensor, "eye": eye + 1}
                ] = energy

    if keep_bad_eyes:
        offsets = xr.where(np.isnan(offsets), 0.0, offsets)

    table = table + offsets
    table.name = "W"
    table.attrs.update(
        description=(
            "Energy table defined in mms/feeps/mms_feeps_energy_table.pro"
        ),
        units="keV",
    )
    return table.pint.quantify()


def get_flat_field_table(keep_bad_eyes: bool = False) -> xr.DataArray:
    r"""Table for flat field factors.

    Parameters
    ----------
    keep_bad_eyes : bool
        Toggle to keep the bad eyes.

    Returns
    -------
    table : DataArray
        Table containing the flat field factors

    """
    # Read json file
    path = Path(__file__).parent / "data" / "flat_field.json"
    data = json.load(path.open("r"))

    # Create table
    table = xr.DataArray(
        name="G_correction",
        data=1.0,
        dims=("probe", "sensor", "eye"),
        coords={"probe": probes, "sensor": sensors, "eye": eyes},
    )
    for probe, d_ in data.items():
        for sensor, d__ in d_.items():
            for eye, value in d__.items():
                table.loc[
                    {"probe": probe, "sensor": sensor, "eye": int(eye)}
                ] = (
                    value
                    if value is not None
                    else 1.0 if keep_bad_eyes else 0.0
                )

    return table


def get_time_dependent_bad_eye_table() -> xr.DataArray:
    r"""Time-dependent table for bad eyes.

    Returns
    -------
    table : DataArray
        Table containing the bad eyes

    """
    # Read json file
    path = Path(__file__).parent / "data" / "bad_eyes.json"
    data = json.load(path.open("r"))

    # Create table
    time = np.array(
        list(data["time_dependent"].keys()),
        dtype="datetime64[ns]",
    )
    table = xr.DataArray(
        name="bad_eyes",
        data=1.0,
        dims=("time", "probe", "sensor", "eye"),
        coords={
            "time": time,
            "probe": probes,
            "sensor": sensors,
            "eye": eyes,
        },
    )
    for day, d_ in data["time_dependent"].items():
        for probe, d__ in d_.items():
            for sensor, d___ in d__.items():
                for eye in d___:
                    ii = {
                        "time": np.datetime64(day),
                        "probe": probe,
                        "sensor": sensor,
                        "eye": eye,
                    }
                    table.loc[ii] = np.nan

    return table


def get_time_independent_bad_eye_table() -> xr.DataArray:
    r"""Time-independent table for bad eyes.

    Returns
    -------
    table : DataArray
        Table containing the bad eyes

    """
    # Read json file
    path = Path(__file__).parent / "data" / "bad_eyes.json"
    data = json.load(path.open("r"))

    # Create table
    table = xr.DataArray(
        name="bad_eyes",
        data=1.0,
        dims=("probe", "sensor", "eye", "energy_channel"),
        coords={
            "probe": probes,
            "sensor": sensors,
            "eye": eyes,
            "energy_channel": channels,
        },
    )
    for channel, d_ in data["time_independent"].items():
        for probe, d__ in d_.items():
            for sensor, d___ in d__.items():
                for eye in d___:
                    table.loc[
                        {
                            "energy_channel": int(channel),
                            "probe": probe,
                            "sensor": sensor,
                            "eye": eye,
                        }
                    ] = np.nan

    return table


def get_sun_contamination_table() -> xr.DataArray:
    r"""Table for sun contamination.

    Returns
    -------
    table : DataArray
        Table containing the bad eyes

    """
    # Read json file
    path = Path(__file__).parent / "data" / "sun_contamination.json"
    data = json.load(path.open("r"))

    # Create table
    time = np.array(list(data.keys()), dtype="datetime64[ns]")
    table = xr.DataArray(
        name="contaminated_sector",
        data=np.nan,
        dims=("time", "probe", "sensor", "eye", "spin_sector"),
        coords={
            "time": time,
            "probe": probes,
            "sensor": sensors,
            "eye": eyes,
            "spin_sector": sectors,
        },
    ).transpose("time", "probe", "sensor", "spin_sector", "eye")
    for day, d in data.items():
        _day = np.datetime64(day)
        for probe, d_ in d.items():
            top = np.array(d_)[:, 0:12]
            bot = np.array(d_)[:, 12:24]
            table.loc[{"time": _day, "probe": probe, "sensor": "top"}] = top
            table.loc[{"time": _day, "probe": probe, "sensor": "bottom"}] = bot

    return table
