r"""Process information from CDF files."""

__all__ = ["process_cdf_time", "process_cdf_metadata", "load_cdf"]

from mmspy.api.processors.cdf.load import load_cdf
from mmspy.api.processors.cdf.metadata import (
    process_cdf_metadata,
    process_cdf_time,
)
