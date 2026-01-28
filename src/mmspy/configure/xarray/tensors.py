"""Define accessors for tensorial xarray objects."""

__all__ = ["TensorAccessor"]


import xarray as xr

from mmspy.compute.vector import vector_norm


@xr.register_dataarray_accessor("tensor")
class TensorAccessor:
    """Accessor for rank-n tensors."""

    def __init__(self, tensor: xr.DataArray) -> None:
        """Entry to tensor accessor.

        Parameters
        ----------
        tensor : DataArray or Dataset
            Xarray object with a `rank_*` dimension

        """
        self._tensor = tensor
        # Extract rank
        ranks = [
            int(str(dimension).strip("rank_"))
            for dimension in tensor.dims
            if str(dimension).startswith("rank_")
        ]
        self._rank = 0 if len(ranks) == 0 else min(ranks)

    def __call__(self) -> xr.DataArray:
        """Return the object as a tensor."""
        match self._rank:
            case 0:
                return self._tensor
            case 1:
                return self._tensor.rename(rank_1="j")
            case 2:
                xx = self._tensor.sel(rank_2="xx", drop=True)
                yy = self._tensor.sel(rank_2="yy", drop=True)
                zz = self._tensor.sel(rank_2="zz", drop=True)
                xy = self._tensor.sel(rank_2="xy", drop=True)
                xz = self._tensor.sel(rank_2="xz", drop=True)
                yz = self._tensor.sel(rank_2="yz", drop=True)
                return (
                    xr.combine_nested(
                        [[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]],
                        concat_dim=[
                            "i",
                            "j",
                            # pd.Index(["x", "y", "z"], name="i"),
                            # pd.Index(["x", "y", "z"], name="j"),
                        ],
                    )
                    .assign_coords(i=["x", "y", "z"], j=["x", "y", "z"])
                    .transpose(..., "i", "j")
                )
            case _:
                msg = "Currently only supporting rank 0, 1 and 2."
                raise NotImplementedError(msg)

    @property
    def magnitude(self) -> xr.DataArray:
        """Return the magnitude of the tensor."""
        match self._rank:
            case 0:
                return self._tensor
            case 1:
                return vector_norm(self._tensor, dim="rank_1")
            case _:
                msg = "Currently only supporting rank 0 and 1."
                raise NotImplementedError(msg)
