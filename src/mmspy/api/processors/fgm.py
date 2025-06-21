__all__ = ["process_fgm"]

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
from mmspy.compute.utils import force_monotonic, match_time_resolution
from mmspy.configure.config import config

# These labels are not needed
drop_labels = [
    f"label_{v}"
    for v in ["b_gse", "b_gsm", "b_dmpa", "b_bcs", "r_gse", "r_gsm"]
] + ["represent_vec_tot"]


def process_fgm(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    interpolate_ephemeris_dataset = config.get(
        "fgm/interpolate_ephemeris_dataset",
        default=False,
    )
    split_ephemeris_dataset = config.get(
        "fgm/split_ephemeris_dataset",
        default=False,
    )
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{data_rate}_{data_level}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["Epoch", "Epoch_state"])

    # Rename epoch
    dataset = dataset.rename(Epoch="time", Epoch_state="ephemeris_time")

    # Rename rank-1 spatial dimension and drop magnitude
    dataset = dataset.rename_dims(dim0="rank_1")
    if "record0" in dataset.dims:
        dataset = dataset.rename(record0="time")
    dataset = dataset.assign_coords(rank_1=["x", "y", "z", "mag"])
    dataset = dataset.drop_sel(rank_1="mag")

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Fix units for some variables
    dataset["mode"].attrs.update(units="1/s")
    dataset["etemp"].attrs.update(units="degreeC")
    dataset["stemp"].attrs.update(units="degreeC")

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Force monotonic
    dataset = force_monotonic(dataset, dimension="time")
    dataset = force_monotonic(dataset, dimension="ephemeris_time")

    # Extract ephemeris dataset from the main dataset
    ephemeris_dataset = dataset.drop_dims("time").rename(ephemeris_time="time")

    if interpolate_ephemeris_dataset or split_ephemeris_dataset:
        dataset = dataset.drop_dims("ephemeris_time")

    # Merge back into main dataset via interpolation
    if interpolate_ephemeris_dataset:
        for variable in ephemeris_dataset:
            dataset[variable] = match_time_resolution(
                ephemeris_dataset[variable],
                dataset.time,
            )

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "rank_1")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    datasets = [(True, metadata["local_path"], dataset)]
    if split_ephemeris_dataset:
        data_type = metadata["local_path"].split("/")[2]
        metadata["local_path"] = metadata["local_path"].replace(
            data_type,
            "ephemeris",
        )
        ephemeris_dataset = ephemeris_dataset.transpose("time", ..., "rank_1")
        ephemeris_dataset = process_cdf_metadata(ephemeris_dataset)
        ephemeris_dataset.attrs.update(**metadata)
        datasets.append((False, metadata["local_path"], ephemeris_dataset))

    return datasets
