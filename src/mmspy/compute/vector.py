"""Provides functionality for vector-related calculations."""

__all__ = [
    "cross",
    "vector_norm",
    "matrix_multiply",
    "quaternion_dot",
    "quaternion_conjugate",
]

import numpy as np
import xarray as xr

from mmspy.compute.utils import is_quantified
from mmspy.configure.units import units as u
from mmspy.types import Dims, Sequence


def cross(
    vector_1: xr.DataArray,
    vector_2: xr.DataArray,
    dim: Dims,
) -> xr.DataArray:
    """Calculate the cross product using `np.cross`.

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
    if quantified := (is_quantified(vector_1) | is_quantified(vector_2)):
        vector_1 = vector_1.pint.dequantify()
        vector_2 = vector_2.pint.dequantify()
        unit_1 = u.Unit(getattr(vector_1, "units", ""))
        unit_2 = u.Unit(getattr(vector_2, "units", ""))

    vector = xr.apply_ufunc(
        np.cross,
        vector_1,
        vector_2,
        input_core_dims=[[dim], [dim]],
        output_core_dims=[[dim]],
        dask="parallelized",
        output_dtypes=[np.result_type(vector_1, vector_2)],
        dask_gufunc_kwargs={"allow_rechunk": True},
    )
    return vector.pint.quantify(unit_1 * unit_2) if quantified else vector


def vector_norm(
    vector: xr.DataArray,
    dim: Dims,
    order: int | float | str | None = None,
) -> xr.DataArray:
    """Calculate the nth-order vector norm using `np.linalg.norm`.

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
    if quantified := is_quantified(vector):
        vector = vector.pint.dequantify()
        unit = u.Unit(getattr(vector, "units", ""))

    norm = xr.apply_ufunc(
        np.linalg.norm,
        vector,
        input_core_dims=[[dim]],
        kwargs={"ord": order, "axis": -1},
        dask="parallelized",
        output_dtypes=[vector.dtype],
        dask_gufunc_kwargs={"allow_rechunk": True},
    )
    return norm.pint.quantify(unit) if quantified else norm


def matrix_multiply(
    matrix_1: xr.DataArray,
    matrix_2: xr.DataArray,
    dims: Sequence[Dims],
) -> xr.DataArray:
    """Multiply two matrices using `np.linalg.norm`.

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
    if quantified := is_quantified(matrix_1) | is_quantified(matrix_2):
        matrix_1 = matrix_1.pint.dequantify()
        matrix_2 = matrix_2.pint.dequantify()
        unit_1 = u.Unit(getattr(matrix_1, "units", ""))
        unit_2 = u.Unit(getattr(matrix_2, "units", ""))

    matrix = xr.apply_ufunc(
        np.matmul,
        matrix_1,
        matrix_2,
        input_core_dims=[dims, dims],
        output_core_dims=[dims],
        dask="parallelized",
        output_dtypes=[np.result_type(matrix_1, matrix_2)],
        dask_gufunc_kwargs={"allow_rechunk": True},
    )
    return matrix.pint.quantify(unit_1 * unit_2) if quantified else matrix


def quaternion_dot(q1: xr.DataArray, q2: xr.DataArray) -> xr.DataArray:
    """Quaternion dot.

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
    """Quaternion conjugation.

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
