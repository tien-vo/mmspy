__all__ = [
    "process_fgm",
]

from cdflib.xarray import cdf_to_xarray

from mmspy.utils.timing import match_time_resolution

from .cdf import process_cdf_epoch, process_cdf_metadata

standard_names = {
    "B_gse": "GSE magnetic field",
    "B_gsm": "GSM magnetic field",
    "R_gse": "GSE spacecraft position",
    "R_gsm": "GSM spacecraft position",
    "flag": "FGM flag",
}


def process_fgm(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{_data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch", "Epoch_state"])
    ds = ds.reset_coords()

    # Rename dimensions and drop magnitude
    ds = ds.rename_dims(dim0="rank_1")
    ds = ds.assign_coords(rank_1=["x", "y", "z", "mag"])
    ds = ds.drop_sel(rank_1="mag")

    # Rename and remove unwanted data variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            "Epoch_state": "eph_time",
            f"{prefix}_b_gse_{suffix}": "B_gse",
            f"{prefix}_b_gsm_{suffix}": "B_gsm",
            f"{prefix}_r_gse_{suffix}": "R_gse",
            f"{prefix}_r_gsm_{suffix}": "R_gsm",
            f"{prefix}_flag_{suffix}": "flag",
        },
    )
    ds = process_cdf_metadata(ds[list(variables.values())])
    for variable, name in standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Extract ephemeris data and interpolate onto field data
    ds_eph = (
        ds.drop_dims("time")
        .rename(eph_time="time")
        .drop_duplicates("time")
        .sortby("time")
    )

    # Combine back into main dataset
    ds = ds.drop_dims("eph_time").drop_duplicates("time").sortby("time")
    for variable in ds_eph:
        ds[variable] = match_time_resolution(ds_eph[variable], ds.time)

    ds = ds.chunk(chunks=chunks)
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)
