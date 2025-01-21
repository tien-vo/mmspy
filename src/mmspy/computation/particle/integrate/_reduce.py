import numpy as np
import xarray as xr

from mmspy.computation.particle.integrate._utils import _precondition_dataset


def _phi_average(ds, threshold):
    f = ds.f
    phi = ds.phi
    dphi = ds.dphi
    f_phi = (f * dphi).integrate("phi")
    fx_phi = (f * np.cos(phi) * dphi).integrate("phi")
    fy_phi = (f * np.sin(phi) * dphi).integrate("phi")
    fxx_phi = (f * np.cos(phi) ** 2 * dphi).integrate("phi")
    fyy_phi = (f * np.sin(phi) ** 2 * dphi).integrate("phi")
    fxy_phi = (f * np.sin(phi) * np.cos(phi) * dphi).integrate("phi")

    if "f_err" in ds:
        f_err_phi = np.sqrt((ds.f_err**2 * dphi).integrate("phi"))
        mask = f_phi > threshold * f_err_phi
        f_phi = xr.where(mask, f_phi, 0.0)
        fx_phi = xr.where(mask, fx_phi, 0.0)
        fy_phi = xr.where(mask, fy_phi, 0.0)
        fxx_phi = xr.where(mask, fxx_phi, 0.0)
        fyy_phi = xr.where(mask, fyy_phi, 0.0)
        fxy_phi = xr.where(mask, fxy_phi, 0.0)

    return xr.Dataset(
        {
            "f_phi": f_phi,
            "fx_phi": fx_phi,
            "fy_phi": fy_phi,
            "fxx_phi": fxx_phi,
            "fyy_phi": fyy_phi,
            "fxy_phi": fxy_phi,
        },
    ).pint.quantify()


def reduce_distribution(
    ds: xr.Dataset,
    flip_direction: bool = True,
    threshold: float = 1.0,
) -> xr.Dataset:
    ds = _precondition_dataset(ds)
    #   ds_avg = _phi_average(ds, threshold)

    #   V = ds_avg.V
    #   f_phi = ds_avg.f_phi
    #   dphi = ds.dphi
    #   dtheta = ds.dtheta

    #   j_2d = (0.5 * V**4 * f_phi) / dphi.integrate("phi")
    #   j_omni = (j_2d * dtheta).integrate("theta") / dtheta.integrate("theta")
    #   return xr.Dataset(
    #       {
    #           "j_2d": j_2d,
    #           "j_omni": j_omni,
    #       }
    #   ).pint.to("number_flux_unit")
