r"""Provides functionality for coordinate transformations."""

__all__ = [
    "rotation_matrix",
    "cartesian_to_fac",
    "fac_to_cartesian",
    "quaternion_rotate",
]

import numpy as np
import xarray as xr

from mmspy.computation.vector import cross, quaternion_conjugate, quaternion_dot
from mmspy.utils.timing import match_time_resolution


def rotation_matrix(
    vector_1: xr.DataArray,
    vector_2: xr.DataArray,
) -> xr.DataArray:
    r"""Rotation matrix.

    Construct a rotation matrix into a frame spanned by the basis
    B = {V1xV2, V2x(V1xV2), V2}.

    Parameters
    ----------
    vector_1 : DataArray
        Vector V1
    vector_2 : DataArray
        Vector V2

    Returns
    -------
    matrix : DataArray
        Rotation matrix to transform from frame A -> B.

    """
    vector_1 = vector_1.copy()
    vector_2 = vector_2.copy()

    e3 = vector_2 / vector_2.rank_1.magnitude
    e1 = cross(vector_1, vector_2, dim="space_rank_1")
    e1 = e1 / e1.rank_1.magnitude  # type: ignore
    e2 = cross(e3, e1, dim="space_rank_1")

    matrix = (
        xr.combine_nested(
            [
                e1.rank_1.tensor,  # type: ignore
                e2.rank_1.tensor,  # type: ignore
                e3.rank_1.tensor,  # type: ignore
            ],
            concat_dim="space_i",
        )
        .chunk(space_i=3, space_j=3)
        .transpose(..., "space_i", "space_j")
    )
    matrix = matrix.assign_coords(space_i=matrix.space_j.values)
    return xr.DataArray(matrix)


def cartesian_to_fac(
    da: xr.DataArray,
    magnetic_field: xr.DataArray,
    reference_vector: xr.DataArray = xr.DataArray(
        np.array([1, 0, 0], dtype="f4"),
        coords={"space_rank_1": ["x", "y", "z"]},
    ),
    average: bool = True,
) -> xr.DataArray:
    r"""Cartesian to field-aligned coordinate transformation.

    Convert a vector to field-aligned coordinates from magnetic field
    data and a reference vector.

    Parameters
    ----------
    da : DataArray
        Vector with a 'space_rank_1' dimension
    magnetic_field : DataArray
        Magnetic field
    reference_vector: DataArray
        A reference vector `V` such that e_perp_1 ~ V x B
    average : bool
        Whether to average when resampling magnetic field data onto
        input vector

    Returns
    -------
    da_fac : DataArray
        Vector in field-aligned coordinates

    """
    da = da.copy()
    magnetic_field = match_time_resolution(
        magnetic_field.copy(),
        da,
        average=average,
    )
    M = rotation_matrix(reference_vector, magnetic_field)

    return (
        xr.dot(M, da.rank_1.tensor, dim="space_j")
        .rename(space_i="space_rank_1")
        .assign_coords(space_rank_1=da.space_rank_1)
        .assign_attrs(da.attrs)
        .transpose(*da.dims)
    )


def fac_to_cartesian(
    da: xr.DataArray,
    magnetic_field: xr.DataArray,
    reference_vector: xr.DataArray = xr.DataArray(
        np.array([1, 0, 0], dtype="f4"),
        coords={"space_rank_1": ["x", "y", "z"]},
    ),
    average: bool = True,
) -> xr.DataArray:
    r"""Cartesian to field-aligned coordinate transformation.

    Convert a vector to field-aligned coordinates from magnetic field
    data and a reference vector.

    Parameters
    ----------
    da : DataArray
        Vector with a 'space_rank_1' dimension
    magnetic_field : DataArray
        Magnetic field
    reference_vector: DataArray
        A reference vector `V` such that e_perp_1 ~ V x B
    average : bool
        Whether to average when resampling magnetic field data onto
        input vector

    Returns
    -------
    da_cartesian : DataArray
        Vector in cartesian coordinates

    """
    da = da.copy()
    magnetic_field = match_time_resolution(
        magnetic_field.copy(),
        da.time,
        average=average,
    )
    M = (
        rotation_matrix(reference_vector, magnetic_field)
        .rename(space_i="space_j", space_j="space_i")
        .transpose(..., "space_i", "space_j")
    )

    return (
        xr.dot(M, da.rename(space_rank_1="space_j"), dim="space_j")
        .rename(space_i="space_rank_1")
        .assign_coords(space_rank_1=da.space_rank_1)
        .assign_attrs(da.attrs)
        .transpose(*da.dims)
    )


def quaternion_rotate(
    vector: xr.DataArray,
    quaternion: xr.DataArray,
    inverse: bool = False,
) -> xr.DataArray:
    r"""3D rotation using quaternions.

    Rotate vector V given quaternion Q

    Parameters
    ----------
    vector: xarray.DataArray
        Vector to rotate, must have 3 spatial dimensions and be in the
        same coordinates as Q depending on whether this is an inverse
        operation.
    quaternion: xarray.DataArray
        Quaternion data
    inverse: bool
        If true, rotated_vector = Q.V.Q^\dagger, otherwise
        rotated_vector = Q^\dagger.V.Q

    Return
    ------
    rotated_vector: xarray.DataArray
        Rotated vector with the same attributes as input vector

    """
    if inverse:
        in_coord = "TO_COORDINATE_SYSTEM"
        out_coord = "COORDINATE_SYSTEM"
    else:
        in_coord = "COORDINATE_SYSTEM"
        out_coord = "TO_COORDINATE_SYSTEM"

    # ---- Sanity checks
    assert (
        "space_rank_1" in vector.coords
    ), "Input vector must have spatial coordinates"
    assert (
        "quaternion" in quaternion.coords
    ), "Input quaternion must have quaternion coordinates"
    assert (
        vector.attrs["COORDINATE_SYSTEM"] == quaternion.attrs[in_coord]
    ), "Inputs must be in the same coordinate system"

    quaternion = quaternion.copy()
    vector = (
        vector.copy()
        .reindex({"space_rank_1": ["w", "x", "y", "z"]}, fill_value=0.0)
        .rename(space_rank_1="quaternion")
    )

    if inverse:
        quaternion = quaternion_conjugate(quaternion)

    rotated_vector = (
        quaternion_dot(
            quaternion,
            quaternion_dot(
                vector,
                quaternion_conjugate(quaternion),
            ),
        )
        .sel(quaternion=["x", "y", "z"])
        .rename(quaternion="space_rank_1")
    )
    rotated_vector.attrs.update(
        vector.attrs,
        COORDINATE_SYSTEM=quaternion.attrs[out_coord],
    )

    return rotated_vector
