"""Format `Axes`."""

__all__ = [
    "format_datetime_labels",
    "format_ticks",
    "autoformat",
]

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

from mmspy.types import Any, Sequence


def format_datetime_labels(
    ax: plt.Axes | Sequence[plt.Axes],
    max_ticks: int = 5,
) -> None:
    """Format the labels for plots with `numpy.datetime64` abscissa.

    Parameter
    ---------
    ax : `~matplotlib.axes.Axes` or sequence of Axes
        An `Axes` instance or a sequence of them
    max_ticks : int
        Maximum number of ticks.

    """
    if not isinstance(ax, plt.Axes):
        if len(ax) == 0:
            return

        format_datetime_labels(ax[0])
        format_datetime_labels(ax[1:])
        return

    if not isinstance(ax.xaxis.get_major_locator(), mdates.AutoDateLocator):
        return

    locator = mdates.AutoDateLocator(maxticks=max_ticks)
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)


def format_ticks(
    ax: plt.Axes | Sequence[plt.Axes],
    max_ticks: int = 5,
) -> None:
    """Fix the number of ticks for linear axes.

    Parameter
    ---------
    ax : `~matplotlib.axes.Axes` or sequence of Axes
        An `Axes` instance or a sequence of them
    max_ticks : int
        Maximum number of ticks.

    """
    if not isinstance(ax, plt.Axes):
        if len(ax) == 0:
            return

        format_ticks(ax[0], max_ticks)
        format_ticks(ax[1:], max_ticks)
        return

    if ax.get_xscale() == "linear" and not isinstance(
        ax.xaxis.get_major_locator(),
        mdates.AutoDateLocator,
    ):
        ax.locator_params(axis="x", nbins=max_ticks)

    if ax.get_yscale() == "linear":
        ax.locator_params(axis="y", nbins=max_ticks)


def autoformat(ax: Any, max_ticks=5) -> None:
    format_ticks(ax, max_ticks)
    format_datetime_labels(ax, max_ticks)
