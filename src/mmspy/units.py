r"""Provide unit support."""

__all__ = ["registry"]

import functools
import re
from collections.abc import Callable
from pathlib import Path

import pint
import pint_xarray  # noqa: F401


def _get_cache_path() -> Path:
    r"""Set up cache directory for ``pint`` units."""
    path = Path("~").expanduser() / ".cache" / "mmspy" / "units"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _attach_exponential_symbol() -> Callable[[str], str]:
    r"""Attach '**' to unit strings.

    Adopted from ``cf-xarray`` package [1]_.

    References
    ----------
    .. [1] https://github.com/xarray-contrib/cf-xarray/blob/22ee634433b988bd101e45e9f9728bbf59915259/cf_xarray/units.py#L63-L76

    """
    pattern = (
        r"(?<=[A-Za-z])"
        r"(?![A-Za-z])"
        r"(?<![0-9\-][eE])"
        r"(?<![0-9\-])"
        r"(?=[0-9\-])"
    )
    return functools.partial(re.compile(pattern).sub, "**")


@pint.register_unit_format("fits")
def fits_formatter(
    unit: pint.util.UnitsContainer,
    registry: pint.UnitRegistry,
) -> str:
    r"""Return a FITS-compliant [1]_ unit string from a ``pint`` unit.

    Adopted from ``cf-xarray`` package [2]_.

    Parameters
    ----------
    unit : UnitsContainer
        Input unit.
    registry : UnitRegistry
        The associated registry

    Returns
    -------
    string : str
        Units following FITS standards, using symbols.

    References
    ----------
    .. [1] https://fits.gsfc.nasa.gov/fits_standard.html
    .. [2] https://github.com/xarray-contrib/cf-xarray/blob/22ee634433b988bd101e45e9f9728bbf59915259/cf_xarray/units.py#L12-L56

    """

    def _get_symbol(name: str) -> str:
        units = getattr(registry, "_units", {})
        return registry.get_symbol(name) if name in units else name

    numerator = (
        (_get_symbol(name), exponent)
        for name, exponent in unit.items()
        if exponent >= 0
    )
    denominator = (
        (_get_symbol(name), exponent)
        for name, exponent in unit.items()
        if exponent < 0
    )

    return pint.formatter(
        numerator=numerator,  # type: ignore[arg-type]
        denominator=denominator,  # type: ignore[arg-type]
        as_ratio=False,
        product_fmt=" ",
        power_fmt="{}{}",
    )


registry = pint.UnitRegistry(
    force_ndarray_like=True,
    autoconvert_offset_to_baseunit=True,
    cache_folder=_get_cache_path(),
    preprocessors=[_attach_exponential_symbol()],
)
registry.preprocessors.insert(0, str)
registry.formatter.default_format = "fits"
registry.setup_matplotlib()
pint.set_application_registry(registry)
