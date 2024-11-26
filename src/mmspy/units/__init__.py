r"""Provide unit support with `pint`."""

__all__ = [
    "CACHE_DIR",
    "PARTICLE_UNITS",
    "is_quantified",
    "registry",
]

import pint
import pint_xarray

import mmspy.units._formatters
from mmspy.units._contexts import elc_context, ion_context
from mmspy.units._path import CACHE_DIR, PARTICLE_UNITS, is_quantified
from mmspy.units._preprocessors import _get_fits_units_processor

registry = pint.UnitRegistry(
    force_ndarray_like=True,
    autoconvert_offset_to_baseunit=True,
    cache_folder=CACHE_DIR,
    preprocessors=[_get_fits_units_processor()],
)
registry.preprocessors.insert(0, str)
registry.formatter.default_format = "fits"
registry.setup_matplotlib()
registry.load_definitions(str(PARTICLE_UNITS))
registry.add_context(ion_context)
registry.add_context(elc_context)
pint.set_application_registry(registry)
