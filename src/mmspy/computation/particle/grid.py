r"""Provide dataclass for particle grid."""

__all__ = ["ParticleGrid"]

from collections.abc import Callable

import numpy as np
from attr import Attribute, define, field
from numpy.typing import NDArray
from pint import Quantity

from mmspy.api.converters._utils import wrap_converter


@wrap_converter(
    signature=Callable[[int | float | Quantity], Quantity],
    takes_field=True,
)
def _to_unit(
    value: int | float | Quantity,
    attribute: Attribute,
) -> Quantity:
    return Quantity(value, attribute.metadata["unit"])


@define
class ParticleGrid:
    r"""Dataclass for the support of the distribution function.

    .. todo:: Better docstring.

    """

    minimum_energy: int | float | Quantity = field(
        default=Quantity(1e0, "energy_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "energy_unit"},
    )

    maximum_energy: int | float | Quantity = field(
        default=Quantity(1e6, "energy_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "energy_unit"},
    )

    minimum_zenith: int | float | Quantity = field(
        default=Quantity(0.0, "angle_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "angle_unit"},
    )

    maximum_zenith: int | float | Quantity = field(
        default=Quantity(180.0, "angle_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "angle_unit"},
    )

    minimum_azimuth: int | float | Quantity = field(
        default=Quantity(0.0, "angle_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "angle_unit"},
    )

    maximum_azimuth: int | float | Quantity = field(
        default=Quantity(360.0, "angle_unit"),
        converter=_to_unit,  # type: ignore[misc]
        metadata={"unit": "angle_unit"},
    )

    energy_resolution: int = 53  # log spacing = 0.1175
    zenith_resolution: int = 19
    azimuth_resolution: int = 37

    @property
    def energy_array(self) -> Quantity:
        r"""Energy array."""
        return Quantity(
            np.logspace(
                np.log10(self.minimum_energy.magnitude),  # type: ignore[union-attr]
                np.log10(self.maximum_energy.magnitude),  # type: ignore[union-attr]
                self.energy_resolution,
            ),
            "energy_unit",
        )

    @property
    def zenith_array(self) -> Quantity:
        r"""Zenith array."""
        return Quantity(
            np.linspace(
                self.minimum_zenith,
                self.maximum_zenith,
                self.zenith_resolution,
            ),
            "angle_unit",
        )

    @property
    def azimuth_array(self) -> Quantity:
        r"""Azimuth array."""
        return Quantity(
            np.linspace(
                self.minimum_azimuth,
                self.maximum_azimuth,
                self.azimuth_resolution,
            ),
            "angle_unit",
        )

    @property
    def shape(self) -> tuple[int, ...]:
        r"""Grid shape."""
        return (
            self.energy_resolution,
            self.zenith_resolution,
            self.azimuth_resolution,
        )

    def edges(self, which: str) -> Quantity:
        r"""Edges."""
        array = getattr(self, f"{which}_array").magnitude

        if which == "energy":
            array = np.log10(array)

        spacing = np.diff(array).min()
        edges = np.append(array, array[-1] + spacing) - spacing / 2
        if which == "energy":
            return Quantity(10.0**edges, "energy_unit")

        return Quantity(edges, "angle_unit")

    def get_bins(self, dimension: int) -> tuple[NDArray, ...]:
        r"""Return all bins."""
        log_W = np.log10(self.edges("energy").magnitude)
        theta = self.edges("zenith").magnitude
        phi = self.edges("azimuth").magnitude

        bins: tuple[NDArray, ...]
        match dimension:
            case 2:
                bins = (log_W, theta)
            case 3:
                bins = (log_W, theta, phi)
            case _:
                msg = f"Expected {dimension!r} to be '2' or '3'"
                raise ValueError(msg)

        return bins

    def get_grids(self, dimension: int) -> tuple[NDArray, ...]:
        r"""Return all grids."""
        log_W = np.log10(self.energy_array.magnitude)
        theta = self.zenith_array.magnitude
        phi = self.azimuth_array.magnitude

        grids: tuple[NDArray, ...]
        match dimension:
            case 2:
                grids = (log_W[:, np.newaxis], theta[np.newaxis, :])
            case 3:
                grids = (
                    log_W[:, np.newaxis, np.newaxis],
                    theta[np.newaxis, :, np.newaxis],
                    phi[np.newaxis, np.newaxis, :],
                )
            case _:
                msg = f"Expected {dimension!r} to be '2' or '3'"
                raise ValueError(msg)

        return grids
