r"""Provide FPI-specific validators for API query parameters."""

__all__ = [
    "convert_fpi_data_type",
]

from typing import TYPE_CHECKING

from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query


def convert_fpi_data_type(
    query: "Query",
    attribute: Attribute,
    data_type: str,
) -> None:
    r"""Convert FPI data type input to the proper values.

    The rules are as follows:
        - '*_distribution' -> '-dist'
        - '*_moments' -> '-moms'
        - '*_partial_moments' -> '-partmoms'
        - 'ion' -> 'dis'
        - 'elc' -> 'des'

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
    is_fpi = getattr(query, "instrument") == "fpi"
    is_data_type = attribute.name == "data_type"
    if not (is_fpi and is_data_type):
        return

    setattr(
        query,
        "_data_type",
        (
            data_type.replace("_distribution", "-dist")
            .replace("_partial_moments", "-partmoms")
            .replace("_moments", "-moms")
            .replace("ion", "dis")
            .replace("elc", "des")
            if data_type is not None
            else data_type
        ),
    )
