r"""Define utility functions for unit registry definition."""

__all__ = [
    "_get_cache_path",
    "_attach_exponential_symbol",
]

import functools
import re
from collections.abc import Callable
from pathlib import Path


def _get_cache_path() -> Path:
    r"""Define and set up cache directory."""
    path = Path("~").expanduser() / ".cache" / "mmspy" / "units"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _attach_exponential_symbol() -> Callable[[str], str]:
    r"""Attach '**' to unit strings.

    Adopted from ``cf-xarray`` [1]_.

    References
    ----------
    .. [1] https://github.com/xarray-contrib/cf-xarray/blob/22ee634433b988bd101e45e9f9728bbf59915259/cf_xarray/units.py#L63-L76

    """
    patterns = (
        r"(?<=[A-Za-z])"
        r"(?![A-Za-z])"
        r"(?<![0-9\-][eE])"
        r"(?<![0-9\-])"
        r"(?=[0-9\-])"
    )
    return functools.partial(re.compile(patterns).sub, "**")
