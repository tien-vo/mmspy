"""Provide xarray accessor for species information."""

__all__ = ["SpeciesAccessor"]

from typing import Generic

import xarray as xr

from mmspy.configure.config import config
from mmspy.configure.units import units as u
from mmspy.types import Quantity, T_Xarray


@xr.register_dataset_accessor("species")
@xr.register_dataarray_accessor("species")
class SpeciesAccessor(Generic[T_Xarray]):
    """Xarray accessor for species information."""

    def __init__(self, xarray: T_Xarray) -> None:
        """Species accessor.

        Initialize accessor for a dataset or data array with species
        information.

        Parameters
        ----------
        xarray : DataArray or Dataset
            Xarray

        """
        self._xarray: T_Xarray = xarray
        self._name: str | None = None

    @property
    def name(self) -> str:
        """Return the name of the species."""
        if self._name is not None:
            return self._name

        name = self._xarray.attrs.get("species")
        source = self._xarray.attrs.get("source")
        info = self._xarray.attrs.get("CATDESC")

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
                name = "electron"

        if info is not None:
            info = info.lower().replace("/", "_").replace(" ", "_").split("_")
            if "dis" in info:
                name = "ion"
            if "des" in info:
                name = "electron"

        return "" if name is None else name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def mass(self) -> Quantity:
        """Return the mass of the species."""
        species = config.get("species", {})
        if self.name not in species:
            msg = "Species unidentified."
            raise ValueError(msg)

        return u(species[f"{self.name}/mass"])

    @property
    def charge(self) -> Quantity:
        """Return the charge of the species."""
        species = config.get("species", {})
        if self.name not in species:
            msg = "Species unidentified."
            raise ValueError(msg)

        return u(species[f"{self.name}/charge"])
