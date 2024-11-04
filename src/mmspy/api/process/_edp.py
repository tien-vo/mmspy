__all__ = [
    "process_efield",
    "process_potential",
]

import numpy as np
from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata

standard_names = {
    "E_gse": "GSE DC electric field",
    "E_dsl": "DSL DC electric field",
    "E_para": "Parallel electric field",
    "E_para_err": "Parallel electric field error",
    "bitmask": "EDP bitmask",
}


def process_efield(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{_data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=[f"{prefix}_epoch_{suffix}"])
    ds = ds.reset_coords()

    # Rename variables and remove unwanted variables
    ds = ds.rename(
        variables := {
            f"{prefix}_epoch_{suffix}": "time",
            f"{prefix}_dce_gse_{suffix}": "E_gse",
            f"{prefix}_dce_par_epar_{suffix}": "E_para",
            f"{prefix}_dce_dsl_{suffix}": "E_dsl",
            f"{prefix}_bitmask_{suffix}": "bitmask",
        },
    )
    attrs = ds.E_para.attrs
    E_para = ds.E_para.values
    ds = ds.assign(
        E_para=("time", E_para[:, -1], attrs),
        E_para_err=("time", E_para[:, 0], {"units": attrs["units"]}),
    )
    ds = ds.rename_dims(dim0="space_rank_1").drop_dims("dim1")
    ds = ds.assign_coords(space_rank_1=["x", "y", "z"])
    ds = process_cdf_metadata(ds[["E_para_err", *variables.values()]])
    for variable, name in standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Save
    ds = ds.drop_duplicates("time").sortby("time")
    ds = ds.chunk(chunks=chunks)
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)


def process_potential(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{instrument}".format(**metadata)
    suffix = "{_data_rate}_{data_level}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(
        temporary_file,
        to_datetime=True,
        fillval_to_nan=True,
    )
    ds = process_cdf_epoch(ds, epoch_variables=[f"{prefix}_epoch_{suffix}"])
    ds = ds.reset_coords()

    # Rename variables and remove unwanted variables
    ds = (
        ds.rename_dims(dim0="probe")
        .assign_coords(probe=np.arange(1, 7))
        .rename(
            variables := {
                f"{prefix}_epoch_{suffix}": "time",
                f"{prefix}_scpot_{suffix}": "V_sc",
                f"{prefix}_dcv_{suffix}": "V_p",
            },
        )
    )
    ds.V_sc.attrs.update(standard_name="Spacecraft potential")
    ds.V_p.attrs.update(standard_name="Probe potential")

    # Final metadata processing
    ds = process_cdf_metadata(ds[list(variables.values())])
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )

    # Save
    ds = ds.drop_duplicates("time").sortby("time")
    ds = ds.chunk(chunks=chunks)
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)
