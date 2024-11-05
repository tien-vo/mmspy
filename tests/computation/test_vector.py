r"""Tests for vector-related computations."""

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from mmspy.computation.vector import (
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
def test_matrix_multiplication(n):
    r"""Compare results with manual calculations using `np.matmul`."""
    matrix_1 = random_matrix(n)
    matrix_2 = random_matrix(n)

    matrix_ref = da.matmul(matrix_1, matrix_2)
    matrix_cal = matrix_multiply(
        matrix_1,
        matrix_2,
        dims=("space_i", "space_j"),
    )
    assert (matrix_cal == matrix_ref).all()


def test_quaternion_dot():
    r"""Compare results with manual calculations using `quaternionic`."""
    quaternionic = pytest.importorskip("quaternionic")

    q1 = random_quaternion()
    q2 = random_quaternion()

    qdot_ref = quaternionic.array(q1.data) * quaternionic.array(q2.data)
    qdot_cal = quaternion_dot(q1, q2)
    assert (qdot_cal == qdot_ref.ndarray).all()


def test_quaternion_conjugate():
    r"""Compare results with manual calculations using `quaternionic`."""
    quaternionic = pytest.importorskip("quaternionic")

    q = random_quaternion()

    qconjugate_cal = quaternion_conjugate(q)
    qconjugate_ref = quaternionic.array(q.data).conjugate()
    assert (qconjugate_cal == qconjugate_ref.ndarray).all()
