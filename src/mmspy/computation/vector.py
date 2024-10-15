r"""Provides functionality for vector-related calculations."""

__all__ = [
    "vector_norm",
    "matrix_multiply",
    "quaternion_dot",
    "quaternion_conjugate",
]

from typing import Sequence

import numpy as np
import xarray as xr
from numpy.typing import NDArray
from scipy.linalg import inv, norm
from xarray.core.types import Dims


def vector_norm(
    vector: xr.DataArray,
    dim: Dims,
    order: int | float | str | None = None,
    check_finite: bool = False,
) -> xr.DataArray:
    r"""Calculate the nth-order vector norm using `np.linalg.norm`.

    Parameters
    ----------
    vector : DataArray
        Vector
    dim : Dims
        Which dimension to apply the function to
    order : non-zero int, inf, -inf, 'fro', 'nuc', optional
        Order of the norm. See documentation for `~numpy.linalg.norm`
    check_finite : bool
        Whether to check if all entries are finite

    Returns
    -------
    norm : DataArray
        Norm of the vector

    """
    return xr.apply_ufunc(
        norm,
        vector,
        input_core_dims=[[dim]],
        kwargs={"ord": order, "axis": -1, "check_finite": check_finite},
        dask="allowed",
    )


def matrix_multiply(
    matrix_1: xr.DataArray,
    matrix_2: xr.DataArray,
    dims: Sequence[Dims],
) -> xr.DataArray:
    r"""Multiply two matrices using `np.linalg.norm`.

    Parameters
    ----------
    matrix_1 : DataArray
        Matrix
    matrix_2 : DataArray
        Matrix
    dims : Dims
        Which dimension to apply the function to

    Returns
    -------
    matrix : DataArray
        Multiplication result

    """
    return xr.apply_ufunc(
        np.matmul,
        matrix_1,
        matrix_2,
        input_core_dims=[dims, dims],
        output_core_dims=[dims],
        dask="allowed",
    )


def inverse_matrix(
    matrix: xr.DataArray,
    check_finite: bool = False,
) -> xr.DataArray:
    r"""Calculate the inverse of an nxn matrix using `np.linalg.inv`.

    Parameters
    ----------
    matrix : DataArray
        Matrix that has at least two dimensions of "space_i", "space_j"
    check_finite : bool
        Whether to check if all entries are finite

    Returns
    -------
    inversed_matrix : DataArray
        Inversed matrix

    """

    def _inverse(data: NDArray) -> NDArray:
        inversed_matrix = inv(data.squeeze(), check_finite=check_finite)
        return np.expand_dims(inversed_matrix, axis=other_axes)

    matrix = matrix.copy()
    other_dims = tuple(
        filter(lambda item: item not in ["space_i", "space_j"], matrix.dims),
    )
    matrix = matrix.transpose("space_i", "space_j", *other_dims)  # type: ignore
    matrix = matrix.chunk({dim: 1 for dim in other_dims})
    other_axes = matrix.get_axis_num(other_dims)

    return xr.DataArray(
        name=matrix.name,
        data=matrix.data.map_blocks(
            _inverse,
            meta=np.array((), dtype=matrix.dtype),
        ),
        coords=matrix.coords,
        attrs=matrix.attrs,
    )


def quaternion_dot(q1: xr.DataArray, q2: xr.DataArray) -> xr.DataArray:
    r"""Quaternion dot.

    Compute the multiplication of two quaternions

    Parameters
    ----------
    q1, q2 : DataArray
        Quaternions

    Returns
    -------
    q : DataArray
        Resulting quaternion

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
