r"""Tests for vector-related computations."""

import numpy as np
import pytest
import quaternionic
import xarray as xr
import dask.array as da

from mmspy.computation.vector import (
    inverse_matrix,
    matrix_multiply,
    quaternion_conjugate,
    quaternion_dot,
    vector_norm,
)


def random_nd_vector(n):
    r"""Generate a random array of 100 nd vectors."""
    return xr.DataArray(
        data=da.random.uniform(low=-10.0, high=10.0, size=(10, 10, n)),
        dims=("dim_1", "dim_2", "space"),
    )


def random_quaternion():
    r"""Generate a random array of 100 quaternions."""
    return xr.DataArray(
        data=da.random.uniform(low=-10.0, high=10.0, size=(10, 10, 4)),
        dims=("dim_1", "dim_2", "quaternion"),
        coords={"quaternion": ["w", "x", "y", "z"]},
    )


def random_matrix(n):
    r"""Generate a random array of 100 nxn matrices."""
    return xr.DataArray(
        data=da.random.uniform(low=-10.0, high=10.0, size=(10, 10, n, n)),
        dims=("dim_1", "dim_2", "space_i", "space_j"),
    )


@pytest.mark.parametrize("n", range(1, 6))
def test_nd_vector_norm(n):
    r"""Compare results from `xr.apply_ufunc` and manual calculations."""
    vector = random_nd_vector(n)
    norm_cal = vector_norm(vector, dim="space")
    norm_ref = da.linalg.norm(vector.data, axis=-1)

    assert (norm_cal == norm_ref).all()


@pytest.mark.parametrize("n", range(3, 6))
def test_matrix_inversion(n):
    r"""Compare results from `xr.apply_ufunc` and manual calculations."""
    M = random_matrix(n)
    M_inv_cal = inverse_matrix(M)

    for i in range(M.sizes["dim_1"]):
        for j in range(M.sizes["dim_2"]):
            M_inv_ref = da.linalg.inv(M.isel(dim_1=i, dim_2=j).data)

            assert (M_inv_ref == M_inv_cal.isel(dim_1=i, dim_2=j)).all()


@pytest.mark.parametrize("n", range(3, 6))
def test_matrix_multiplication(n):
    r"""Compare results with manual calculations using `np.matmul`."""
    M1 = random_matrix(n)
    M2 = random_matrix(n)
    M = matrix_multiply(M1, M2, dims=["space_i", "space_j"])
    for i in range(M.sizes["dim_1"]):
        for j in range(M.sizes["dim_2"]):
            M_ref = np.matmul(
                M1.isel(dim_1=i, dim_2=j).data,
                M2.isel(dim_1=i, dim_2=j).data,
            )
            assert np.isclose(M_ref, M.isel(dim_1=i, dim_2=j)).all()


def test_quaternion_dot():
    r"""Compare results with manual calculations using `quaternionic`."""
    q1 = random_quaternion()
    q2 = random_quaternion()
    qdot_cal = quaternion_dot(q1, q2)

    q1_ = quaternionic.array(q1.data)
    q2_ = quaternionic.array(q2.data)
    qdot_ref = q1_ * q2_

    assert (qdot_cal.data == qdot_ref.ndarray).all()


def test_quaternion_conjugate():
    r"""Compare results with manual calculations using `quaternionic`."""
    q = random_quaternion()

    qconjugate_cal = quaternion_conjugate(q)
    qconjugate_ref = quaternionic.array(q.data).conjugate()

    assert (qconjugate_cal.data == qconjugate_ref.ndarray).all()
