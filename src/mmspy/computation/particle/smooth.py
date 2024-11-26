import numpy as np
import xarray as xr
from astropy.convolution import Gaussian2DKernel, convolve
from numpy.typing import NDArray


def _smooth_chunk(
    data_chunk: NDArray,
    dimensions: int,
    sigma: float,
    kwargs: dict,
) -> NDArray:
    match dimensions:
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

    data_chunk = data_chunk.squeeze()
    return convolve(data_chunk, kernel, **kwargs)[np.newaxis, ...]


def smooth_distribution(
    da: xr.DataArray,
    sigma: float = 1.0,
    kwargs: dict = {"boundary": "extend", "nan_treatment": "interpolate"},
) -> xr.DataArray:
    r"""Apply a smoothing kernel on a distribution function.

    Parameters
    ----------
    da : DataArray
        Xarray data array.
    sigma : float
        How large the kernel is, only applicable for 2D distribution.
    kwargs : dict
        Additional keywords for `~astropy.convolution.convolve`.

    Returns
    -------
    smoothed_da : DataArray
        Smoothed data array

    """
    da = da.copy()
    if "time" not in da.dims:
        da = da.expand_dims("time")

    dimensions = len([dim for dim in da.dims if dim != "time"])

    da = da.chunk(time=1)
    return xr.DataArray(
        name=da.name,
        data=da.data.map_blocks(
            _smooth_chunk,
            dimensions,
            sigma,
            kwargs,
            meta=np.array((), dtype=da.dtype),
        ),
        coords=da.coords,
        attrs=da.attrs,
    )
