r"""Tests for vector-related computations."""

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from mmspy.computation.vector import (
    cross,
    matrix_multiply,
    quaternion_conjugate,
    quaternion_dot,
    vector_norm,
)


def random_vector(n):
    r"""Generate a random array of 100 nd vectors."""
    return xr.DataArray(
        data=da.random.uniform(low=-10.0, high=10.0, size=(10, 10, n)),
        dims=("dim_1", "dim_2", "space"),
    )


def random_qvector(n):
    r"""Generate a random quantified array of 100 nd vectors."""
    return random_vector(n).pint.quantify("km")


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


def random_qmatrix(n):
    r"""Generate a random quantified array of 100 nxn matrices."""
    return random_matrix(n).pint.quantify("km")


@pytest.mark.parametrize("generate", [random_vector, random_qvector])
def test_cross_product(generate):
    r"""Compare results from `xr.apply_ufunc` and manual calculations."""
    vector_1 = generate(3)
    vector_2 = generate(3)

    cross_cal = cross(vector_1, vector_2, dim="space")
    cross_ref = np.cross(
        vector_1.data.compute(),
        vector_2.data.compute(),
        axis=-1,
    )
    assert (cross_cal == cross_ref).all()


@pytest.mark.parametrize("n", range(1, 6))
@pytest.mark.parametrize("generate", [random_vector, random_qvector])
def test_vector_norm(n, generate):
    r"""Compare results from `xr.apply_ufunc` and manual calculations."""
    vector = generate(n)

    norm_cal = vector_norm(vector, dim="space")
    norm_ref = da.linalg.norm(vector.data, axis=-1)
    assert (norm_cal == norm_ref).all()


@pytest.mark.parametrize("n", range(3, 6))
@pytest.mark.parametrize("generate", [random_matrix, random_qmatrix])
def test_matrix_multiplication(n, generate):
    r"""Compare results with manual calculations using `np.matmul`."""
    matrix_1 = generate(n)
    matrix_2 = generate(n)

    matrix_ref = np.matmul(matrix_1.data, matrix_2.data)
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
