"""Provides chunked implementation of `scipy.signal` filters.

.. todo:: Add test.

"""

__all__ = ["lowpass_filter"]

import numpy as np
import xarray as xr
from scipy.signal import butter
from scipy.signal import sosfilt as _sosfilt
from scipy.signal._arraytools import axis_reverse, axis_slice
from scipy.signal._filter_design import _validate_sos  # type: ignore[attr-defined]
from scipy.signal._signaltools import _validate_pad, _validate_x, sosfilt_zi  # type: ignore[attr-defined]

from mmspy.compute.utils import sampling_information
from mmspy.types import NDArray, Quantity


def sosfilt(
    sos: NDArray,
    x: NDArray,
    chunksize: int | None = None,
    axis: int = -1,
    zi: NDArray | None = None,
) -> NDArray:
    """Unidirectional filter using cascaded second-order sections.

    This implementation is intended to give the same result as
    `scipy.signal.sosfilt`, but it allows for the data to be chunked
    to provide some memory optimization [1]_.

    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. Each row corresponds to a second-order
        section, with the first three columns providing the numerator
        coefficients and the last three providing the denominator
        coefficients.
    x : array_like
        An N-dimensional input array.
    chunksize : int, optional
        The size of each data chunk. If None, ``chunksize`` is set to the
        entire ``axis`` length.
    axis : int, optional
        The axis of the input data array along which to apply the
        linear filter. The filter is applied to each subarray along
        this axis.  Default is -1.
    zi : array_like, optional
        Initial conditions for the cascaded filter delays.  It is a (at
        least 2D) vector of shape ``(n_sections, ..., 2, ...)``, where
        ``..., 2, ...`` denotes the shape of `x`, but with ``x.shape[axis]``
        replaced by 2.  If `zi` is None or is not given then initial rest
        (i.e. all zeros) is assumed.
        Note that these initial conditions are *not* the same as the initial
        conditions given by `lfiltic` or `lfilter_zi`.

    Returns
    -------
    y : ndarray
        The output of the digital filter.

    References
    ----------
    .. [1] https://dsp.stackexchange.com/a/73942

    """
    x = _validate_x(x)
    sos, n_sections = _validate_sos(sos)

    # Calculate the initial conditions
    if zi is None:
        # Shape (n_sections, 2) --> (n_sections, ..., 2, ...)
        zi = sosfilt_zi(sos)
        zi_shape = [1] * x.ndim
        zi_shape[axis] = 2
        zi.shape = [n_sections, *zi_shape]
        x_0 = axis_slice(x, stop=1, axis=axis)
        zi = x_0 * zi

    # Calculate chunked data
    chunksize = x.shape[axis] if chunksize is None else chunksize
    x_chunks = np.array_split(x, x.shape[axis] // chunksize)
    for i, chunk in enumerate(x_chunks):
        x_chunks[i], zi = _sosfilt(sos, chunk, zi=zi, axis=axis)

    return np.concat(x_chunks, axis=axis)


def sosfiltfilt(  # noqa: PLR0913
    sos: NDArray,
    x: NDArray,
    chunksize: int | None = None,
    axis: int = -1,
    padtype: str | None = "odd",
    padlen: int | None = None,
) -> NDArray:
    """Bidirectional filter using cascaded second-order sections.

    This implementation is intended to give the same result as
    `scipy.signal.sosfiltfilt`, but it allows for the data to be chunked
    to provide some memory optimization [1]_.

    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. Each row corresponds to a second-order
        section, with the first three columns providing the numerator
        coefficients and the last three providing the denominator
        coefficients.
    x : array_like
        An N-dimensional input array.
    chunksize : int, optional
        The size of each data chunk. If None, ``chunksize`` is set to the
        entire ``axis`` length.
    axis : int, optional
        The axis of the input data array along which to apply the
        linear filter. The filter is applied to each subarray along
        this axis.  Default is -1.
    padtype : {'odd', 'even', 'constant'}, optional
        This determines the type of extension to use for the padded signal
        to which the filter is applied.  If ``padtype`` is None,
        no padding is used.  The default is 'odd'.
    padlen : int, optional
        The number of elements by which to extend ``x`` at both ends of
        ``axis`` before applying the filter.  This value must be less than
        ``x.shape[axis] - 1``.  ``padlen=0`` implies no padding.
        The default value is::

            3 * (2 * len(sos) + 1 - min((sos[:, 2] == 0).sum(),
                                        (sos[:, 5] == 0).sum()))

        The extra subtraction at the end attempts to compensate for poles
        and zeros at the origin (e.g. for odd-order filters) to yield
        equivalent estimates of ``padlen`` to those of `filtfilt` for
        second-order section filters built with `scipy.signal` functions.

    Returns
    -------
    y : ndarray
        The filtered output with the same shape as ``x``.

    References
    ----------
    .. [1] https://dsp.stackexchange.com/a/73942

    """
    x = _validate_x(x)
    sos, n_sections = _validate_sos(sos)

    # If data is padded...
    ntaps = 2 * n_sections + 1
    ntaps -= min((sos[:, 2] == 0).sum(), (sos[:, 5] == 0).sum())
    edge, ext = _validate_pad(padtype, padlen, x, axis, ntaps=ntaps)

    chunksize = ext.shape[axis] if chunksize is None else chunksize

    # Calculate initial conditions
    zi = sosfilt_zi(sos)
    # Shape (n_sections, 2) --> (n_sections, ..., 2, ...)
    zi_shape = [1] * x.ndim
    zi_shape[axis] = 2
    zi.shape = [n_sections, *zi_shape]

    # -- Apply filters
    fkw = {"chunksize": chunksize, "axis": axis}
    # Forward
    x_0 = axis_slice(ext, stop=1, axis=axis)
    y = sosfilt(sos, ext, zi=x_0 * zi, **fkw)
    # Backward
    y_0 = axis_slice(y, start=-1, axis=axis)
    y = sosfilt(sos, axis_reverse(y, axis=axis), zi=y_0 * zi, **fkw)

    # Flip data back to original order
    y = axis_reverse(y, axis=axis)
    if edge > 0:
        y = axis_slice(y, start=edge, stop=-edge, axis=axis)

    return y


def lowpass_filter(
    array: xr.DataArray,
    frequency: Quantity,
    order: int = 10,
) -> xr.DataArray:
    """Appy low-pass filter to array."""
    array = array.pint.dequantify()
    fs = sampling_information(array.time)["frequency"]
    sos = butter(
        order,
        frequency.to("Hz").magnitude,
        output="sos",
        fs=float(fs.to("Hz").magnitude),
    )
    return xr.DataArray(
        data=sosfiltfilt(
            sos,
            array.fillna(0.0).data,
            chunksize=2 * int(fs / frequency),
            padtype="constant",
            padlen=array.time.size - 1,
            axis=0,
        ),
        coords=array.coords,
        attrs={"filter_frequency": str(frequency), **array.attrs},
    ).pint.quantify()
