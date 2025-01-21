r"""Tests for functionalities in `mmspy.computation.transform`"""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from mmspy.computation.transform import (
    cartesian_to_fac,
    fac_to_cartesian,
    rotation_matrix,
)
from mmspy.computation.vector import matrix_multiply


def random_3d_vector(n):
    r"""Generate a random array of n 3d vectors."""
    return xr.DataArray(
        data=np.random.uniform(low=-10.0, high=10.0, size=(n, 3)),
        coords={
            "time": pd.date_range("2024-01-01", "2024-01-02", n),
            "rank_1": ["x", "y", "z"],
        },
        attrs={"units": ""},
    )


def test_fac_reversibility():
    r"""Check that `fac_to_cartesian` is the inverse of `cartesian_to_fac`."""
    B = random_3d_vector(1000)
    V = random_3d_vector(1000)

    V_fac = cartesian_to_fac(V, B, average=False)
    V_ = fac_to_cartesian(V_fac, B, average=False)
    assert np.allclose(V, V_)


def test_identity_transformation():
    r"""Check an identity transformation with `cartesian_to_fac`."""
    V = random_3d_vector(1000)

    coords = {"rank_1": ["x", "y", "z"]}
    e2 = xr.DataArray([0, 1, 0], coords=coords)
    e3 = (
        xr.DataArray([0, 0, 1], coords=coords)
        .expand_dims(time=V.sizes["time"])
        .assign_coords(time=V.time)
    )

    V1 = cartesian_to_fac(V, e3, reference_vector=e2, average=False)
    V2 = fac_to_cartesian(V, e3, reference_vector=e2, average=False)
    assert np.allclose(V, V1)
    assert np.allclose(V, V2)


@pytest.mark.parametrize(
    "case",
    [
        {
            "e2": np.array([1, 0, 0]),
            "e3": np.array([1, 1, 0]),
            "V": np.array(
                [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                ]
            ),
            "V_expected": np.array(
                [
                    [0, 0.7071, 0.7071],
                    [0, -0.7071, 0.7071],
                    [1, 0, 0],
                ]
            ),
        },
        {
            "e2": np.array([1, 0, 0]),
            "e3": np.array([-1, 1, 0]),
            "V": np.array(
                [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                ]
            ),
            "V_expected": np.array(
                [
                    [0, 0.7071, -0.7071],
                    [0, 0.7071, 0.7071],
                    [1, 0, 0],
                ]
            ),
        },
        {
            "e2": np.array([-1, 0, 0]),
            "e3": np.array([-1, 1, 0]),
            "V": np.array(
                [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1],
                ]
            ),
            "V_expected": np.array(
                [
                    [0, -0.7071, -0.7071],
                    [0, -0.7071, 0.7071],
                    [-1, 0, 0],
                ]
            ),
        },
    ],
)
def test_unit_vector_rotation(case):
    r"""Check that unit vectors are rotated correctly."""
    V = random_3d_vector(3)
    V[...] = case["V"]

    coords = {"rank_1": ["x", "y", "z"]}
    e2 = xr.DataArray(case["e2"], coords=coords)
    e3 = (
        xr.DataArray(case["e3"], coords=coords)
        .expand_dims(time=V.sizes["time"])
        .assign_coords(time=V.time)
    )

    V_ = cartesian_to_fac(V, e3, reference_vector=e2, average=False)
    assert np.allclose(V_, case["V_expected"])


def test_orthogonality():
    r"""Check that the rotation matrix is orthogonal."""
    V1 = random_3d_vector(1000)
    V2 = random_3d_vector(1000)
    M = rotation_matrix(V1, V2)
    Mt = M.rename(i="j", j="i").transpose(..., "i", "j")
    left = matrix_multiply(M, Mt, dims=["i", "j"])
    right = matrix_multiply(Mt, M, dims=["i", "j"])
    for i in range(M.sizes["time"]):
        assert np.isclose(np.identity(3), left.isel(time=i)).all()
        assert np.isclose(np.identity(3), right.isel(time=i)).all()
