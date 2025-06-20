__all__ = ["process_edp_dce"]

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

# These labels are not needed
drop_labels = [
    "representation1",
    "representation2",
    "label1",
    "label2",
    "label3",
]


def process_edp_dce(
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

    # Rename rank-1 spatial dimension
    dataset = dataset.rename_dims(dim0="rank_1")
    dataset = dataset.assign_coords(rank_1=["x", "y", "z"])

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix, suffix=suffix)

    # Break up the parallel electric field
    attrs = dataset.dce_par_epar.attrs
    E_para = dataset.dce_par_epar.values
    dataset = dataset.assign(
        dce_par_epar=("time", E_para[:, -1], attrs),
        dce_par_epar_err=("time", E_para[:, 0], {"units": attrs["units"]}),
    )

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Filter variables
    dataset = filter_variables(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "rank_1")
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
