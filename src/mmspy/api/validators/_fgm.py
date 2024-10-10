r"""Provide FGM-specific validators for API query parameters."""

__all__ = [
    "reset_data_type",
]

from typing import TYPE_CHECKING

from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query


def reset_data_type(
    query: "Query",
    attribute: Attribute,
    value: str,
) -> None:
    r"""Reset `query.data_type` to ``None`` if the instrument is 'fgm'.

    Parameters
    ----------
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``Attribute`` of ``query``.
    value : str
        Input value.

    """
    if value == "fgm" and attribute.name == "instrument":
        setattr(query, "data_type", None)
