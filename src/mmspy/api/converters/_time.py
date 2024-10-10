r"""Provide converters for time parameter for API query."""

__all__ = [
    "shift_date",
]

from collections.abc import Callable
from typing import TYPE_CHECKING

import pandas as pd
from attr import Attribute

from ._utils import wrap_converter

if TYPE_CHECKING:
    from mmspy.api.query import Query


@wrap_converter(
    signature=Callable[[pd.Timestamp], pd.Timestamp],
    takes_self=True,
    takes_field=True,
)
def shift_date(
    time: pd.Timestamp,
    query: "Query",
    attribute: Attribute,
) -> pd.Timestamp:
    r"""Shift start and end date to match PySPEDAS behaviors [1]_ [2]_.

    Parameters
    ----------
    time : Timestamp
        Time stamp value to set to ``attribute``.
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``time`` attribute of ``query``.

    Returns
    -------
    shifted_time : Timestamp
        Shifted time.

    Raises
    ------
    ValueError
        If ``attribute.name`` is neither 'start_date' nor 'end_date'

    References
    ----------
    .. [1] :pyspedas_time_shift:`mms_load_data_spdf.py#L71-L75`
    .. [2] :pyspedas_time_shift:`mms_load_data.py#L80-L87`

    """
    if time is None:
        return None

    if not query.FLAG_SHIFT_TIME_RANGE:
        return time

    one_second = pd.Timedelta(1, "s")
    zero_minutes = pd.Timedelta(0, "m")
    five_minutes = pd.Timedelta(5, "m")
    ten_minutes = pd.Timedelta(10, "m")

    is_brst = getattr(query, "data_rate") == "brst"
    close_to_day_start = (time - pd.to_datetime(time.date())) < ten_minutes
    match attribute.name:
        case "start_date":
            shift = (
                zero_minutes
                if not is_brst
                else ten_minutes if close_to_day_start else five_minutes
            )
        case "end_date":
            shift = one_second
        case _:
            msg = "Validator only applicable to time parameters."
            raise ValueError(msg)

    return time - shift
