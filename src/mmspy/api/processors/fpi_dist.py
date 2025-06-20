__all__ = ["process_fpi_dist"]


import warnings

import numpy as np
import xarray as xr

from mmspy.api.processors.cdf import (
    load_cdf,
    process_cdf_metadata,
)
from mmspy.api.processors.utils import (
    alias_variable_names,
    center_timestamps,
    filter_variables,
    shorten_variable_names,
)

# Ignore warning due to cdf_to_xarray on CDF moment files
warnings.filterwarnings(
    "ignore",
    message="Duplicate dimension names present",
)

# These labels are not needed
drop_labels = ["sector_label", "pixel_label", "energy_label"]


def process_fpi_dist(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{data_type}".format(**metadata).replace("-dist", "")
    suffix = "{data_rate}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["Epoch"])
    dataset = center_timestamps(
        dataset,
        time_variable="Epoch",
        plus_variable="Epoch_plus_var",
        minus_variable="Epoch_minus_var",
    )

    # Rename epoch
    dataset = dataset.rename(Epoch="time")

    # Rename dimensions
    swap_dimensions = {
        f"{prefix}_energy_{suffix}_dim": "energy_channel",
        f"{prefix}_theta_{suffix}": "zenith_sector",
    } | (
        {f"{prefix}_phi_{suffix}_dim": "azimuthal_sector"}
        if metadata["data_rate"] == "brst"
        else {f"{prefix}_phi_{suffix}": "azimuthal_sector"}
    )
    dataset = dataset.swap_dims(swap_dimensions)
    dataset = dataset.assign_coords(
        energy_channel=("energy_channel", np.arange(32, dtype="i1")),
        zenith_sector=("zenith_sector", np.arange(16, dtype="i1")),
        azimuthal_sector=("azimuthal_sector", np.arange(32, dtype="i1")),
    ).reset_coords()

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Fix units
    dataset["compressionloss"].attrs.update(units="")
    dataset["errorflags"].attrs.update(units="")
    dataset["startdelphi_count"].attrs.update(units="")

    # Burst-related processing
    if metadata["data_rate"] == "brst":
        dataset = dataset.rename(dim0="energy_channel")
        dataset["sector_despinp"].attrs.update(units="")
        dataset["steptable_parity"].attrs.update(units="")

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
