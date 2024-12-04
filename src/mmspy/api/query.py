r"""Provide interface for API query parameters."""

__all__ = ["Query"]

import pandas as pd
from attr import define, field
from attr.converters import optional, pipe
from pandas.core.tools.datetimes import DatetimeScalar

from .converters import shift_date
from .validators import convert_data_rate as _convert_data_rate
from .validators import (
    convert_edp_data_type,
    convert_feeps_data_type,
    convert_fgm_data_type,
    convert_fpi_data_type,
    convert_mec_data_type,
    one_of,
    time_in_range,
    time_range_is_valid,
)


@define
class Query:
    r"""Interface for query parameters.

    .. todo:: Clarify docstring.
    .. todo:: Attributes need docstring.
    .. todo:: Validate query payload together, instead of separately.

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
    shift_time_range: bool = field(default=False, repr=False, converter=bool)
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
        validator=[
            one_of(["mec", "fgm", "edp", "fpi", "feeps"]),
            _convert_data_rate,
        ],
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
            one_of(["brst", "srvy", "fast", "slow"]),
            _convert_data_rate,
        ],
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
            one_of(
                [
                    "bfield",
                    "efield",
                    "potential",
                    "t89d",
                    "t89q",
                    "ts04d",
                    "ion_distribution",
                    "ion_moments",
                    "ion_partial_moments",
                    "elc_distribution",
                    "elc_moments",
                    "elc_partial_moments",
                ],
            ),
            convert_mec_data_type,
            convert_fgm_data_type,
            convert_edp_data_type,
            convert_fpi_data_type,
            convert_feeps_data_type,
        ],
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

    start_date: DatetimeScalar = field(
        default=None,
        converter=pipe(optional(pd.to_datetime), shift_date),  # type: ignore[misc]
        validator=[
            time_in_range,
        ],
    )

    end_date: DatetimeScalar = field(
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
        fmt = "%Y-%m-%d-%H-%M-%S" if self.data_rate == "brst" else "%Y-%m-%d"
        return {
            "start_date": (
                self.start_date
                if self.start_date is None
                else self.start_date.strftime("%Y-%m-%d")  # type: ignore[union-attr]
            ),
            "end_date": (
                self.end_date
                if self.end_date is None
                else self.end_date.strftime(fmt)  # type: ignore[union-attr]
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

    def __repr__(self) -> str:
        r"""Repr for query class."""

        def _or_na(arg):  # noqa: ANN001,ANN202
            if arg is None:
                return "N/A"

            return arg

        return (
            "Query parameters:\n"
            f"  * start_date  : {_or_na(self.start_date)}\n"
            f"  * end_date    : {_or_na(self.end_date)}\n"
            f"  * probe       : {_or_na(self.probe)}\n"
            f"  * instrument  : {_or_na(self.instrument)}\n"
            f"  * data_rate   : {_or_na(self.data_rate)}\n"
            f"  * data_type   : {_or_na(self.data_type)}\n"
            f"  * data_level  : {_or_na(self.data_level)}\n"
            f"  * product     : {_or_na(self.product)}"
        )
