__all__ = [
    "process_feeps_distribution",
]

import logging

import numpy as np
import xarray as xr
from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata


class IgnoreFeepsIstpWarningsFilter(logging.Filter):
    r"""Filter ITSP warnings for FEEPS.

    The metadata in FEEPS raw CDF files seem to be buggy right now.
    There is nothing we can do except for opening a PR for `cdflib`.
    So for now, this filter is to ignore the ISTP warning messages
    until the issues are fixed.

    """

    def filter(self, record: logging.LogRecord) -> bool:
        r"""Filter message if FEEPS patterns are detected."""

        def _in_msg(pattern: str) -> bool:
            return "feeps" in record.msg and pattern in record.msg

        different_dimension = _in_msg("but they have different dimension")
        dimension_not_match = _in_msg("but the dimensions do not match")

        return not (different_dimension or dimension_not_match)


logging.getLogger("cdflib.logging").addFilter(IgnoreFeepsIstpWarningsFilter())

standard_names = {
    "intensity": ["n", "Differential number flux"],
    "count_rate": ["R", "Count rate"],
    "energy": ["W", "Energy centroid"],
    "percent_error": ["sigma", "Percentage error"],
    "spin": ["spin_count", "Number of rotation"],
    "spinsectnum": ["spin_sector_number", "Current sector"],
    "pitch_angle": ["theta_fac", "Pitch angle"],
}
eyes = {
    "ion": [6, 7, 8],
    "elc": [1, 2, 3, 4, 5, 9, 10, 11, 12],
}


def process_feeps_distribution(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    r""".. todo:: Add docstring and refactor for less complexity."""
    prefix = (
        "{probe}_epd_{instrument}_{_data_rate}_{data_level}_{_data_type}"
    ).format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["epoch"]).reset_coords()

    # Rename variables and remove unwanted variables
    energy_depend_list = [
        "intensity",
        "count_rate",
        "percent_error",
    ]
    energy_nodepend_list = [
        "quality_indicator",
        "sector_mask",
        "sun_contamination",
    ]
    angle_nodepend_list = [
        "spin",
        "spinsectnum",
        "integration_sectors",
        "spin_duration",
    ]
    ds = ds.rename(
        {
            "epoch": "time",
            **{
                f"{prefix}_{sensor}_{variable}_sensorid_{eye}": (
                    f"{variable}_{sensor}_{eye}"
                )
                for sensor in ["top", "bottom"]
                for eye in eyes[metadata["species"]]
                for variable in [
                    "energy_centroid",
                    *energy_depend_list,
                    *energy_nodepend_list,
                ]
            },
            **{
                f"{prefix}_{variable}": variable
                for variable in ["pitch_angle", *angle_nodepend_list]
            },
        },
    )

    # Create empty dataset for reindexing
    ds_reindex = xr.Dataset(attrs=ds.attrs).merge(ds[angle_nodepend_list])

    # Reindex angle-dependent variables
    channels = np.arange(16)
    for variable in energy_depend_list + energy_nodepend_list:
        for sensor in ["top", "bottom"]:
            for eye in eyes[metadata["species"]]:
                da = ds[f"{variable}_{sensor}_{eye}"].to_dataset(name=variable)
                if variable in energy_depend_list:
                    energy_centroid = f"energy_centroid_{sensor}_{eye}"
                    da = (
                        da.assign_coords(
                            energy_channel=(energy_centroid, channels),
                        )
                        .swap_dims({energy_centroid: "energy_channel"})
                        .rename({energy_centroid: "energy"})
                        .reset_coords("energy")
                    )
                    if (da.energy < 0).all():
                        da = da.assign(
                            {
                                "energy": np.nan * da["energy"],
                                variable: np.nan * da[variable],
                            },
                        )

                da = da.expand_dims(["sensor", "eye"])
                da = da.assign_coords(sensor=[sensor], eye=[eye])
                ds_reindex = ds_reindex.merge(
                    da,
                    combine_attrs="drop_conflicts",
                )

    ds_reindex = ds_reindex.rename(dim1="spin_sector")
    ds_reindex = ds_reindex.assign_coords(spin_sector=np.arange(64))

    # The pitch angle needs extra processing
    dim = tuple(filter(lambda item: item != "time", ds.pitch_angle.dims))
    assert len(dim) == 1, "Expecting pitch angle to have only 2 dimensions"
    idx = ds.pitch_angle.get_index(dim := dim[0])
    for sensor_idx in [idx[idx > 0], idx[idx < 0]]:
        for eye_idx in sensor_idx:
            sensor = "top" if eye_idx > 0 else "bottom"
            eye = int(abs(eye_idx))
            da = ds.pitch_angle.sel({dim: eye_idx}).to_dataset().drop_vars(dim)
            da = da.expand_dims(["sensor", "eye"])
            da = da.assign_coords(sensor=[sensor], eye=[eye])
            if np.isnan(ds_reindex.energy.sel(sensor=sensor, eye=eye)).all():
                da = da.assign(pitch_angle=np.nan * da.pitch_angle)
            ds_reindex = ds_reindex.merge(da, combine_attrs="drop_conflicts")

    # Mannually fix some units and metadata
    ds_reindex.count_rate.attrs.update(units="count/s")
    ds_reindex.percent_error.attrs.update(units="%")
    ds_reindex = (
        process_cdf_metadata(ds_reindex)
        .transpose("time", "sensor", "eye", "energy_channel", "spin_sector")
        .chunk(chunks=chunks)
    )
    for variable, (symbol, name) in standard_names.items():
        ds_reindex = ds_reindex.rename({variable: symbol})
        ds_reindex[symbol].attrs.update(standard_name=name)

    ds_reindex = ds_reindex.set_coords(["W", "theta_fac"])
    ds_reindex.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        Data_version=metadata["version"],
        start_date=str(ds_reindex.time.values[0]),
        end_date=str(ds_reindex.time.values[-1]),
    )
    ds_reindex.to_zarr(mode="w", store=metadata["group"], consolidated=True)
