r"""Unit support with `pint`."""

__all__ = ["unit_registry"]

import cf_xarray.units  # noqa: F401
import pint_xarray  # noqa: F401
from pint import application_registry as unit_registry

unit_registry.formatter.default_format = "cf"
