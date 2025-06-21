"""Define species-specific contexts."""

__all__ = ["ion_context", "elc_context", "electron_context"]

from functools import partial
from typing import Callable

import pint

from mmspy.configure.units.plasma_parameters import (
    cyclotron_frequency_to_magnetic_field,
    density_to_plasma_frequency,
    kinetic_energy_to_lorentz_factor,
    kinetic_energy_to_momentum,
    kinetic_energy_to_speed,
    magnetic_field_to_cyclotron_frequency,
    momentum_to_kinetic_energy,
    momentum_to_lorentz_factor,
    number_flux_to_phase_space_density,
    phase_space_density_to_number_flux,
    plasma_frequency_to_density,
    speed_to_kinetic_energy,
    voltage_to_potential_energy,
)

ion_context = pint.Context("ion")
elc_context = pint.Context("elc")
electron_context = pint.Context("electron")

transformations: list[tuple[str, str, Callable]] = [
    ("[electric_potential]", "[energy]", voltage_to_potential_energy),
    ("[energy]", "[]", kinetic_energy_to_lorentz_factor),
    ("[energy]", "[momentum]", kinetic_energy_to_momentum),
    ("[momentum]", "[energy]", momentum_to_kinetic_energy),
    ("[momentum]", "[]", momentum_to_lorentz_factor),
    ("[energy]", "[speed]", kinetic_energy_to_speed),
    ("[speed]", "[energy]", speed_to_kinetic_energy),
    ("[magnetic_field]", "[frequency]", magnetic_field_to_cyclotron_frequency),
    ("[frequency]", "[magnetic_field]", cyclotron_frequency_to_magnetic_field),
    ("[number_density]", "[frequency]", density_to_plasma_frequency),
    ("[frequency]", "[number_density]", plasma_frequency_to_density),
    (
        "[phase_space_density]",
        "[number_flux]",
        phase_space_density_to_number_flux,
    ),
    (
        "[number_flux]",
        "[phase_space_density]",
        number_flux_to_phase_space_density,
    ),
]
for context in [ion_context, elc_context, electron_context]:
    for from_unit, to_unit, transformation in transformations:
        context.add_transformation(
            from_unit,
            to_unit,
            partial(transformation, species=context.name),
        )
