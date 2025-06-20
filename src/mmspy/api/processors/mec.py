__all__ = ["process_mec"]

import xarray as xr

from mmspy.api.processors.cdf import (
    load_cdf,
    process_cdf_metadata,
)
from mmspy.api.processors.utils import (
    alias_variable_names,
    shorten_variable_names,
)

# These labels are not needed
drop_labels = [
    "quaternion_representation",
    "radec_representation",
    "3vec_representation",
] + [
    f"{variable}_label"
    for variable in [
        "quat_eci_to_bcs",
        "quat_eci_to_gse",
        "quat_eci_to_gsm",
        "quat_eci_to_geo",
        "quat_eci_to_sm",
        "quat_eci_to_dbcs",
        "quat_eci_to_smpa",
        "quat_eci_to_dmpa",
        "quat_eci_to_dsl",
        "quat_eci_to_ssl",
        "quat_eci_to_gse2000",
        "r_sun_de421_eci",
        "r_moon_de421_eci",
        "L_vec",
        "Z_vec",
        "P_vec",
        "r_eci",
        "r_gse",
        "r_gse2000",
        "r_gsm",
        "r_geo",
        "r_sm",
        "v_eci",
        "v_gse",
        "v_gse2000",
        "v_gsm",
        "v_geo",
        "v_sm",
        "bsc_gsm",
        "pmin_gsm",
        "bmin_gsm",
        "bfn_gsm",
        "pfn_gsm",
        "bfs_gsm",
        "pfs_gsm",
        "pfn_geod_latlon",
        "pfs_geod_latlon",
    ]
]


def process_mec(
    temporary_file: str,
    metadata: dict,
) -> list[tuple[bool, str, xr.Dataset]]:
    prefix = "{probe}_{instrument}".format(**metadata)

    # ---- Load and process
    dataset = load_cdf(temporary_file, time_variables=["Epoch"])

    # Rename epoch
    dataset = dataset.rename(Epoch="time", record0="time")

    # Rename other dimensions and assign labels
    dataset = dataset.rename_dims(
        dim0="quaternion",
        dim1="attitude",
        dim2="field_model",
        dim3="rank_1",
    )
    dataset = dataset.assign_coords(
        rank_1=["x", "y", "z"],
        quaternion=["x", "y", "z", "w"],
        attitude=["right_ascension", "declination"],
    )

    # Shorten variable names
    dataset = shorten_variable_names(dataset, prefix=prefix)

    # Drop unnecessary labels
    dataset = dataset.drop_vars(drop_labels)

    # Alias variables
    dataset = alias_variable_names(dataset, instrument=metadata["instrument"])

    # Final metadata clean-up
    dataset = dataset.transpose("time", ..., "rank_1").squeeze()
    dataset = process_cdf_metadata(dataset)
    dataset.attrs.update(**metadata)

    return [(True, metadata["local_path"], dataset)]
