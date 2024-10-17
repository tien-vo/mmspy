__all__ = [
    "process_mec",
]

from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata

standard_names = {
    "dipole_tilt": "Dipole tilt",
    "kp": "Kp index",
    "dst": "Dst index",
}


def process_mec(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{instrument}".format(**metadata)

    # Load file and fix metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch"])
    ds = ds.reset_coords()
    ds = ds.rename_dims(dim0="quaternion", dim2="space_rank_1")
    ds = ds.assign_coords(
        space_rank_1=["x", "y", "z"],
        quaternion=["x", "y", "z", "w"],
    )

    # Rename variables and remove unwanted variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            f"{prefix}_dipole_tilt": "dipole_tilt",
            f"{prefix}_kp": "kp",
            f"{prefix}_dst": "dst",
            f"{prefix}_r_gse": "R_gse",
            f"{prefix}_r_gsm": "R_gsm",
            f"{prefix}_v_gse": "V_gse",
            f"{prefix}_v_gsm": "V_gsm",
            f"{prefix}_quat_eci_to_dbcs": "Q_eci_to_dbcs",
            f"{prefix}_quat_eci_to_dsl": "Q_eci_to_dsl",
            f"{prefix}_quat_eci_to_gse": "Q_eci_to_gse",
            f"{prefix}_quat_eci_to_gsm": "Q_eci_to_gsm",
        },
    )
    ds = process_cdf_metadata(ds[list(variables.values())])
    for variable, name in standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Save
    ds = ds.drop_duplicates("time").sortby("time").chunk(chunks=chunks)
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        Data_verion=metadata["version"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)
