r"""Provide EDP-specific validators for API query parameters."""

__all__ = [
    "convert_edp_data_type",
]

from typing import TYPE_CHECKING

from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query


def convert_edp_data_type(
    query: "Query",
    attribute: Attribute,
    data_type: str,
) -> None:
    r"""Convert EDP data type input to the proper values.

    The rules are as follows:
        - 'efield' -> 'dce'
        - 'potential' -> 'scpot'

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
    is_edp = getattr(query, "instrument") == "edp"
    is_data_type = attribute.name == "data_type"
    if not (is_edp and is_data_type):
        return

    setattr(
        query,
        "_data_type",
        (
            data_type.replace("efield", "dce").replace("potential", "scpot")
            if data_type is not None
            else data_type
        ),
    )
