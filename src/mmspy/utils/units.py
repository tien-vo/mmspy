r"""Utilities for `~astropy.units`."""

__all__ = ["Units"]

from collections.abc import Callable
from typing import TypeAlias

import astropy.units as u
from attr import Attribute, define, field

UnitLike: TypeAlias = str | u.Unit
Validator: TypeAlias = Callable[["Units", Attribute, UnitLike], None]


def _to_unit(unit: UnitLike) -> u.Unit:
    r"""Convert unit-like variable to unit."""
    return u.Unit(unit)


def _is_physical_type(physical_type: str) -> Validator:
    r"""Check if an input unit is of a given physical type.

    Parameters
    ----------
    physical_type : str
        Physical type to check.

    Returns
    -------
    validator : Callable
        Validator for parameters defined with `~attr.field` [1]_

    Raises
    ------
    ValueError
        If input unit is not of ``physical_type``.

    References
    ----------
    .. [1] https://www.attrs.org/en/stable/examples.html#validators

    """

    def validator(
        units: "Units",  # noqa: ARG001
        attribute: Attribute,  # noqa: ARG001
        unit: UnitLike,
    ) -> None:
        if u.Unit(unit).physical_type != physical_type:
            msg = (
                f"Expected {unit!r} to be of {physical_type!r} physical type."
            )
            raise ValueError(msg)

    return validator


@define
class Units:
    r"""Dataclass for preferred units."""

    angle: u.Unit = field(
        default="deg",
        converter=_to_unit,
        validator=_is_physical_type("angle"),
    )

    density: u.Unit = field(
        default="cm-3",
        converter=_to_unit,
        validator=_is_physical_type("number density"),
    )

    velocity: u.Unit = field(
        default="km/s",
        converter=_to_unit,
        validator=_is_physical_type("velocity"),
    )

    energy: u.Unit = field(
        default="eV",
        converter=_to_unit,
        validator=_is_physical_type("energy"),
    )

    pressure: u.Unit = field(
        default="nPa",
        converter=_to_unit,
        validator=_is_physical_type("pressure"),
    )

    energy_flux: u.Unit = field(
        default="cm-2 s-1",
        converter=_to_unit,
        validator=_is_physical_type("particle flux"),
    )

    @property
    def phase_space_density(self) -> u.Unit:
        r"""Phase space density."""
        return self.density / self.velocity**3

    @property
    def A(self) -> u.Unit:  # noqa: N802
        r"""Alias for ``angle``."""
        return self.angle

    @property
    def N(self) -> u.Unit:  # noqa: N802
        r"""Alias for ``density``."""
        return self.density

    @property
    def V(self) -> u.Unit:  # noqa: N802
        r"""Alias for ``velocity``."""
        return self.velocity

    @property
    def W(self) -> u.Unit:  # noqa: N802
        r"""Alias for ``energy``."""
        return self.energy

    @property
    def P(self) -> u.Unit:  # noqa: N802
        r"""Alias for ``pressure``."""
        return self.pressure

    @property
    def j(self) -> u.Unit:
        r"""Alias for ``energy_flux``."""
        return self.energy_flux

    @property
    def f(self) -> u.Unit:
        r"""Alias for ``phase_space_density``."""
        return self.phase_space_density
