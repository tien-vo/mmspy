import numpy as np
import xarray as xr


def _precondition_dataset(ds: xr.Dataset) -> xr.Dataset:
    r"""Precondition the input distribution function for integration.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset containing the distribution function ``ds.f`` defined
        on (``W``, ``theta``, ``phi``) coordinates.

    Returns
    -------
    ds : xr.Dataset
        The original dataset with (1) variables converted to standard
        units, (2) energy converted to (log) speed, (3) angles converted
        to radians. If the error ``ds.f_err`` is present, gyroscopic
        filtering will be applied to ``ds.f``.

    """
    ds = ds.pint.quantify()
    species = ds.f.species.name

    # ---- Conversions
    # -- Phase space density and error
    ds["f"] = ds.f.pint.to("phase_space_density_unit").fillna(0.0)
    if "f_err" in ds:
        ds["f_err"] = ds.f_err.pint.to("phase_space_density_unit").fillna(0.0)

    # -- Support
    ds["V"] = (ds.W.dims, ds.W.data.to("velocity_unit", species))
    ds["log_V"] = np.log10(ds.V.pint.dequantify())
    ds["theta"] = ds.theta.pint.to("rad")
    ds["dV"] = ds.V**3 * np.log(10)
    ds["dtheta"] = np.sin(ds.theta) * ds.theta.pint.units
    if "phi" in ds:
        ds["phi"] = ds.phi.pint.to("rad")
        ds["dphi"] = xr.ones_like(ds.phi) * ds.phi.pint.units

    return ds.set_coords(
        ["V", "log_V", "theta"] + (["phi"] if "phi" in ds else []),
    )
