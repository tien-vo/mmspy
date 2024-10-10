r""".. todo:: Write docstring."""

from attr import define

from .query import Query
from .request import Request
from .sync import Synchronizer


@define
class MMS:
    r"""Manager for MMS data.

    .. todo:: Write docstring
    """

    query: Query = Query(
        data="science",
        data_level="l2",
    )
    request: Request = Request(query)
    sync: Synchronizer = Synchronizer(query, request)
