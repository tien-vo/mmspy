"""Provide interpolation methods for the distribution function."""

import numpy as np
import xarray as xr
from scipy.interpolate import griddata
from scipy.spatial._qhull import QhullError
from scipy.stats import binned_statistic_dd

from mmspy.compute.particle.grid import ParticleGrid
from mmspy.types import Callable, NDArray


def propagate_error(error: NDArray) -> float:
    """Propagate error for `binned_statistic_dd`."""
    if (count := len(error)) == 0:
        return np.nan
    return np.sqrt(np.nansum(error**2)) / count


def process_chunk(  # noqa: PLR0913
    data_chunk: NDArray,
    method: str,
    statistic: str,
    grid_center: list[NDArray],
    grid_edge: list[NDArray],
    grid_shape: list[int],
) -> NDArray:
    """Interpolate a ``data_chunk`` onto a regular grid.

    Parameters
    ----------
    data_chunk : ndarray (1, n, d+1)
        A chunked data block containing ``n`` samples. The first index
        of the last axis is the values and the rest the corresponding
        ``d``-dimensional coordinates.
    method : {'histogram', 'nearest', 'linear', 'cubic'}
        Method of interpolation. 'histogram' is performed with
        `scipy.stats.binned_statistics_dd`. Other methods are performed
        with `scipy.interpolate.griddata`.
    statistic : {'mean', 'std', `propagate_error`}
        This option is only available for ``method='histogram'``. It is
        used to calculate the weighted mean, spread (std), and to
        propagate error in each histogram bin.
    grid_center : tuple of ndarray
        Center points of the grid
    grid_edge : tuple of ndarray
        Edges of the grid, including the left-most and right-most
        boundaries.
    grid_shape : tuple of int
        Shape of the grid

    Returns
    -------
    results : ndarray (1, grid_shape)
        Interpolation result.

    """
    # Filter invalid data
    data_chunk = data_chunk.squeeze()
    valid = np.isfinite(data_chunk).all(axis=1)
    if np.sum(valid) == 0:
        return np.zeros((1, *grid_shape))

    # Unpack valid data
    data_chunk = data_chunk[valid, ...]
    value = data_chunk[:, 0]
    coord = data_chunk[:, 1:]

    # Calculate statistics
    match method:
        case "histogram":
            results = binned_statistic_dd(
                sample=coord,
                values=value,
                statistic=statistic,
                bins=grid_edge,
            )[0]
        case "nearest" | "linear" | "cubic":
            try:
                results = griddata(
                    points=coord,
                    values=value,
                    method=method,
                    xi=np.meshgrid(*grid_center, indexing="ij"),
                    fill_value=0.0,
                )
            except QhullError:
                results = np.zeros(grid_shape)
    return np.nan_to_num(results)[np.newaxis, ...]


def interpolate_distribution(
    ds: xr.Dataset,
    grid: dict[str, ParticleGrid],
    variable: str = "f",
    mode: str = "mean",
    method: str = "histogram",
) -> xr.DataArray:
    """Interpolate a particle distribution function onto a regular grid.

    Parameters
    ----------
    ds : Dataset
        Dataset containing the ``variable`` and the coordinates used to
        interpolate.
    grid : dict of ParticleGrid
        Dictionary containing the coordinates (keys) and the
        regular grid (values) used for interpolation.
    variable : str
        Variable used for interpolation.
    mode : {'mean', 'spread', 'error'}
        Only applicable for ``method='histogram'``. Use 'mean' to
        calculate the mean of the ``variable`` in each bin, 'spread'
        to calculate its standard deviation, and 'error' to propagate
        error.
    method : {'histogram', 'nearest', 'linear', 'cubic'}
        Method of interpolation. 'histogram' is performed with
        `scipy.stats.binned_statistics_dd`. Other methods are performed
        with `scipy.interpolate.griddata`.

    Returns
    -------
    da : DataArray
        Interpolated data array defined on ``grid``.

    """
    # Remove irrelevant variables in the dataset.
    coordinates = grid.keys()
    ds = ds.pint.quantify().reset_coords()[[variable, *coordinates]]

    # Ensure the coordinates in the dataset have the same units as the grid.
    for coordinate in coordinates:
        ds[coordinate].data = ds[coordinate].data.to(grid[coordinate].units)

    # Stack (value, coordinates) into a data array
    ds = ds.pint.dequantify()
    ds = ds.stack(sample=[dim for dim in ds.dims if dim != "time"])
    da = ds.to_dataarray()
    if "time" not in da.dims:
        da = da.expand_dims("time")
    da = da.chunk(time=1).transpose("time", "sample", "variable")

    # Define metadata for block mapping
    grid_center = [item.center.magnitude for item in grid.values()]
    grid_edge = [item.edge.magnitude for item in grid.values()]
    grid_shape = [item.size for item in grid.values()]
    new_coordinates = {"time": da.time} | {
        item.name: np.arange(item.size) if item.index is None else item.index
        for item in grid.values()
    }

    statistic: str | Callable
    match mode:
        case "mean":
            statistic = "mean"
        case "spread":
            statistic = "std"
        case "error":
            statistic = propagate_error
        case _:
            msg = (
                f"Expected {mode!r} to be one of "
                "{'mean', 'spread', 'error'}"
            )
            raise ValueError(msg)

    return (
        xr.DataArray(
            name=variable,
            data=da.data.map_blocks(
                process_chunk,
                method,
                statistic,
                grid_center,
                grid_edge,
                grid_shape,
                meta=np.array((), dtype=ds[variable].dtype),
                drop_axis=(1, 2),
                new_axis=tuple(range(1, len(grid_shape) + 1)),
                chunks=(1, *grid_shape),
            ),
            coords=new_coordinates,
        )
        .squeeze()
        .reset_coords(drop=True)
        .pint.quantify(ds[variable].attrs["units"])
        .assign_coords(
            {key: (item.name, item.center) for key, item in grid.items()},
        )
    )
