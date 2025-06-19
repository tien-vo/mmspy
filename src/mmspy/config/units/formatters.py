"""Define custom unit string format."""

__all__ = ["fits_formatter", "latex_formatter"]

from typing import cast

import pint

from mmspy.types import FractionComponent, Registry, Unit


def _get_symbol(name: str, registry: Registry) -> str:
    units = getattr(registry, "_units", {})
    return registry.get_symbol(name) if name in units else name


def _get_fraction_components(
    unit: Unit,
    registry: Registry,
) -> tuple[FractionComponent, FractionComponent]:
    numerator = (
        (_get_symbol(name, registry), exponent)
        for name, exponent in unit.items()
        if exponent >= 0
    )
    denominator = (
        (_get_symbol(name, registry), exponent)
        for name, exponent in unit.items()
        if exponent < 0
    )
    numerator = cast(FractionComponent, numerator)
    denominator = cast(FractionComponent, denominator)
    return numerator, denominator


@pint.register_unit_format("fits")
def fits_formatter(unit: Unit, registry: Registry) -> str:
    """Return a FITS-compliant [1]_ unit string from a ``pint`` unit.

    Adopted from ``cf-xarray`` [2]_.

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
    .. [2] :cf_xarray:`units.py#L12-L56`

    """
    numerator, denominator = _get_fraction_components(unit, registry)
    return pint.formatter(
        numerator=numerator,
        denominator=denominator,
        as_ratio=False,
        product_fmt=" ",
        power_fmt="{}{}",
    )


@pint.register_unit_format("latex")
def latex_formatter(unit: Unit, registry: Registry) -> str:
    """Return a latex-inline unit string from a ``pint`` unit.

    Tries to emulate `astropy.units.format.LatexInline`.

    Parameters
    ----------
    unit : UnitsContainer
        Input unit.
    registry : UnitRegistry
        The associated registry

    Returns
    -------
    string : str
        Units following Latex format.

    """
    numerator, denominator = _get_fraction_components(unit, registry)
    string = pint.formatter(
        numerator=numerator,
        denominator=denominator,
        as_ratio=False,
        product_fmt=r"\,",
        power_fmt="{}^{{{}}}",
    )
    string = string.replace("nan", r"{\rm NaN}")
    return rf"$\mathrm{{{string}}}$"
