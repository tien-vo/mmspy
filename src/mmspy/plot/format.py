"""Format `Axes`."""

__all__ = [
    "format_datetime_labels",
    "format_ybins",
    "autoformat",
]

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from mmspy.types import Any


def format_datetime_labels(ax: Any) -> None:
    """Format the labels for plots with `numpy.datetime64` abscissa.

    Parameter
    ---------
    ax : `~matplotlib.axes.Axes` or array of Axes
        An `Axes` instance or an array of them

    """
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    if isinstance(ax, plt.Axes):
        ax.xaxis.set_major_formatter(formatter)
    else:
        for index in np.ndindex(ax.shape):
            ax[index].xaxis.set_major_formatter(formatter)


def format_ybins(ax: Any) -> None:
    if isinstance(ax, plt.Axes):
        if ax.get_yscale() != "log":
            ax.locator_params(axis="y", nbins=5)
            return
    for index in np.ndindex(ax.shape):
        if ax[index].get_yscale() != "log":
            ax[index].locator_params(axis="y", nbins=5)


def autoformat(ax: Any) -> None:
    format_datetime_labels(ax)
    format_ybins(ax)
