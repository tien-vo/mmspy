"""Dask-related utilities.

.. todo:: Add docstring.

"""

__all__ = ["enable_diagnostics"]

from dask.distributed import Client
import logging

log = logging.getLogger(__name__)


def enable_diagnostics():
    """Open `dask` dashboard for diagnostics."""
    client = Client()
    msg = f"Dask dashboard opened at {client.dashboard_link}"
    log.info(msg)
    return client
