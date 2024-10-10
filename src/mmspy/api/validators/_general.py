r"""General validators."""

__all__ = [
    "one_of",
    "convert_data_rate",
]

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from attr import Attribute

if TYPE_CHECKING:
    from mmspy.api.query import Query

log = logging.getLogger(__name__)


def one_of(
    options: list[str | None] | None = None,
    from_metadata: bool = False,
    allow_optional: bool = True,
) -> Callable[["Query", Attribute, str], None]:
    r"""Check if an input is one of the given options.

    Parameters
    ----------
    options : list of str or None
        Valid options.
    from_metadata : bool
        Whether to also add options from ``attribute.metadata``.
    allow_optional : bool
        Whether to allow ``None`` in the list of ``options``.

    Returns
    -------
    validator : Callable
        Validator for parameters defined with `~attr.field` [1]_

    Raises
    ------
    ValueError
        If ``option`` is not one of the given ``options``.

    References
    ----------
    .. [1] https://www.attrs.org/en/stable/examples.html#validators

    """

    def validator(query: "Query", attribute: Attribute, option: str) -> None:
        instrument = getattr(query, "instrument")
        ext_options: list[str | None] = [] if options is None else options

        if allow_optional:
            ext_options += [None]

        if from_metadata and instrument is not None:
            ext_options += attribute.metadata["options"][instrument]

        if option not in ext_options:
            if None in ext_options:
                ext_options.remove(None)
            msg = (
                f"Expected `Query.{attribute.name}` ({option!r}) to be "
                f"one of {ext_options!r}."
            )
            raise ValueError(msg)

    return validator


def convert_data_rate(
    query: "Query",
    attribute: Attribute,
    data_rate: str,
) -> None:
    r"""Convert `srvy` data rate to `fast` for selected instruments.

    Parameters
    ----------
    query : Query
        `~mmspy.Query` instance in which ``time`` is defined.
    attribute : Attribute
        ``Attribute`` of ``query``.
    data_rate : str
        Input data rate value.

    """
    is_data_rate = attribute.name == "data_rate"
    is_srvy = data_rate == "srvy"
    is_edp_or_fpi = getattr(query, "instrument") in ["edp", "fpi"]
    setattr(
        query,
        "_data_rate",
        "fast" if is_data_rate and is_srvy and is_edp_or_fpi else data_rate,
    )
