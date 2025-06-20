__all__ = ["process_hpca_moments"]

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
    shorten_variable_names,
)

# Ignore warning due to cdf_to_xarray on CDF moment files
warnings.filterwarnings(
    "ignore",
    message="Duplicate dimension names present",
)


def process_hpca_moments(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{instrument}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["Epoch"])
    dataset = center_timestamps(
        dataset,
        time_variable="Epoch",
        plus_variable="Epoch_PLUS",
        minus_variable="Epoch_MINUS",
    )

    # Rename epoch
    dataset = dataset.rename(Epoch="time")

    # Rename dimensions
    dataset = dataset.rename(dim0="energy_channel", dim2="rank_1")
    dataset = dataset.assign_coords(
        energy_channel=("energy_channel", np.arange(63, dtype="i1")),
        rank_1=["x", "y", "z", "mag"],
        rank_2=(
            "rank_2",
            ["xx", "yy", "zz", "xy", "xz", "yz"],
        ),
    )
    dataset = dataset.drop_sel(rank_1="mag")
    dataset = dataset.rename(dim1="rank_1")

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix)

    # Fix units
    dataset["ion_energy"].attrs.update(units="eV/C")

    # Reorganize rank-2 tensors
    for variable in [
        f"{species}_{quantity}"
        for species in ["hplus", "heplus", "heplusplus", "oplus"]
        for quantity in ["ion_pressure", "temperature_tensor"]
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

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", "energy_channel", "rank_1", "rank_2")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
