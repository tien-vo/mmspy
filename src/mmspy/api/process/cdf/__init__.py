r"""Process information from CDF files."""

__all__ = [
    "process_cdf_epoch",
    "process_cdf_metadata",
]

from .epoch import process_cdf_epoch
from .metadata import process_cdf_metadata
