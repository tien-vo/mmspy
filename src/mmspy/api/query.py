r"""Provide interface for API query parameters."""

__all__ = [
    "Query",
]

from itertools import product as cross

import pandas as pd
from attr import define, field
from attr.converters import optional, pipe

from .converters import shift_date
from .validators import convert_data_rate as _convert_data_rate
from .validators import (
    convert_edp_data_type,
    convert_feeps_data_type,
    convert_fgm_data_type,
    convert_fpi_data_type,
    one_of,
    time_in_range,
    time_range_is_valid,
)


@define
class Query:
    r"""Interface for query parameters.

    .. todo:: Clarify docstring.

    Parameters
    ----------
    data : {'science', 'ancillary', 'hk'}, optional
        Type of query.
    probe : {'mms1', 'mms2', 'mms3', 'mms4'}, optional
        Probe name (API equivalence: sc_id)
    instrument: {'mec', 'fgm', 'edp', 'fpi', 'feeps'}, optional
        Instrument name (API equivalence: instrument_id)
    data_rate: {'brst', 'srvy', 'fast', 'slow'}, optional
        Data rate mode (API equivalence: data_rate_mode)
    data_type: str, optional
        Data descriptor (API equivalence: descriptor)
    data_level: str, optional
        Data level (API equivalence: data_level)
    product: str, optional
        Ancillary product (API equivalence: product)
    start_date, end_date : date_like, optional
        Query start and end dates (API equivalence: start_date, end_date)

    """

    valid_time_range = (pd.Timestamp("2015-09-01"), pd.Timestamp.today())

    # ---- Flags
    shift_time_range: bool = field(default=True, repr=False, converter=bool)
    convert_data_rate: bool = field(default=True, repr=False, converter=bool)

    # ---- Query parameters
    data: str = field(
        default=None,
        converter=optional(str),
        validator=one_of(["science"]),
    )

    probe: str = field(
        default=None,
        converter=optional(str),
        validator=one_of(["mms1", "mms2", "mms3", "mms4"]),
    )

    instrument: str = field(
        default=None,
        converter=optional(str),
        validator=one_of(["mec", "fgm", "edp", "fpi", "feeps"]),
    )

    _data_rate: str = field(
        init=False,
        repr=False,
        default=None,
        converter=optional(str),
    )

    data_rate: str = field(
        default=None,
        converter=optional(str),
        validator=[
            one_of(from_metadata=True),
            _convert_data_rate,
        ],
        metadata={
            "options": {
                "mec": ["brst", "srvy"],
                "fgm": ["brst", "srvy"],
                "edp": ["brst", "srvy", "fast", "slow"],
                "fpi": ["brst", "srvy", "fast"],
                "feeps": ["brst", "srvy"],
            },
        },
    )

    _data_type: str = field(
        init=False,
        repr=False,
        default=None,
        converter=optional(str),
    )

    data_type: str = field(
        default=None,
        converter=optional(str),
        validator=[
            one_of(from_metadata=True),
            convert_fgm_data_type,
            convert_edp_data_type,
            convert_fpi_data_type,
            convert_feeps_data_type,
        ],
        metadata={
            "options": {
                "mec": ["epht89d", "epht89q", "ephts04d"],
                "fgm": ["bfield"],
                "edp": ["efield", "potential"],
                "fpi": [
                    f"{i}_{j}"
                    for i, j in cross(
                        ["ion", "elc"],
                        ["distribution", "moments", "partial_moments"],
                    )
                ],
                "feeps": ["ion_distribution", "elc_distribution"],
            },
        },
    )

    data_level: str = field(
        default=None,
        converter=optional(str),
        validator=one_of(["l2"]),
    )

    product: str = field(
        default=None,
        converter=optional(str),
        validator=one_of([]),
    )

    start_date: pd.Timestamp = field(
        default=None,
        converter=pipe(optional(pd.to_datetime), shift_date),  # type: ignore[misc]
        validator=[
            time_in_range,
            time_range_is_valid,
        ],
    )

    end_date: pd.Timestamp = field(
        default=None,
        converter=pipe(optional(pd.to_datetime), shift_date),  # type: ignore[misc]
        validator=[
            time_in_range,
            time_range_is_valid,
        ],
    )

    @property
    def payload(self) -> dict[str, str | None]:
        r"""HTTP payload constructed from query parameters."""
        fmt = "%Y-%m-%d-%H-%M-%S"
        return {
            "start_date": (
                self.start_date
                if self.start_date is None
                else self.start_date.strftime(fmt)
            ),
            "end_date": (
                self.end_date
                if self.end_date is None
                else self.end_date.strftime(fmt)
            ),
            "sc_id": self.probe,
            "instrument_id": self.instrument,
            "data_rate_mode": self._data_rate,
            "descriptor": self._data_type,
            "data_level": self.data_level,
            "product": self.product,
        }

    @property
    def metadata(self) -> dict[str, str]:
        r"""Metadata from query parameters."""
        return {
            "probe": self.probe,
            "instrument": self.instrument,
            "data_rate": self.data_rate,
            "_data_rate": self._data_rate,
            "data_type": self.data_type,
            "_data_type": str(self._data_type),
            "data_level": self.data_level,
            "product": self.product,
        }
