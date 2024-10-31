r"""Tests for query parameters."""

from itertools import product as cross

import pytest
from attr import define, fields

from mmspy.api import Query


@define
class Case:
    parameter: str | None
    value: str | int | None
    exception: type[Exception] | None
    msg: str | None = "to be one of"
    instrument: str | None = None


@pytest.fixture
def query():
    return Query(data="science", data_level="l2")


data_cases = [
    Case("data", "science", None, None),
    Case("data", "something", ValueError),
]

probe_cases = [Case("probe", f"mms{i}", None, None) for i in range(1, 5)] + [
    Case("probe", probe, ValueError) for probe in ["some", "other", "value"]
]

instrument_cases = [
    Case("instrument", instrument, None, None)
    for instrument in ["mec", "fgm", "edp", "fpi", "feeps"]
] + [
    Case("instrument", "something", ValueError),
]

data_level_cases = [Case("data_level", "l2", None, None)] + [
    Case("data_level", level, ValueError)
    for level in ["l1", "l3", "or", "something", "else"]
]

data_rate_cases = (
    [
        Case("data_rate", data_rate, None, None, instrument=instrument)
        for data_rate in ["brst", "srvy"]
        for instrument in ["mec", "fgm", "feeps"]
    ]
    + [
        Case("data_rate", "fast", ValueError, instrument=instrument)
        for instrument in ["mec", "fgm", "feeps"]
    ]
    + [
        Case("data_rate", data_rate, None, None, instrument="edp")
        for data_rate in ["brst", "srvy", "fast", "slow"]
    ]
    + [
        Case("data_rate", data_rate, ValueError, None, instrument="edp")
        for data_rate in ["something", "else"]
    ]
    + [
        Case("data_rate", data_rate, None, None, instrument="fpi")
        for data_rate in ["brst", "srvy", "fast"]
    ]
    + [
        Case("data_rate", data_rate, ValueError, None, instrument="fpi")
        for data_rate in ["slow", "something", "else"]
    ]
)

data_type_cases = (
    [
        Case("data_type", data_type, None, None, instrument="mec")
        for data_type in ["t89d", "t89q", "ts04d"]
    ]
    + [
        Case("data_type", data_type, ValueError, instrument="mec")
        for data_type in ["something", "else"]
    ]
    + [
        Case("data_type", data_type, None, None, instrument="fgm")
        for data_type in [None, "bfield"]
    ]
    + [
        Case("data_type", data_type, ValueError, instrument="fgm")
        for data_type in ["anything", "but", "none"]
    ]
    + [
        Case("data_type", data_type, None, None, instrument="edp")
        for data_type in ["efield", "potential"]
    ]
    + [
        Case("data_type", data_type, ValueError, instrument="edp")
        for data_type in ["something", "else"]
    ]
    + [
        Case("data_type", f"{i}_{j}", None, None, instrument="fpi")
        for i, j in cross(
            ["ion", "elc"],
            ["distribution", "moments", "partial_moments"],
        )
    ]
    + [
        Case("data_type", data_type, ValueError, instrument="fpi")
        for data_type in ["ion-dist", "elc-idst", "or" "something", "else"]
    ]
    + [
        Case("data_type", data_type, None, None, instrument="feeps")
        for data_type in ["ion_distribution", "elc_distribution"]
    ]
    + [
        Case("data_type", data_type, ValueError, instrument="feeps")
        for data_type in ["something", "else"]
    ]
)


@pytest.mark.parametrize(
    "case",
    data_cases + probe_cases + instrument_cases + data_level_cases,
)
def test_independent_options(query, case):
    if case.exception is None:
        setattr(query, case.parameter, case.value)
        return

    with pytest.raises(case.exception, match=case.msg):
        setattr(query, case.parameter, case.value)


@pytest.mark.parametrize(
    "case",
    data_rate_cases + data_type_cases,
)
def test_dependent_options(query, case):
    query.instrument = case.instrument
    if case.exception is None:
        setattr(query, case.parameter, case.value)
        return

    with pytest.raises(case.exception, match=case.msg):
        setattr(query, case.parameter, case.value)
