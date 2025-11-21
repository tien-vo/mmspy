"""Dask-related utilities.

.. todo:: Add docstring.

"""

__all__ = ["enable_diagnostics"]

from dask.distributed import Client
import logging

log = logging.getLogger(__name__)


def enable_diagnostics(**kwargs):
    """Open `dask` dashboard for diagnostics."""
    client = Client(**kwargs)
    msg = f"Dask dashboard opened at {client.dashboard_link}"
    log.info(msg)
    return client
