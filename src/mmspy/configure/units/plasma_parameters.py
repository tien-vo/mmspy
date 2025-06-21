"""Provide calculations of plasma parameters.

.. todo:: Add docstring and tests.

"""

__all__ = [
    "voltage_to_potential_energy",
    "kinetic_energy_to_lorentz_factor",
    "momentum_to_lorentz_factor",
    "kinetic_energy_to_momentum",
    "momentum_to_kinetic_energy",
    "kinetic_energy_to_speed",
    "speed_to_kinetic_energy",
    "magnetic_field_to_cyclotron_frequency",
    "cyclotron_frequency_to_magnetic_field",
    "density_to_plasma_frequency",
    "plasma_frequency_to_density",
    "phase_space_density_to_number_flux",
    "number_flux_to_phase_space_density",
]

import numpy as np

from mmspy.types import Quantity, Registry


def parse_species(
    species: str,
    registry: Registry,
) -> tuple[Quantity, Quantity]:
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


def voltage_to_potential_energy(
    registry: Registry,
    voltage: Quantity,
    species: str,
) -> Quantity:
    """Convert electric potential to potential energy."""
    charge, _ = parse_species(species, registry)
    return charge * voltage


def kinetic_energy_to_lorentz_factor(
    registry: Registry,
    energy: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    rest_energy = mass * registry.c**2
    return 1 + (energy / rest_energy).to("dimensionless")


def momentum_to_lorentz_factor(
    registry: Registry,
    momentum: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    return np.sqrt(1 + (momentum / mass / registry.c) ** 2).to("dimensionless")


def kinetic_energy_to_momentum(
    registry: Registry,
    energy: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    gamma = kinetic_energy_to_lorentz_factor(registry, energy, species)
    return np.sqrt(gamma**2 - 1) * mass * registry.c


def momentum_to_kinetic_energy(
    registry: Registry,
    momentum: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    rest_energy = mass * registry.c**2
    gamma = momentum_to_lorentz_factor(registry, momentum, species)
    return (gamma - 1) * rest_energy


def kinetic_energy_to_speed(
    registry: Registry,
    energy: Quantity,
    species: str,
) -> Quantity:
    gamma = kinetic_energy_to_lorentz_factor(registry, energy, species)
    return registry.c * np.sqrt(1 - 1 / gamma**2)


def speed_to_kinetic_energy(
    registry: Registry,
    speed: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    rest_energy = mass * registry.c**2
    gamma = 1 / np.sqrt(1 - (speed / registry.c) ** 2)
    return (gamma - 1) * rest_energy


def magnetic_field_to_cyclotron_frequency(
    registry: Registry,
    magnetic_field: Quantity,
    species: str,
) -> Quantity:
    charge, mass = parse_species(species, registry)
    return np.abs(charge / mass) * magnetic_field / 2 / np.pi


def cyclotron_frequency_to_magnetic_field(
    registry: Registry,
    frequency: Quantity,
    species: str,
) -> Quantity:
    charge, mass = parse_species(species, registry)
    return 2 * np.pi * frequency * np.abs(mass / charge)


def density_to_plasma_frequency(
    registry: Registry,
    density: Quantity,
    species: str,
) -> Quantity:
    charge, mass = parse_species(species, registry)
    eps0 = registry.eps_0
    return np.sqrt(charge**2 * density / eps0 / mass) / 2 / np.pi


def plasma_frequency_to_density(
    registry: Registry,
    frequency: Quantity,
    species: str,
) -> Quantity:
    charge, mass = parse_species(species, registry)
    eps0 = registry.eps_0
    return (eps0 * mass / charge**2) * (2 * np.pi * frequency) ** 2


def phase_space_density_to_number_flux(
    registry: Registry,
    phase_space_density: Quantity,
    energy: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    momentum = kinetic_energy_to_momentum(registry, energy, species)
    return momentum**2 / mass**3 * phase_space_density * energy


def number_flux_to_phase_space_density(
    registry: Registry,
    number_flux: Quantity,
    energy: Quantity,
    species: str,
) -> Quantity:
    _, mass = parse_species(species, registry)
    momentum = kinetic_energy_to_momentum(registry, energy, species)
    return mass**3 / momentum**2 * number_flux / energy
