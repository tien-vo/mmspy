"""Provide unit support with `pint`."""

__all__ = ["units"]

import logging
from importlib.resources import files

import pint
import pint_xarray

import mmspy.utils.pint.formatters
from mmspy.utils.paths import CACHE_DIR
from mmspy.utils.pint.contexts import elc_context, ion_context
from mmspy.utils.pint.preprocessors import _get_fits_units_processor

log = logging.getLogger(__name__)


def _configure_units():
    config = str(files("mmspy.data") / "particle-unit-definitions.txt")
    log.debug(f"Setting up custom pint registry at {CACHE_DIR / 'units'}")

    registry = pint.UnitRegistry(
        force_ndarray_like=True,
        autoconvert_offset_to_baseunit=True,
        cache_folder=CACHE_DIR / "units",
        preprocessors=[_get_fits_units_processor()],
    )
    registry.preprocessors.insert(0, str)
    registry.formatter.default_format = "fits"

    registry.setup_matplotlib()
    registry.load_definitions(config)
    log.debug(f"Loaded particle units from {config}")

    registry.add_context(ion_context)
    log.debug("Added ion contexts.")

    registry.add_context(elc_context)
    log.debug("Added electron contexts.")

    pint.set_application_registry(registry)

    return pint.get_application_registry()


units = _configure_units()
