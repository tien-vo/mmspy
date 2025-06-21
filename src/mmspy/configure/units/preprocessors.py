"""Preprocessors for unit strings."""

__all__ = ["_get_fits_units_processor"]

import functools
import re
from collections.abc import Callable


def _get_fits_units_processor() -> Callable[[str], str]:
    """Attach '**' to unit strings.

    Adopted from ``cf-xarray`` [1]_. FITS-compliant unit strings, for
    example, 'cm-2 s-1 keV-1' parses as 'cm**(-2) s**(-1) keV**(-1)'.

    References
    ----------
    .. [1] :cf_xarray:`units.py#L63-L76`

    """
    patterns = (
        r"(?<=[A-Za-z])"
        r"(?![A-Za-z])"
        r"(?<![0-9\-][eE])"
        r"(?<![0-9\-])"
        r"(?=[0-9\-])"
    )
    return functools.partial(re.compile(patterns).sub, "**")
