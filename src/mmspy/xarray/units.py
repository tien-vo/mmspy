r"""Provide accessors related to data with units."""

__all__ = [
    "has_equivalent_units",
    "UnitsAccessor",
]

from collections.abc import Sequence
from typing import Union

import xarray as xr
from astropy.units import Unit

UnitLike = Union[str, Unit]


def has_equivalent_units(list_of_array: Sequence[xr.DataArray]) -> bool:
    r"""Check if a sequence of `DataArray` has compatible units.

    Parameters
    ----------
    list_of_array : sequence of DataArray
        Sequence of arrays with units

    Returns
    -------
    result : bool
        True if all elements can be converted to one another

    """
    units = list_of_array[0].units.from_metadata
    return all(
        array.units.from_metadata.is_equivalent(units)
        for array in list_of_array
    )


@xr.register_dataarray_accessor("units")
class UnitsAccessor:
    r"""Xarray accessor for units handling."""

    def __init__(self, da: xr.DataArray) -> None:
        r"""Initialize accessor for a data array.

        Parameters
        ----------
        da : DataArray
            Xarray data array

        """
        self._da = da

    @property
    def from_metadata(self) -> Unit:
        r"""Return the units from the metadata of a data array.

        Returns
        -------
        units : Unit
            The unit as an `~astropy.units.Unit`

        """
        units = self._da.attrs.get("units")
        units = "" if units is None else units
        return Unit(units)

    def to(self, units: UnitLike) -> xr.DataArray:
        r"""Return a data array with new units.

        Parameters
        ----------
        units : unit-like
            New units to convert to

        Returns
        -------
        da : DataArray
            Converted array with updated metadata

        """
        units = Unit(units)
        da = self._da.copy()

        conversion_factor = da.units.from_metadata.to(units)
        with xr.set_options(keep_attrs=True):
            da = da * conversion_factor
            da.attrs.update(units=str(units))

        return da
