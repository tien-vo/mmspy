"""Provide functionality for curlometer calculations.

This module implements 4-point spatial interpolation techniques
discussed in Chapter 14 of Paschmann, G., & Daly, P. W. 1998
"""

__all__ = ["curlometer"]

from collections.abc import Sequence

import numpy as np
import pandas as pd
import xarray as xr

from mmspy.compute.utils import match_time_resolution, sampling_information
from mmspy.compute.vector import cross


def _has_equivalent_units(list_of_array: Sequence[xr.DataArray]) -> bool:
    """Check if a sequence of `DataArray` has compatible units.

    Parameters
    ----------
    list_of_array : sequence of DataArray
        Sequence of arrays with units

    Returns
    -------
    result : bool
        True if all elements can be converted to one another

    """
    units = list_of_array[0].pint.units
    return all(
        array.pint.units.is_compatible_with(units) for array in list_of_array
    )


def _validate_input(list_of_xarrays: Sequence[xr.DataArray]) -> None:
    """Validate the inputs of functions in this module.

    Check that the list of arrays have 4 elements and that
    their units are compatible.
    """
    expected_length = 4
    if len(list_of_xarrays) != expected_length:
        msg = "Input quantity must be 4-point measurements"
        raise ValueError(msg)
    if not _has_equivalent_units(list_of_xarrays):
        msg = "Input quantity have incompatible units"
        raise ValueError(msg)


def curlometer(
    quantity: Sequence[xr.DataArray],
    position: Sequence[xr.DataArray],
    name: str = "Q",
) -> xr.Dataset:
    """Curlometer.

    Calculate the linearly interpolated spatial gradients of a
    quantity from 4-point measurements.

    Parameters
    ----------
    quantity : Sequence of DataArray
        4-point measurements of a scalar or vector quantity. If `quantity`
        is a vector field, it must have a rectangular (x, y, z) 'rank_1'
        dimension.
    position : Sequence of DataArray
        Corresponding positions of the measurements.
    name : str
        Name of quantity (default: Q)

    Returns
    -------
    ds_clm : Dataset
        Dataset containing gradients of the quantity

    """
    _validate_input(quantity)
    _validate_input(position)

    # Get units and unpack variables
    Q_unit = quantity[0].pint.quantify().pint.units
    R_unit = position[0].pint.quantify().pint.units
    Q1, Q2, Q3, Q4 = [
        da.pint.quantify().pint.to(Q_unit).pint.dequantify() for da in quantity
    ]
    R1, R2, R3, R4 = [
        da.pint.quantify().pint.to(R_unit).pint.dequantify() for da in position
    ]

    # Calculate time array to interpolate everyone onto
    Ts = min([sampling_information(da.time)["period"] for da in quantity])
    Ts = pd.Timedelta(int(Ts.to("ns").magnitude), "ns")
    start_time = min([da.time[0].values for da in quantity])
    end_time = max([da.time[-1].values for da in quantity])
    time = np.arange(start_time, end_time + Ts, Ts).astype("datetime64[ns]")
    time = xr.DataArray(time, coords={"time": time})

    # Interpolate every array onto the same time grid
    Q1 = match_time_resolution(Q1, time)
    Q2 = match_time_resolution(Q2, time)
    Q3 = match_time_resolution(Q3, time)
    Q4 = match_time_resolution(Q4, time)
    R1 = match_time_resolution(R1, time)
    R2 = match_time_resolution(R2, time)
    R3 = match_time_resolution(R3, time)
    R4 = match_time_resolution(R4, time)

    # Calculate separation
    R_12 = R2 - R1
    R_13 = R3 - R1
    R_14 = R4 - R1

    # Calculate reciprocal vectors
    numerator = cross(R_13, R_14, dim="rank_1")
    denumerator = xr.dot(R_12, numerator, dim="rank_1")
    k2 = numerator / denumerator

    numerator = cross(R_12, R_14, dim="rank_1")
    denumerator = xr.dot(R_13, numerator, dim="rank_1")
    k3 = numerator / denumerator

    numerator = cross(R_12, R_13, dim="rank_1")
    denumerator = xr.dot(R_14, numerator, dim="rank_1")
    k4 = numerator / denumerator
    k1 = -k2 - k3 - k4

    # Create resulting dataset
    ds_clm = xr.Dataset().pint.quantify()

    # Calculate barycentric quantities
    ds_clm = ds_clm.assign(
        {
            "r_bc": 0.25 * (R1 + R2 + R3 + R4).pint.quantify(R_unit),
            f"{name}_bc": 0.25 * (Q1 + Q2 + Q3 + Q4).pint.quantify(Q_unit),
        },
    )

    # Calculate gradients
    if "rank_1" in Q1.dims:
        kw = {"dim": "rank_1"}
        kw_i = {"rank_1": "i"}
        kw_j = {"rank_1": "j"}
        grad = (
            k1.rename(**kw_i) * Q1.rename(**kw_j)
            + k2.rename(**kw_i) * Q2.rename(**kw_j)
            + k3.rename(**kw_i) * Q3.rename(**kw_j)
            + k4.rename(**kw_i) * Q4.rename(**kw_j)
        ).pint.quantify(Q_unit / R_unit)
        grad = xr.combine_nested(
            [
                grad.sel(i="x", j="x").reset_coords(drop=True),
                grad.sel(i="y", j="y").reset_coords(drop=True),
                grad.sel(i="z", j="z").reset_coords(drop=True),
                grad.sel(i="x", j="y").reset_coords(drop=True),
                grad.sel(i="x", j="z").reset_coords(drop=True),
                grad.sel(i="y", j="z").reset_coords(drop=True),
            ],
            concat_dim=[
                pd.Index(["xx", "yy", "zz", "xy", "xz", "yz"], name="rank_2"),
            ],
            combine_attrs="no_conflicts",
        )
        ds_clm = ds_clm.assign(
            {
                f"grad_{name}": grad,
                f"div_{name}": (
                    xr.dot(k1, Q1, **kw)
                    + xr.dot(k2, Q2, **kw)
                    + xr.dot(k3, Q3, **kw)
                    + xr.dot(k4, Q4, **kw)
                ).pint.quantify(Q_unit / R_unit),
                f"curl_{name}": (  # type: ignore[union-attr]
                    cross(k1, Q1, **kw)
                    + cross(k2, Q2, **kw)
                    + cross(k3, Q3, **kw)
                    + cross(k4, Q4, **kw)
                ).pint.quantify(Q_unit / R_unit),
            },
        )
    else:
        ds_clm = ds_clm.assign(
            {
                f"grad_{name}": (
                    k1 * Q1 + k2 * Q2 + k3 * Q3 + k4 * Q4
                ).pint.quantify(Q_unit / R_unit),
            },
        )

    return ds_clm
