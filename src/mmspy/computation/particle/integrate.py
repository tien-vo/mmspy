import numpy as np
import pandas as pd
import xarray as xr
from pint import application_registry as u


def integrate_distribution(
    f: xr.DataArray,
    f_err: xr.DataArray | None = None,
    flip_direction: bool = True,
):
    f = f.pint.quantify().pint.to("phase_space_density_unit").fillna(0.0)
    if f_err is not None:
        f_err = (
            f_err.pint.quantify()
            .pint.to("phase_space_density_unit")
            .fillna(0.0)
        )

    # ---- Prepare the support for integration
    # Convert energy to speed
    W = f.W * u(f.W.units).to("energy_unit")
    V = xr.DataArray(
        data=W.data.to("velocity_unit", f.species.name),
        coords=W.coords,
    )
    log_V = np.log10(V.pint.dequantify())
    f = f.assign_coords(log_V=log_V)

    # Convert angles to radians
    f = f.assign_coords(
        theta=(f.theta * u(f.theta.units).to("rad")).pint.dequantify(),
        phi=(f.phi * u(f.phi.units).to("rad")).pint.dequantify(),
    )

    # Calculate solid angle
    theta = f.theta
    phi = f.phi
    dV = V**3 * np.log(10)
    dtheta = np.sin(theta)
    dphi = xr.ones_like(phi)

    # ---- Integrate
    dims = ("theta", "log_V")

    # Collapse in phi
    f_phi = (f * dphi).integrate("phi")
    fx_phi = (f * np.cos(phi) * dphi).integrate("phi")
    fy_phi = (f * np.sin(phi) * dphi).integrate("phi")
    fxx_phi = (f * np.cos(phi) ** 2 * dphi).integrate("phi")
    fyy_phi = (f * np.sin(phi) ** 2 * dphi).integrate("phi")
    fxy_phi = (f * np.sin(phi) * np.cos(phi) * dphi).integrate("phi")
    if f_err is not None:
        f_err = f_err.assign_coords(theta=theta, phi=phi)
        f_err_phi = np.sqrt((f_err**2 * dphi).integrate("phi"))
        mask = f_phi > f_err_phi
        f_phi = xr.where(mask, f_phi, 0.0)
        fx_phi = xr.where(mask, fx_phi, 0.0)
        fy_phi = xr.where(mask, fy_phi, 0.0)
        fxx_phi = xr.where(mask, fxx_phi, 0.0)
        fyy_phi = xr.where(mask, fyy_phi, 0.0)
        fxy_phi = xr.where(mask, fxy_phi, 0.0)

    # Density
    N = (f_phi * dV * dtheta).integrate(dims)
    N = xr.where(N != 0.0, N, np.nan).pint.to("number_density_unit")

    # Velocity
    sign = -1 if flip_direction else 1
    V_perp = sign * V * np.sin(theta)
    V_para = sign * V * np.cos(theta)
    Vx_avg = (fx_phi * V_perp * dV * dtheta).integrate(dims) / N
    Vy_avg = (fy_phi * V_perp * dV * dtheta).integrate(dims) / N
    Vz_avg = (f_phi * V_para * dV * dtheta).integrate(dims) / N
    V_avg = xr.combine_nested(
        [Vx_avg, Vy_avg, Vz_avg],
        concat_dim=[pd.Index(["x", "y", "z"], name="space_rank_1")],
    ).pint.to("velocity_unit")

    # Pressure
    mass = f.species.mass
    Pxx = mass * (
        (fxx_phi * V_perp**2 * dV * dtheta).integrate(dims)
        - N * Vx_avg * Vx_avg
    )
    Pyy = mass * (
        (fyy_phi * V_perp**2 * dV * dtheta).integrate(dims)
        - N * Vy_avg * Vy_avg
    )
    Pzz = mass * (
        (f_phi * V_para**2 * dV * dtheta).integrate(dims)
        - N * Vx_avg * Vx_avg
    )
    Pxy = mass * (
        (fxy_phi * V_perp**2 * dV * dtheta).integrate(dims)
        - N * Vx_avg * Vy_avg
    )
    Pxz = mass * (
        (fx_phi * V_perp * V_para * dV * dtheta).integrate(dims)
        - N * Vx_avg * Vz_avg
    )
    Pyz = mass * (
        (fy_phi * V_perp * V_para * dV * dtheta).integrate(dims)
        - N * Vy_avg * Vz_avg
    )
    P = xr.combine_nested(
        [Pxx, Pyy, Pzz, Pxy, Pxz, Pyz],
        concat_dim=[
            pd.Index(
                ["xx", "yy", "zz", "xy", "xz", "yz"],
                name="space_rank_2",
            ),
        ],
    ).pint.to("pressure_unit")

    # Energy flux
    F_omni = (
        (0.5 * V**4)
        * (f_phi * dtheta).integrate("theta")
        / dtheta.integrate("theta")
        / dphi.integrate("phi")
    ).pint.to("number_flux_unit sr-1")

    return (
        xr.Dataset(
            {
                "N": N,
                "V": V_avg,
                "P": P,
                "F_omni": F_omni,
            },
        )
        .transpose("time", ...)
        .drop("log_V")
        .pint.quantify()
    )

    #  Vx = sign * V * np.sin(theta) * np.cos(phi)
    #  Vy = sign * V * np.sin(theta) * np.sin(phi)
    #  Vz = sign * V * np.cos(theta) * xr.ones_like(phi)
    #  Vx_avg = (f * Vx * dOmega).integrate(dims) / N
    #  Vy_avg = (f * Vy * dOmega).integrate(dims) / N
    #  Vz_avg = (f * Vz * dOmega).integrate(dims) / N
    #  V_avg = xr.combine_nested(
    #      [Vx_avg, Vy_avg, Vz_avg],
    #      concat_dim=[pd.Index(["x", "y", "z"], name="space_rank_1")],
    #  ).pint.to("velocity_unit")


#  def integrate_distribution(f: xr.DataArray, flip_direction: bool = True):
#      f = f.pint.quantify().pint.to("phase_space_density_unit").fillna(0.0)
#
#      # ---- Prepare support
#      # Convert energy to speed
#      W = f.W * u(f.W.units).to("energy_unit")
#      V = xr.DataArray(
#          data=W.data.to("velocity_unit", f.species.name),
#          coords=W.coords,
#      )
#      log_V = np.log10(V.pint.dequantify())
#      f = f.assign_coords(log_V=log_V)
#
#      # Convert angles to radians
#      f = f.assign_coords(
#          theta=(f.theta * u(f.theta.units).to("rad")).pint.dequantify(),
#          phi=(f.phi * u(f.phi.units).to("rad")).pint.dequantify(),
#      )
#
#      # Calculate solid angle
#      theta = f.theta
#      phi = f.phi
#      dOmega = V**3 * np.log(10) * np.sin(theta) * xr.ones_like(phi)
#
#      # ---- Integrate
#      dims = ("phi", "theta", "log_V")
#
#      # Density
#      N = (f * dOmega).integrate(dims)
#      N = xr.where(N != 0.0, N, np.nan).pint.to("number_density_unit")
#
#      # Velocity
#      sign = -1 if flip_direction else 1
#      Vx = sign * V * np.sin(theta) * np.cos(phi)
#      Vy = sign * V * np.sin(theta) * np.sin(phi)
#      Vz = sign * V * np.cos(theta) * xr.ones_like(phi)
#      Vx_avg = (f * Vx * dOmega).integrate(dims) / N
#      Vy_avg = (f * Vy * dOmega).integrate(dims) / N
#      Vz_avg = (f * Vz * dOmega).integrate(dims) / N
#      V_avg = xr.combine_nested(
#          [Vx_avg, Vy_avg, Vz_avg],
#          concat_dim=[pd.Index(["x", "y", "z"], name="space_rank_1")],
#      ).pint.to("velocity_unit")
#
#      # Pressure tensor
#      mass = f.species.mass
#      Pxx = (
#          mass * (f * Vx * Vx * dOmega).integrate(dims)
#          - mass * N * Vx_avg * Vx_avg
#      )
#      Pyy = (
#          mass * (f * Vy * Vy * dOmega).integrate(dims)
#          - mass * N * Vy_avg * Vy_avg
#      )
#      Pzz = (
#          mass * (f * Vz * Vz * dOmega).integrate(dims)
#          - mass * N * Vz_avg * Vz_avg
#      )
#      Pxy = (
#          mass * (f * Vx * Vy * dOmega).integrate(dims)
#          - mass * N * Vx_avg * Vy_avg
#      )
#      Pxz = (
#          mass * (f * Vx * Vz * dOmega).integrate(dims)
#          - mass * N * Vx_avg * Vz_avg
#      )
#      Pyz = (
#          mass * (f * Vy * Vz * dOmega).integrate(dims)
#          - mass * N * Vy_avg * Vz_avg
#      )
#      P = xr.combine_nested(
#          [Pxx, Pyy, Pzz, Pxy, Pxz, Pyz],
#          concat_dim=[
#              pd.Index(
#                  ["xx", "yy", "zz", "xy", "xz", "yz"],
#                  name="space_rank_2",
#              ),
#          ],
#      ).pint.to("pressure_unit")
#
#      # Energy flux
#      dims = ("phi", "theta")
#      dOmega = np.sin(theta) * xr.ones_like(phi)
#      F_omni = (0.5 * V**4 * f * dOmega).integrate(dims) / dOmega.integrate(dims)
#      F_omni = F_omni.pint.to("number_flux_unit sr-1")
#
#      return (
#          xr.Dataset(
#              {
#                  "N": N,
#                  "V": V_avg,
#                  "P": P,
#                  "F_omni": F_omni,
#              },
#          )
#          .transpose("time", ...)
#          .drop("log_V")
#          .pint.quantify()
#      )
