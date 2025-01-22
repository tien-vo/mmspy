r"""Provide xarray accessor for FEEPS datasets."""

__all__ = [
    "FeepsAccessor",
]

import numpy as np
import xarray as xr
from pint_xarray import unit_registry as u

from mmspy.xarray._utils import validate_dataset

from .tables import (
    get_energy_table,
    get_flat_field_table,
    get_sun_contamination_table,
    get_time_dependent_bad_eye_table,
    get_time_independent_bad_eye_table,
)


def _apply_time_dependent_table(
    ds: xr.Dataset,
    table: xr.DataArray,
) -> xr.Dataset:
    r"""Apply table on dataset."""
    ds = ds.copy()
    table = table.copy().sortby("time")

    if "time" not in ds.dims and "time" not in ds.coords:
        return ds

    if ds.time.size == 1:
        table = table.sel(time=ds.time, method="nearest")
        return ds * table

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
            left = ds.time <= midpoint
            right = (midpoint < ds.time) & (ds.time <= next_time)
        elif it == N_tables - 2:
            left = (this_time <= ds.time) & (ds.time < midpoint)
            right = ds.time >= midpoint
        else:
            left = (this_time <= ds.time) & (ds.time <= midpoint)
            right = (midpoint < ds.time) & (ds.time <= next_time)

        this_table = this_table.reset_coords(drop=True)
        next_table = next_table.reset_coords(drop=True)
        for variable in ["n", "R"]:
            ds[variable] = xr.where(
                left,
                ds[variable] * this_table,
                ds[variable],
            )
            ds[variable] = xr.where(
                right,
                ds[variable] * next_table,
                ds[variable],
            )

    return ds


@xr.register_dataset_accessor("feeps")
class FeepsAccessor:
    r"""Xarray accessor for FEEPS datasets."""

    def __init__(self, ds: xr.Dataset) -> None:
        r"""Validate and initialize accessor for a dataset.

        Parameters
        ----------
        ds : Dataset
            Xarray dataset

        """
        validate_dataset(ds, "FEEPS", ["FEEPS"])
        self._ds = ds.pint.quantify()

    @property
    def eyes(self) -> list[int]:
        r"""Return the eyes in this dataset."""
        if (name := self._ds.species.name) not in ["ion", "elc"]:
            msg = "Cannot determine species from metadata."
            raise ValueError(msg)

        if name == "ion":
            return [6, 7, 8]

        return [1, 2, 3, 4, 5, 9, 10, 11, 12]

    def mask_data(
        self,
        keep_bad_eyes: bool = False,
        remove_one_count: bool = False,
        error_tolerance: u.Quantity = u("100 %"),
    ) -> xr.Dataset:
        r"""Mask dataset using all tables."""
        ds = self._ds.copy()
        ds = ds.isel(energy_channel=slice(1, -1))

        # Remove non-sensical error
        mask = ds.sigma >= 0
        for variable in ["n", "R", "sigma"]:
            ds[variable] = xr.where(mask, ds[variable], np.nan)

        ds = ds.feeps.apply_energy_correction_table(keep_bad_eyes)
        ds = ds.feeps.apply_flat_field_correction(keep_bad_eyes)
        ds = ds.feeps.remove_bad_eyes()
        ds = ds.feeps.remove_sun_contamination()

        if remove_one_count:
            for variable in ["n", "R"]:
                ds[variable] = xr.where(
                    ds.sigma < error_tolerance,
                    ds[variable],
                    np.nan,
                )

        return ds

    def apply_energy_correction_table(
        self,
        keep_bad_eyes: bool = False,
    ) -> xr.Dataset:
        r"""Apply energy correction table.

        Parameters
        ----------
        keep_bad_eyes : bool
            Toggle to keep the bad eyes.

        Returns
        -------
        ds : Dataset
            Dataset corrected with new energies

        """
        ds = self._ds.copy()

        table = (
            get_energy_table(keep_bad_eyes)
            .sel(probe=ds.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        ds["W"] = table
        return ds

    def apply_flat_field_correction(
        self,
        keep_bad_eyes: bool = False,
    ) -> xr.Dataset:
        r"""Apply flat field correction.

        Parameters
        ----------
        keep_bad_eyes : bool
            Toggle to keep the bad eyes.

        Returns
        -------
        ds : Dataset
            Dataset corrected with flat field factors

        """
        ds = self._ds.copy()

        table = (
            get_flat_field_table(keep_bad_eyes)
            .sel(probe=ds.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        for variable in ["n", "R", "sigma"]:
            attrs = ds[variable].attrs
            ds[variable] = ds[variable] * table
            ds[variable].attrs.update(attrs)

        return ds

    def remove_bad_eyes(self) -> xr.Dataset:
        r"""Remove bad eyes.

        Returns
        -------
        ds : Dataset
            Dataset with bad eyes masked using both time-dependent and
            time-independent tables.

        """
        ds = self._ds.copy()

        table = (
            get_time_independent_bad_eye_table()
            .sel(probe=ds.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )
        for variable in ["n", "R", "sigma"]:
            attrs = ds[variable].attrs
            ds[variable] = ds[variable] * table
            ds[variable].attrs.update(attrs)

        table = (
            get_time_dependent_bad_eye_table()
            .sel(probe=ds.attrs["probe"], eye=self.eyes)
            .reset_coords(drop=True)
        )

        return _apply_time_dependent_table(ds, table)

    def remove_sun_contamination(self) -> xr.Dataset:
        r"""Remove sun contamination.

        Returns
        -------
        ds : Dataset
            Dataset with bad eyes masked using sun contamination tables.

        """
        ds = self._ds.copy()

        table = (
            get_sun_contamination_table()
            .sel(probe=ds.attrs["probe"], eye=self.eyes)
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
                left = ds.time <= midpoint
                right = (midpoint < ds.time) & (ds.time <= next_time)
            elif it == N_tables - 2:
                left = (this_time <= ds.time) & (ds.time < midpoint)
                right = ds.time >= midpoint
            else:
                left = (this_time <= ds.time) & (ds.time <= midpoint)
                right = (midpoint < ds.time) & (ds.time <= next_time)

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
                ds.spin_sector_number == this_bad_sector,
                1,
                0,
            ).sum(dim="spin_sector")
            next_bad = xr.where(
                ds.spin_sector_number == next_bad_sector,
                1,
                0,
            ).sum(dim="spin_sector")

            kw = {"time": ds.time, "sensor": ds.sensor, "eye": ds.eye}
            left_mask = (left & (this_bad == 1)).sel(**kw)
            right_mask = (right & (next_bad == 1)).sel(**kw)

            for variable in ["n", "R", "sigma"]:
                ds[variable] = xr.where(~left_mask, ds[variable], np.nan)
                ds[variable] = xr.where(~right_mask, ds[variable], np.nan)

        return ds
