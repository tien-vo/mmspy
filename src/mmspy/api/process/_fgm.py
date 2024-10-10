__all__ = [
    "process_fgm",
]

from pathlib import Path

from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata

standard_names = {
    "B_gse": "GSE magnetic field",
    "B_gsm": "GSM magnetic field",
    "R_gse": "GSE spacecraft position",
    "R_gsm": "GSM spacecraft position",
    "flag": "FGM flag",
}


def process_fgm(
    path: Path,
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    pfx = "{probe}_{instrument}".format(**metadata)
    sfx = "{data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch", "Epoch_state"])
    ds = ds.reset_coords()

    # Rename dimensions and drop magnitude
    ds = ds.rename_dims(dim0="space_rank_1")
    ds = ds.assign_coords(space_rank_1=["x", "y", "z", "mag"])
    ds = ds.drop_sel(space_rank_1="mag")

    # Rename and remove unwanted data variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            "Epoch_state": "eph_time",
            f"{pfx}_b_gse_{sfx}": "B_gse",
            f"{pfx}_b_gsm_{sfx}": "B_gsm",
            f"{pfx}_r_gse_{sfx}": "R_gse",
            f"{pfx}_r_gsm_{sfx}": "R_gsm",
            f"{pfx}_flag_{sfx}": "flag",
        },
    )
    ds = process_cdf_metadata(ds[list(variables.values())])
    for variable, name in standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Save FGM field measurements
    ds_field = ds.drop_dims("eph_time")
    ds_field = ds_field.drop_duplicates("time").sortby("time")
    ds_field = ds_field.chunk(chunks=chunks)
    ds_field.attrs.update(
        source=metadata["file_name"],
        probe=metadata["probe"],
        start_date=str(ds_field.time.values[0]),
        end_date=str(ds_field.time.values[-1]),
    )
    ds_field.to_zarr(
        mode="w",
        store=path / metadata["group"][1:],
        consolidated=True,
    )

    # Save FGM ephemeris measurements
    ds_eph = ds.drop_dims("time").rename({"eph_time": "time"})
    ds_eph = ds_eph.drop_duplicates("time").sortby("time")
    ds_eph = ds_eph.sel(
        time=slice(
            ds_field.attrs["start_date"],
            ds_field.attrs["end_date"],
        ),
    )

    # Slice the data to avoid out of range issue
    ds_eph = ds_eph.chunk(chunks=chunks)
    ds_eph.attrs.update(
        source=metadata["file_name"],
        probe=metadata["probe"],
        start_date=str(ds_eph.time.values[0]),
        end_date=str(ds_eph.time.values[-1]),
    )
    ds_eph.to_zarr(
        mode="w",
        store=path / metadata["eph_group"][1:],
        consolidated=True,
    )
