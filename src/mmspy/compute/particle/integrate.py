import numpy as np
import pandas as pd
import xarray as xr

from mmspy.compute.utils import match_time_resolution
from mmspy.configure.units import units as u


def precondition_dataset(
    ds,
    variable,
    zenith,
    azimuth,
    mask_level,
    normalize_jacobian,
):
    ds = ds.pint.quantify()

    # -- Apply mask using 1-count error
    if f"{variable}_err" in ds:
        threshold = 1.01 * np.sqrt(mask_level)
        mask = ds[variable] > (threshold * ds[f"{variable}_err"])
        ds[variable] = xr.where(mask, ds[variable], 0.0)
        ds[f"{variable}_err"] = xr.where(mask, ds[f"{variable}_err"], 0.0)

    # -- Calculate zenith jacobian
    ds = ds.set_coords(zenith)
    theta = ds[zenith].pint.to("rad")
    theta.attrs["spacing"] = theta.diff(theta.dims[0]).min().compute().data
    theta_jacobian = np.sin(theta)
    if normalize_jacobian:
        theta_jacobian /= theta_jacobian.integrate(zenith)
    ds[zenith] = theta
    ds[f"{zenith}_jacobian"] = theta_jacobian

    # -- Calculate azimuthal jacobian if available
    if azimuth not in ds:
        return ds

    ds = ds.set_coords(azimuth)
    phi = ds[azimuth].pint.to("rad")
    phi.attrs["spacing"] = phi.diff(phi.dims[0]).min().compute().data
    phi_jacobian = xr.ones_like(phi)
    if normalize_jacobian:
        phi_jacobian /= phi_jacobian.integrate(azimuth)
    ds[azimuth] = phi
    ds[f"{azimuth}_jacobian"] = phi_jacobian

    return ds


def reduce_distribution(
    ds,
    variable="f",
    zenith="theta",
    azimuth=None,
    mask_level=0.0,
    normalize_jacobian=False,
):
    # -- Precondition and unpack dataset
    ds = precondition_dataset(
        ds,
        variable,
        zenith,
        azimuth,
        mask_level,
        normalize_jacobian,
    )
    f = ds[variable]
    if has_error := (f"{variable}_err" in ds):
        f_err = ds[f"{variable}_err"]

    # -- Azimuthal integration
    if azimuth in ds:
        azimuth_jacobian = ds[f"{azimuth}_jacobian"]
        ds[f"{variable}_phi"] = (f * azimuth_jacobian).integrate(azimuth)
        if has_error:
            ds[f"{variable}_phi_err"] = ds[azimuth].spacing * np.sqrt(
                ((f_err * azimuth_jacobian) ** 2).sum(azimuth_jacobian.dims)
            )
    else:
        ds[f"{variable}_phi"] = f.copy()
        if has_error:
            ds[f"{variable}_phi_err"] = f_err.copy()

    # -- Zenith integration
    zenith_jacobian = ds[f"{zenith}_jacobian"]
    ds[f"{variable}_omni"] = (
        ds[f"{variable}_phi"] * zenith_jacobian
    ).integrate(zenith)
    if has_error:
        ds[f"{variable}_omni_err"] = ds[zenith].spacing * np.sqrt(
            ((ds[f"{variable}_phi_err"] * zenith_jacobian) ** 2).sum(
                zenith_jacobian.dims
            )
        )

    return ds.transpose("time", ...)


def integrate_distribution(
    f,
    energy="W",
    zenith="theta",
    azimuth="phi",
    flip_direction=True,
    density=None,
    W0=u("100 eV"),
):
    # -- Extract particle information
    mass = f.species.mass

    # -- Conversion
    # PSD
    f = f.pint.quantify().pint.to("phase_space_density_unit").fillna(0.0)
    # Particle support
    f = f.assign_coords(
        u=(f[energy] / (f[energy] + W0)).pint.to("dimensionless")
    )
    f[zenith] = f[zenith].pint.to("rad")
    f[azimuth] = f[azimuth].pint.to("rad")

    # -- Calculate the jacobian
    v = np.sqrt(2 * W0 / mass) * np.sqrt(f.u / (1 - f.u))
    theta = f[zenith]
    phi = f[azimuth]
    dv = np.sqrt(2) * (W0 / mass) ** 1.5 * np.sqrt(f.u) / (1 - f.u) ** 2.5
    dtheta = np.sin(theta)
    dphi = xr.ones_like(phi)
    jacobian = dv * dtheta * dphi
    dims = ("u", zenith, azimuth)

    # -- Integrate
    # Density
    N = (f * jacobian).integrate(dims).pint.to("number_density_unit")
    N = xr.where(N > 0, N, np.nan)
    N_ = (
        N
        if density is None
        else match_time_resolution(density, N.time, average=False)
    )

    # Velocity
    sign = -1 if flip_direction else 1
    vx = sign * v * np.sin(theta) * np.cos(phi)
    vy = sign * v * np.sin(theta) * np.sin(phi)
    vz = sign * v * np.cos(theta)
    Vx = (f * vx * jacobian).integrate(dims) / N_
    Vy = (f * vy * jacobian).integrate(dims) / N_
    Vz = (f * vz * jacobian).integrate(dims) / N_
    V = xr.combine_nested(
        [Vx, Vy, Vz],
        concat_dim=[pd.Index(["x", "y", "z"], name="rank_1")],
    ).pint.to("velocity_unit")

    # Pressure
    Pxx = mass * ((f * vx * vx * jacobian).integrate(dims) - N_ * Vx * Vx)
    Pyy = mass * ((f * vy * vy * jacobian).integrate(dims) - N_ * Vy * Vy)
    Pzz = mass * ((f * vz * vz * jacobian).integrate(dims) - N_ * Vz * Vz)
    Pxy = mass * ((f * vx * vy * jacobian).integrate(dims) - N_ * Vx * Vy)
    Pxy = mass * ((f * vx * vy * jacobian).integrate(dims) - N_ * Vx * Vy)
    Pxz = mass * ((f * vx * vz * jacobian).integrate(dims) - N_ * Vx * Vz)
    Pyz = mass * ((f * vy * vz * jacobian).integrate(dims) - N_ * Vy * Vz)
    P = xr.combine_nested(
        [Pxx, Pyy, Pzz, Pxy, Pxz, Pyz],
        concat_dim=[
            pd.Index(
                ["xx", "yy", "zz", "xy", "xz", "yz"],
                name="rank_2",
            ),
        ],
    ).pint.to("pressure_unit")

    return (
        xr.Dataset({"N": N, "V": V, "P": P})
        .transpose("time", ...)
        .pint.quantify()
    )
