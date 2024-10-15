r"""Define accessors for tensorial xarray objects."""

__all__ = [
    "RankOneAccessor",
    "RankTwoAccessor",
]


import pandas as pd
import xarray as xr

from mmspy.computation.vector import vector_norm


@xr.register_dataarray_accessor("rank_1")
@xr.register_dataset_accessor("rank_1")
class RankOneAccessor:
    r"""Accessor for rank-1 tensors (n-d vectors)."""

    def __init__(self, vector: xr.DataArray) -> None:
        r"""Entry to rank_1 accessor.

        Parameters
        ----------
        vector : DataArray
            Xarray object with a `space_rank_1` dimension

        """
        if "space_rank_1" not in vector.dims:
            msg = "Cannot find a `space_rank_1` dimension."
            raise ValueError(msg)

        self._vector = vector

    @property
    def tensor(self) -> xr.DataArray:
        r"""Return the object as a column vector."""
        return self._vector.rename(space_rank_1="space_j")

    @property
    def magnitude(self) -> xr.DataArray:
        r"""Return the magnitude of the vector."""
        return vector_norm(self._vector, dim="space_rank_1")

    def component(self, component: str) -> xr.DataArray:
        r"""Return the component of the vector."""
        return self._vector.sel(space_rank_1=component)


@xr.register_dataarray_accessor("rank_2")
@xr.register_dataset_accessor("rank_2")
class RankTwoAccessor:
    r"""Accessor for rank-2 tensors (mxn matrices)."""

    def __init__(self, matrix: xr.DataArray) -> None:
        r"""Entry to rank_2 accessor.

        Parameters
        ----------
        matrix : DataArray
            Xarray object with a `space_rank_2` dimension

        """
        if "space_rank_2" not in matrix.dims:
            msg = "Cannot find a `space_rank_2` dimension."
            raise ValueError(msg)

        self._matrix = matrix

    @property
    def tensor(self) -> xr.DataArray:
        r"""Return the object as a matrix."""
        xx = self._matrix.sel(space_rank_2="xx")
        yy = self._matrix.sel(space_rank_2="yy")
        zz = self._matrix.sel(space_rank_2="zz")
        xy = self._matrix.sel(space_rank_2="xy")
        xz = self._matrix.sel(space_rank_2="xz")
        yz = self._matrix.sel(space_rank_2="yz")
        return xr.DataArray(
            xr.combine_nested(
                [[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]],
                concat_dim=[
                    pd.Index(["x", "y", "z"], name="space_i"),
                    pd.Index(["x", "y", "z"], name="space_j"),
                ],
                combine_attrs="identical",
            )
            .drop_vars("space_rank_2")
            .transpose(..., "space_i", "space_j"),
        )

    def component(self, component: str) -> xr.DataArray:
        r"""Return the component of the vector."""
        return self._matrix.sel(space_rank_2=component)
