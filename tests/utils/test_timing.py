r"""Tests for functionality in `mmspy.utils.timing`.

.. todo::
    Add more tests
"""

import astropy.units as u
import numpy as np
import pytest
import xarray as xr

from mmspy.utils.timing import match_time_resolution


class TestMatchTimeResolution:
    r"""Tests for `match_time_resolution`."""

    time = np.arange("2024-01-01T00", "2024-01-02T01", dtype="datetime64[h]")
    data = xr.DataArray(
        data=np.arange(time.size),
        dims=("time",),
        coords={"time": time.astype("datetime64[ns]")},
    )

    @pytest.mark.parametrize("step", range(1, 25, 1))
    @pytest.mark.parametrize("average", [True, False])
    def test_quantity_input(self, step, average):
        r"""Test for target input as an astropy quantity."""
        data = match_time_resolution(self.data, u.Quantity(step, "h"), average)
        assert (data == self.data[slice(0, -1, step)]).all()
