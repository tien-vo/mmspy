from __future__ import annotations

from importlib import import_module

import numpy as np
import pytest
from cdflib.epochs import CDFepoch

from mmspy.api.processors.cdf.load import (
    _convert_cdf_time_sentinels,
    _sentinel_aware_cdf_time_conversion,
)


def test_tt2000_sentinels_become_nat() -> None:
    values = np.asarray(
        [
            0,
            CDFepoch.FILLED_TT2000_VALUE,
            CDFepoch.DEFAULT_TT2000_PADVALUE,
        ],
        dtype=np.int64,
    )

    result = _convert_cdf_time_sentinels(
        values,
        converter=CDFepoch.to_datetime,
    )

    expected_valid = np.asarray(CDFepoch.to_datetime(np.int64(0))).reshape(-1)[0]
    assert result[0] == expected_valid
    assert np.isnat(result[1:]).all()
    assert result.dtype == np.dtype("datetime64[ns]")


def test_valid_tt2000_values_are_unchanged() -> None:
    values = np.asarray([0, 1_000_000_000], dtype=np.int64)

    result = _convert_cdf_time_sentinels(
        values,
        converter=CDFepoch.to_datetime,
    )

    np.testing.assert_array_equal(result, CDFepoch.to_datetime(values))


def test_noninteger_values_are_delegated() -> None:
    marker = RuntimeError("delegated")

    def converter(values: object) -> object:
        raise marker

    with pytest.raises(RuntimeError) as caught:
        _convert_cdf_time_sentinels(1.5, converter=converter)

    assert caught.value is marker


@pytest.mark.parametrize("raise_inside", [False, True])
def test_conversion_context_restores_descriptor(raise_inside: bool) -> None:
    converter_module = import_module("cdflib.xarray.cdf_to_xarray")
    epoch_class = converter_module.cdfepoch
    original_descriptor = epoch_class.__dict__["to_datetime"]
    original_converter = epoch_class.to_datetime

    if raise_inside:
        with pytest.raises(RuntimeError, match="failure inside context"):
            with _sentinel_aware_cdf_time_conversion():
                assert epoch_class.__dict__["to_datetime"] is not original_descriptor
                raise RuntimeError("failure inside context")
    else:
        with _sentinel_aware_cdf_time_conversion():
            assert epoch_class.__dict__["to_datetime"] is not original_descriptor

    assert epoch_class.__dict__["to_datetime"] is original_descriptor
    assert epoch_class.to_datetime == original_converter
