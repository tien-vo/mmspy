__all__ = [
    "process_fpi_distribution",
    "process_fpi_moments",
    "process_fpi_partial_moments",
]
import warnings

import numpy as np
import pandas as pd
import xarray as xr
from cdflib.xarray import cdf_to_xarray

from .cdf import process_cdf_epoch, process_cdf_metadata

# Ignore warning due to cdf_to_xarray on CDF moment files
warnings.filterwarnings(
    "ignore",
    message="Duplicate dimension names present",
)

distribution_standard_names = {
    "f": "Phase space density",
    "f_err": "Phase space density error",
    "W": "Energy",
    "theta_dbcs": "DBCS zenith angle",
    "phi_dbcs": "DBCS azimuthal angle",
}
moments_standard_names = {
    "flag": "FPI flag",
    "N": "Number density",
    "V_dbcs": "DBCS velocity",
    "V_gse": "GSE velocity",
    "V_spintone_dbcs": "DBCS spintone velocity",
    "V_spintone_gse": "GSE spintone velocity",
    "P_dbcs": "DBCS pressure",
    "P_gse": "GSE pressure",
    "T_para": "Parallel temperature",
    "T_perp": "Perpendicular temperature",
    "Q_dbcs": "DBCS heat flux",
    "Q_gse": "GSE heat flux",
    "j_omni": "Omni-directional energy flux",
    "W": "Energy",
}
partial_moments_standard_names = {
    "flag": "FPI flag",
    "N": "Number density",
    "V_dbcs": "DBCS velocity",
    "V_gse": "GSE velocity",
    "P_dbcs": "DBCS pressure",
    "P_gse": "GSE pressure",
    "T_para": "Parallel temperature",
    "T_perp": "Perpendicular temperature",
    "W": "Energy",
    "index": "Index for partial moment integration",
    "V_sc": "Spacecraft potential",
    "b_dbcs": "DBCS unit magnetic field",
}


def center_timestamps(ds: xr.Dataset) -> xr.Dataset:
    r"""Center dataset timestamps.

    .. todo:: Add docstring.

    References
    ----------
    .. [1] :pytplot_center_time:`cdf_to_tplot.py#L195-L231`

    """
    ds = ds.copy()

    # dt = np.int64(0.5e9 * (ds.Epoch_plus_var - ds.Epoch_minus_var).values)
    dt = pd.Timedelta(
        0.5 * (ds.Epoch_plus_var - ds.Epoch_minus_var).values,
        unit=ds.Epoch_plus_var.units,
    )
    with xr.set_options(keep_attrs=True):
        ds = ds.assign_coords(Epoch=ds.Epoch + dt)
        ds.Epoch.attrs.update(CATDESC="Centered timestamps")

    return ds


def process_fpi_distribution(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{_data_type}".format(**metadata)
    suffix = "{_data_rate}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch"])
    ds = center_timestamps(ds)

    # Rename dimensions
    ds = ds.swap_dims(
        {
            f"{prefix}_energy_{suffix}_dim": "energy_channel",
            f"{prefix}_theta_{suffix}": "zenith_sector",
        },
    )
    if metadata["data_rate"] == "brst":
        ds = ds.swap_dims({f"{prefix}_phi_{suffix}_dim": "azimuthal_sector"})
    else:
        ds = ds.swap_dims({f"{prefix}_phi_{suffix}": "azimuthal_sector"})
    ds = ds.assign_coords(
        energy_channel=("energy_channel", np.arange(32, dtype="i1")),
        zenith_sector=("zenith_sector", np.arange(16, dtype="i1")),
        azimuthal_sector=("azimuthal_sector", np.arange(32, dtype="i1")),
    ).reset_coords()

    # Rename and remove unwanted variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            f"{prefix}_energy_{suffix}": "W",
            f"{prefix}_theta_{suffix}": "theta_dbcs",
            f"{prefix}_phi_{suffix}": "phi_dbcs",
            f"{prefix}_dist_{suffix}": "f",
            f"{prefix}_disterr_{suffix}": "f_err",
        },
    ).set_coords(["W", "theta_dbcs", "phi_dbcs"])
    ds = process_cdf_metadata(ds[list(variables.values())])
    for variable, name in distribution_standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Force monotonic
    ds = ds.drop_duplicates("time").sortby("time")

    # Save
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds = ds.chunk(chunks=chunks)
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)


def process_fpi_moments(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{_data_type}".format(**metadata)
    suffix = "{_data_rate}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch"])
    ds = center_timestamps(ds)

    # Rename dimensions
    ds = ds.swap_dims(
        {
            "dim0": "space_rank_1",
            f"{prefix}_energy_{suffix}_dim": "energy_channel",
        },
    )
    ds = ds.assign_coords(
        space_rank_1=("space_rank_1", ["x", "y", "z"]),
        space_rank_2=(
            "space_rank_2",
            ["xx", "yy", "zz", "xy", "xz", "yz"],
        ),
        energy_channel=("energy_channel", np.arange(32, dtype="i1")),
    ).reset_coords()

    # Reorganize rank-2 tensors
    P_dbcs = ds[f"{prefix}_prestensor_dbcs_{suffix}"]
    P_gse = ds[f"{prefix}_prestensor_gse_{suffix}"]
    ds = ds.assign(
        P_dbcs=xr.DataArray(
            data=np.array(
                [
                    P_dbcs.values[:, 0, 0],
                    P_dbcs.values[:, 1, 1],
                    P_dbcs.values[:, 2, 2],
                    P_dbcs.values[:, 0, 1],
                    P_dbcs.values[:, 0, 2],
                    P_dbcs.values[:, 1, 2],
                ],
            ).T,
            dims=("time", "space_rank_2"),
            attrs=P_dbcs.attrs,
        ),
        P_gse=xr.DataArray(
            data=np.array(
                [
                    P_gse.values[:, 0, 0],
                    P_gse.values[:, 1, 1],
                    P_gse.values[:, 2, 2],
                    P_gse.values[:, 0, 1],
                    P_gse.values[:, 0, 2],
                    P_gse.values[:, 1, 2],
                ],
            ).T,
            dims=("time", "space_rank_2"),
            attrs=P_gse.attrs,
        ),
    )

    # Rename and remove unwanted variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            f"{prefix}_errorflags_{suffix}": "flag",
            f"{prefix}_energyspectr_omni_{suffix}": "j_omni",
            f"{prefix}_numberdensity_{suffix}": "N",
            f"{prefix}_bulkv_dbcs_{suffix}": "V_dbcs",
            f"{prefix}_bulkv_gse_{suffix}": "V_gse",
            f"{prefix}_bulkv_spintone_dbcs_{suffix}": "V_spintone_dbcs",
            f"{prefix}_bulkv_spintone_gse_{suffix}": "V_spintone_gse",
            f"{prefix}_heatq_dbcs_{suffix}": "Q_dbcs",
            f"{prefix}_heatq_gse_{suffix}": "Q_gse",
            f"{prefix}_temppara_{suffix}": "T_para",
            f"{prefix}_tempperp_{suffix}": "T_perp",
            f"{prefix}_energy_{suffix}": "W",
        },
    ).set_coords("W")
    ds = process_cdf_metadata(ds[["P_dbcs", "P_gse", *variables.values()]])
    for variable, name in moments_standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Remove flag units attribute to make it compliant with `pint`
    ds.flag.attrs.update(units="")

    # Force monotonic
    ds = ds.drop_duplicates("time").sortby("time")

    # Save
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds = ds.chunk(chunks=chunks)
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)


def process_fpi_partial_moments(
    temporary_file: str,
    metadata: dict,
    chunks: dict[str, str] = {"time": "1MB"},
) -> None:
    prefix = "{probe}_{_data_type}".format(**metadata)
    suffix = "{_data_rate}".format(**metadata)

    # Load file and fix epoch metadata
    ds = cdf_to_xarray(temporary_file, to_datetime=True, fillval_to_nan=True)
    ds = process_cdf_epoch(ds, epoch_variables=["Epoch"])
    ds = center_timestamps(ds)

    # Rename dimensions
    ds = ds.swap_dims(
        {
            "dim0": "space_rank_1",
            f"{prefix}_energy_{suffix}_dim": "energy_channel",
        },
    )
    ds = ds.assign_coords(
        space_rank_1=("space_rank_1", ["x", "y", "z"]),
        space_rank_2=(
            "space_rank_2",
            ["xx", "yy", "zz", "xy", "xz", "yz"],
        ),
        energy_channel=("energy_channel", np.arange(32, dtype="i1")),
    ).reset_coords()

    # Reorganize rank-2 tensors
    P_dbcs = ds[f"{prefix}_prestensor_part_dbcs_{suffix}"]
    P_gse = ds[f"{prefix}_prestensor_part_gse_{suffix}"]
    ds = ds.assign(
        P_dbcs=xr.DataArray(
            data=np.array(
                [
                    P_dbcs.values[:, :, 0, 0],
                    P_dbcs.values[:, :, 1, 1],
                    P_dbcs.values[:, :, 2, 2],
                    P_dbcs.values[:, :, 0, 1],
                    P_dbcs.values[:, :, 0, 2],
                    P_dbcs.values[:, :, 1, 2],
                ],
            ),
            dims=("space_rank_2", "time", "energy_channel"),
            attrs=P_dbcs.attrs,
        ),
        P_gse=xr.DataArray(
            data=np.array(
                [
                    P_gse.values[:, :, 0, 0],
                    P_gse.values[:, :, 1, 1],
                    P_gse.values[:, :, 2, 2],
                    P_gse.values[:, :, 0, 1],
                    P_gse.values[:, :, 0, 2],
                    P_gse.values[:, :, 1, 2],
                ],
            ),
            dims=("space_rank_2", "time", "energy_channel"),
            attrs=P_gse.attrs,
        ),
    )

    # Rename and remove unwanted variables
    ds = ds.rename(
        variables := {
            "Epoch": "time",
            f"{prefix}_errorflags_{suffix}": "flag",
            f"{prefix}_numberdensity_part_{suffix}": "N",
            f"{prefix}_bulkv_part_dbcs_{suffix}": "V_dbcs",
            f"{prefix}_bulkv_part_gse_{suffix}": "V_gse",
            f"{prefix}_temppara_part_{suffix}": "T_para",
            f"{prefix}_tempperp_part_{suffix}": "T_perp",
            f"{prefix}_energy_{suffix}": "W",
            f"{prefix}_part_index_{suffix}": "index",
            f"{prefix}_scpmean_{suffix}": "V_sc",
            f"{prefix}_bhat_dbcs_{suffix}": "b_dbcs",
        },
    ).set_coords("W")
    ds = process_cdf_metadata(ds[["P_dbcs", "P_gse", *variables.values()]])
    for variable, name in partial_moments_standard_names.items():
        ds[variable].attrs.update(standard_name=name)

    # Remove flag and index units attribute to make it compliant with `pint`
    ds.flag.attrs.update(units="")
    ds.index.attrs.update(units="")

    # Force monotonic and transpose data
    ds = (
        ds.drop_duplicates("time")
        .sortby("time")
        .transpose("time", "space_rank_1", "space_rank_2", "energy_channel")
    )

    # Save
    ds.attrs.update(
        source=metadata["cdf_file_name"],
        probe=metadata["probe"],
        start_date=str(ds.time.values[0]),
        end_date=str(ds.time.values[-1]),
    )
    ds = ds.chunk(chunks=chunks)
    ds.to_zarr(mode="w", store=metadata["group"], consolidated=True)
