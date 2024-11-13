r"""Provide unit support with `pint`."""

from importlib.resources import files

import pint
import pint_xarray

from mmspy.units._format import fits_formatter, latex_formatter
from mmspy.units._utils import _attach_exponential_symbol, _get_cache_path

registry = pint.UnitRegistry(
    force_ndarray_like=True,
    autoconvert_offset_to_baseunit=True,
    cache_folder=_get_cache_path(),
    preprocessors=[_attach_exponential_symbol()],
)
registry.formatter.default_format = "fits"
registry.setup_matplotlib()
registry.load_definitions(str(files("mmspy.units") / "data" / "particle.txt"))
pint.set_application_registry(registry)
