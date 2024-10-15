"""Tests for functionality in `mmspy.utils.index`."""

import numpy as np
import pytest
import xarray as xr

from mmspy.utils.index import first_valid_index, last_valid_index


class TestFindValidIndex:
    data_np = np.array(
        [
            [np.nan, 1, 1, 0.5, np.nan, np.nan, np.nan],
            [np.nan, 1, 1, np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, 1, np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, 1, 0.5, 0.25, 0.125, 0.075],
            [np.nan, 1, 1, 0.25, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            [np.nan, np.nan, np.nan, 0.5, np.nan, np.nan, np.nan],
        ]
    )
    data_xr = xr.DataArray(data=data_np, dims=("x", "y"))

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            (0, [0, 4, 4, 6, 3, 3, 3]),
            (1, [3, 2, 2, 6, 3, 0, 3]),
            (-1, [3, 2, 2, 6, 3, 0, 3]),
            (-2, [0, 4, 4, 6, 3, 3, 3]),
        ],
    )
    def test_last_index_np(self, axis, expected):
        indices = last_valid_index(self.data_np, axis)
        assert (indices == np.array(expected)).all()

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            (0, [0, 4, 4, 6, 3, 3, 3]),
            (1, [3, 2, 2, 6, 3, 0, 3]),
            (-1, [3, 2, 2, 6, 3, 0, 3]),
            (-2, [0, 4, 4, 6, 3, 3, 3]),
            ("x", [0, 4, 4, 6, 3, 3, 3]),
            ("y", [3, 2, 2, 6, 3, 0, 3]),
        ],
    )
    def test_last_index_xr(self, axis, expected):
        indices = last_valid_index(self.data_xr, axis)
        assert (indices == np.array(expected)).all()

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            (0, [0, 0, 0, 0, 3, 3, 3]),
            (1, [1, 1, 2, 2, 1, 0, 3]),
            (-1, [1, 1, 2, 2, 1, 0, 3]),
            (-2, [0, 0, 0, 0, 3, 3, 3]),
        ],
    )
    def test_first_index_np(self, axis, expected):
        indices = first_valid_index(self.data_np, axis)
        assert (indices == np.array(expected)).all()

    @pytest.mark.parametrize(
        ("axis", "expected"),
        [
            (0, [0, 0, 0, 0, 3, 3, 3]),
            (1, [1, 1, 2, 2, 1, 0, 3]),
            (-1, [1, 1, 2, 2, 1, 0, 3]),
            (-2, [0, 0, 0, 0, 3, 3, 3]),
            ("x", [0, 0, 0, 0, 3, 3, 3]),
            ("y", [1, 1, 2, 2, 1, 0, 3]),
        ],
    )
    def test_first_index_xr(self, axis, expected):
        indices = first_valid_index(self.data_xr, axis)
        assert (indices == np.array(expected)).all()
