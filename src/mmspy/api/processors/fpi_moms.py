__all__ = ["process_fpi_moms"]


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
drop_labels = [
    f"{variable}_label"
    for variable in [
        "bulkv_dbcs",
        "bulkv_gse",
        "bulkv_err",
        "bulkv_spintone_dbcs",
        "bulkv_spintone_gse",
        "heatq_dbcs",
        "heatq_gse",
        "heatq_err",
    ]
] + ["cartrep"]


def process_fpi_moms(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{data_type}".format(**metadata).replace("-moms", "")
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
        "dim0": "rank_1",
        f"{prefix}_energy_{suffix}_dim": "energy_channel",
    }
    dataset = dataset.swap_dims(swap_dimensions)
    dataset = dataset.assign_coords(
        rank_1=("rank_1", ["x", "y", "z"]),
        rank_2=(
            "rank_2",
            ["xx", "yy", "zz", "xy", "xz", "yz"],
        ),
        energy_channel=("energy_channel", np.arange(32, dtype="i1")),
    ).reset_coords()

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Reorganize rank-2 tensors
    for variable in [
        "prestensor_dbcs",
        "prestensor_gse",
        "temptensor_dbcs",
        "temptensor_gse",
        "prestensor_err",
        "temptensor_err",
    ]:
        array = dataset[variable]
        dataset[variable] = xr.DataArray(
            data=np.array(
                [
                    array.values[:, 0, 0],
                    array.values[:, 1, 1],
                    array.values[:, 2, 2],
                    array.values[:, 0, 1],
                    array.values[:, 0, 2],
                    array.values[:, 1, 2],
                ],
            ).T,
            dims=("time", "rank_2"),
            attrs=array.attrs,
        )

    dataset = dataset.set_coords("energy")

    # Fix units
    dataset["compressionloss"].attrs.update(units="")
    dataset["errorflags"].attrs.update(units="")
    dataset["startdelphi_count"].attrs.update(units="")

    # Burst-related processing
    if metadata["data_rate"] == "brst":
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
