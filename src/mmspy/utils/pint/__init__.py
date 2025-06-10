r"""Provide unit support with `pint`."""

__all__ = ["configure_units"]

from importlib.resources import files

import pint
import pint_xarray

import mmspy.config.units.formatters
from mmspy.config.directories import CACHE_DIR
from mmspy.config.units.contexts import elc_context, ion_context
from mmspy.config.units.preprocessors import _get_fits_units_processor

config = str(files("mmspy.data") / "particle-unit-definitions.txt")


def configure_units(config=config, cache_dir=CACHE_DIR / "units"):
    registry = pint.UnitRegistry(
        force_ndarray_like=True,
        autoconvert_offset_to_baseunit=True,
        cache_folder=cache_dir,
        preprocessors=[_get_fits_units_processor()],
    )
    registry.preprocessors.insert(0, str)
    registry.formatter.default_format = "fits"
    registry.setup_matplotlib()
    registry.load_definitions(config)
    registry.add_context(ion_context)
    registry.add_context(elc_context)
    pint.set_application_registry(registry)
    return pint.get_application_registry()
