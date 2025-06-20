__all__ = ["process_edp_scpot"]

import numpy as np
import xarray as xr

from mmspy.api.processors.cdf import (
    load_cdf,
    process_cdf_metadata,
)
from mmspy.api.processors.utils import (
    alias_variable_names,
    shorten_variable_names,
)


def process_edp_scpot(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{data_rate}_{data_level}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(
        temporary_file,
        time_variables=[f"{prefix}_epoch_{suffix}"],
    )

    # Rename epoch
    dataset = dataset.rename({f"{prefix}_epoch_{suffix}": "time"})

    # Rename probe dimension
    dataset = dataset.rename_dims(dim0="probe")
    dataset = dataset.assign_coords(probe=np.arange(1, 7))

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Drop unnecessary labels
    dataset = dataset.drop_vars(["label1"])

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "probe")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
