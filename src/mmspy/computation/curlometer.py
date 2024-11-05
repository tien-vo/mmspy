r"""Provides functionality for curlometer calculations.

This module implements 4-point spatial interpolation techniques
discussed in Chapter 14 of Paschmann, G., & Daly, P. W. 1998
"""

__all__ = ["curlometer"]

from collections.abc import Sequence

import xarray as xr

from mmspy.computation.vector import cross
from mmspy.utils.timing import match_time_resolution


def _has_equivalent_units(list_of_array: Sequence[xr.DataArray]) -> bool:
    r"""Check if a sequence of `DataArray` has compatible units.

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
    r"""Validate the inputs of functions in this module.

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
    r"""Curlometer.

    Calculate the linearly interpolated spatial gradients of a
    quantity from 4-point measurements.

    Parameters
    ----------
    quantity : Sequence of DataArray
        4-point measurements of a scalar or vector quantity. If `quantity`
        is a vector field, it must have a rectangular (x, y, z) 'space_rank_1'
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
    Q_unit = quantity[0].pint.quantify().units
    R_unit = position[0].pint.quantify().units
    Q1, Q2, Q3, Q4 = [
        da.pint.quantify().to(Q_unit).pint.dequantify() for da in quantity
    ]
    R1, R2, R3, R4 = [
        da.pint.quantify().to(R_unit).pint.dequantify() for da in position
    ]

    # Interpolate every array onto q1 time
    kw = {"target": Q1.time, "average": False}
    Q2 = match_time_resolution(Q2, **kw)
    Q3 = match_time_resolution(Q3, **kw)
    Q4 = match_time_resolution(Q4, **kw)
    R1 = match_time_resolution(R1, **kw)
    R2 = match_time_resolution(R2, **kw)
    R3 = match_time_resolution(R3, **kw)
    R4 = match_time_resolution(R4, **kw)

    # Calculate separation
    R_12 = R2 - R1
    R_13 = R3 - R1
    R_14 = R4 - R1

    # Calculate reciprocal vectors
    numerator = cross(R_13, R_14, dim="space_rank_1")
    denumerator = xr.dot(R_12, numerator, dim="space_rank_1")
    k2 = numerator / denumerator

    numerator = cross(R_12, R_14, dim="space_rank_1")
    denumerator = xr.dot(R_13, numerator, dim="space_rank_1")
    k3 = numerator / denumerator

    numerator = cross(R_12, R_13, dim="space_rank_1")
    denumerator = xr.dot(R_14, numerator, dim="space_rank_1")
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
    if "space_rank_1" in Q1.dims:
        kw = {"dim": "space_rank_1"}
        kw_i = {"space_rank_1": "space_i"}
        kw_j = {"space_rank_1": "space_j"}
        ds_clm = ds_clm.assign(
            {
                f"grad_{name}": (
                    k1.rename(**kw_i) * Q1.rename(**kw_j)
                    + k2.rename(**kw_i) * Q2.rename(**kw_j)
                    + k3.rename(**kw_i) * Q3.rename(**kw_j)
                    + k4.rename(**kw_i) * Q4.rename(**kw_j)
                ).pint.quantify(Q_unit / R_unit),
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
