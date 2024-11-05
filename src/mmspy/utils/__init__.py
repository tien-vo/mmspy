r"""Provide generic utility functions."""

__all__ = [
    "first_valid_index",
    "last_valid_index",
    "force_odd",
    "match_time_resolution",
    "sampling_information",
    "is_quantified",
]

from .index import first_valid_index, last_valid_index
from .timing import force_odd, match_time_resolution, sampling_information
from .units import is_quantified
