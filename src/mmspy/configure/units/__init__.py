"""Provide unit support with `pint`."""

__all__ = [
    "UNIT_DEFINITIONS",
    "units",
]

from importlib.resources import files

import pint
import pint_xarray

import mmspy.configure.units.formatters
from mmspy.configure.paths import CACHE_DIR
from mmspy.configure.units.contexts import (
    elc_context,
    electron_context,
    ion_context,
)
from mmspy.configure.units.preprocessors import _get_fits_units_processor
from mmspy.types import Registry


def _configure_units() -> Registry:
    registry = pint.UnitRegistry(
        force_ndarray_like=True,
        autoconvert_offset_to_baseunit=True,
        cache_folder=CACHE_DIR / "units",
        preprocessors=[_get_fits_units_processor()],
    )
    registry.preprocessors.insert(0, str)
    registry.formatter.default_format = "fits"

    registry.setup_matplotlib()
    registry.load_definitions(UNIT_DEFINITIONS)
    registry.add_context(ion_context)
    registry.add_context(elc_context)
    registry.add_context(electron_context)
    pint.set_application_registry(registry)

    return pint.get_application_registry()


UNIT_DEFINITIONS = str(files("mmspy.data") / "units.definition")
units = _configure_units()
