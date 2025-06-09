r"""Provide generic utility functions."""

__all__ = [
    "force_odd",
    "match_time_resolution",
    "sampling_information",
    "is_quantified",
]

from mmspy.utils.timing import (
    force_odd,
    match_time_resolution,
    sampling_information,
)
from mmspy.utils.units import is_quantified
