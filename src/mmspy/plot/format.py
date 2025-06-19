"""Format `Axes`."""

__all__ = ["format_datetime_labels"]

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
