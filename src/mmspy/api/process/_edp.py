__all__ = [
    "process_dce",
    "process_scpot",
]

from pathlib import Path

from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata

standard_names = {
    "E_gse": "GSE DC electric field",
    "E_dsl": "DSL DC electric field",
    "E_para": "Parallel electric field",
    "E_para_err": "Parallel electric field error",
    "bitmask": "EDP bitmask",
}


def process_dce(
    path: Path,
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    pfx = "{probe}_{instrument}".format(**metadata)
    sfx = "{data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(
        temporary_file,
        to_datetime=True,
        fillval_to_nan=True,
    )
    ds = process_cdf_epoch(ds, epoch_variables=[f"{pfx}_epoch_{sfx}"])
    ds = ds.reset_coords()

    # Rename variables and remove unwanted variables
    ds = ds.rename(
        variables := {
            f"{pfx}_epoch_{sfx}": "time",
            f"{pfx}_dce_gse_{sfx}": "E_gse",
            f"{pfx}_dce_par_epar_{sfx}": "E_para",
            f"{pfx}_dce_dsl_{sfx}": "E_dsl",
            f"{pfx}_bitmask_{sfx}": "bitmask",
        },
    )
    attrs = ds.E_para.attrs
    E_para = ds.E_para.values
    ds = ds.assign(
        E_para=("time", E_para[:, -1]),
        E_para_err=("time", E_para[:, 0]),
    )
    ds.E_para.attrs.update(**attrs)
    ds = ds.rename_dims(dim0="space_rank_1").drop_dims("dim1")
    ds = ds.assign_coords(space_rank_1=["x", "y", "z"])
    ds = process_cdf_metadata(ds[["E_para_err", *variables.values()]])
    for variable, name in standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Save
    ds = ds.drop_duplicates("time").sortby("time")
    ds = ds.chunk(chunks=chunks)
    ds.attrs.update(
        source=metadata["file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds.to_zarr(
        mode="w",
        store=path / metadata["group"][1:],
        consolidated=True,
    )


def process_scpot(
    path: Path,
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    pfx = "{probe}_{instrument}".format(**metadata)
    sfx = "{data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(
        temporary_file,
        to_datetime=True,
        fillval_to_nan=True,
    )
    ds = process_cdf_epoch(ds, epoch_variables=[f"{pfx}_epoch_{sfx}"])
    ds = ds.reset_coords()

    # Rename variables and remove unwanted variables
    ds = ds.drop_dims("dim0").rename(
        variables := {
            f"{pfx}_epoch_{sfx}": "time",
            f"{pfx}_scpot_{sfx}": "V_sc",
        },
    )
    ds.V_sc.attrs.update(standard_name="Spacecraft potential")

    # Final metadata processing
    ds = process_cdf_metadata(ds[list(variables.values())])
    ds.attrs.update(
        source=metadata["file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )

    # Save
    ds = ds.drop_duplicates("time").sortby("time")
    ds = ds.chunk(chunks=chunks)
    ds.to_zarr(
        mode="w",
        store=path / metadata["group"][1:],
        consolidated=True,
    )
