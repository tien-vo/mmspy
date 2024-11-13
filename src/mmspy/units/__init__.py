r"""Provide unit support with `pint`."""

import pint
import pint_xarray

from mmspy.units._utils import _attach_exponential_symbol, _get_cache_path
from mmspy.units._format import fits_formatter, latex_formatter

registry = pint.UnitRegistry(
    force_ndarray_like=True,
    autoconvert_offset_to_baseunit=True,
    cache_folder=_get_cache_path(),
    preprocessors=[_attach_exponential_symbol()],
)
registry.formatter.default_format = "fits"
registry.setup_matplotlib()
pint.set_application_registry(registry)
