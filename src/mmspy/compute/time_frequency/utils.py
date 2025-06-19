"""Utilities for this module."""

import numpy as np

from mmspy.types import ArrayLike, NDArray


def pad(
    x: ArrayLike,
    n: int,
    axis: int = -1,
    padtype: str = "right",
) -> tuple[int, NDArray]:
    """Pad an array along a given axis.

    If `n` is the same as the original axis length, do nothing.
    If `n` is smaller than the original axis length, truncate.
    If `n` is larger than the original axis length, pad zeros.

    Parameters
    ----------
    x : array-like
        Input array, can be complex.
    n : int, optional
        Length of the transformed axis of the output.
        If `n` is smaller than the length of the input, the input is cropped.
        If it is larger, the input is padded with zeros. If `n` is not given,
        the length of the input along the axis specified by `axis` is used.
    axis : int, optional
        Axis over which to compute the FFT. If not given, the last axis is
        used.
    padtype : {'right', 'left', 'both'}, optional
        How to zero-pad. Default is 'right', which is the same behavior
        as `np.fft.fft`.

    Returns
    -------
    pad_index : int
        The start index of where to recover the original signal, i.e.,
        ``x = padded_x[pad_index:pad_index + N]``.
    padded_x : ndarray
        The padded signal.

    """
    x = np.asarray(x)
    axis = axis % x.ndim
    N_axis = x.shape[axis]
    if n <= N_axis:
        return 0, x.take(indices=range(n), axis=axis)

    N_pad = n - N_axis
    if padtype == "right":
        pad_index = 0
        pad_width = (0, N_pad)
    elif padtype == "left":
        pad_index = N_pad
        pad_width = (N_pad, 0)
    else:
        pad_index = N_pad // 2
        pad_width = (pad_index, pad_index if N_pad % 2 == 0 else pad_index + 1)

    return (
        pad_index,
        np.pad(
            x,
            [pad_width if i == axis else (0, 0) for i in range(x.ndim)],
        ),
    )
