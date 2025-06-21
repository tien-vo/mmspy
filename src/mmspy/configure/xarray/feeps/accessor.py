"""Provide xarray accessor for FEEPS datasets."""

__all__ = [
    "FeepsAccessor",
]

import numpy as np
import xarray as xr

from mmspy.configure.units import units as u
from mmspy.configure.xarray.feeps.tables import (
    get_energy_table,
    get_flat_field_table,
    get_sun_contamination_table,
    get_time_dependent_bad_eye_table,
    get_time_independent_bad_eye_table,
)
from mmspy.configure.xarray.utils import validate_dataset
from mmspy.types import Iterable, Quantity


def _is_distribution(
    array: xr.DataArray,
    dimensions: Iterable[str] = ("energy_channel", "sensor", "eye"),
) -> bool:
    return all(map(lambda x: x in array.dims, dimensions))


def _apply_time_dependent_table(
    dataset: xr.Dataset,
    table: xr.DataArray,
) -> xr.Dataset:
    """Apply table on dataset."""
    dataset = dataset.copy()
    table = table.copy().sortby("time")

    if "time" not in dataset.dims and "time" not in dataset.coords:
        return dataset

    if dataset.time.size == 1:
        table = table.sel(time=dataset.time, method="nearest")
        return dataset * table

    # Loop through each time table, find the range of application
    N_tables = table.sizes["time"]
    for it in range(N_tables - 1):
        this_table = table.isel(time=it)
        next_table = table.isel(time=it + 1)

        this_time = this_table.time.values
        next_time = next_table.time.values
        midpoint = (
            0.5 * (this_time.astype(float) + next_time.astype(float))
        ).astype("datetime64[ns]")

        if it == 0:
            left = dataset.time <= midpoint
            right = (midpoint < dataset.time) & (dataset.time <= next_time)
        elif it == N_tables - 2:
            left = (this_time <= dataset.time) & (dataset.time < midpoint)
            right = dataset.time >= midpoint
        else:
            left = (this_time <= dataset.time) & (dataset.time <= midpoint)
            right = (midpoint < dataset.time) & (dataset.time <= next_time)

        this_table = this_table.reset_coords(drop=True)
        next_table = next_table.reset_coords(drop=True)
        not_time_dimensions = [dim for dim in dataset.dims if dim != "time"]
        for variable in dataset.data_vars:
            if _is_distribution(dataset[variable], not_time_dimensions):
                dataset[variable] = xr.where(
                    left,
                    dataset[variable] * this_table,
                    dataset[variable],
                )
                dataset[variable] = xr.where(
                    right,
                    dataset[variable] * next_table,
                    dataset[variable],
                )

    return dataset


@xr.register_dataset_accessor("feeps")
class FeepsAccessor:
    """Xarray accessor for FEEPS datasets."""

    energy_variable: str
    error_variable: str
    sector_variable: str

    def __init__(self, dataset: xr.Dataset) -> None:
        """Validate and initialize accessor for a dataset.

        Parameters
        ----------
        dataset : Dataset
            Xarray dataset

        """
        validate_dataset(dataset, "FEEPS", ["FEEPS"])
        self._dataset = dataset.pint.quantify()

        variables = list(self._dataset.data_vars)
        coords = list(self._dataset.coords)
        for variable in variables + coords:
            array = self._dataset[variable]
            if not bool(array.pint.units):
                continue
            if array.pint.units.is_compatible_with("eV"):
                self.energy_variable = variable
            if array.pint.units.is_compatible_with("%"):
                self.error_variable = variable
            if array.attrs.get("CATDESC", "") == (
                "Spin sector in which the spacecraft "
                "was oriented during data acquisition"
            ):
                self.sector_variable = variable

    @property
    def eyes(self) -> list[int]:
        """Return the eyes in this dataset."""
        if self._dataset.species.name == "ion":
            return [6, 7, 8]

        return [1, 2, 3, 4, 5, 9, 10, 11, 12]

    def mask_data(
        self,
        keep_bad_eyes: bool = False,
        remove_one_count: bool = False,
        error_tolerance: Quantity = u("100 %"),
    ) -> xr.Dataset:
        """Mask dataset using all tables."""
        dataset = self._dataset.copy()
        dataset = dataset.isel(energy_channel=slice(1, -1))

        # Remove non-sensical error
        mask = dataset[self.error_variable] >= 0
        not_time_dimensions = [dim for dim in dataset.dims if dim != "time"]
        for variable in dataset.data_vars:
            if _is_distribution(dataset[variable], not_time_dimensions):
                dataset[variable] = xr.where(mask, dataset[variable], np.nan)

        dataset = dataset.feeps.apply_energy_correction_table(keep_bad_eyes)
        dataset = dataset.feeps.apply_flat_field_correction(keep_bad_eyes)
        dataset = dataset.feeps.remove_bad_eyes()
        dataset = dataset.feeps.remove_sun_contamination()

        if remove_one_count:
            for variable in dataset.data_vars:
                if not _is_distribution(
                    dataset[variable],
                    not_time_dimensions,
                ):
                    continue
                dataset[variable] = xr.where(
                    dataset[self.error_variable] < error_tolerance,
                    dataset[variable],
                    np.nan,
                )

        return dataset

    def apply_energy_correction_table(
        self,
        keep_bad_eyes: bool = False,
    ) -> xr.Dataset:
        """Apply energy correction table.

        Parameters
        ----------
        keep_bad_eyes : bool
            Toggle to keep the bad eyes.

        Returns
        -------
        dataset : Dataset
            Dataset corrected with new energies

        """
        dataset = self._dataset.copy()

        table = (
            get_energy_table(keep_bad_eyes)
            .sel(probe=dataset.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        dataset[self.energy_variable] = table
        return dataset

    def apply_flat_field_correction(
        self,
        keep_bad_eyes: bool = False,
    ) -> xr.Dataset:
        """Apply flat field correction.

        Parameters
        ----------
        keep_bad_eyes : bool
            Toggle to keep the bad eyes.

        Returns
        -------
        dataset : Dataset
            Dataset corrected with flat field factors

        """
        dataset = self._dataset.copy()

        table = (
            get_flat_field_table(keep_bad_eyes)
            .sel(probe=dataset.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        not_time_dimensions = [dim for dim in dataset.dims if dim != "time"]
        for variable in dataset:
            if not _is_distribution(dataset[variable], not_time_dimensions):
                continue
            attrs = dataset[variable].attrs
            dataset[variable] = dataset[variable] * table
            dataset[variable].attrs.update(attrs)

        return dataset

    def remove_bad_eyes(self) -> xr.Dataset:
        """Remove bad eyes.

        Returns
        -------
        dataset : Dataset
            Dataset with bad eyes masked using both time-dependent and
            time-independent tables.

        """
        dataset = self._dataset.copy()

        table = (
            get_time_independent_bad_eye_table()
            .sel(probe=dataset.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        not_time_dimensions = [dim for dim in dataset.dims if dim != "time"]
        for variable in dataset:
            if not _is_distribution(dataset[variable], not_time_dimensions):
                continue
            attrs = dataset[variable].attrs
            dataset[variable] = dataset[variable] * table
            dataset[variable].attrs.update(attrs)

        table = (
            get_time_dependent_bad_eye_table()
            .sel(probe=dataset.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )

        return _apply_time_dependent_table(dataset, table)

    def remove_sun_contamination(self) -> xr.Dataset:
        """Remove sun contamination.

        Returns
        -------
        dataset : Dataset
            Dataset with bad eyes masked using sun contamination tables.

        """
        dataset = self._dataset.copy()

        table = (
            get_sun_contamination_table()
            .sel(probe=dataset.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
            .sortby("time")
        )

        # Loop through each time table, find the range of application
        N_tables = table.sizes["time"]
        for it in range(N_tables - 1):
            this_table = table.isel(time=it)
            next_table = table.isel(time=it + 1)

            this_time = this_table.time.values
            next_time = next_table.time.values
            midpoint = (
                0.5 * (this_time.astype(float) + next_time.astype(float))
            ).astype("datetime64[ns]")

            if it == 0:
                left = dataset.time <= midpoint
                right = (midpoint < dataset.time) & (dataset.time <= next_time)
            elif it == N_tables - 2:
                left = (this_time <= dataset.time) & (dataset.time < midpoint)
                right = dataset.time >= midpoint
            else:
                left = (this_time <= dataset.time) & (dataset.time <= midpoint)
                right = (midpoint < dataset.time) & (dataset.time <= next_time)

            this_table = this_table.reset_coords(drop=True)
            next_table = next_table.reset_coords(drop=True)

            this_bad_sector = xr.where(
                this_table == 1,
                this_table.spin_sector,
                np.nan,
            )
            next_bad_sector = xr.where(
                next_table == 1,
                next_table.spin_sector,
                np.nan,
            )

            this_bad = xr.where(
                dataset[self.sector_variable] == this_bad_sector,
                1,
                0,
            ).sum(dim="spin_sector")
            next_bad = xr.where(
                dataset[self.sector_variable] == next_bad_sector,
                1,
                0,
            ).sum(dim="spin_sector")

            kw = {
                "time": dataset.time,
                "sensor": dataset.sensor,
                "eye": dataset.eye,
            }
            left_mask = (left & (this_bad == 1)).sel(**kw)
            right_mask = (right & (next_bad == 1)).sel(**kw)

            not_time_dimensions = [
                dim for dim in dataset.dims if dim != "time"
            ]
            for variable in dataset:
                if not _is_distribution(
                    dataset[variable], not_time_dimensions
                ):
                    continue

                dataset[variable] = xr.where(
                    ~left_mask,
                    dataset[variable],
                    np.nan,
                )
                dataset[variable] = xr.where(
                    ~right_mask,
                    dataset[variable],
                    np.nan,
                )

        return dataset
