"""Draw things onto an `Axes` instance."""

__all__ = [
    "draw_arrows",
    "draw_earth",
    "draw_multicolored_line",
    "add_panel_label",
    "add_colorbar",
]

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

from mmspy.types import ArrayLike


def draw_arrows(
    ax: plt.Axes,
    x: ArrayLike,
    y: ArrayLike,
    number_of_arrows: int | None = None,
    color: str = "k",
) -> None:
    """Draws arrows along a path on a given `Axes` instance

    Parameters
    ----------
    ax : `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    x : array_like, shape (n,)
        1D array containing the path's x-coordinates.
    y : array_like, shape (n,)
        1D array containing the path's y-coordinates.
    number_of_arrows : int
        Number of arrows to draw.
    color : str
        Arrow color

    """

    # Pre-process inputs and sanity checks
    x = np.array(x)
    y = np.array(y)
    assert x.ndim == y.ndim == 1, "Input `x` and `y` coordinates must be 1D"

    # Calculate arrow spacing along the path and where to draw them
    data_size = len(x)
    number_of_arrows = (
        data_size // 5 if number_of_arrows is None else number_of_arrows
    )
    spacing = data_size // (number_of_arrows + 1)
    draw_idx = np.arange(spacing, data_size, spacing)

    # Draw arrows on patches
    for i in draw_idx:
        arrow_patch = mpl.patches.FancyArrowPatch(
            (x[i - 1], y[i - 1]),
            (x[i], y[i]),
            arrowstyle="->",
            mutation_scale=20,
            color=color,
        )
        ax.add_patch(arrow_patch)


def draw_earth(
    ax: plt.Axes,
    radius: float = 1,
    number_of_points: int = 50,
    zorder: int = 999,
) -> None:
    """
    Draws the Earth on a given `Axes` instance with shading indicating
    day/night. Dayside is x>0.

    Parameters
    ----------
    ax : `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    radius : float
        The radius of the Earth on the `Axes`.
    number_of_points : int
        The larger the number of points, the smoother the drawn shape.
    zorder : int
        Order on the `Axes`.

    """

    # Nightside
    theta = np.linspace(np.pi / 2, 3 * np.pi / 2, number_of_points)
    Xn = radius * np.cos(theta)
    Yn = radius * np.sin(theta)
    Xn = np.append(Xn, Xn[0])
    Yn = np.append(Yn, Yn[0])

    # Dayside
    theta = np.linspace(-np.pi / 2, np.pi / 2, number_of_points)
    Xd = radius * np.cos(theta)
    Yd = radius * np.sin(theta)
    Xd = np.append(Xd, Xd[0])
    Yd = np.append(Yd, Yd[0])

    # Plot
    ax.plot(Xd, Yd, "-k", zorder=zorder)
    ax.plot(Xn, Yn, "-k", zorder=zorder)
    ax.fill(Xd, Yd, color="w")
    ax.fill(Xn, Yn, color="k")


def draw_multicolored_line(
    ax: plt.Axes,
    x: ArrayLike,
    y: ArrayLike,
    c: ArrayLike,
    cmap: str = "cet_rainbow",
    vmin: float | None = None,
    vmax: float | None = None,
    **kwargs,
) -> mpl.collections.Collection:
    """Draw a colored line on a given `Axes` instance.

    Parameters
    ----------
    ax : `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    x : array_like, shape (n,)
        1D array containing the x-coordinates.
    y : array_like, shape (n,)
        1D array containing the y-coordinates.
    c : array_like, shape (n,)
        1D array containing the colored data.
    cmap : str

    Returns
    -------
    line : `mpl.collections.LineCollection`
        The line collection instance created from drawing all the colored
        segments.

    """

    # Pre-process inputs and sanity checks
    x = np.array(x)
    y = np.array(y)
    c = np.array(c)
    vmin = c.min() if vmin is None else vmin
    vmax = c.max() if vmax is None else vmax
    assert (
        x.ndim == y.ndim == c.ndim == 1
    ), "Input `x` and `y` coordinates and colored data `c` must be 1D"

    # Create points and segments from coordinates
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Create line segments and color them based on `c`
    lc = mpl.collections.LineCollection(
        segments,
        cmap=cmap,
        norm=mpl.colors.Normalize(vmin, vmax),
        **kwargs,
    )
    lc.set_array(c)
    line = ax.add_collection(lc)

    # Automatically set limits to axis
    if len(ax.get_lines()) == 1:
        Lx = x.max() - x.min()
        Ly = y.max() - y.min()
        ax.set_xlim(x.min() - 0.1 * Lx, x.max() + 0.1 * Lx)
        ax.set_ylim(y.min() - 0.1 * Ly, y.max() + 0.1 * Ly)

    return line


def add_panel_label(
    ax: plt.Axes,
    x: float,
    y: float,
    text: str,
    box_format: dict = dict(facecolor="wheat", alpha=0.9),
    **kwargs,
) -> None:
    """Add a boxed text to an `Axes` instance.

    Intended for drawing panel annotations for a figure.

    Parameters
    ----------
    ax : `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    x, y : float
        Location of the text.
    text : str
        Content of the the text.
    box_format : dict
        Formatting of the enclosing box.
    kwargs : dict
        Other options for `Axes.text` method.

    """
    ax.text(x, y, text, transform=ax.transAxes, bbox=box_format, **kwargs)


def add_colorbar(
    ax: plt.Axes,
    where: str = "right",
    pad: float = 0.05,
    size: str = "2%",
) -> plt.Axes:
    """Add colorbar next to a given `Axes` instance.

    See `matplotlib` documentation for `where`, `pad`, and `size` options.

    Parameters
    ----------
    ax : `matplotlib.axes.Axes`
        The `Axes` instance to draw on.
    where : str
        Where to append the colorbar with respective to the `Axes`.
    pad : str
        Padding of the colorbar from the `Axes`.
    size : str
        Size of the colorbar relative to the `Axes`.

    Returns
    -------
    cax : `matplotlib.axes.Axes`
        A child `Axes` instance created relative to the input `Axes` for
        drawing the colorbar.

    """
    divider = make_axes_locatable(ax)
    return divider.append_axes(where, size=size, pad=pad)
