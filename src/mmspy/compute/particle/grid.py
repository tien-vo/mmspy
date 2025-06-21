"""Provide dataclass for particle grid."""

__all__ = ["ParticleGrid"]

import numpy as np
from attrs import define

from mmspy.configure.units import units as u
from mmspy.types import NDArray, Quantity, Unit


@define
class ParticleGrid:
    """Dataclass for the support of the distribution function."""

    name: str
    center: Quantity
    log_scale: bool = False
    index: NDArray | None = None

    def __attrs_post_init__(self) -> None:
        """Perform unit and dimension checks on initialization."""
        self.check_dimension()
        self.check_units()

    def check_units(self) -> None:
        """Check the units of the grid center and return a valid unit."""
        valid_units = ["energy_unit", "velocity_unit", "angle_unit"]
        if not any(
            self.units.is_compatible_with(units) for units in valid_units
        ):
            msg = (
                f"Expected grid units {self.units!r} to be compatible "
                f"with one of {valid_units!r}."
            )
            raise ValueError(msg)

    def check_dimension(self) -> None:
        """Ensure the grid is 1D and has at least 2 grid points."""
        if self.center.ndim != 1:
            msg = "Expected grid dimension to be 1."
            raise ValueError(msg)
        if self.size <= 1:
            msg = "Expected grid size to be at least 2."
            raise ValueError(msg)

    @property
    def size(self) -> int:
        """Size of the grid."""
        return self.center.size

    @property
    def units(self) -> Unit:
        """Units of the grid."""
        return self.center.units  # type: ignore[return-value]

    @property
    def log_center(self) -> NDArray:
        """Base-10 logarithm of the grid center, respecting signs."""
        if not self.log_scale:
            msg = "Grid is not on log scale."
            raise NotImplementedError(msg)

        return np.sign(self.center) * np.log10(np.abs(self.center.magnitude))

    @property
    def edge(self) -> Quantity:
        """Grid edges including the left-most and right-most boundaries."""
        center = (
            self.center.magnitude if not self.log_scale else self.log_center
        )
        spacing = np.diff(center).min()
        edge = np.append(center, center[-1] + spacing) - spacing / 2
        if self.log_scale:
            return np.sign(edge) * u.Quantity(
                10.0 ** np.abs(edge),
                self.center.units,
            )

        return u.Quantity(edge, self.center.units)

    def to_log(self) -> "ParticleGrid":
        if not self.log_scale:
            msg = "Grid is not on log scale."
            raise NotImplementedError(msg)

        return ParticleGrid(
            name=self.name,
            center=u.Quantity(self.log_center),
            log_scale=False,
            index=self.index,
        )
