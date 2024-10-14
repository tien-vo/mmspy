r"""Provide FGM-specific validators for API query parameters."""

__all__ = [
    "convert_fgm_data_type",
]

from typing import TYPE_CHECKING

from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query


def convert_fgm_data_type(
    query: "Query",
    attribute: Attribute,
    data_type: str,  # noqa: ARG001
) -> None:
    r"""Convert FGM data type input to the proper values.

    The rules are as follows:
        - '*' -> None

    Parameters
    ----------
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``Attribute`` of ``query``.
    data_type : str
        Data type value.

    Returns
    -------
    transformed_data_type : str
        Transformed data type.

    """
    is_fgm = getattr(query, "instrument") == "fgm"
    is_data_type = attribute.name == "data_type"
    if not (is_fgm and is_data_type):
        return

    setattr(query, "_data_type", None)
