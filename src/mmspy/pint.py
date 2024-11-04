r"""Unit support with `pint`."""

__all__ = ["units"]

import cf_xarray.units  # noqa: F401
import pint_xarray  # noqa: F401
from pint import application_registry as units

units.formatter.default_format = "cf"
