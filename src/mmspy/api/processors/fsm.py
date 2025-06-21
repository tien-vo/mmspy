__all__ = ["process_fsm"]

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
from mmspy.configure.config import config

# These labels are not needed
drop_labels = ["label_r_gse", "b_gse_labls", "represent_vec_tot"]


def process_fsm(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{data_rate}_{data_level}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(
        temporary_file,
        time_variables=["Epoch", "Epoch_fgm", "Epoch_state"],
    )

    # Rename epoch
    dataset = dataset.rename(
        Epoch="time",
        Epoch_fgm="fluxgate_time",
        Epoch_state="ephemeris_time",
    )
    if "record0" in dataset:
        dataset = dataset.rename(record0="time")

    # Rename rank-1 spatial dimension
    dataset = dataset.rename_dims(dim0="rank_1")
    dataset = dataset.assign_coords(rank_1=["x", "y", "z"])

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Fix units for some variables
    dataset["mode"].attrs.update(units="1/s")
    dataset["etemp"].attrs.update(units="degreeC")
    dataset["stemp"].attrs.update(units="degreeC")

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "rank_1")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
