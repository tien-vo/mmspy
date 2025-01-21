r"""Provide xarray accessor for species information."""

__all__ = ["SpeciesAccessor"]

from typing import Generic

import xarray as xr
from pint import Quantity
from pint import application_registry as u
from xarray.core.types import T_Xarray


@xr.register_dataset_accessor("species")
@xr.register_dataarray_accessor("species")
class SpeciesAccessor(Generic[T_Xarray]):
    r"""Xarray accessor for species information."""

    def __init__(self, data: T_Xarray) -> None:
        r"""Species accessor.

        Initialize accessor for a dataset or data array with species
        information.

        Parameters
        ----------
        data : DataArray or Dataset
            Xarray data array or dataset

        """
        self._data: T_Xarray = data
        self._name: str | None = None

    @property
    def species_options(self) -> dict[str, dict[str, Quantity]]:
        r"""Return supported species options."""
        return {
            "ion": {
                "mass": u.Quantity(1.0, "proton_mass"),
                "charge": u.Quantity(1.0, "elementary_charge"),
            },
            "elc": {
                "mass": u.Quantity(1.0, "electron_mass"),
                "charge": u.Quantity(-1.0, "elementary_charge"),
            },
        }

    @property
    def name(self) -> str:
        r"""Return the name of the species."""
        if self._name is not None:
            return self._name

        name = self._data.attrs.get("species_name")
        source = self._data.attrs.get("source")
        info = self._data.attrs.get("CATDESC")
        if name is None and source is None and info is None:
            msg = "Unable to extract species information."
            raise ValueError(msg)

        if name is not None:
            return name

        if source is not None:
            source = source.lower().replace("-", "_").split("_")
            if "dis" in source or "ion" in source:
                name = "ion"
            if "des" in source or "electron" in source:
                name = "elc"

        if info is not None:
            info = info.lower().replace("/", "_").replace(" ", "_").split("_")
            if "dis" in info:
                name = "ion"
            if "des" in info:
                name = "elc"

        return "" if name is None else name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def mass(self) -> Quantity:
        r"""Return the mass of the species."""
        if self.name not in self.species_options:
            msg = "Species unidentified."
            raise ValueError(msg)

        return self.species_options[self.name]["mass"]

    @property
    def charge(self) -> Quantity:
        r"""Return the charge of the species."""
        if self.name not in self.species_options:
            msg = "Species unidentified."
            raise ValueError(msg)

        return self.species_options[self.name]["charge"]
