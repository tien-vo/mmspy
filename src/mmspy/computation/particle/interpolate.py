import numpy as np
import xarray as xr
from numpy.typing import NDArray
from scipy.interpolate import griddata
from scipy.spatial._qhull import QhullError

from mmspy.computation.particle.grid import ParticleGrid


def _precondition_dataset(ds: xr.Dataset) -> xr.Dataset:
    r"""Convert units and turn phase space density and energy to log scale."""
    ds = ds.pint.quantify()

    f = ds.f.pint.to("phase_space_density_unit").pint.dequantify()
    ds = ds.assign(f=np.log10(xr.where(f > 0.0, f, np.nan)))

    W = ds.W.pint.to("energy_unit").pint.dequantify()
    ds = ds.assign(W=np.log10(xr.where(W > 0.0, W, np.nan)))

    ds = ds.assign(theta=ds.theta.pint.to("angle_unit"))
    if "phi" in ds:
        ds = ds.assign(phi=ds.phi.pint.to("angle_unit"))

    return ds.pint.dequantify()


def _histogram(
    coord: NDArray,
    value: NDArray,
    mode: str,
    bins: tuple[NDArray, ...],
) -> NDArray:
    r""".. todo:: Add docstring."""
    N = np.histogramdd(coord, bins=bins)[0]
    N[N == 0] = np.nan

    match mode:
        case "absolute":
            weight = np.histogramdd(coord, bins=bins, weights=value)[0]
            f = weight / N
        case "error":
            # This is average in log scale. Must rederive the error!
            weight = np.histogramdd(coord, bins=bins, weights=value**2)[0]
            f = np.sqrt(weight / N**2)
        case _:
            msg = f"Expected {mode!r} to be one of {{'absolute', 'error'}}"
            raise ValueError(msg)

    return f


def _scipy(
    coord: NDArray,
    value: NDArray,
    method: str,
    new_coords: tuple[NDArray, ...],
) -> NDArray:
    r""".. todo:: Add docstring."""
    # Calculate results and mask out-of-bound data
    kw = {"points": coord, "values": value, "xi": new_coords}
    results = griddata(method=method, **kw)

    # Mask data outside valid energy range
    log_W_grid = new_coords[0].squeeze()
    log_W_min = np.nanmin(coord[:, 0])
    log_W_max = np.nanmax(coord[:, 0])
    out_of_bound = (log_W_grid > log_W_max) | (log_W_grid < log_W_min)
    results[out_of_bound, :] = np.nan

    return results


def _interpolate_chunk(  # noqa: PLR0913
    data_chunk: NDArray,
    grid: ParticleGrid,
    mode: str,
    method: str,
    chunks: tuple[int, ...],
    keep_nan: bool,
) -> NDArray:
    r""".. todo:: Add docstring."""
    # Reshape data chunk so that the last axis are the variables
    number_of_variables = len(chunks)
    data_chunk = data_chunk.squeeze()
    data_chunk = data_chunk.reshape(
        data_chunk.size // number_of_variables,
        number_of_variables,
    )

    # Unpack values and coordinates
    value = data_chunk[:, 0]
    coord = data_chunk[:, 1:]

    # Filter bad coordinates
    good_coord = np.isfinite(coord).all(axis=1)
    value = value[good_coord]
    coord = coord[good_coord, ...]

    # Handle exception when there is no good data
    good_data = np.isfinite(value)
    if np.sum(good_data) == 0:
        return np.nan * np.ones(chunks)

    # Filter bad data
    value = value if keep_nan else value[good_data]
    coord = coord if keep_nan else coord[good_data, ...]

    match method:
        case "histogram":
            results = _histogram(
                coord,
                value,
                mode,
                grid.get_bins(number_of_variables - 1),
            )
        case "nearest" | "linear" | "cubic":
            try:
                results = _scipy(
                    coord,
                    value,
                    method,
                    grid.get_grids(number_of_variables - 1),
                )
            except QhullError:
                results = np.nan * np.ones(chunks)

    return results[np.newaxis, ...]


def interpolate_distribution(
    ds: xr.Dataset,
    grid: ParticleGrid = ParticleGrid(),
    mode: str = "absolute",
    method: str = "histogram",
    keep_nan: bool = False,
) -> xr.DataArray:
    r""".. todo:: Add docstring."""
    ds = _precondition_dataset(ds)

    # Prepare metadata for map_blocks
    is_3d = "phi" in ds
    chunks = (1, *grid.shape) if is_3d else (1, *grid.shape[:2])
    coords = {
        "time": ds.time,
        "W": grid.energy_array.magnitude,
        "theta": grid.zenith_array.magnitude,
    }
    if is_3d:
        coords["phi"] = grid.azimuth_array.magnitude

    # Stack values and coordinates into samples
    f = ds.stack(sample=[d for d in ds.dims if d != "time"]).to_dataarray()
    if "time" not in f.dims:
        f = f.expand_dims("time")

    f = f.transpose("time", "sample", "variable").chunk(time=1)
    f = xr.DataArray(
        name="f",
        data=10.0
        ** f.data.map_blocks(
            _interpolate_chunk,
            grid,
            mode,
            method,
            chunks,
            keep_nan,
            meta=np.array((), dtype=f.dtype),
            chunks=chunks,
            drop_axis=(1, 2),
            new_axis=(1, 2, 3) if is_3d else (1, 2),
        ),
        coords=coords,
        attrs=ds.f.attrs,
    ).squeeze()

    # Populate attributes
    f.W.attrs.update(units="energy_unit")
    f.theta.attrs.update(units="angle_unit")
    if is_3d:
        f.phi.attrs.update(units="angle_unit")

    return f.pint.quantify()
