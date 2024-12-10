# mypy: disable-error-code="arg-type,operator,misc"
r"""Define species-specific contexts.

.. todo:: Add tests.
"""

__all__ = [
    "ion_context",
    "elc_context",
]

from functools import partial

import numpy as np
import pint


def _get_species_properties(
    species: str,
    registry: pint.UnitRegistry,
) -> tuple[pint.Quantity, pint.Quantity]:
    match species:
        case "proton" | "ion" | "H+":
            charge = registry("1 elementary_charge")
            mass = registry("proton_mass")
        case "electron" | "elc" | "e-":
            charge = registry("-1 elementary_charge")
            mass = registry("electron_mass")
        case _:
            raise NotImplementedError

    return charge, mass


def voltage_to_energy(
    registry: pint.UnitRegistry,
    voltage: pint.Quantity,
    species: str,
) -> pint.Quantity:
    charge, _ = _get_species_properties(species, registry)
    return charge * voltage


def energy_to_speed(
    registry: pint.UnitRegistry,
    energy: pint.Quantity,
    species: str,
) -> pint.Quantity:
    _, mass = _get_species_properties(species, registry)
    return np.sqrt(2 * energy / mass)


def speed_to_energy(
    registry: pint.UnitRegistry,
    speed: pint.Quantity,
    species: str,
) -> pint.Quantity:
    _, mass = _get_species_properties(species, registry)
    return 0.5 * mass * speed**2


def magnetic_field_to_cyclotron_frequency(
    registry: pint.UnitRegistry,
    magnetic_field: pint.Quantity,
    species: str,
) -> pint.Quantity:
    charge, mass = _get_species_properties(species, registry)
    return np.abs(charge / mass) * magnetic_field / 2 / np.pi


def cyclotron_frequency_to_magnetic_field(
    registry: pint.UnitRegistry,
    frequency: pint.Quantity,
    species: str,
) -> pint.Quantity:
    charge, mass = _get_species_properties(species, registry)
    return 2 * np.pi * frequency * np.abs(mass / charge)


def density_to_plasma_frequency(
    registry: pint.UnitRegistry,
    density: pint.Quantity,
    species: str,
) -> pint.Quantity:
    charge, mass = _get_species_properties(species, registry)
    eps0 = registry.eps_0
    return np.sqrt(charge**2 * density / eps0 / mass) / 2 / np.pi


def plasma_frequency_to_density(
    registry: pint.UnitRegistry,
    frequency: pint.Quantity,
    species: str,
) -> pint.Quantity:
    charge, mass = _get_species_properties(species, registry)
    eps0 = registry.eps_0
    return (eps0 * mass / charge**2) * (2 * np.pi * frequency) ** 2


ion_context = pint.Context("ion")
elc_context = pint.Context("elc")

transformations = [
    ["[electric_potential]", "[energy]", voltage_to_energy],
    ["[energy]", "[speed]", energy_to_speed],
    ["[speed]", "[energy]", speed_to_energy],
    ["[magnetic_field]", "[frequency]", magnetic_field_to_cyclotron_frequency],
    ["[frequency]", "[magnetic_field]", cyclotron_frequency_to_magnetic_field],
    ["[number_density]", "[frequency]", density_to_plasma_frequency],
    ["[frequency]", "[number_density]", plasma_frequency_to_density],
]
for context in [ion_context, elc_context]:
    for from_unit, to_unit, transformation in transformations:
        context.add_transformation(
            from_unit,
            to_unit,
            partial(transformation, species=context.name),
        )
