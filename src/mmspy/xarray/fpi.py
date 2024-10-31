r"""Provide xarray accessor for FPI datasets."""

__all__ = [
    "FpiAccessor",
]

import numpy as np
import xarray as xr

from mmspy.utils.timing import match_time_resolution

from ._utils import validate_dataset


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
    t1 = angle_1[0].pint.quantify().to("rad")
    t2 = angle_2[0].pint.quantify().to("rad")
    p1 = angle_1[1].pint.quantify().to("rad")
    p2 = angle_2[1].pint.quantify().to("rad")
    return (
        np.sin(t1) * np.sin(t2) * np.cos(p1 - p2) + np.cos(t1) * np.cos(t2)
    ).pint.dequantify()


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
    theta.attrs.update(units="deg")

    phi = np.degrees(np.arctan2(vy, vx)) % 360.0
    phi.attrs.update(units="deg")

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
    ) -> xr.Dataset:
        r"""Subtract spacecraft potential from the recorded energy.

        Parameters
        ----------
        spacecraft_potential: DataArray
            Potential from EDP scpot data

        Returns
        -------
        ds : Dataset
            FPI dataset with corrected energies

        """
        ds = self._ds.copy()

        Phi = match_time_resolution(
            spacecraft_potential.pint.dequantify(),
            ds.time,
        ).pint.quantify()
        Phi = (ds.species.charge * Phi).pint.to(ds.W.pint.units)

        if ds.species.name == "elc":
            dims = ds.f.dims
            f = xr.where(np.abs(Phi) < ds.W, ds.f, 0.0).transpose(*dims)
            ds = ds.assign(f=(dims, f.data, ds.f.attrs))

        ds = ds.assign(W=ds.W + Phi)
        ds.W.attrs["VAR_NOTES"] += "; Adjusted for spacecraft potential"

        return ds

    def add_field_aligned_coordinates(
        self,
        magnetic_field: xr.DataArray,
        reference_vector: xr.DataArray = xr.DataArray(
            np.array([1, 0, 0], dtype="f4"),
            coords={"space_rank_1": ["x", "y", "z"]},
        ),
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
        spatial_dimension : str
            Name of spatial dimension

        Returns
        -------
        ds : Dataset
            FPI dataset with corrected energies

        """
        ds = self._ds.copy()

        # Interpolate inputs onto ds time resolution
        B = match_time_resolution(
            magnetic_field.pint.dequantify(),
            ds.time,
        )
        if "time" in reference_vector.dims:
            reference_vector = match_time_resolution(
                reference_vector.pint.dequantify(),
                ds.time,
            )

        # Construct unit vectors
        e3 = B / B.rank_1.magnitude
        e1 = xr.cross(reference_vector, e3, dim="space_rank_1")
        e1 = e1 / e1.rank_1.magnitude  # type: ignore
        e2 = xr.DataArray(xr.cross(e3, e1, dim="space_rank_1"))

        # Calculate decomposition
        V_angle = (ds.theta_dbcs, ds.phi_dbcs)
        V_perp_1 = spherical_dot(V_angle, spherical_angle(e1))
        V_perp_2 = spherical_dot(V_angle, spherical_angle(e2))
        V_para = spherical_dot(V_angle, spherical_angle(e3))

        ds = ds.assign(
            B_avg=B,
            theta_fac=np.degrees(np.arccos(V_para)),
            phi_fac=np.degrees(np.arctan2(V_perp_2, V_perp_1)) % 360.0,
        )
        ds.B_avg.attrs.update(B.attrs)
        ds.theta_fac.attrs.update(units="deg")
        ds.phi_fac.attrs.update(units="deg")

        return ds
