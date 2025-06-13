"""Provide unit support with `pint`."""

__all__ = ["units", "unit_definitions"]

from importlib.resources import files

import pint
import pint_xarray

import mmspy.utils.pint.formatters
from mmspy.utils.paths import CACHE_DIR
from mmspy.utils.pint.contexts import elc_context, ion_context
from mmspy.utils.pint.preprocessors import _get_fits_units_processor


def _configure_units():
    registry = pint.UnitRegistry(
        force_ndarray_like=True,
        autoconvert_offset_to_baseunit=True,
        cache_folder=CACHE_DIR / "units",
        preprocessors=[_get_fits_units_processor()],
    )
    registry.preprocessors.insert(0, str)
    registry.formatter.default_format = "fits"

    registry.setup_matplotlib()
    registry.load_definitions(unit_definitions)
    registry.add_context(ion_context)
    registry.add_context(elc_context)
    pint.set_application_registry(registry)

    return pint.get_application_registry()


unit_definitions = str(files("mmspy.data") / "units.definition")
units = _configure_units()
