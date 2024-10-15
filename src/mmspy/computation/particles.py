r"""Provides functionality for particle distribution calculations."""

__all__ = [
    "smooth_distribution",
    "interpolate_2d_distribution",
    "interpolate_3d_distribution",
    "integrate_3d_distribution",
]

from typing import TypeAlias

import astropy.units as u
import numpy as np
import pandas as pd
import xarray as xr
from astropy.convolution import Gaussian2DKernel, convolve
from astropy.units.typing import QuantityLike
from numpy.typing import NDArray
from scipy.interpolate import griddata
from scipy.spatial._qhull import QhullError

UnitLike: TypeAlias = str | u.Unit


def smooth_distribution(
    da: xr.DataArray,
    dim: int = 2,
    sigma: float = 1.0,
    **kwargs,
) -> xr.DataArray:
    r"""Apply a smoothing kernel on a 2D/3D distribution function.

    Parameters
    ----------
    da : DataArray
        Xarray data array
    dim : int
        2 or 3
    sigma : float
        How large the kernel is, only applicable for dim = 2
    **kwargs : dict
        Additional keywords for `~astropy.convolution.convolve`

    Returns
    -------
    smoothed_da : DataArray
        Smoothed data array

    """

    def _smooth_chunk(data: NDArray) -> NDArray:
        match dim:
            case 2:
                kernel = Gaussian2DKernel(sigma)
            case 3:
                kernel = np.array(
                    [
                        [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
                        [[0, 1, 0], [2, 3, 2], [0, 1, 0]],
                        [[0, 0, 0], [0, 2, 0], [0, 0, 0]],
                    ],
                )
            case _:
                msg = "Smoothing only supporting 2 or 3D"
                raise NotImplementedError(msg)

        return convolve(
            data.squeeze(),
            kernel,
            **kwargs,
        )[np.newaxis, ...]

    da = da.copy()

    if "time" not in da.dims:
        da = da.expand_dims("time")

    da = da.chunk(time=1)
    return xr.DataArray(
        name=da.name,
        data=da.data.map_blocks(
            _smooth_chunk,
            meta=np.array((), dtype=da.dtype),
        ),
        coords=da.coords,
        attrs=da.attrs,
    )


def interpolate_2d_distribution(  # noqa: PLR0913
    f: xr.DataArray,
    W: xr.DataArray,
    theta: xr.DataArray,
    W_grid: QuantityLike = u.Quantity(np.logspace(0.0, 5.0, 51), "eV"),
    theta_grid: QuantityLike = u.Quantity(np.linspace(0.0, 180.0, 19), "deg"),
    method: str = "nearest",
    drop_nan: bool = False,
    roll: bool = False,
) -> xr.DataArray:
    r"""Interpolate a 2D distribution function onto a regular grid.

    Parameters
    ----------
    f : DataArray
        Distribution function
    W : DataArray
        Energy
    theta : DataArray
        Zenith angle
    W_grid: QuantityLike
        Energy grid
    theta_grid: QuantityLike
        Zenith angle grid
    method : {"nearest", "linear"}
        Interpolation method
    drop_nan : bool
        Whether to drop invalid data before interpolation
    roll : bool
        Whether to chunk data into a rolling window. By default, the
            interpolation is applied onto the distribution in chunks of
            one time step.

    Returns
    -------
    interpolated_da : DataArray
        Interpolated distribution

    """

    def _interpolate_chunk(data_chunk: NDArray) -> NDArray:
        # Unpack value and coordinates
        data_chunk = data_chunk.squeeze()
        value = data_chunk[..., 0].flatten()
        W_coord = data_chunk[..., 1].flatten()
        theta_coord = data_chunk[..., 2].flatten()
        coord = np.vstack((W_coord, theta_coord)).T

        # First filter out bad coordinates
        good_coord = np.isfinite(coord).all(axis=1)
        value = value[good_coord]
        coord = coord[good_coord, :]

        # Handle all invalid chunks
        good_value = np.isfinite(value)
        number_of_good_samples = 4 if method == "linear" else 0
        if len(value[good_value]) <= number_of_good_samples:
            return np.nan * np.ones((1, *chunk_shape))

        # Calculate results and mask out-of-bound data
        kw = {
            "points": coord[good_value, :] if drop_nan else coord,
            "values": value[good_value] if drop_nan else value,
            "xi": (
                np.log10(W_grid[:, np.newaxis].value),
                theta_grid[np.newaxis, :].value,
            ),
        }
        try:
            results = griddata(method=method, **kw)
        except QhullError:
            return np.nan * np.ones((1, *chunk_shape))
            #  results = griddata(method="nearest", **kw)

        # Mask data outside valid energy range
        log_W_grid = np.log10(W_grid.value)
        log_W_min = np.nanmin(coord[:, 0])
        log_W_max = np.nanmax(coord[:, 0])
        out_of_bound = (log_W_grid > log_W_max) | (log_W_grid < log_W_min)
        results[out_of_bound, :] = np.nan

        return results[np.newaxis, ...]

    # Convert units and calculate log scales
    with xr.set_options(keep_attrs=True):
        log_f = np.log10(xr.where(f > 0.0, f.copy(), np.nan))
        log_W = np.log10(
            xr.where(W > 0.0, W.copy().units.to(W_grid.unit), np.nan),
        )
        theta = theta.copy().units.to(theta_grid.unit)

    # Stack values and coordinates into samples and chunk
    da = (
        xr.merge([log_f, log_W, theta])  # type: ignore
        .stack(sample=tuple(filter(lambda item: item != "time", f.dims)))
        .to_dataarray()
    )
    if "time" not in da.dims:
        da = da.expand_dims("time")

    if roll:
        da = (
            da.rolling(time=65, center=True)
            .construct("window")
            .transpose("time", "window", "sample", "variable")
        )
        drop_axis = (1, 2, 3)
    else:
        da = da.transpose("time", "sample", "variable")
        drop_axis = (1, 2)  # type: ignore

    da = da.chunk(time=1)

    # Map blocks
    chunk_shape = (W_grid.size, theta_grid.size)
    da = xr.DataArray(
        name=f.name,
        data=10.0
        ** da.data.map_blocks(
            _interpolate_chunk,
            meta=np.array((), dtype=da.dtype),
            chunks=(1, *chunk_shape),
            drop_axis=drop_axis,
            new_axis=(1, 2),
        ),
        coords={
            "time": da.time,
            "W": W_grid.value,
            "theta": theta_grid.value,
        },
    ).squeeze()

    # Populate attributes
    da.attrs.update(units=str(f.units.from_metadata))
    da.W.attrs.update(units=str(W_grid.unit))
    da.theta.attrs.update(units=str(theta_grid.unit))

    return da


def interpolate_3d_distribution(  # noqa: PLR0913
    f: xr.DataArray,
    W: xr.DataArray,
    theta: xr.DataArray,
    phi: xr.DataArray,
    W_grid: QuantityLike = u.Quantity(np.logspace(0.0, 5.0, 51), "eV"),
    theta_grid: QuantityLike = u.Quantity(np.linspace(0.0, 180.0, 19), "deg"),
    phi_grid: QuantityLike = u.Quantity(np.linspace(0.0, 360.0, 37), "deg"),
    method: str = "nearest",
    drop_nan: bool = False,
) -> xr.DataArray:
    r"""Interpolate a 3D distribution function onto a regular grid.

    Parameters
    ----------
    f : DataArray
        Distribution function
    W : DataArray
        Energy
    theta : DataArray
        Zenith angle
    phi : DataArray
        Azimuthal angle
    W_grid: QuantityLike
        Energy grid
    theta_grid: QuantityLike
        Zenith angle grid
    phi_grid : QuantityLike
        Azimuthal angle grid
    method : {"nearest", "linear"}
        Interpolation method
    drop_nan : bool
        Whether to drop invalid data before interpolation

    Returns
    -------
    interpolated_da : DataArray
        Interpolated distribution

    """

    def _interpolate_chunk(data_chunk: NDArray) -> NDArray:
        # Unpack value and coordinates
        data_chunk = data_chunk.squeeze()
        value = data_chunk[:, 0]
        coord = data_chunk[:, 1:4]

        # First filter out bad coordinates
        good_coord = np.isfinite(coord).all(axis=1)
        value = value[good_coord]
        coord = coord[good_coord, :]

        # Handle all invalid chunks
        good_value = np.isfinite(value)
        number_of_good_samples = 4 if method == "linear" else 0
        if len(value[good_value]) <= number_of_good_samples:
            return np.nan * np.ones((1, *chunk_shape))

        # Calculate results and mask out-of-bound data
        results = griddata(
            coord[good_value, :] if drop_nan else coord,
            value[good_value] if drop_nan else value,
            (
                np.log10(W_grid[:, np.newaxis, np.newaxis].value),
                theta_grid[np.newaxis, :, np.newaxis].value,
                phi_grid[np.newaxis, np.newaxis, :].value,
            ),
            method=method,
        )

        # Mask data outside valid energy range
        log_W_grid = np.log10(W_grid.value)
        log_W_min = np.min(coord[:, 0])
        log_W_max = np.max(coord[:, 0])
        out_of_bound = (log_W_grid > log_W_max) | (log_W_grid < log_W_min)
        results[out_of_bound, :, :] = np.nan

        return results[np.newaxis, ...]

    # Convert units and calculate log scales
    with xr.set_options(keep_attrs=True):
        log_f = np.log10(xr.where(f > 0.0, f.copy(), np.nan))
        log_W = np.log10(
            xr.where(W > 0.0, W.copy().units.to(W_grid.unit), np.nan),
        )
        theta = theta.copy().units.to(theta_grid.unit)
        phi = phi.copy().units.to(theta_grid.unit)

    # Stack values and coordinates into samples and chunk
    da = (
        xr.merge([log_f, log_W, theta, phi])  # type: ignore
        .stack(sample=tuple(filter(lambda item: item != "time", f.dims)))
        .to_dataarray()
    )
    if "time" not in da.dims:
        da = da.expand_dims("time")

    da = da.transpose("time", "sample", "variable").chunk(time=1)

    # Map blocks
    chunk_shape = (W_grid.size, theta_grid.size, phi_grid.size)
    da = xr.DataArray(
        name=f.name,
        data=10.0
        ** da.data.map_blocks(
            _interpolate_chunk,
            meta=np.array((), dtype=da.dtype),
            chunks=(1, *chunk_shape),
            drop_axis=(1, 2),
            new_axis=(1, 2, 3),
        ),
        coords={
            "time": da.time,
            "W": W_grid.value,
            "theta": theta_grid.value,
            "phi": phi_grid.value,
        },
    ).squeeze()

    # Populate attributes
    da.attrs.update(units=str(f.units.from_metadata))
    da.W.attrs.update(units=str(W_grid.unit))
    da.theta.attrs.update(units=str(theta_grid.unit))
    da.phi.attrs.update(units=str(phi_grid.unit))

    return da


def integrate_3d_distribution(  # noqa: PLR0913
    f: xr.DataArray,
    N_unit: UnitLike = u.Unit("cm-3"),
    V_unit: UnitLike = u.Unit("km/s"),
    P_unit: UnitLike = u.Unit("nPa"),
    F_unit: UnitLike = u.Unit("cm-2 s-1 sr-1"),
    flip_aspect: bool = True,
) -> xr.Dataset:
    r"""Integrate a 3D distribution function for its plasma moments.

    Parameters
    ----------
    f : DataArray
        Distribution function
    N_unit : UnitLike
        Density unit
    V_unit : UnitLike
        Velocity unit
    P_unit : UnitLike
        Pressure unit
    F_unit : UnitLike
        Energy flux unit
    flip_aspect : bool
        If the distribution function is in DBCS, the velocity is in
            look direction and needs to be flipped to turn into
            plasma frame.

    Returns
    -------
    ds : Dataset
        Dataset containing the plasma moments

    """
    N_unit = u.Unit(N_unit)
    V_unit = u.Unit(V_unit)
    P_unit = u.Unit(P_unit)
    F_unit = u.Unit(F_unit)
    W_unit = f.W.units.from_metadata
    f_unit = N_unit / V_unit**3
    m = f.species.mass

    # Unpack components
    f = f.copy().units.to(f_unit).fillna(0.0)
    W = f.W
    V_mag = np.sqrt(2 * W) * np.sqrt(W_unit / m).to(V_unit).value
    f = f.assign_coords(
        log_V=np.log10(V_mag),
        theta=f.theta.units.to("rad"),
        phi=f.phi.units.to("rad"),
    )

    # Calculate domain and solid angle
    theta = f.theta
    phi = f.phi
    dOmega = (V_mag**3 * np.log(10)) * np.sin(theta) * xr.ones_like(phi)
    integrate_dims = ["phi", "theta", "log_V"]

    # ---- Integrate density
    N = (f * dOmega).integrate(integrate_dims)
    N = xr.where(N != 0.0, N, np.nan)
    N.attrs.update(units=str(N_unit))

    # ---- Integrate velocity
    velocity_sign = -1 if flip_aspect else 1
    Vx = velocity_sign * V_mag * np.sin(theta) * np.cos(phi)
    Vy = velocity_sign * V_mag * np.sin(theta) * np.sin(phi)
    Vz = velocity_sign * V_mag * np.cos(theta) * xr.ones_like(phi)
    Vx_int = (f * Vx * dOmega).integrate(integrate_dims) / N
    Vy_int = (f * Vy * dOmega).integrate(integrate_dims) / N
    Vz_int = (f * Vz * dOmega).integrate(integrate_dims) / N
    V = xr.combine_nested(
        [Vx_int, Vy_int, Vz_int],
        concat_dim=[pd.Index(["x", "y", "z"], name="space_rank_1")],
    ).assign_attrs(units=str(V_unit))

    # ---- Integrate pressure tensor
    factor_1 = (m * f_unit * V_unit**5).to(P_unit).value
    factor_2 = (m * N_unit * V_unit**2).to(P_unit).value
    Pxx_int = (f * Vx * Vx * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vx_int * Vx_int * factor_2
    Pxy_int = (f * Vx * Vy * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vx_int * Vy_int * factor_2
    Pxz_int = (f * Vx * Vz * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vx_int * Vz_int * factor_2
    Pyy_int = (f * Vy * Vy * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vy_int * Vy_int * factor_2
    Pyz_int = (f * Vy * Vz * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vy_int * Vz_int * factor_2
    Pzz_int = (f * Vz * Vz * dOmega * factor_1).integrate(
        integrate_dims,
    ) - N * Vz_int * Vz_int * factor_2
    P = xr.combine_nested(
        [Pxx_int, Pyy_int, Pzz_int, Pxy_int, Pxz_int, Pyz_int],
        concat_dim=[
            pd.Index(
                ["xx", "yy", "zz", "xy", "xz", "yz"],
                name="space_rank_2",
            ),
        ],
    ).assign_attrs(units=str(P_unit))

    # ---- Integrate energy flux
    dims = ["phi", "theta"]
    dOmega = np.sin(theta) * xr.ones_like(phi)
    Omega = dOmega.integrate(dims)
    integrand = (0.5 * V_mag**4 * f * dOmega) * (V_unit**4 * f_unit).to(
        F_unit * u.Unit("sr"),
    )
    F_omni = integrand.integrate(dims) / Omega
    F_omni.attrs.update(units=str(F_unit))

    return (
        xr.Dataset(
            {
                "N": N,
                "V": V,
                "P": P,
                "F_omni": F_omni,
            },
        )
        .transpose("time", ...)
        .drop("log_V")
    )
