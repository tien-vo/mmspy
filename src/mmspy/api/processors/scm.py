__all__ = ["process_scm"]

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


def process_scm(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{data_type}_{data_rate}_{data_level}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["Epoch"])

    # Rename epoch
    dataset = dataset.rename(Epoch="time")

    # Rename rank-1 dimension
    dataset = dataset.rename_dims(dim0="rank_1")
    dataset = dataset.assign_coords(rank_1=["x", "y", "z"])

    # Drop unnecessary labels
    dataset = dataset.drop_vars(
        [
            f"{prefix}_acb_gse_{suffix}_{label}"
            for label in ["labl_1", "representation_1"]
        ]
    )

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "rank_1")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
