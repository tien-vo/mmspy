__all__ = ["process_feeps"]

import numpy as np
import xarray as xr

from mmspy.api.processors.cdf import (
    load_cdf,
    process_cdf_metadata,
)
from mmspy.api.processors.utils import (
    alias_variable_names,
    filter_variables,
    shorten_variable_names,
)

eyes = {
    "ion": [6, 7, 8],
    "electron": [1, 2, 3, 4, 5, 9, 10, 11, 12],
}


def process_feeps(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = (
        "{probe}_epd_{instrument}_{data_rate}_{data_level}_{data_type}"
    ).format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["epoch"])

    # Rename epoch
    dataset = dataset.rename(epoch="time")

    # Rename rank-1 spatial dimension
    dataset = dataset.rename_dims(
        dim0="energy_channel",
        dim1="spin_sector",
        dim2="rank_1",
        dim3="sensor_id",
    )
    dataset = dataset.assign_coords(
        rank_1=["x", "y", "z"],
        spin_sector=np.arange(64),
    )

    # Shorten variable names
    for name in list(dataset.data_vars) + list(dataset.coords):
        short = name.replace(f"{prefix}_", "")
        if "top" in short:
            short = short.replace("top_", "").replace("sensorid", "top")
        else:
            short = short.replace("bottom_", "").replace("sensorid", "bottom")
        dataset = dataset.rename({name: short})

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
    time_depend_list = [
        "scpos_ec_gse",
        "scx_vec_gse",
        "scy_vec_gse",
        "scz_vec_gse",
        "moon_position_gse",
        "radius",
        "lat_gse",
        "lon_gse",
        "l_shell",
        "lat_gsm",
        "lon_gsm",
    ]

    # Create empty dataset for reindexing
    reindexed_dataset = xr.Dataset(attrs=dataset.attrs)
    reindexed_dataset = reindexed_dataset.merge(dataset[angle_nodepend_list])

    # Reindex angle-dependent variables
    for variable in energy_depend_list + energy_nodepend_list:
        for sensor in ["top", "bottom"]:
            for eye in eyes[metadata["species"]]:
                array = dataset[f"{variable}_{sensor}_{eye}"]
                array = array.to_dataset(name=variable)
                if variable in energy_depend_list:
                    energy_centroid = f"energy_centroid_{sensor}_{eye}"
                    array = (
                        array.assign_coords(
                            energy_channel=(energy_centroid, np.arange(16)),
                        )
                        .swap_dims({energy_centroid: "energy_channel"})
                        .rename({energy_centroid: "energy"})
                        .reset_coords("energy")
                    )
                    if (array.energy < 0).all():
                        array = array.assign(
                            {
                                "energy": np.nan * array["energy"],
                                variable: np.nan * array[variable],
                            },
                        )

                array = array.expand_dims(["sensor", "eye"])
                array = array.assign_coords(sensor=[sensor], eye=[eye])
                reindexed_dataset = reindexed_dataset.merge(
                    array,
                    combine_attrs="drop_conflicts",
                )

    # The pitch angle needs extra processing
    dim = tuple(filter(lambda item: item != "time", dataset.pitch_angle.dims))
    if len(dim) != 1:
        msg = "Expecting pitch angle to have only 2 dimensions"
        raise ValueError(msg)

    idx = dataset.pitch_angle.get_index(dim := dim[0])
    for sensor_idx in [idx[idx > 0], idx[idx < 0]]:
        for eye_idx in sensor_idx:
            sensor = "top" if eye_idx > 0 else "bottom"
            eye = int(abs(eye_idx))
            array = (
                dataset.pitch_angle.sel({dim: eye_idx})
                .to_dataset()
                .drop_vars(dim)
            )
            array = array.expand_dims(["sensor", "eye"])
            array = array.assign_coords(sensor=[sensor], eye=[eye])
            if np.isnan(
                reindexed_dataset.energy.sel(sensor=sensor, eye=eye)
            ).all():
                array = array.assign(pitch_angle=np.nan * array.pitch_angle)
            reindexed_dataset = reindexed_dataset.merge(
                array,
                combine_attrs="drop_conflicts",
            )

    # Mannually fix some units and metadata
    reindexed_dataset.count_rate.attrs.update(units="count/s")
    reindexed_dataset.percent_error.attrs.update(units="%")

    # Merge some remaining variables
    reindexed_dataset = reindexed_dataset.merge(dataset[time_depend_list])
    for variable in ["energy_lower_bound", "energy_upper_bound"]:
        for sensor in ["top", "bottom"]:
            for eye in eyes[metadata["species"]]:
                name = f"{variable}_{sensor}_{eye}"
                array = dataset[name].to_dataset(name=variable)
                array = array.expand_dims(["sensor", "eye"])
                array = array.assign_coords(sensor=[sensor], eye=[eye])
                reindexed_dataset = reindexed_dataset.merge(
                    array,
                    combine_attrs="drop_conflicts",
                )

    reindexed_dataset = reindexed_dataset.set_coords(["energy", "pitch_angle"])

    # Alias variables
    reindexed_dataset = alias_variable_names(
        reindexed_dataset,
        instrument=metadata["instrument"],
    )

    # Filter variables
    reindexed_dataset = filter_variables(
        reindexed_dataset,
        instrument=metadata["instrument"],
    )

    # Clean up metadata
    reindexed_dataset = process_cdf_metadata(reindexed_dataset)
    reindexed_dataset = reindexed_dataset.transpose(
        "time",
        "sensor",
        "eye",
        "energy_channel",
        ...,
    )
    reindexed_dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], reindexed_dataset)]
