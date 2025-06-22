"""Provide xarray accessor for FPI datasets."""

__all__ = ["FpiAccessor"]

import numpy as np
import xarray as xr

from mmspy.compute.utils import match_time_resolution
from mmspy.compute.vector import cross
from mmspy.configure.units import units as u
from mmspy.configure.xarray.utils import validate_dataset


def spherical_dot(
    angle_1: tuple[xr.DataArray, xr.DataArray],
    angle_2: tuple[xr.DataArray, xr.DataArray],
) -> xr.DataArray:
    """Calculate the dot product in spherical coordinates.

    ..todo:: Migrate this function to `mmspy.compute` and add tests

    Parameters
    ----------
    angle_1 : 2-tuple of DataArray
        (theta, phi) pair for the first vector
    angle_2 : 2-tuple of DataArray
        (theta, phi) pair for the second vector

    Returns
    -------
    dot : DataArray
        Dot product of the two vectors

    """
    t1 = angle_1[0].pint.to("rad")
    t2 = angle_2[0].pint.to("rad")
    p1 = angle_1[1].pint.to("rad")
    p2 = angle_2[1].pint.to("rad")
    return np.sin(t1) * np.sin(t2) * np.cos(p1 - p2) + np.cos(t1) * np.cos(t2)


def spherical_angle(vector: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    """Calculate the spherical angles of a vector in Cartesian coordinates.

    ..todo:
        Migrate this function to `mmspy.compute` and add tests

    Parameters
    ----------
    vector : DataArray
        Vector in cartesian coordinates

    Returns
    -------
    angle : 2-tuple of DataArray
        (theta, phi) pair of the input vector

    """
    vector = vector.copy()
    vx = vector.sel(rank_1="x")
    vy = vector.sel(rank_1="y")
    vz = vector.sel(rank_1="z")
    v_mag = np.sqrt(vx**2 + vy**2 + vz**2)

    theta = np.degrees(np.arccos(vz / v_mag))
    phi = np.degrees(np.arctan2(vy, vx)) % u("360.0 deg")
    return (theta, phi)


@xr.register_dataset_accessor("fpi")
class FpiAccessor:
    """Xarray accessor for FPI datasets."""

    psd_variable: str
    energy_variable: str
    zenith_variable: str
    azimuth_variable: str

    def __init__(self, dataset: xr.Dataset) -> None:
        """Validate and initialize accessor for a dataset.

        Parameters
        ----------
        dataset : Dataset
            Xarray dataset

        """
        validate_dataset(dataset, "FPI", ["DIS", "DES"])
        self._dataset = dataset.pint.quantify()
        variables = list(self._dataset.data_vars)
        coords = list(self._dataset.coords)
        for variable in variables + coords:
            array = self._dataset[variable]
            if not bool(array.pint.units):
                continue

            DESC = array.attrs.get("CATDESC", "")
            if (
                "sky-map instrument distribution" in DESC
                and "error" not in DESC
            ):
                self.psd_variable = variable
            if "energies" in DESC and "delta" not in DESC:
                self.energy_variable = variable
            if "zenith angles" in DESC and "bin delta" not in DESC:
                self.zenith_variable = variable
            if "azimuth angles" in DESC and "bin delta" not in DESC:
                self.azimuth_variable = variable

    def correct_for_spacecraft_potential(
        self,
        spacecraft_potential: xr.DataArray,
        average: bool = False,
    ) -> xr.Dataset:
        """Subtract spacecraft potential from the recorded energy.

        Parameters
        ----------
        spacecraft_potential: DataArray
            Potential from EDP scpot data
        average : bool
            Whether to average the potential down to FPI resolution.

        Returns
        -------
        dataset : Dataset
            FPI dataset with corrected energies

        """
        dataset = self._dataset.copy()

        V_sc = match_time_resolution(
            spacecraft_potential,
            dataset.time,
            average=average,
        )
        V_sc = xr.DataArray(
            name=V_sc.name,
            data=V_sc.data.to("energy_unit", species := dataset.species.name),
            dims=V_sc.dims,
            coords=V_sc.coords,
            attrs=V_sc.attrs,
        )

        if species == "elc":
            dataset = dataset.assign(
                {
                    self.psd_variable: xr.where(
                        np.abs(V_sc) < dataset[self.energy_variable],
                        dataset[self.psd_variable],
                        0.0,
                    )
                }
            )

        dataset = dataset.assign(
            {self.energy_variable: dataset[self.energy_variable] + V_sc}
        )
        dataset[self.energy_variable].attrs[
            "VAR_NOTES"
        ] += "; Adjusted for spacecraft potential"

        return dataset

    def add_field_aligned_coordinates(
        self,
        magnetic_field: xr.DataArray,
        reference_vector: xr.DataArray = xr.DataArray(
            np.array([0, 1, 0], dtype="f4"),
            coords={"rank_1": ["x", "y", "z"]},
        ).pint.quantify("dimensionless"),
        average: bool = False,
    ) -> xr.Dataset:
        """Add field aligned coordinates.

        Convert the distribution function's support to field-aligned
        coordinates and add to dataset.

        Parameters
        ----------
        magnetic_field: DataArray
            Magnetic field from from FGM
        reference_vector: DataArray
            A reference vector used to construct an orthogonal triad
            for FAC (typically one mostly perpendicular to the magnetic
            field)
        average : bool
            Whether to average the magnetic field down to FPI resolution.

        Returns
        -------
        dataset : Dataset
            FPI dataset with corrected energies

        """
        dataset = self._dataset.copy()

        # Interpolate inputs onto ds time resolution
        kw = {"target": dataset.time, "average": average}
        B = match_time_resolution(magnetic_field, **kw)
        if "time" in reference_vector.dims:
            reference_vector = match_time_resolution(reference_vector, **kw)

        # Construct unit vectors
        e3 = B / B.tensor.magnitude
        e1 = cross(reference_vector, e3, dim="rank_1")
        e1 = e1 / e1.tensor.magnitude  # type: ignore
        e2 = cross(e3, e1, dim="rank_1")

        # Calculate decomposition
        V_angle = (
            dataset[self.zenith_variable],
            dataset[self.azimuth_variable],
        )
        V_perp_1 = spherical_dot(V_angle, spherical_angle(e1))
        V_perp_2 = spherical_dot(V_angle, spherical_angle(e2))
        V_para = spherical_dot(V_angle, spherical_angle(e3))

        theta = np.degrees(np.arccos(V_para))
        phi = np.degrees(np.arctan2(V_perp_2, V_perp_1)) % u("360 deg")

        dataset = dataset.assign(B_avg=B, theta_fac=theta, phi_fac=phi)
        dataset = dataset.set_coords(["theta_fac", "phi_fac"])
        dataset = dataset.transpose(
            "time",
            "energy_channel",
            "azimuthal_sector",
            "zenith_sector",
            ...,
        )

        return dataset
