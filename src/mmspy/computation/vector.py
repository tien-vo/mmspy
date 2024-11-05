r"""Provides functionality for vector-related calculations."""

__all__ = [
    "cross",
    "vector_norm",
    "matrix_multiply",
    "quaternion_dot",
    "quaternion_conjugate",
]

from typing import Sequence

import numpy as np
import xarray as xr
from xarray.core.types import Dims

from mmspy.units import registry as u
from mmspy.utils.units import is_quantified


def cross(
    vector_1: xr.DataArray,
    vector_2: xr.DataArray,
    dim: Dims,
) -> xr.DataArray:
    r"""Calculate the cross product using `np.cross`.

    .. todo:: Open issue regarding pint units and dask.
    .. todo:: Check input dimensions and coordinates.

    Parameters
    ----------
    vector_1 : DataArray
        Vector 1.
    vector_2 : DataArray
        Vector 2.
    dim : Dims
        Which dimension to apply the function to.

    Returns
    -------
    cross : DataArray
        Cross product of ``vector_1`` and ``vector_2``.

    """
    quantified = is_quantified(vector_1)
    vector_1 = vector_1.pint.dequantify() if quantified else vector_1
    vector_2 = vector_2.pint.dequantify() if quantified else vector_2
    vector = xr.apply_ufunc(
        np.cross,
        vector_1,
        vector_2,
        input_core_dims=[[dim], [dim]],
        output_core_dims=[[dim]],
        dask="parallelized",
        output_dtypes=[np.result_type(vector_1, vector_2)],
    )
    return (
        vector.pint.quantify(u.Unit(vector_1.units) * u.Unit(vector_2.units))
        if quantified
        else vector
    )


def vector_norm(
    vector: xr.DataArray,
    dim: Dims,
    order: int | float | str | None = None,
) -> xr.DataArray:
    r"""Calculate the nth-order vector norm using `np.linalg.norm`.

    Parameters
    ----------
    vector : DataArray
        Vector.
    dim : Dims
        Which dimension to apply the function to.
    order : non-zero int, inf, -inf, 'fro', 'nuc', optional
        Order of the norm. See documentation for `~numpy.linalg.norm`.

    Returns
    -------
    norm : DataArray
        Norm of ``vector``.

    """
    quantified = is_quantified(vector)
    vector = vector.pint.dequantify() if quantified else vector
    norm = xr.apply_ufunc(
        np.linalg.norm,
        vector,
        input_core_dims=[[dim]],
        kwargs={"ord": order, "axis": -1},
        dask="parallelized",
        output_dtypes=[vector.dtype],
    )
    return norm.pint.quantify() if quantified else norm


def matrix_multiply(
    matrix_1: xr.DataArray,
    matrix_2: xr.DataArray,
    dims: Sequence[Dims],
) -> xr.DataArray:
    r"""Multiply two matrices using `np.linalg.norm`.

    .. todo:: Add logical check for matrix types and quantification.

    Parameters
    ----------
    matrix_1 : DataArray
        Matrix 1.
    matrix_2 : DataArray
        Matrix 2.
    dims : Dims
        Which dimensions to apply the function to.

    Returns
    -------
    matrix : DataArray
        Multiplication between ``matrix_1`` and ``matrix_2``.

    """
    quantified = is_quantified(matrix_1)
    matrix_1 = matrix_1.pint.dequantify() if quantified else matrix_1
    matrix_2 = matrix_2.pint.dequantify() if quantified else matrix_2
    matrix = xr.apply_ufunc(
        np.matmul,
        matrix_1,
        matrix_2,
        input_core_dims=[dims, dims],
        output_core_dims=[dims],
        dask="parallelized",
        output_dtypes=[np.result_type(matrix_1, matrix_2)],
    )
    return (
        matrix.pint.quantify(u.Unit(matrix_1.units) * u.Unit(matrix_2.units))
        if quantified
        else matrix
    )


def quaternion_dot(q1: xr.DataArray, q2: xr.DataArray) -> xr.DataArray:
    r"""Quaternion dot.

    Compute the multiplication of two quaternions.

    Parameters
    ----------
    q1, q2 : DataArray
        Quaternions.

    Returns
    -------
    q : DataArray
        Resulting quaternion.

    """
    a1 = q1.sel(quaternion="w").reset_coords(drop=True)
    b1 = q1.sel(quaternion="x").reset_coords(drop=True)
    c1 = q1.sel(quaternion="y").reset_coords(drop=True)
    d1 = q1.sel(quaternion="z").reset_coords(drop=True)

    a2 = q2.sel(quaternion="w").reset_coords(drop=True)
    b2 = q2.sel(quaternion="x").reset_coords(drop=True)
    c2 = q2.sel(quaternion="y").reset_coords(drop=True)
    d2 = q2.sel(quaternion="z").reset_coords(drop=True)

    q = q1.copy()
    q.loc[{"quaternion": "w"}] = a1 * a2 - b1 * b2 - c1 * c2 - d1 * d2
    q.loc[{"quaternion": "x"}] = a1 * b2 + b1 * a2 + c1 * d2 - d1 * c2
    q.loc[{"quaternion": "y"}] = a1 * c2 - b1 * d2 + c1 * a2 + d1 * b2
    q.loc[{"quaternion": "z"}] = a1 * d2 + b1 * c2 - c1 * b2 + d1 * a2
    return q


def quaternion_conjugate(q: xr.DataArray) -> xr.DataArray:
    r"""Quaternion conjugation.

    Compute the conjugation of a quaternion

    Parameters
    ----------
    q : DataArray
        Quaternion

    Returns
    -------
    q_conjugated : DataArray
        Resulting quaternion

    """
    q = q.copy()
    q.loc[{"quaternion": "x"}] = -q.sel(quaternion="x")
    q.loc[{"quaternion": "y"}] = -q.sel(quaternion="y")
    q.loc[{"quaternion": "z"}] = -q.sel(quaternion="z")
    return q
