__all__ = ["process_fpi_partmoms"]


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
    f"{variable}_label" for variable in ["bulkv_dbcs", "bulkv_gse"]
] + ["cartrep"]


def process_fpi_partmoms(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{data_type}".format(**metadata).replace("-partmoms", "")
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
    dataset["gse_xform"] = xr.DataArray(
        data=np.array(
            [
                dataset["gse_xform"].values[:, 0, 0],
                dataset["gse_xform"].values[:, 1, 1],
                dataset["gse_xform"].values[:, 2, 2],
                dataset["gse_xform"].values[:, 0, 1],
                dataset["gse_xform"].values[:, 0, 2],
                dataset["gse_xform"].values[:, 1, 2],
            ],
        ).T,
        dims=("time", "rank_2"),
        attrs=dataset["gse_xform"].attrs,
    )
    for variable in [
        "prestensor_part_dbcs",
        "prestensor_part_gse",
        "temptensor_part_dbcs",
        "temptensor_part_gse",
    ]:
        array = dataset[variable]
        dataset[variable] = xr.DataArray(
            data=np.array(
                [
                    array.values[:, :, 0, 0],
                    array.values[:, :, 1, 1],
                    array.values[:, :, 2, 2],
                    array.values[:, :, 0, 1],
                    array.values[:, :, 0, 2],
                    array.values[:, :, 1, 2],
                ],
            ),
            dims=("rank_2", "time", "energy_channel"),
            attrs=array.attrs,
        )

    dataset = dataset.set_coords("energy")

    # Fix units
    dataset["errorflags"].attrs.update(units="")
    dataset["part_index"].attrs.update(units="")

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", "rank_1", "rank_2", "energy_channel")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
