r"""Provide validators for API time query parameters."""

__all__ = [
    "time_in_range",
    "time_range_is_valid",
]

from typing import TYPE_CHECKING

import pandas as pd
from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query


def time_in_range(
    query: "Query",
    attribute: Attribute,
    time: pd.Timestamp,
) -> None:
    r"""Validate input time value.

    Check that ``time`` input is in a given range [1]_.

    Parameters
    ----------
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``time`` attribute of ``query``.
    time : Timestamp
        Time stamp value to set to ``attribute``.

    Raises
    ------
    ValueError
        If ``time`` is not in range.

    References
    ----------
    .. [1] https://www.attrs.org/en/stable/examples.html#validators

    """
    if time is None:
        return

    valid_start_date, valid_end_date = query.valid_time_range
    if time < valid_start_date or time > valid_end_date:
        msg = (
            f"{attribute.name!r} ({time}) is out of valid range "
            f"({valid_start_date} - {valid_end_date})"
        )
        raise ValueError(msg)


def time_range_is_valid(
    query: "Query",
    attribute: Attribute,
    time: pd.Timestamp,
) -> None:
    r"""Validate time range.

    Check that the resulting time range
    (``query.start_date`` - ``query.end_date``) is valid for a given
    ``time`` input [1]_.

    Parameters
    ----------
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``time`` attribute of ``query``.
    time : Timestamp
        Time stamp value to set to ``attribute``.

    Raises
    ------
    ValueError
        If ``query.end_date`` < ``query.start_date`` or
        ``query.start_date`` > ``query.end_date``.

    References
    ----------
    .. [1] https://www.attrs.org/en/stable/examples.html#validators

    """
    if time is None:
        return

    match attribute.name:
        case "start_date":
            if (end_date := getattr(query, "end_date")) is None:
                return
            if time > end_date:
                msg = (
                    f"Start date ({time}) must be earlier than the "
                    f"current end date ({end_date})."
                )
                raise ValueError(msg)
        case "end_date":
            if (start_date := getattr(query, "start_date")) is None:
                return
            if time < start_date:
                msg = (
                    f"End date ({time}) must be later than the "
                    f"current start date ({start_date})."
                )
                raise ValueError(msg)
        case _:
            msg = "Validator only applicable to time parameters."
            raise ValueError(msg)
