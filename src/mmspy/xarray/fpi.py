r"""Provide xarray accessor for FPI datasets."""

__all__ = [
    "FpiAccessor",
]

import numpy as np
import xarray as xr
from pint import application_registry as u

from mmspy.computation.vector import cross
from mmspy.utils.timing import match_time_resolution
from mmspy.xarray._utils import validate_dataset


def spherical_dot(
    angle_1: tuple[xr.DataArray, xr.DataArray],
    angle_2: tuple[xr.DataArray, xr.DataArray],
) -> xr.DataArray:
    r"""Calculate the dot product in spherical coordinates.

    ..todo:: Migrate this function to `mmsws.computation` and add tests

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
    r"""Calculate the spherical angles of a vector in Cartesian coordinates.

    ..todo:
        Migrate this function to `mmsws.computation` and add tests

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
    vx = vector.sel(space_rank_1="x")
    vy = vector.sel(space_rank_1="y")
    vz = vector.sel(space_rank_1="z")
    v_mag = np.sqrt(vx**2 + vy**2 + vz**2)

    theta = np.degrees(np.arccos(vz / v_mag))
    phi = np.degrees(np.arctan2(vy, vx)) % u("360.0 deg")
    return (theta, phi)


@xr.register_dataset_accessor("fpi")
class FpiAccessor:
    r"""Xarray accessor for FPI datasets."""

    def __init__(self, ds: xr.Dataset) -> None:
        r"""Validate and initialize accessor for a dataset.

        Parameters
        ----------
        ds : Dataset
            Xarray dataset

        """
        validate_dataset(ds, "FPI", ["DIS", "DES"])
        self._ds = ds.pint.quantify()

    def correct_for_spacecraft_potential(
        self,
        spacecraft_potential: xr.DataArray,
        average: bool = True,
    ) -> xr.Dataset:
        r"""Subtract spacecraft potential from the recorded energy.

        Parameters
        ----------
        spacecraft_potential: DataArray
            Potential from EDP scpot data
        average : bool
            Whether to average the potential down to FPI resolution.

        Returns
        -------
        ds : Dataset
            FPI dataset with corrected energies

        """
        ds = self._ds.copy()

        V_sc = match_time_resolution(
            spacecraft_potential,
            ds.time,
            average=average,
        )
        V_sc = xr.DataArray(
            name=V_sc.name,
            data=V_sc.data.to("energy_unit", species := ds.species.name),
            dims=V_sc.dims,
            coords=V_sc.coords,
            attrs=V_sc.attrs,
        )

        if species == "elc":
            ds = ds.assign(f=xr.where(np.abs(V_sc) < ds.W, ds.f, 0.0))

        ds = ds.assign(W=ds.W + V_sc)
        ds.W.attrs["VAR_NOTES"] += "; Adjusted for spacecraft potential"

        return ds

    def add_field_aligned_coordinates(
        self,
        magnetic_field: xr.DataArray,
        reference_vector: xr.DataArray = xr.DataArray(
            np.array([0, 1, 0], dtype="f4"),
            coords={"space_rank_1": ["x", "y", "z"]},
        ).pint.quantify("dimensionless"),
        average: bool = True,
    ) -> xr.Dataset:
        r"""Add field aligned coordinates.

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
        ds : Dataset
            FPI dataset with corrected energies

        """
        ds = self._ds.copy()

        # Interpolate inputs onto ds time resolution
        kw = {"target": ds.time, "average": average}
        B = match_time_resolution(magnetic_field, **kw)
        if "time" in reference_vector.dims:
            reference_vector = match_time_resolution(reference_vector, **kw)

        # Construct unit vectors
        e3 = B / B.rank_1.magnitude
        e1 = cross(reference_vector, e3, dim="space_rank_1")
        e1 = e1 / e1.rank_1.magnitude  # type: ignore
        e2 = cross(e3, e1, dim="space_rank_1")

        # Calculate decomposition
        V_angle = (ds.theta_dbcs, ds.phi_dbcs)
        V_perp_1 = spherical_dot(V_angle, spherical_angle(e1))
        V_perp_2 = spherical_dot(V_angle, spherical_angle(e2))
        V_para = spherical_dot(V_angle, spherical_angle(e3))

        theta = np.degrees(np.arccos(V_para))
        phi = np.degrees(np.arctan2(V_perp_2, V_perp_1)) % u("360 deg")

        return ds.assign(B_avg=B, theta_fac=theta, phi_fac=phi)
